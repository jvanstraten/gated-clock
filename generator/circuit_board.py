from coordinates import *
from part import get_part
from netlist import Netlist

class Paths:
    """Given a bunch of short paths (or just segments) and flashes, tries to
    join paths together."""

    def __init__(self):
        super().__init__()
        self._endps = {}

    def _pop_path(self, coord, suffix):
        path = self._endps.get(coord, None)
        if path is None:
            return [coord]
        self._endps.pop(path[0], None)
        self._endps.pop(path[-1], None)
        return path

    def add(self, *path):
        path = list(path)
        assert len(path) >= 1
        if len(path) == 1:
            if path[0] not in self._endps:
                self._endps[path[0]] = path
            return

        prefix = self._pop_path(path[0], False)
        if prefix[-1] != path[0]:
            prefix.reverse()
        assert prefix[-1] == path[0]

        suffix = self._pop_path(path[-1], True)
        if suffix[0] != path[-1]:
            suffix.reverse()
        assert suffix[0] == path[-1]

        path = prefix + path[1:-1] + suffix

        self._endps[path[0]] = path
        self._endps[path[-1]] = path

    def __iter__(self):
        ids = set()
        for path in self._endps.values():
            if id(path) not in ids:
                ids.add(id(path))
                yield path

class GerberLayer:
    """Represents a Gerber layer of a PCB."""

    def __init__(self, name):
        super().__init__()
        self._name = name
        self._paths = {}

    def get_name(self):
        return self._name

    def add_path(self, aper, *path):
        paths = self._paths.get(aper, None)
        if paths is None:
            paths = Paths()
            self._paths[aper] = paths
        paths.add(*path)

    def to_file(self, fname):
        fname = '{}.{}'.format(fname, self._name if self._name != 'Mill' else 'GM1')
        with open(fname, 'w') as f:
            f.write('%FSLAX44Y44*%\n%MOMM*%\nG71*\nG01*\nG75*\n')
            data = []
            for aper, paths in self._paths.items():
                idx = len(data) + 10
                data.append((idx, paths))
                if isinstance(aper, int):
                    f.write('%ADD{:02}C,{}*%\n'.format(idx, to_grb_mm(aper)))
                else:
                    f.write('%AMSHAPE{}*\n4,1,{},'.format(idx, len(aper)))
                    for coord in list(aper) + [aper[0]]:
                        f.write('{},{},'.format(to_grb_mm(coord[0]), to_grb_mm(coord[1])))
                    f.write('0.0*\n%\n%ADD{:02}SHAPE{}*%\n'.format(idx, idx))
            f.write('%LPD*%\n')
            x = None
            y = None
            for idx, paths in data:
                f.write('D{:02}*\n'.format(idx))
                for path in paths:
                    for i, coord in enumerate(path):
                        if x != coord[0]:
                            x = coord[0]
                            f.write('X{}'.format(to_grb_int(x)))
                        if y != coord[1]:
                            y = coord[1]
                            f.write('Y{}'.format(to_grb_int(y)))
                        if i == 0:
                            f.write('D02*\n')
                        else:
                            f.write('D01*\n')
                    if len(path) == 1:
                        f.write('D03*\n')
            f.write('M02*\n')

class DrillLayer:
    """Represents a drilling layer."""

    def __init__(self):
        super().__init__()
        self._holes = {}

    def add_hole(self, coord, dia, plated=False):
        """Drills a hole. Dimensions are integer nanometers."""
        key = (dia, plated)
        points = self._holes.get(key, None)
        if points is None:
            points = []
            self._holes[key] = points
        points.append(coord)

    def to_file(self, fname):
        fname = '{}.TXT'.format(fname)
        with open(fname, 'w') as f:
            f.write('M48\n;FILE_FORMAT=4:4\nMETRIC,LZ\n')
            data = []
            for do_plated in [True, False]:
                first = True
                for (dia, plated), points in self._holes.items():
                    if plated != do_plated:
                        continue
                    if first:
                        if do_plated:
                            f.write(';TYPE=PLATED\n')
                        else:
                            f.write(';TYPE=NON_PLATED\n')
                        first = False
                    idx = len(data) + 1
                    data.append((idx, points))
                    f.write('T{}F00S00C{}\n'.format(idx, to_ncd_mm(dia)))
            f.write('%\n')
            x = None
            y = None
            for idx, points in data:
                f.write('T{:02}\n'.format(idx))
                for coord in points:
                    either = False
                    if x != coord[0]:
                        x = coord[0]
                        f.write('X{}'.format(to_ncd_int(x)))
                        either = True
                    if y != coord[1]:
                        y = coord[1]
                        f.write('Y{}'.format(to_ncd_int(y)))
                        either = True
                    assert either
                    f.write('\n')
            f.write('M30\n')

