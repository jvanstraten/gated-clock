from part import get_part

data = {}

for board in ('mainboard', 'support_board'):
    with open('output/{}.parts.txt'.format(board), 'r') as f:
        for line in f.readlines():
            line = line.split('#')[0].strip()
            if not line:
                continue
            part, *_ = line.split()
            if part not in data:
                data[part] = 1
            else:
                data[part] += 1

mouser_order = []
tinytronics_order = []

for name, count in data.items():
    data = get_part(name).get_data()
    if 'mouser' in data:
        mouser_order.append((data['mouser'], count))
    elif 'tinytronics' in data:
        tinytronics_order.append((data['tinytronics'], count))
    else:
        raise ValueError('no order info for part {}'.format(name))

with open('output/mouser.txt', 'w') as f:
    for order_no, count in mouser_order:
        f.write('{} {}\n'.format(order_no, count))

with open('output/tinytronics.txt', 'w') as f:
    for order_no, count in tinytronics_order:
        f.write('{} {}\n'.format(order_no, count))
