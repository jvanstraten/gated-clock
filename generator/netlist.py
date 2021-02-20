import math
from coordinates import to_mm

class LogicalNet:
    """Represents a logical net."""

    def __init__(self, name):
        super().__init__()
        self._name = name
        self._points = set()

    def get_name(self):
        return self._name

    def add_point(self, layer, coord, mode):
        self._points.add((layer, coord, mode))

    def iter_points(self):
        for data in self._points:
            yield data

class PhysicalNet:
    """Represents a physical net."""

    def __init__(self, name):
        super().__init__()
        self._name = name
        self._logical_nets = []

    def get_name(self):
        return self._name

    def add_logical_net(self, logical_net):
        self._logical_nets.append(logical_net)

    def iter_points(self):
        for logical_net in self._logical_nets:
            for data in logical_net.iter_points():
                yield data

    def check(self, is_subcircuit, good=True):
        users = 0
        drivers = 0
        inputs = 0
        outputs = 0
        total = 0
        for _, (_, _), mode in self.iter_points():
            if mode == 'driver':
                drivers += 1
            elif mode == 'user':
                users += 1
            elif mode == 'in':
                inputs += 1
            elif mode == 'out':
                outputs += 1
            total += 1
        if is_subcircuit:
            drivers += inputs
            users += outputs
        if total < 2:
            print('DRC error: net {} has only one connection point'.format(self._name))
            good = False
        if users or drivers:
            if users == 0:
                print('DRC error: net {} is never used'.format(self._name))
                good = False
            if drivers == 0:
                print('DRC error: net {} has no drivers'.format(self._name))
                good = False
            if drivers > 1:
                print('DRC error: net {} has multiple drivers'.format(self._name))
                good = False
        if not is_subcircuit:
            if inputs < outputs:
                print('DRC error: net {} has unconnected subcircuit outputs'.format(self._name))
                good = False
            if inputs > outputs:
                print('DRC error: net {} has unconnected subcircuit inputs'.format(self._name))
                good = False
        return good

class Netlist:
    """Represents a netlist."""

    def __init__(self):
        super().__init__()
        self._logical_nets = {}
        self._physical_nets = {}
        self._net_ties = {}

    def get_physical(self, name):
        """Returns the physical net for the given name. Any * suffix is
        stripped."""
        name = name.split('*', maxsplit=1)[0]
        physical_net = self._physical_nets.get(name, None)
        if physical_net is None:
            physical_net = PhysicalNet(name)
            self._physical_nets[name] = physical_net
        return physical_net

    def iter_physical(self):
        """Iterates over all physical nets, treating nets connected via net tie
        as distinct."""
        for net in self._physical_nets.values():
            yield net

    def get_logical(self, name):
        """Returns the logical net for the given name. Adds one if it doesn't
        exist yet."""
        logical_net = self._logical_nets.get(name, None)
        if logical_net is None:
            logical_net = LogicalNet(name)
            self._logical_nets[name] = logical_net
            self.get_physical(name).add_logical_net(logical_net)
        return logical_net

    def iter_logical(self):
        """Iterates over all logical nets."""
        for net in self._logical_nets.values():
            yield net

    def add(self, name, layer, coord, mode='passive'):
        """Marks that the given coordinate on the given layer is part of the
        given logical net. mode must be 'passive', 'driver', 'user', 'in', or
        'out'."""
        if mode not in {'passive', 'driver', 'user', 'in', 'out'}:
            raise ValueError('invalid net mode')
        logical_net = self.get_logical(name)
        logical_net.add_point(layer, coord, mode)

    def add_net_tie(self, master, slave):
        """Indicates that the given two physical net names actually refer to
        different parts of the same net, connected via a net tie."""
        self._net_ties[master] = self._net_ties.get(slave, slave)

    def iter_ties(self):
        """Iterates over all the net ties."""
        return iter(self._net_ties.items())

    def get_true_net_name(self, name):
        """Returns the master net name for the given net name. This gets rid
        of ~ and * suffixes, and processes net ties."""
        name = name.split('*', maxsplit=1)[0].split('~', maxsplit=1)[0]
        name = self._net_ties.get(name, name)
        return name

    def check_subcircuit(self, good=True):
        """Checks the (physical) netlist for subcircuit DRC errors. That is:
         - all nets need at least two connection points;
         - every net with non-passive connection points must have:
            - one driver or input connection;
            - one or more user or output connections.
        """
        for net in self._physical_nets.values():
            good = net.check(True, good)
        return good

    def check_composite(self, good=True):
        """Checks the (physical) netlist for subcircuit DRC errors. That is:
         - all nets need at least two connection points;
         - every net with non-passive connection points must have:
            - one driver;
            - one or more user.
         - all nets must have an equal number of inputs and outputs.
        """
        for net in self._physical_nets.values():
            good = net.check(False, good)
        return good

    def to_file(self, fname):
        with open('{}.nets.txt'.format(fname), 'w') as f:
            for net in self.iter_physical():
                f.write('net {}\n'.format(net.get_name()))
                for layer, (x, y), mode in net.iter_points():
                    f.write('  {} {} {} {}\n'.format(
                        mode, layer, to_mm(x), to_mm(y)))

