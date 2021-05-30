from part import get_part

variants = ['O']

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

mouser_order = {}
tinytronics_order = {}

for variant in variants:
    for name, count in data.items():
        data = get_part(name).get_data()
        if 'mouser' in data:
            add(mouser_order, data['mouser'], count)
        elif variant + '/mouser' in data:
            add(mouser_order, data[variant + '/mouser'], count)
        elif 'tinytronics' in data:
            add(tinytronics_order, data['tinytronics'], count)
        else:
            raise ValueError('no order info for part {}'.format(name))

with open('output/mouser.txt', 'w') as f:
    for order_no, count in sorted(mouser_order.items()):
        f.write('{} {}\n'.format(order_no, count))

with open('output/tinytronics.txt', 'w') as f:
    for order_no, count in sorted(tinytronics_order.items()):
        f.write('{} {}\n'.format(order_no, count))
