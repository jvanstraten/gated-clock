import os
import math
from coordinates import from_mm, to_mm, transrot
from pin_map import Pins, PinMap
from netlist import Netlist
from primitive import get_primitive

class GridDimension:
    """Represents one of the two dimensions of the table grid."""

    def __init__(self, mirror):
        super().__init__()
        self._positions = []
        self._mirror = mirror

    def _convert_mm(self, pos):
        """Converts a grid position to millimeters."""
        if pos < 0 or pos > len(self._positions):
            raise ValueError('invalid grid position')
        idx1 = int(pos)
        if idx1 == len(self._positions) - 1:
            return self._positions[idx1]
        idx2 = idx1 + 1
        f2 = idx2 - pos
        f1 = 1 - f2
        return self._positions[idx1] * f1 + self._positions[idx2] * f2

    def convert(self, pos):
        """Converts a grid position to internal units."""
        return from_mm(self._convert_mm(float(pos)))

    def configure(self, *args):
        """Parses a grid layout command. The first N-1 arguments must be of the
        form `<count>x<length><aligment>`, where count is used to set N
        rows/columns at once, length sets the size of each row/column, and
        alignment is L/T/C/R/B to specify where in relation to the row/column
        the placed part centers should be. The last argument specifies where
        in the specified layout the subcircuit origin should end up."""
        self._positions = []
        pos = 0.0
        for arg in args[:-1]:
            count, length = arg[:-1].split('x')
            count = int(count)
            length = float(length)
            align = {
                'L': 0.0, 'T': 0.0,
                'C': 0.5,
                'R': 1.0, 'B': 1.0
            }[arg[-1]]
            for _ in range(count):
                self._positions.append(pos + length * align)
                pos += length
        ref = self._convert_mm(float(args[-1]))
        if self._mirror:
            for i in range(len(self._positions)):
                self._positions[i] = self._positions[i] - ref
        else:
            for i in range(len(self._positions)):
                self._positions[i] = ref - self._positions[i]

class RoutingColumn:
    """Represents a routing column."""

    def __init__(self, x_coord, net_names):
        super().__init__()
        self._x_coord = x_coord
        self._nets = nets

class Instance:
    """Represents a primitive or subcircuit instance."""

    def __init__(self, is_primitive, typ, name, coord, rotation, *mappings):
        super().__init__()
        self._name = name
        self._is_primitive = is_primitive
        self._data = get_primitive(typ) if is_primitive else get_subcircuit(typ)
        self._coord = coord
        self._rotation = rotation
        self._pinmap = PinMap(self._data.get_pins(), *mappings)

    def get_name(self):
        return self._name

    def is_primitive(self):
        return self._is_primitive

    def get_data(self):
        return self._data

    def get_coord(self):
        return self._coord

    def get_rotation(self):
        return self._rotation

    def get_pinmap(self):
        return self._pinmap

class Subcircuit:
    """Represents a subcircuit for PCB composition."""

    def __init__(self, name):
        super().__init__()
        print('loading subcircuit {}...'.format(name))
        if not os.path.isdir(os.path.join('subcircuits', name)):
            raise ValueError('subcircuit {} does not exist'.format(name))
        if not os.path.isfile(os.path.join('subcircuits', name, '{}.circuit.txt'.format(name))):
            raise ValueError('missing .circuit.txt file for subcircuit {}'.format(name))
        cols = GridDimension(False)
        rows = GridDimension(True)
        self._name = name
        self._pins = Pins()
        self._netlist = Netlist()
        self._instances = []
        self._routers = []
        with open(os.path.join('subcircuits', name, '{}.circuit.txt'.format(name)), 'r') as f:
            for line in f.read().split('\n'):
                line = line.split('#', maxsplit=1)[0].strip()
                if not line:
                    continue
                args = line.split()

                if args[0] == 'columns':
                    cols.configure(*args[1:])
                    continue

                if args[0] == 'rows':
                    rows.configure(*args[1:])
                    continue

                if args[0] in ('in', 'out'):
                    coord = (cols.convert(args[2]), rows.convert(args[3]))
                    self._pins.add(args[1], args[0], 'GTL', coord)
                    name = '.{}'.format(args[1])
                    self._netlist.add(name, 'GTL', coord, args[0] == 'in')
                    continue

                if args[0] in ('prim', 'subc'):
                    coord = (cols.convert(args[4]), rows.convert(args[5]))
                    rotation = float(args[3]) / 180 * math.pi
                    instance = Instance(
                        args[0] == 'prim', args[1], args[2],
                        coord, rotation, *args[6:]
                    )
                    for pin, net in instance.get_pinmap():
                        self._netlist.add(
                            '.{}'.format(net),
                            pin.get_layer(),
                            transrot(pin.get_coord(), coord, rotation),
                            pin.is_output()
                        )
                    self._instances.append(instance)
                    continue

                if args[0] == 'route':
                    self._routers.append((cols.convert(args[1]), ['.{}'.format(x) for x in args[2:]]))
                    continue

                print('warning: unknown subcircuit construct: {}'.format(line))

        print('doing basic DRC for subcircuit {}...'.format(self._name))
        good = self._netlist.check()
        unrouted = set(map(lambda x: x.get_name(), self._netlist.iter_logical()))
        routed = set()
        for x, nets in self._routers:
            ranges = []
            for net in nets:
                if net in routed:
                    print('net {} is routed multiple times'.format(net))
                    good = False
                elif net not in unrouted:
                    print('net {} cannot be routed because it does not exist'.format(net))
                    good = False
                routed.add(net)
                unrouted.remove(net)
                y_min = None
                y_max = None
                for _, (_, y), _ in self._netlist.get_logical(net).iter_points():
                    if y_min is None or y < y_min:
                        y_min = y
                    if y_max is None or y > y_max:
                        y_max = y
                assert y_min is not None
                assert y_max is not None
                ranges.append((y_min, y_max, net))
            ranges.sort()
            for i in range(len(ranges) - 1):
                if ranges[i+1][0] - from_mm(0.5) < ranges[i][1]:
                    print('nets {} and {} overlap in routing column;'.format(ranges[i][2], ranges[i+1][2]))
                    print('  {} goes down to Y{} and {} up to Y{} at X{}'.format(
                        ranges[i+1][2], to_mm(ranges[i+1][0]),
                        ranges[i][2], to_mm(ranges[i][1]),
                        to_mm(x)))
                    good = False
        for net in unrouted:
            print('net {} is not routed'.format(net))
            good = False
        # TODO reenable
        #if not good:
            #raise ValueError('basic DRC failed for subcircuit {}'.format(self._name))
        print('finished loading subcircuit {}, basic DRC passed'.format(self._name))

    def get_name(self):
        return self._name

    def get_pins(self):
        return self._pins

_subcircuits = {}

def get_subcircuit(name):
    """Loads a subcircuit from the subcircuits directory."""
    subcirc = _subcircuits.get(name, None)
    if subcirc is None:
        subcirc = Subcircuit(name)
        _subcircuits[name] = subcirc
    return subcirc

# TODO removeme
if __name__ == '__main__':
    get_subcircuit('decode10')
