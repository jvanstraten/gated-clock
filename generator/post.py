
import math
import xml.etree.ElementTree as ET
import os
import sys

if len(sys.argv) < 2:
    print('usage: {} <pcb>'.format(sys.argv[0]), file=sys.stderr)
    sys.exit(255)
pcb = sys.argv[1]

for side in ('front', 'back'):
    if not os.path.isfile('output/{}.{}.svg'.format(pcb, side)):
        continue

    tree = ET.parse('output/{}.{}.svg'.format(pcb, side))
    root = tree.getroot()
    root.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
    del root[0][0]
    del root[0][1]
    del root[0][2]
    del root[0][5][0]
    root[0][5][0].attrib['fill'] = 'rgb(255,255,0)'
    root[0][5][0].attrib['fill-opacity'] = '0.3'

    root[0][0][0].attrib['fill'] = 'rgb(104,178,67)'

    defs = ET.Element('ns0:defs')
    filt = ET.Element('ns0:filter')
    filt.attrib['id'] = 'blur'
    filt.attrib['x'] = '0'
    filt.attrib['y'] = '0'
    blur = ET.Element('ns0:feGaussianBlur')
    blur.attrib['in'] = 'SourceGraphic'
    blur.attrib['stdDeviation'] = '1'
    filt.append(blur)
    defs.append(filt)

    if side == 'front':
        colors = ('rgb(204,104,67)', 'rgb(67,104,204)', 'rgb(0,0,0)')
    else:
        colors = ('rgb(67,104,204)', 'rgb(204,104,67)', 'rgb(0,0,0)')
    for idx, color in enumerate(colors, 1):
        path = ET.Element('ns0:path')
        path.attrib['id'] = 'poly{}'.format(idx)
        path.attrib['d'] = root[0][idx][0].attrib['d']
        defs.append(path)
        clip = ET.Element('ns0:clipPath')
        clip.attrib['id'] = 'clip{}'.format(idx)
        use = ET.Element('ns0:use')
        use.attrib['xlink:href'] = '#poly{}'.format(idx)
        clip.append(use)
        defs.append(clip)
        del root[0][idx][0].attrib['d']
        del root[0][idx][0].attrib['fill']
        root[0][idx][0].tag = 'ns0:g'
        use = ET.Element('ns0:use')
        use.attrib['xlink:href'] = '#poly{}'.format(idx)
        use.attrib['clip-path'] = 'url(#clip{})'.format(idx)
        use.attrib['fill'] = 'none'
        use.attrib['stroke'] = color
        use.attrib['stroke-width'] = '0.3'
        use.attrib['stroke-opacity'] = '0.3'
        use.attrib['filter'] = 'url(#blur)'
        root[0][idx][0].append(use)
        use = ET.Element('ns0:use')
        use.attrib['xlink:href'] = '#poly{}'.format(idx)
        use.attrib['clip-path'] = 'url(#clip{})'.format(idx)
        use.attrib['fill'] = 'none'
        use.attrib['stroke'] = color
        use.attrib['stroke-width'] = '0.3'
        use.attrib['stroke-opacity'] = '0.5'
        root[0][idx][0].append(use)

    root.insert(0, defs)

    group = ET.Element('ns0:g')
    group.attrib['id'] = 'parts'
    with open('output/{}.parts.txt'.format(pcb), 'r') as f:
        for line in f.readlines():
            line = line.split('#')[0].strip()
            if not line:
                continue
            name, _, layer, x, y, rot = line.split()
            if (layer == 'Ctop' and side == 'back') or (layer == 'Cbottom' and side == 'front'):
                continue
            if not os.path.isfile('parts/{0}/{0}.verif.txt'.format(name)):
                continue
            x = float(x)
            y = float(y)
            rot = float(rot)
            si = math.sin(-rot / 180 * math.pi)
            co = math.cos(-rot / 180 * math.pi)
            pgroup = ET.Element('ns0:g')
            pathdata = []
            with open('parts/{0}/{0}.verif.txt'.format(name), 'r') as f2:
                for line2 in f2.readlines():
                    line2 = line2.split('#')[0].strip()
                    if not line2:
                        continue
                    line2 = line2.split()
                    if line2[0] == 'line':
                        _, lx1, ly1, lx2, ly2 = line2
                        lx1 = float(lx1)
                        ly1 = float(ly1)
                        lx2 = float(lx2)
                        ly2 = float(ly2)
                        if side == 'back':
                            lx1 = -lx1
                            lx2 = -lx2
                        x1 = co * lx1 + si * ly1 + x
                        y1 = co * ly1 - si * lx1 + y
                        x2 = co * lx2 + si * ly2 + x
                        y2 = co * ly2 - si * lx2 + y
                        pathdata.append('M {},{} L {},{}'.format(x1, y1, x2, y2))
                    elif line2[0] == 'label':
                        _, text, lx, ly, lrot, tscale = line2
                        lx = float(lx)
                        ly = float(ly)
                        if side == 'back':
                            lx = -lx
                        lrot = float(lrot)
                        tscale = float(tscale)
                        lrot = lrot * 180 / math.pi
                        tx = co * lx + si * ly + x
                        ty = co * ly - si * lx + y
                        trot = rot + lrot
                        if side == 'front':
                            trot = -trot
                        while trot > 90:
                            trot -= 180
                        while trot < -90:
                            trot += 180
                        text = text.replace('~', ' ')
                        label = ET.Element('ns0:text')
                        label.attrib['transform'] = 'translate({} {}) scale({} -1) rotate({})'.format(tx, ty, -1 if side == 'back' else 1, trot)
                        label.attrib['dominant-baseline'] = 'middle'
                        label.attrib['text-anchor'] = 'middle'
                        label.attrib['font-size'] = str(tscale * 0.7)
                        label.attrib['fill'] = 'black'
                        label.text = text
                        pgroup.append(label)
                        continue
                    else:
                        print(line2)
                        assert False

            ppath = ET.Element('ns0:path')
            ppath.attrib['d'] = ' '.join(pathdata)
            ppath.attrib['fill'] = 'none'
            ppath.attrib['stroke'] = 'black'
            ppath.attrib['stroke-width'] = '0.05'
            ppath.attrib['d'] = ' '.join(pathdata)
            pgroup.insert(0, ppath)

            group.append(pgroup)

    root[1].append(group)

    group = ET.Element('ns0:g')
    group.attrib['id'] = 'nets'
    with open('output/{}.nets.txt'.format(pcb), 'r') as f:
        net = '???'
        for line in f.readlines():
            line = line.split('#')[0].strip()
            if not line:
                continue
            if line.startswith('net'):
                net = line.split(maxsplit=1)[1]
            else:
                _, layer, x, y = line.split()
                if not ((side == 'front' and layer in ('GTL', 'GTS')) or (side == 'back' and layer in ('GBL', 'GBS'))):
                    continue
                x = float(x)
                y = float(y)
                label = ET.Element('ns0:text')
                label.attrib['transform'] = 'translate({} {}) scale({} -1) rotate(45)'.format(x, y, -1 if side == 'back' else 1)
                label.attrib['dominant-baseline'] = 'middle'
                label.attrib['text-anchor'] = 'middle'
                label.attrib['font-size'] = '0.3'
                label.attrib['fill'] = 'red'
                label.text = net
                group.append(label)
    root[1].append(group)

    with open('output/{}.{}.traces.svg'.format(pcb, side), 'wb') as f:
        tree.write(f)
