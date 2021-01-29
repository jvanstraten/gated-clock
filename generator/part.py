import os

class Part:
    """Represents programmatic access to a part from the parts directory."""

    def __init__(self, name):
        super().__init__()
        if not os.path.isdir(os.path.join('parts', name)):
            raise ValueError('part {} does not exist'.format(name))
        try:
            self._name = name
            self._meta = {}
            with open(os.path.join('parts', name, 'meta.txt'), 'r') as f:
                for line in f.read().split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                    line = line.split(maxsplit=1)
                    if len(line) != 2:
                        raise ValueError('line is not key/value: {}'.format(line))
                    self._meta[line[0]] = line[1]
        except:
            print('error while loading part {}'.format(name))
            raise

    def get_name():
        """Returns the name of the part."""
        return self._name

    def __getattr__(self, attr):
        val = self._meta.get(attr, None)
        if val is None:
            raise KeyError('no attribute named {} in part {}'.format(attr, self._name))
        return val

_parts = {}

def get_part(name):
    """Loads a part from the parts directory."""
    part = _parts.get(name, None)
    if part is None:
        part = Part(name)
        _parts[name] = part
    return part
