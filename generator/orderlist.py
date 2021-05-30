from part import get_part
import math

# Seven variants are defined, for different primary colors:
#  - R: red
#  - OR: orange-red
#  - O: orange
#  - Y: yellow
#  - YG: yellow-green
#  - G: green
#  - B: blue
# You can generate an order list for multiple clocks at once by adding multiple
# variants to the list. If you're just ordering for yourself, make sure there's
# only one here.
variants = ['O']

# When stuff is out of stock, you can specify alternative ordering numbers
# here. You'll need to find the alternatives yourself. Supply-chain management
# is a bitch!
alternatives = {
    #'863-MMBT4403WT1G':     '863-BC858BWT1G',
    #'71-CRCW06031K00FKEAC': '603-RC0603FR-071KL',
    #'71-CRCW0603100RFKEAC': '603-RC0603JR-07100RL',
    #'652-CR0603JW-471ELF':  '603-AC0603JR-13470RL',
    #'611-PTS526SK15SMR2L':  '611-PTS526SMG15SMR2L',
    #'603-RT0603FRE07680RL': '603-RC0603JR-07680RL',
    #'603-RC0603FR-0710KL':  '603-RC0603JR-0710KL',
    #'595-TPS26631PWPR':     '595-TPS26631PWPT',
    #'595-SN74LVC1G17DCKR':  '595-SN74LVC1G17DCK3',
    #'530-5ET1-R':           '530-5TT1-R',
    #'530-FC-203BRIGHTTIN':  '534-3521',
}

# Make sure that, once stuff is in your cart, you round things like resistors
# up to the nearest logical multiple. This will actually save you a few bucks
# due to the insane price breaks Mouser has for small parts! It might also save
# you from having to re-order stuff.

def add(data, key, amount):
    if key not in data:
        data[key] = amount
    else:
        data[key] += amount

data = {}

for board in ('mainboard', 'support_board'):
    with open('output/{}.parts.txt'.format(board), 'r') as f:
        for line in f.readlines():
            line = line.split('#')[0].strip()
            if not line:
                continue
            part, *_ = line.split()
            add(data, part, 1)

def print_led_color(part, variant):
    data = get_part(part).get_data()
    if 'wavelength' in data:
        wavelength = data['wavelength']
    else:
        wavelength = data[variant + '/wavelength']

    assert wavelength.endswith('nm')
    wavelength = int(wavelength[:-2])

    # Stolen from https://academo.org/demos/wavelength-to-colour-relationship/
    if wavelength >= 380 and wavelength < 440:
        red = -(wavelength - 440) / (440 - 380)
        green = 0.0
        blue = 1.0
    elif wavelength >= 440 and wavelength < 490:
        red = 0.0
        green = (wavelength - 440) / (490 - 440)
        blue = 1.0
    elif wavelength >= 490 and wavelength < 510:
        red = 0.0
        green = 1.0
        blue = -(wavelength - 510) / (510 - 490)
    elif wavelength >= 510 and wavelength < 580:
        red = (wavelength - 510) / (580 - 510)
        green = 1.0
        blue = 0.0
    elif wavelength >= 580 and wavelength < 645:
        red = 1.0
        green = -(wavelength - 645) / (645 - 580)
        blue = 0.0
    elif wavelength >= 645 and wavelength < 781:
        red = 1.0
        green = 0.0
        blue = 0.0
    else:
        red = 0.0
        green = 0.0
        blue = 0.0

    # Let the intensity fall off near the vision limits
    if wavelength >= 380 and wavelength < 420:
        factor = 0.3 + 0.7*(wavelength - 380) / (420 - 380)
    elif wavelength >= 420 and wavelength < 701:
        factor = 1.0
    elif wavelength >= 701 and wavelength < 781:
        factor = 0.3 + 0.7*(780 - wavelength) / (780 - 700)
    else:
        factor = 0.0

    red = round(255 * math.pow(red * factor, 0.8))
    green = round(255 * math.pow(green * factor, 0.8))
    blue = round(255 * math.pow(blue * factor, 0.8))

    return '\033[38;2;{r};{g};{b}m\033[48;2;{r};{g};{b}m  \033[0m'.format(r=red, g=green, b=blue)


mouser_order = {}
tinytronics_order = {}

for name, count in data.items():
    get_part(name).get_data()

for variant in variants:
    print('Adding variant {} to the order list...'.format(variant))
    print('  Flipflop LED color:     {}'.format(print_led_color('FFLED', variant)))
    print('  Gate LED color:         {}'.format(print_led_color('LTST-C230-GATE', variant)))
    print('  Synchroscope LED color: {}'.format(print_led_color('APD3224', variant)))
    print('  uC activity LED color:  {}'.format(print_led_color('LTST-C230-UC', variant)))

    for name, count in data.items():
        part_data = get_part(name).get_data()
        if 'mouser' in part_data:
            add(mouser_order, part_data['mouser'], count)
        elif variant + '/mouser' in part_data:
            add(mouser_order, part_data[variant + '/mouser'], count)
        elif 'tinytronics' in part_data:
            add(tinytronics_order, part_data['tinytronics'], count)
        else:
            raise ValueError('no order info for part {}'.format(name))

with open('output/mouser.txt', 'w') as f:
    for order_no, count in sorted(mouser_order.items()):
        order_no = alternatives.get(order_no, order_no)
        f.write('{} | {}\n'.format(order_no, count))

with open('output/tinytronics.txt', 'w') as f:
    for order_no, count in sorted(tinytronics_order.items()):
        f.write('{} {}\n'.format(order_no, count))
