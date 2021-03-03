from coordinates import LinearTransformer, CircularTransformer
from circuit_board import CircuitBoard
from subcircuit import get_subcircuit
from primitive import get_primitive
from coordinates import from_mm, to_mm
import gerbertools
import math
import sys

mainboard = CircuitBoard(mask_expansion=0.05)
t = LinearTransformer()
get_primitive('mainboard').instantiate(mainboard, t, (0, 0), 0, '', {})
t = CircularTransformer((0, 0), from_mm(159.15), 0)
get_subcircuit('mainboard').instantiate(mainboard, t, (from_mm(500), from_mm(0.85)), math.pi/2, '', {})

print('*** pouring inner layer polygons...')
mainboard.add_poly_pours()

print('*** writing gerber output...')
mainboard.to_file('output/mainboard')

print('*** running circuit DRC...')
any_violations = False
if not mainboard.get_netlist().check_composite():
    any_violations = True

print('*** building PCB...')
#mainboard_gbr = gerbertools.read('output/mainboard.PCB')
print('outline and hole data...')
mainboard_gbr = gerbertools.CircuitBoard('output/mainboard.PCB', '.GM1', '.TXT');
print('bottom mask...')
mainboard_gbr.add_mask_layer('.GBS', '.GBO');
print('bottom layer...')
mainboard_gbr.add_copper_layer('.GBL', 0.035)
mainboard_gbr.add_substrate_layer(0.1)
print('vcc layer...')
mainboard_gbr.add_copper_layer('.G2', 0.0175)
mainboard_gbr.add_substrate_layer(1.265)
print('gnd layer...')
mainboard_gbr.add_copper_layer('.G1', 0.0175)
mainboard_gbr.add_substrate_layer(0.1)
print('top layer...')
mainboard_gbr.add_copper_layer('.GTL', 0.035)
print('top mask...')
mainboard_gbr.add_mask_layer('.GTS', '.GTO');
print('surface finish...')
mainboard_gbr.add_surface_finish()

print('*** building acrylic plates...')
display_gbr = gerbertools.CircuitBoard('output/mainboard.Display', '.GM1', '')
display_gbr.add_substrate_layer(3)

front_gbr = gerbertools.CircuitBoard('output/mainboard.Front', '.GM1', '')
front_gbr.add_mask_layer('', '.GM2')
front_gbr.add_substrate_layer(3)

highlight_gbr = gerbertools.CircuitBoard('output/mainboard.Highlight', '.GM1', '')
highlight_gbr.add_substrate_layer(5)

print('*** rendering to SVG...')
with open('output/mainboard.normal.svg', 'w') as f:
    f.write('<svg viewBox="0 0 410 410" width="5125" height="5125" xmlns="http://www.w3.org/2000/svg">\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 1 rgba(0, 0, 0, 0.2))">\n')
    f.write(mainboard_gbr.get_svg(False, gerbertools.color.mask_white(), gerbertools.color.silk_black(), id_prefix='mainboard'))

    #f.write('<g id="top-parts">\n')
    #for part in mainboard.get_parts():
        #if part.get_layer() == 'Ctop':
            #f.write('<text transform="translate({} {}) scale(1 -1) rotate({})" dominant-baseline="middle" text-anchor="middle" font-size="0.5" fill="blue">{}</text>\n'.format(
                #to_mm(part.get_coord()[0]),
                #to_mm(part.get_coord()[1]),
                #-part.get_rotation() * 180 / math.pi,
                #part.get_name()))
    #f.write('</g>\n')
    #f.write('<g id="top-nets">\n')
    #for net in mainboard.get_netlist().iter_physical():
        #for layer, coord, mode in net.iter_points():
            #if layer == 'GTL':
                #f.write('<text transform="translate({} {}) scale(1 -1)" dominant-baseline="middle" text-anchor="middle" font-size="0.7" fill="red">{}</text>\n'.format(
                    #to_mm(coord[0]),
                    #to_mm(coord[1]),
                    #net.get_name()))
    #f.write('</g>\n')

    f.write('</g>\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 3 rgba(0, 0, 0, 0.5))">\n')
    f.write(display_gbr.get_svg(False, soldermask=(0, 0, 0, 0), silkscreen=(0.7, 0.7, 0.7, 0.8), substrate=(0.1, 0.1, 0.1, 0.95), id_prefix='display'))
    f.write(highlight_gbr.get_svg(False, soldermask=(0, 0, 0, 0), silkscreen=(0.7, 0.7, 0.7, 0.8), substrate=(0.95, 0.95, 0.95, 0.95), id_prefix='highlight'))
    f.write('</g>\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 3 rgba(0, 0, 0, 0.1))" style="stroke: white; stroke-width: 0.2">\n')
    f.write(front_gbr.get_svg(False, soldermask=(0, 0, 0, 0), silkscreen=(0.7, 0.7, 0.7, 0.8), substrate=(0.6, 0.6, 0.6, 0.05), id_prefix='front'))
    f.write('</g>\n')
    f.write('</svg>\n')

#mainboard_gbr.write_svg('output/mainboard.normal.svg', False, 12.5, gerbertools.color.mask_white(), gerbertools.color.silk_black())
#mainboard_gbr.write_svg('output/mainboard.flipped.svg', True, 12.5, gerbertools.color.mask_white(), gerbertools.color.silk_black())

print('*** rendering to OBJ...')
mainboard_gbr.write_obj('output/mainboard.PCB.obj')
display_gbr.write_obj('output/mainboard.Display.obj')
front_gbr.write_obj('output/mainboard.Front.obj')
highlight_gbr.write_obj('output/mainboard.Highlight.obj')

print('*** running physical DRC...')
nets = []
nl = mainboard.get_netlist()
for net in nl.iter_physical():
    name = nl.get_true_net_name(net.get_name())
    for layer, (x, y), mode in net.iter_points():
        layer = {
            'GBS': 0,
            'GBL': 0,
            'G2': 1,
            'G1': 2,
            'GTL': 3,
            'GTS': 3,
        }[layer]
        nets.append(((to_mm(x), to_mm(y)), layer, name))
violations = mainboard_gbr.build_netlist(nets, clearance=0.13, annular_ring=0.13).drc()
for violation in violations:
    if violation.startswith('logical net NO_NET is divided up into'):
        continue
    print(violation)
    any_violations = True

print()
if any_violations:
    print('There were DRC errors :(')
    #sys.exit(1)
else:
    print('Everything checks out! :D')

