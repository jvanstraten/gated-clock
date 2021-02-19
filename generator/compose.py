from coordinates import LinearTransformer, CircularTransformer
from circuit_board import CircuitBoard
from subcircuit import get_subcircuit
from primitive import get_primitive
from coordinates import from_mm
import gerbertools
import math

mainboard = CircuitBoard(mask_expansion=0.05)
t = LinearTransformer()
get_primitive('mainboard').instantiate(mainboard, t, (0, 0), 0, 'mainboard', {})
t = CircularTransformer((0, 0), from_mm(159.15), 0)
get_subcircuit('border').instantiate(mainboard, t, (from_mm(500), from_mm(0.85)), math.pi/2, 'border', {})
mainboard.to_file('output/mainboard')

mainboard_gbr = gerbertools.read('output/mainboard.PCB')

display_gbr = gerbertools.CircuitBoard('output/mainboard.Display', '.GM1', '')
display_gbr.add_substrate_layer(3)
display_gbr.add_mask_layer('', '.GM2')

front_gbr = gerbertools.CircuitBoard('output/mainboard.Front', '.GM1', '')
front_gbr.add_substrate_layer(3)
front_gbr.add_mask_layer('', '.GM2')

highlight_gbr = gerbertools.CircuitBoard('output/mainboard.Highlight', '.GM1', '')
highlight_gbr.add_substrate_layer(3)
highlight_gbr.add_mask_layer('', '.GM2')


with open('output/mainboard.normal.svg', 'w') as f:
    f.write('<svg viewBox="0 0 410 410" width="5125" height="5125" xmlns="http://www.w3.org/2000/svg">\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 1 rgba(0, 0, 0, 0.2))">\n')
    f.write(mainboard_gbr.get_svg(False, gerbertools.color.mask_white(), gerbertools.color.silk_black(), id_prefix='mainboard'))
    f.write('</g>\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 3 rgba(0, 0, 0, 0.5))">\n')
    f.write(display_gbr.get_svg(False, soldermask=(0, 0, 0, 0), silkscreen=(0.7, 0.7, 0.7, 0.8), substrate=(0.1, 0.1, 0.1, 0.95), id_prefix='display'))
    f.write(highlight_gbr.get_svg(False, soldermask=(0, 0, 0, 0), silkscreen=(0.7, 0.7, 0.7, 0.8), substrate=(0.95, 0.95, 0.95, 0.95), id_prefix='highlight'))
    f.write('</g>\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 3 rgba(0, 0, 0, 0.5))">\n')
    f.write(front_gbr.get_svg(False, soldermask=(0, 0, 0, 0), silkscreen=(0.7, 0.7, 0.7, 0.8), substrate=(0.6, 0.6, 0.6, 0.05), id_prefix='front'))
    f.write('</g>\n')
    f.write('</svg>\n')

#mainboard_gbr.write_svg('output/mainboard.normal.svg', False, 12.5, gerbertools.color.mask_white(), gerbertools.color.silk_black())
#mainboard_gbr.write_svg('output/mainboard.flipped.svg', True, 12.5, gerbertools.color.mask_white(), gerbertools.color.silk_black())

