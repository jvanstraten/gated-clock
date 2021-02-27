
import xml.etree.ElementTree as ET

tree = ET.parse('output/mainboard.normal.svg')
root = tree.getroot()
root.attrib['xmlns:xlink'] = 'http://www.w3.org/1999/xlink'
del root[1]
del root[1]
del root[0][0]
del root[0][1]
del root[0][2]
del root[0][3]
del root[0][4]

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

for idx, color in enumerate(('rgb(204,104,67)', 'rgb(67,104,204)'), 1):
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
    use.attrib['stroke-width'] = '0.1'
    root[0][idx][0].append(use)


root.insert(0, defs)

with open('output/mainboard.traces.svg', 'wb') as f:
    tree.write(f)

#print(root[0][0].attrib)
