import os
from coordinates import from_mm
from circuit_board import CircuitBoard
from pin_map import Pins

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
        self._pins = Pins()
        with open(os.path.join('primitives', name, '{}.blend.txt'.format(name)), 'r') as f:
            layer = None
            aperture = None
            flash_region = None
            for line in f.read().split('\n') + ['end']:
                line = line.strip()
                if not line:
                    continue
                args = line.split()

                if flash_region is not None and args[0] != 'vert':
                    self._board.add_flashed_region(layer, *flash_region)
                    flash_region = None

                if args[0] == 'end':
                    break

                if args[0] == 'layer':
                    layer = args[1]
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
                    else:
                        self._board.add_flash(layer, aperture, (from_mm(args[1]), from_mm(args[2])))
                    continue

                if args[0] == 'line':
                    if flash_region is not None:
                        raise ValueError('can only draw lines in circular aperture mode')
                    self._board.add_trace(
                        layer, aperture,
                        (from_mm(args[1]), from_mm(args[2])),
                        (from_mm(args[3]), from_mm(args[4]))
                    )
                    continue

                if args[0] == 'label':
                    name = args[1]
                    coord = (from_mm(args[2]), from_mm(args[3]))
                    rotation = float(args[4])
                    if layer in ('Ctop', 'Cbottom'):
                        self._board.add_part(args[1], layer, coord, rotation)
                        continue
                    if layer in ('GTS', 'GBS'):
                        layer = layer[:2] + 'L'
                    if layer in ('GTL', 'GBL', 'G1', 'G2'):
                        if name[0] == '>':
                            mode = 'in'
                            name = '.' + name[1:]
                        elif name[0] == '<':
                            mode = 'out'
                            name = '.' + name[1:]
                        else:
                            mode = 'passive'
                        if mode != 'passive':
                            self._pins.add(name[1:], mode, layer, coord)
                        self._board.add_net(name, layer, coord, mode)
                        continue

                if args[0] == 'hole':
                    self._board.add_hole((from_mm(args[1]), from_mm(args[2])), from_mm(args[3]))
                    continue

                if args[0] == 'via':
                    self._board.add_via((from_mm(args[1]), from_mm(args[2])), from_mm(args[3]), from_mm(args[4]))
                    continue

                print('warning: unknown construct for layer {}: {}'.format(layer, line))

    def get_name(self):
        return self._name

    def get_pins(self):
        return self._pins

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


# TODO removeme
if __name__ == '__main__':
    #p = get_primitive('nand1')
    #p._board.add_outline(
        #(from_mm(-10), from_mm(-10)),
        #(from_mm(10), from_mm(-10)),
        #(from_mm(10), from_mm(10)),
        #(from_mm(-10), from_mm(10)),
        #(from_mm(-10), from_mm(-10)),
    #)
    #p._board.to_file('kek')

    pcb = CircuitBoard()
    pcb.add_outline(
        (from_mm(-15), from_mm(-10)),
        (from_mm(15), from_mm(-10)),
        (from_mm(15), from_mm(10)),
        (from_mm(-15), from_mm(10)),
        (from_mm(-15), from_mm(-10)),
    )
    from coordinates import LinearTransformer, CircularTransformer
    import math
    t = CircularTransformer((0, from_mm(-5.0)), from_mm(5))
    get_primitive('nand1').instantiate(pcb, t, (from_mm(-8), 0), 0.0, '', {})
    get_primitive('nand1').instantiate(pcb, t, (0, 0), 0.0, '', {})
    get_primitive('nand1').instantiate(pcb, t, (from_mm(8), 0), 0.0, '', {})
    pcb.to_file('kek')
