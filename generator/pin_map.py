
class Pin:
    """Represents an input or output of a primitive or subcircuit."""

    def __init__(self, name, direction, layer, coord):
        if layer not in ('GTL', 'GBL', 'G1', 'G2'):
            raise ValueError('layer must be GTL, GBL, G1, or G2')
        if direction not in ('in', 'out'):
            raise ValueError('direction must be in or out')
        super().__init__()
        self._name = name
        self._direction = direction
        self._layer = layer
        self._coord = coord

    def get_name(self):
        return self._name

    def get_direction(self):
        return self._direction

    def is_input(self):
        return self._direction == 'in'

    def is_output(self):
        return self._direction == 'out'

    def get_layer(self):
        return self._layer

    def get_coord(self):
        return self._coord

class Pins:
    """Set of pins of a primitive or subcircuit."""

    def __init__(self):
        super().__init__()
        self._pins = {}

    def add(self, name, direction, layer, coord):
        if name in self._pins:
            raise ValueError('duplicate pin {}'.format(name))
        self._pins[name] = Pin(name, direction, layer, coord)

    def get(self, name):
        return self._pins[name]

    def names(self):
        return set(self._pins)

class PinMap:
    """Mapping of pins of a primitive or subcircuit to net names in the parent
    circuit."""

    def __init__(self, pins, *cmds):
        super().__init__()
        self._connections = {}
        remain = pins.names()
        for cmd in cmds:
            pin, net = cmd.split('=', maxsplit=1)
            if pin in self._connections:
                raise ValueError('pin {} connected multiple times'.format(pin))
            if pin not in remain:
                raise ValueError('pin {} does not exist'.format(pin))
            remain.remove(pin)
            self._connections[pin] = (pins.get(pin), '.{}'.format(net))
        for pin in remain:
            raise ValueError('pin {} is not connected'.format(pin))

    def get(self, pin):
        """Returns the Pin object and the name of the net in the parent circuit
        it connects to."""
        return self._connections[pin]

    def __iter__(self):
        """Yields all Pin object/parent circuit netname pairs."""
        for data in self._connections.values():
            yield data
