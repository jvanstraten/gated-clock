
class Pin:
    """Represents an input or output of a primitive or subcircuit.

    translate and rotate specify the transformation of the primitive the
    pin is tied to with respect to the parent subcircuit, while coord
    specifies the coordinate in linearized primitive coordinates. If the
    pin is not tied to a primitive, translate will contain all the
    coordinate information; rotate is not needed, and coord will be
    (0, 0)."""

    def __init__(self, name, direction, layer, coord, translate, rotate):
        if layer not in ('GTL', 'GBL', 'G1', 'G2'):
            raise ValueError('layer must be GTL, GBL, G1, or G2')
        if direction not in ('in', 'out'):
            raise ValueError('direction must be in or out')
        super().__init__()
        self._name = name
        self._direction = direction
        self._layer = layer
        self._coord = coord
        self._translate = translate
        self._rotate = rotate

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

    def get_translate(self):
        return self._translate

    def get_rotate(self):
        return self._rotate

class Pins:
    """Set of pins of a primitive or subcircuit."""

    def __init__(self):
        super().__init__()
        self._pins = {}

    def add(self, name, direction, layer, coord, translate, rotate):
        if name in self._pins:
            raise ValueError('duplicate pin {}'.format(name))
        self._pins[name] = Pin(name, direction, layer, coord, translate, rotate)

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
        remain = {}
        for full_name in pins.names():
            name = full_name.split('~')[0]
            full_names = remain.get(name, None)
            if full_names is None:
                full_names = []
                remain[name] = full_names
            full_names.append(name)
        for cmd in cmds:
            name, net = cmd.split('=', maxsplit=1)
            if name in self._connections:
                raise ValueError('pin {} connected multiple times'.format(name))
            full_names = remain.pop(name, None)
            if full_names is None:
                raise ValueError('pin {} does not exist'.format(name))
            for full_name in full_names:
                self._connections[full_name] = (pins.get(full_name), '.{}'.format(net))
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
