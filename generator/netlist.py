
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
        self._n_drivers = 0
        self._n_users = 0
        self._logical_nets = []

    def get_name(self):
        return self._name

    def add_logical_net(self, logical_net):
        self._logical_nets.append(logical_net)

    def iter_points(self):
        for logical_net in self._logical_nets:
            for data in logical_net.iter_points():
                yield data

    def use(self):
        self._n_users += 1

    def drive(self):
        self._n_drivers += 1

    def check(self, good=True):
        if self._n_users == 0:
            print('DRC error: net {} is never used'.format(self._name))
            good = False
        if self._n_drivers == 0:
            print('DRC error: net {} has no drivers'.format(self._name))
            good = False
        if self._n_drivers > 1:
            print('DRC error: net {} has multiple drivers'.format(self._name))
            good = False
        return good

class Netlist:
    """Represents a netlist."""

    def __init__(self):
        super().__init__()
        self._logical_nets = {}
        self._physical_nets = {}

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
        """Iterates over all physical nets."""
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
        logical_net = self.get_logical(name)
        logical_net.add_point(layer, coord, mode)
        if mode in ('driver', 'in'):
            self.get_physical(name).drive()
        elif mode in ('user', 'out'):
            self.get_physical(name).use()

    def check(self, good=True):
        """Checks the netlist for subcircuit DRC errors."""
        for net in self._physical_nets.values():
            good = net.check(good)
        return good