class Net:
    """Represents a physical net."""

    def __init__(self, name):
        super().__init__()
        self._name = name
        self._points = set()

    def get_name(self):
        return self._name

    def add_point(self, layer, coord):
        self._points.add((layer, coord))

class PartInstance:
    """Represents an instance of a part."""

    def __init__(self, name, layer, coord, rotation):
        if layer not in ('Ctop', 'Cbottom'):
            raise ValueError('layer must be Ctop or Cbottom')
        super().__init__()
        self._part = get_part(name)
        self._layer = layer
        self._coord = coord
        self._rotation = rotation

    def get_name(self):
        return self._name

    def get_layer(self):
        return self._layer

    def get_coord(self):
        return self._coord

    def get_rotation(self):
        return self._rotation

class CircuitBoard:
    """Represents (part of) a PCB."""

    def __init__(self):
        super().__init__()
        self._layers = {
            layer: GerberLayer(layer) for layer in [
                'GTO', 'GTS',
                'GTL', 'G1', 'G2', 'GBL',
                'GBS', 'GBO',
                'Mill'
            ]
        }
        self._drill = DrillLayer()
        self._netlist = Netlist()
        self._parts = []

    def add_trace(self, layer, thickness, *path):
        """Adds a trace. Dimensions are integer nanometers."""
        self._layers[layer].add_path(thickness, *path)

    def add_flash(self, layer, aperture, coord):
        """Adds a pad. Dimensions are integer nanometers. Aperture must be a
        tuple of coords that form a path relative to the flash coordinate, or
        a single integer for a circular flash, in which case it is the
        diameter."""
        self._layers[layer].add_path(aperture, coord)

    def add_flashed_region(self, layer, *path):
        """Adds a pad. Dimensions are integer nanometers. Path specifies the
        absolute referenced path to is to be flashed. The actual flash will
        be at the mean position."""
        mx = 0
        my = 0
        for coord in path:
            mx += coord[0]
            my += coord[1]
        mx //= len(path)
        my //= len(path)
        aperture = tuple(((x - mx, y - my) for x, y in path))
        self.add_flash(layer, aperture, (mx, my))

    def add_outline(self, *path):
        """Adds a trace to the outline. Dimensions are integer nanometers."""
        self.add_trace('Mill', from_mm(0.1), *path)

    def add_hole(self, coord, dia, plated=False):
        """Drills a hole. Dimensions are integer nanometers."""
        self._drill.add_hole(coord, dia, plated)

    def add_via(self, coord, inner=from_mm(0.35), outer=from_mm(0.65)):
        """Adds a via. Dimensions are integer nanometers."""
        self.add_hole(coord, inner, True)
        self.add_flash('GTL', outer, coord)
        self.add_flash('G1', outer, coord)
        self.add_flash('G2', outer, coord)
        self.add_flash('GBL', outer, coord)

    def add_net(self, name, layer, coord, driver=None):
        """Indicates that the copper at layer/coord is connected to the given
        net. Dimensions are integer nanometers. If driver is set to True, a
        driver is also added for the net. If driver is set to False, a user
        is added for the net."""
        self._netlist.add(name, layer, coord, driver)

    def add_part(self, name, layer, coord, rotation):
        """Adds a soldered part to the PCB."""
        self._parts.append(PartInstance(name, layer, coord, rotation))

    def to_file(self, fname):
        for layer in self._layers.values():
            layer.to_file(fname)
        self._drill.to_file(fname)
