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
        f2 = pos - idx1
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
                self._positions[i] = ref - self._positions[i]
        else:
            for i in range(len(self._positions)):
                self._positions[i] = self._positions[i] - ref

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

    def instantiate(self, pcb, transformer, translate, rotate, net_prefix, net_override):
        """Instantiate this instance to the given PCB. The transformation and
        net overrides are treated as being for the parent subcircuit -- the
        transformations for this instance are applied on top of it. Note that
        the parent is assumed to be warpable."""

        # Figure out net prefix for the child instance.
        child_net_prefix = '{}.{}'.format(net_prefix, self.get_name())

        # Figure out net override for the child instance.
        child_net_override = dict(net_override)
        for pin, net in self._pinmap:
            pin = pin.get_name()
            if net in net_override:
                net = net_override[net]
            elif net.startswith('.'):
                net = net_prefix + net
            child_net_override['.{}'.format(pin)] = net

        self.get_name() if not net_prefix else '{}.{}'.format(net_prefix, self.get_name())
        self._data.instantiate(
            pcb,
            transformer,
            transrot(self._coord, translate, rotate),
            self._rotation + rotate,
            child_net_prefix,
            child_net_override)

class RoutingColumn:
    """Represents a routing column."""

    def __init__(self, x_coord, net_names):
        super().__init__()
        self._x_coord = x_coord
        self._horizontals = {net: [] for net in net_names}
        self._bridges = []
        self._ranges = {}

    def get_x_coord(self):
        return self._x_coord

    def register(self, net, router_x, coord, layer):
        horizontals = self._horizontals.get(net, None)
        if horizontals is not None:
            horizontals.append((coord, layer))
            rnge = self._ranges.get(net, None)
            if rnge is None:
                rnge = [coord[1], coord[1]]
                self._ranges[net] = rnge
            else:
                rnge[0] = min(rnge[0], coord[1])
                rnge[1] = max(rnge[1], coord[1])
            assert router_x == self._x_coord
        else:
            min_x = min(router_x, coord[0])
            max_x = max(router_x, coord[0])
            if self._x_coord >= min_x and self._x_coord <= max_x:
                self._bridges.append(coord[1])

    def generate(self, pcb, transformer, translate, rotate):
        BH = from_mm(0.3)
        BW = from_mm(0.5)
        NP = 3
        b = sorted(self._bridges)
        bi = 0
        x = self._x_coord
        endpoints = set()
        for min_y, max_y in sorted(self._ranges.values()):
            endpoints.add(min_y)
            endpoints.add(max_y)
            y = min_y
            bridging = False
            path = []
            def add_to_path(coord):
                if path and path[-1] == coord:
                    return
                path.append(coord)
            while y < max_y:
                while bi < len(b) and b[bi] <= y and b[bi] < max_y:
                    bi += 1
                if not bridging:
                    y0 = None                       # no previous bridge
                    y1 = y                          # start of line
                    if bi == len(b) or b[bi] > max_y:
                        y2 = max_y                  # end of line
                        y3 = None                   # no next bridge
                    else:
                        y2 = max(y1, b[bi] - BW)    # end of line, start of next bridge
                        y3 = b[bi]                  # middle of next bridge
                else:
                    y0 = y                          # middle of previous bridge
                    if bi == len(b) or b[bi] > max_y:
                        y1 = min(y0 + BW, max_y)    # end of previous bridge, start of line
                        y2 = max_y                  # end of line
                        y3 = None                   # no next bridge
                    else:
                        y1 = y + BW                 # end of previous bridge, start of line
                        y2 = b[bi] - BW             # end of line, start of next bridge
                        y3 = b[bi]                  # middle of next bridge
                        if y1 > y2:
                            y1 = None               # no room for bridge
                            y2 = None

                if y0 is not None:
                    add_to_path((x + BH, y0))
                if y0 is not None and y1 is not None:
                    for i in range(1, NP):
                        a = i / NP * math.pi * 0.5
                        add_to_path((x + math.cos(a) * BH, y0 + math.sin(a) * (y1 - y0)))
                if y1 is not None:
                    add_to_path((x, y1))
                if y2 is not None:
                    add_to_path((x, y2))
                if y2 is not None and y3 is not None:
                    for i in range(1, NP):
                        a = i / NP * math.pi * 0.5
                        add_to_path((x + math.sin(a) * BH, y3 + math.cos(a) * (y2 - y3)))
                if y3 is not None:
                    add_to_path((x + BH, y3))

                bridging = y3 is not None
                y = y2 if y3 is None else y3

            if path:
                path = transformer.path_to_global(path, translate, rotate, True)
                pcb.add_trace('GTO', from_mm(0.2), *path)


                #pcb.add_trace('GTL', from_mm(0.2), *path)

        for horizontal in self._horizontals.values():
            for coord, layer in horizontal:
                path = [coord, (x, coord[1])]
                path = transformer.path_to_global(path, translate, rotate, True)
                pcb.add_trace('GTO', from_mm(0.2), *path)
                if coord[1] not in endpoints:
                    pcb.add_trace('GTO', from_mm(0.6), path[-1])


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
        self._net_insns = []
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
                    coord = (cols.convert(args[3]), rows.convert(args[4]))
                    self._pins.add(args[1], args[0], args[2], coord)
                    name = '.{}'.format(args[1])
                    self._net_insns.append((name, args[2], (0, 0), coord, 0.0, False, args[0]))
                    continue

                if args[0] in ('prim', 'subc'):
                    coord = (cols.convert(args[4]), rows.convert(args[5]))
                    rotation = float(args[3]) / 180 * math.pi
                    instance = Instance(
                        args[0] == 'prim', args[1], args[2],
                        coord, rotation, *args[6:]
                    )
                    for pin, net in instance.get_pinmap():
                        if pin.is_output():
                            mode = 'driver' if args[0] == 'prim' else 'in'
                        else:
                            mode = 'user' if args[0] == 'prim' else 'out'
                        self._net_insns.append((
                            net,
                            pin.get_layer(),
                            pin.get_coord(), coord, rotation,
                            args[0] == 'prim',
                            mode
                        ))
                    self._instances.append(instance)
                    continue

                if args[0] == 'route':
                    self._routers.append((cols.convert(args[1]), ['.{}'.format(x) for x in args[2:]]))
                    continue

                print('warning: unknown subcircuit construct: {}'.format(line))

        print('doing basic DRC for subcircuit {}...'.format(self._name))
        netlist = Netlist()
        for net, layer, coord, translate, rotate, _, mode in self._net_insns:
            netlist.add(net, layer, transrot(coord, translate, rotate), mode)
        good = netlist.check_subcircuit()
        unrouted = set(map(lambda x: x.get_name(), netlist.iter_logical()))
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
                for _, (_, y), _ in netlist.get_logical(net).iter_points():
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
        if not good:
            raise ValueError('basic DRC failed for subcircuit {}'.format(self._name))
        print('finished loading subcircuit {}, basic DRC passed'.format(self._name))

    def get_name(self):
        return self._name

    def get_pins(self):
        return self._pins

    def instantiate(self, pcb, transformer, translate, rotate, net_prefix, net_override):
        """Instantiates this subcircuit on the given PCB with the given
        transformer and local coordinate + rotation. Nets found in the
        net_override map will be renamed accordingly. Local nets not found
        in the map will be prefixed by net_prefix."""

        # Rebuild netlist with the correct transformations.
        netlist = Netlist()
        for net, layer, coord, trans, rot, prim, mode in self._net_insns:
            trans = transrot(trans, translate, rotate)
            rot += rotate
            netlist.add(net, layer, transformer.to_global(coord, trans, rot, not prim), mode)

        # Handle primitive artwork and netlist.
        for instance in self._instances:
            instance.instantiate(pcb, transformer, translate, rotate, net_prefix, net_override)
        for net in netlist.iter_physical():
            name = net.get_name()
            if name in net_override:
                name = net_override[name]
            elif name.startswith('.'):
                name = net_prefix + name
            for layer, coord, mode in net.iter_points():
                pcb.add_net(name, layer, coord, mode)

        # Perform routing.
        routers = [RoutingColumn(*x) for x in self._routers]
        x_coords = {net: x for x, nets in self._routers for net in nets}
        for net in netlist.iter_logical():
            for layer, coord, _ in net.iter_points():
                name = net.get_name()
                coord = transformer.to_local(coord)
                coord = transrot(coord, (-translate[0], -translate[1]), 0.0)
                coord = transrot(coord, (0, 0), -rotate)
                for router in routers:
                    router.register(name, x_coords[name], coord, layer)
        for router in routers:
            router.generate(pcb, transformer, translate, rotate)


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
    from coordinates import LinearTransformer, CircularTransformer
    from circuit_board import CircuitBoard
    import math
    pcb = CircuitBoard()
    pcb.add_outline(
        (from_mm(-45), from_mm(-45)),
        (from_mm(50), from_mm(-45)),
        (from_mm(50), from_mm(45)),
        (from_mm(-45), from_mm(45)),
        (from_mm(-45), from_mm(-45)),
    )
    t = LinearTransformer()
    t = CircularTransformer((from_mm(200), 0), from_mm(200), math.pi/2)
    get_subcircuit('decode10').instantiate(pcb, t, (from_mm(30), from_mm(-30)), -math.pi/2, '', {})
    pcb.get_netlist().check_composite()
    pcb.to_file('kek')

