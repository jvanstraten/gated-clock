import requests
import zipfile
import csv
import os
import time
import collections
import datetime
import itertools

script_dir = os.path.dirname(os.path.realpath(__file__))

# Download timezone database.
timezonedb_fname = script_dir + '/cache/timezonedb.csv.zip'
timezonedb_url = 'https://timezonedb.com/files/timezonedb.csv.zip'
if not os.path.isfile(timezonedb_fname) or time.time() - os.stat(timezonedb_fname).st_mtime > 60*60*24:
    if not os.path.isdir('cache'):
        os.mkdir('cache')
    print('downloading ' + timezonedb_url + ' to ' + timezonedb_fname + '...')
    data = requests.get(timezonedb_url).content
    with open(timezonedb_fname, 'wb') as f:
        f.write(data)
else:
    print(timezonedb_fname + ' is up to date')

# Parse the ZIP/CSV archive into something remotely Pythonic.
print('parsing ' + timezonedb_fname + '...')
with open(timezonedb_fname, 'rb') as f:
    with zipfile.ZipFile(f) as zf:
        with zf.open('country.csv') as zfi:
            countries = dict(csv.reader(map(lambda x: x.decode('utf8'), zfi)))
        with zf.open('zone.csv') as zfi:
            def combine(country, path):
                path = path.split('/')
                path.insert(1, country)
                return '/'.join(path)
            Zone = collections.namedtuple('Zone', ['name', 'offsets'])
            zone_dict = dict(map(lambda x: (int(x[0]), Zone(combine(countries[x[1]], x[2]), [])), csv.reader(map(lambda x: x.decode('utf8'), zfi))))
        with zf.open('timezone.csv') as zfi:
            Offset = collections.namedtuple('Offset', ['start', 'offset', 'dst'])
            for zone, name, ts, off, dst in csv.reader(map(lambda x: x.decode('utf8'), zfi)):
                zone = int(zone)
                ts = int(ts)
                off = int(off)
                dst = bool(int(dst))
                zone_dict[zone].offsets.append(Offset(ts, off, dst))

# Strip unnecessary data.
print('compressing...')
strip_before = time.time() - 60*60*24*356
strip_after = time.time() + 60*60*24*356*50
locations = []
zones = []
zone_map = {}
for location, offsets in sorted(zone_dict.values()):
    offsets.sort()
    for i in range(2, len(offsets)):
        if offsets[i].start > strip_before:
            del offsets[:i-1]
            break
    else:
        del offsets[:-1]
    for i in range(0, len(offsets)):
        if offsets[i].start > strip_after:
            del offsets[i:]
            break
    offsets[0] = Offset(0, offsets[0].offset, offsets[0].dst)
    offsets = tuple(offsets)

    if offsets in zone_map:
        zone_index = zone_map[offsets]
    else:
        zone_index = len(zones)
        zones.append(offsets)
        zone_map[offsets] = zone_index
    locations.append((location, zone_index))

# Encode to a list of 32-bit numbers, where each number is built up as follows:
#  - 31..25: y = year (7 bit, offset 2000)
#  - 24..21: m = month (4 bit, offset 1)
#  - 20..16: d = day (5 bit, offset 1)
#  - 15..11: h = hour (5 bit)
#  - 10..9: q = quarter of hour (2 bit)
#  - 8..4: oh = timezone hour (5 bit signed)
#  - 3..2: oq = timezone quarter of hour (2 bit)
#  - 1: d = DST flag
#  - 0: continuation flag
# The date/time indicates the UTC when the offset is to go into effect. The
# timezones are stored sequentially, with offsets encoded ascending by
# date/time. The first offset in each zone is stored with all date/time fields
# zero, allowing the zone boundaries to be easily detected. The end of the list
# is encoded via the LSB. NOTE: some countries seem to think it's a good idea
# to change timezone on weird timestamps that cannot be exactly encoded with
# our quarter-of-an-hour resolution. These are just rounded to nearest.
print('encoding...')
def encode_offset(offset, first):
    dt = datetime.datetime.fromtimestamp(offset.start)
    if first:
        y = 0
        m = 0
        d = 0
        h = 0
        q = 0
    else:
        assert dt.year > 2000
        y = min(max(0, dt.year - 2000), 127)
        m = dt.month - 1
        d = dt.day - 1
        h = dt.hour
        q = int(round(dt.minute / 15))
    oh = offset.offset // (60*60)
    if oh > 15 or oh < -16:
        assert False
    oq = (offset.offset // (15*60)) % 4
    if offset.offset % 15*60:
        assert False
    ds = 1 if offset.dst else 0
    return (
        ((y  & 0x7F) << 25) |
        ((m  & 0x0F) << 21) |
        ((d  & 0x1F) << 16) |
        ((h  & 0x1F) << 11) |
        ((q  & 0x03) << 9) |
        ((oh & 0x1F) << 4) |
        ((oq & 0x03) << 2) |
        ((ds & 0x01) << 1) |
        1
    )
encoded = []
size = 0
for offsets in zones:
    first = True
    prev = 0
    for offset in offsets:
        value = encode_offset(offset, first)
        assert value >= prev
        encoded.append(value)
        first = False
        prev = value
encoded.append(0)
print('encoded size = {} bytes'.format(len(encoded) * 4))

# Write the header file with the data in it.
with open(script_dir + '/timezones.inc', 'w') as f:
    f.write('static const uint32_t TIMEZONES[{}] = {{\n'.format(len(encoded)))
    for word in encoded[:-1]:
        f.write('    0x{:08X},\n'.format(word))
    f.write('    0x{:08X}\n'.format(encoded[-1]))
    f.write('};\n')

# Write documentation as appropriate.
with open(script_dir + '/../timezones.md', 'w') as f:
    f.write("""
# Timezone data

The clock is capable of automatic time synchronization and DST adjustment via
GPS. It's not, however, smart enough to automatically deduce your timezone from
the GPS coordinates... the database for this would simply be too large for the
Teensy LC. So, if you want to use this feature, you'll have to configure which
zone you're in. To keep things simple for the firmware, this is done by a zone
index, that you'll have to look up in the following list yourself.
""")
    prev_path = []
    for location, index in locations:
        path = [x[0] for x in itertools.groupby(location.split('/', maxsplit=2))]
        different = False
        for idx, (prev, cur) in enumerate(itertools.zip_longest(prev_path, path)):
            if cur is None:
                break
            if prev != cur:
                different = True
            if different:
                if idx == len(path) - 1:
                    f.write(' - {0}: [{1}](#zone-index-{1})\n'.format(cur, index + 1))
                else:
                    f.write('\n{} {}\n\n'.format('#' * (idx + 2), cur))
        prev_path = path
    f.write("""
## Zone data

The data associated with each zone index is shown below.
""")
    index = 0
    for value in encoded:
        if not value:
            break
        oh = (value >> 4) & 0x1F
        if oh & 0x10:
            oh -= 0x20
        oq = (value >> 2) & 0x03
        ds = (value >> 1) & 0x01
        if (value >> 9) == 0:
            index += 1
            f.write('\n## Zone index {}\n\n - Initial offset: '.format(index))
        else:
            y = (value >> 25) & 0x7F
            m = (value >> 21) & 0x0F
            d = (value >> 16) & 0x1F
            h = (value >> 11) & 0x1F
            q = (value >> 9) & 0x03
            f.write(' - From {:04d}-{:02d}-{:02d} {}:{:02d} UTC: '.format(y + 2000, m + 1, d + 1, h, q*15))
        f.write('{:+d}:{:02d}'.format(oh, oq*15))
        if ds:
            f.write(' (DST)')
        f.write('\n')
