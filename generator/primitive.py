import os
from coordinates import from_mm, transrot, LinearTransformer
from circuit_board import CircuitBoard
from pin_map import Pins
from text import Label
import datetime
import subprocess
import qrcode

class Primitive:
    """Represents a manually-drawn primitive for PCB composition."""

    def __init__(self, name):
        super().__init__()
        print('loading primitive {}...'.format(name))
        if not os.path.isdir(os.path.join('primitives', name)):
            raise ValueError('primitive {} does not exist'.format(name))
        if not os.path.isfile(os.path.join('primitives', name, '{}.blend.txt'.format(name))):
            raise ValueError('missing .blend.txt file for primitive {}'.format(name))
        self._name = name
        self._board = CircuitBoard()
        plates = self._board.get_plates()
        self._pins = Pins()
        self._labels = []
        with open(os.path.join('primitives', name, '{}.blend.txt'.format(name)), 'r') as f:
            layer = None
            aperture = None
            flash_region = None
            plate = None
            cut = False
            for line in f.read().split('\n') + ['end']:
                line = line.strip()
                if not line:
                    continue
                args = line.split()

                if flash_region is not None and args[0] != 'vert':
                    if plate is not None:
                        if cut:
                            raise ValueError('region not supported for plate cutting')
                        plate.add_region(*flash_region, flash_region[0])
                    elif layer in ('G1', 'G2'):
                        self._board.add_region_no_cutout(layer, True, *flash_region, flash_region[0])
                    else:
                        self._board.add_flashed_region(layer, *flash_region)
                    flash_region = None

                if args[0] == 'end':
                    break

                if args[0] == 'layer':
                    plate = None
                    layer = args[1]
                    if layer.startswith('Acrylic.'):
                        _, name, mode = layer.split('.')
                        assert mode in ('Cut', 'Engrave')
                        cut = mode == 'Cut'
                        if not plates.has_plate(name):
                            if name == 'Front':
                                plate = plates.add(name, 'Acrylaat Doorzichtig', '3mm', True)
                            elif name == 'Display':
                                plate = plates.add(name, 'Acrylaat Ondoorzichtig Zwart', '3mm')
                            elif name == 'Highlight':
                                plate = plates.add(name, 'Acrylaat Ondoorzichtig Wit', '5mm')
                            else:
                                raise ValueError('unknown plate name {}'.format(name))
                        else:
                            plate = plates.get(name)

                    continue

                if args[0] == 'mode':
                    if args[1] == 'region':
                        flash_region = []
                    elif args[1][0] == 'C':
                        aperture = from_mm(args[1][1:])
                    else:
                        raise ValueError('unknown mode {}'.format(args[1]))
                    continue

                if args[0] == 'vert':
                    if flash_region is not None:
                        flash_region.append((from_mm(args[1]), from_mm(args[2])))
                    elif plate is not None:
                        raise ValueError('vert not supported for plates')
                    else:
                        self._board.add_flash(layer, aperture, (from_mm(args[1]), from_mm(args[2])))
                    continue

                if args[0] == 'line':
                    if flash_region is not None:
                        raise ValueError('can only draw lines in circular aperture mode')
                    elif plate is not None:
                        if cut:
                            plate.add_cut(
                                (from_mm(args[1]), from_mm(args[2])),
                                (from_mm(args[3]), from_mm(args[4]))
                            )
                        else:
                            plate.add_line(
                                (from_mm(args[1]), from_mm(args[2])),
                                (from_mm(args[3]), from_mm(args[4]))
                            )
                    else:
                        self._board.add_trace(
                            layer, aperture,
                            (from_mm(args[1]), from_mm(args[2])),
                            (from_mm(args[3]), from_mm(args[4]))
                        )
                    continue

                if args[0] == 'label':
                    if plate is not None:
                        raise ValueError('label not supported for plates')
                    name = args[1]
                    coord = (from_mm(args[2]), from_mm(args[3]))
                    rotation = float(args[4])
                    scale = float(args[5]) / 1.2
                    if layer in ('Ctop', 'Cbottom'):
                        self._board.add_part(args[1], layer, coord, rotation)
                        continue
                    if layer in ('GTS', 'GBS'):
                        layer = layer[:2] + 'L'
                    if layer in ('GTL', 'GBL', 'G1', 'G2'):
                        if name[0] == '>':
                            self._pins.add(name[1:], 'in', layer, coord, (0, 0), 0.0)
                            mode = 'user'
                            name = '.' + name[1:]
                        elif name[0] == '<':
                            self._pins.add(name[1:], 'out', layer, coord, (0, 0), 0.0)
                            mode = 'driver'
                            name = '.' + name[1:]
                        elif name[0] == '~':
                            name = name[1:]
                            mode = 'passive'
                            # TODO
                        else:
                            mode = 'passive'
                        self._board.add_net(name, layer, coord, mode)
                        continue
                    if layer == 'GTO':
                        name = name.replace('~', ' ').strip()
                        if '#DATE' in name:
                            name = name.replace('#DATE', str(datetime.date.today()))
                        if '#REVISION' in name:
                            name = name.replace('#REVISION', subprocess.run(
                                ['git', 'rev-parse', '--short', 'HEAD'],
                                stdout=subprocess.PIPE,
                                check=True
                            ).stdout.decode('utf-8').strip())
                        if '#VERSION' in name:
                            name = name.replace('#VERSION', subprocess.run(
                                ['git', 'describe', '--tags', '--abbrev=0'],
                                stdout=subprocess.PIPE
                            ).stdout.decode('utf-8').strip())
                        if name.startswith('#QR'):
                            qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
                            qr.add_data(name[3:].strip())
                            qr.make(fit=True)
                            qr = qr.get_matrix()
                            box_size = from_mm(scale * 0.5)
                            for y, line in enumerate(qr):
                                y = ((len(qr) - 1) / 2 - y) * box_size
                                for x, filled in enumerate(line):
                                    if not filled:
                                        continue
                                    x = (x - (len(line) - 1) / 2) * box_size
                                    self._board.add_flashed_region(
                                        'GTO',
                                        transrot((x - box_size / 2, y - box_size / 2), coord, rotation),
                                        transrot((x + box_size / 2, y - box_size / 2), coord, rotation),
                                        transrot((x + box_size / 2, y + box_size / 2), coord, rotation),
                                        transrot((x - box_size / 2, y + box_size / 2), coord, rotation),
                                    )
                        else:
                            Label(
                                name,
                                coord,
                                rotation,
                                scale,
                                0.5, 0.5
                            ).instantiate(
                                self._board,
                                LinearTransformer(),
                                (0, 0),
                            0)
                        continue

                if args[0] == 'hole':
                    if plate is not None:
                        raise ValueError('hole not supported for plates')
                    self._board.add_hole((from_mm(args[1]), from_mm(args[2])), from_mm(args[3]))
                    continue

                if args[0] == 'via':
                    if from_mm(args[3]) > from_mm(0.5):
                        self._board.add_pth_pad((from_mm(args[1]), from_mm(args[2])), from_mm(args[3]), from_mm(args[4]))
                    else:
                        self._board.add_via((from_mm(args[1]), from_mm(args[2])), from_mm(args[3]), from_mm(args[4]))
                    continue

                print('warning: unknown construct for layer {}: {}'.format(layer, line))

        iface_file = os.path.join('primitives', self._name, '{}.vhd.txt'.format(self._name))
        self._interfaces = []
        if os.path.isfile(iface_file):
            with open(iface_file, 'r') as f:
                for line in f.read().split('\n'):
                    line = line.split('#')[0].strip()
                    if not line:
                        continue
                    direction, vhd_type, name = line.split()
                    self._interfaces.append((direction, vhd_type, name))

    def get_name(self):
        return self._name

    def get_pins(self):
        return self._pins

    def get_interfaces(self):
        return self._interfaces

    def instantiate(self, pcb, transformer, coord, rotation, net_prefix, net_override):
        """Instantiates this primitive on the given PCB with the given
        transformer and local coordinate + rotation. Nets found in the
        net_override map will be renamed accordingly. Local nets not found
        in the map will be prefixed by net_prefix."""
        warpable = False
        self._board.instantiate(pcb, transformer, coord, rotation, warpable, net_prefix, net_override)

_primitives = {}

def get_primitive(name):
    """Loads a primitive from the primitives directory."""
    prim = _primitives.get(name, None)
    if prim is None:
        prim = Primitive(name)
        _primitives[name] = prim
    return prim
