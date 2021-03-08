from coordinates import LinearTransformer
from circuit_board import CircuitBoard
from subcircuit import get_subcircuit
from primitive import get_primitive
from coordinates import from_mm, to_mm
import gerbertools
import math
import sys

support_board = CircuitBoard(mask_expansion=0.05)
t = LinearTransformer()
get_primitive('support_board').instantiate(support_board, t, (0, 0), 0, '', {})

print('*** pouring inner layer polygons...')
support_board.add_poly_pours()

print('*** writing gerber output...')
support_board.to_file('output/support_board')

print('*** running circuit DRC...')
any_violations = False
if not support_board.get_netlist().check_composite():
    any_violations = True

print('*** building PCB...')
print('outline and hole data...')
support_board_gbr = gerbertools.CircuitBoard('output/support_board.PCB', '.GM1', '.TXT');
print('bottom mask...')
support_board_gbr.add_mask_layer('.GBS', '.GBO');
print('bottom layer...')
support_board_gbr.add_copper_layer('.GBL', 0.035)
support_board_gbr.add_substrate_layer(0.1)
print('vcc layer...')
support_board_gbr.add_copper_layer('.G2', 0.0175)
support_board_gbr.add_substrate_layer(1.265)
print('gnd layer...')
support_board_gbr.add_copper_layer('.G1', 0.0175)
support_board_gbr.add_substrate_layer(0.1)
print('top layer...')
support_board_gbr.add_copper_layer('.GTL', 0.035)
print('top mask...')
support_board_gbr.add_mask_layer('.GTS', '.GTO');
print('surface finish...')
support_board_gbr.add_surface_finish()

print('*** rendering to SVG...')
with open('output/support_board.normal.svg', 'w') as f:
    f.write('<svg viewBox="0 0 410 410" width="5125" height="5125" xmlns="http://www.w3.org/2000/svg">\n')
    f.write('<g transform="translate(205 205) scale(1 -1) " filter="drop-shadow(0 0 1 rgba(0, 0, 0, 0.2))">\n')
    f.write(support_board_gbr.get_svg(False, gerbertools.color.mask_green(), gerbertools.color.silk_white(), id_prefix='support_board'))
    f.write('</g>\n')
    f.write('</svg>\n')

support_board_gbr.write_svg('output/support_board.front.svg', False, 50.0, gerbertools.color.mask_green(), gerbertools.color.silk_white())
support_board_gbr.write_svg('output/support_board.back.svg', True, 50.0, gerbertools.color.mask_green(), gerbertools.color.silk_white())

print('*** rendering to OBJ...')
support_board_gbr.write_obj('output/support_board.PCB.obj')

print('*** running physical DRC...')
nets = []
nl = support_board.get_netlist()
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
violations = support_board_gbr.build_netlist(nets, clearance=0.13, annular_ring=0.13).drc()
for violation in violations:
    if violation.startswith('logical net NO_NET is divided up into'):
        continue
    print(violation)
    any_violations = True

print()
if any_violations:
    print('There were DRC errors :(')
    sys.exit(1)
else:
    print('Everything checks out! :D')

