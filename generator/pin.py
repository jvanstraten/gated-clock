
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

