from coordinates import *
from part import get_part
from netlist import Netlist
from paths import Paths
from acrylic import LaseredAcrylic
import gerbertools
import sys

class Region:
    """Represents a filled region."""

    def __init__(self, path, polarity=True, plane_cutout=True):
        super().__init__()
        assert path[0] == path[-1]
        self._path = path
        self._polarity = polarity
        self._plane_cutout = plane_cutout

    def get_path(self):
        return tuple(self._path)

    def get_polarity(self):
        return self._polarity

    def is_plane_cutout(self):
        return self._plane_cutout

class GerberLayer:
    """Represents a Gerber layer of a PCB."""

    def __init__(self, name, expansion=0.0):
        super().__init__()
        self._name = name
        self._expansion = expansion
        self._paths = {}
        self._regions = []

    def get_name(self):
        return self._name

    def add_path(self, aper, *path):

        if self._expansion > 0.0:
            if isinstance(aper, tuple):
                s = gerbertools.Shape(1e6)
                s.append_int(aper)
                s = s.offset(self._expansion, True)
                assert len(s) == 1
                aper = tuple(s.get_int(0))
            else:
                aper += from_mm(self._expansion)

        paths = self._paths.get(aper, None)

        # Due to roundoff error during rotation, some almost-identical
        # (actually identical in the gerber file) apertures can appear
        # for region apertures. To avoid this, look for apertures that
        # are "close enough".
        if paths is None and isinstance(aper, tuple):
            for ap2 in self._paths:
                if not isinstance(ap2, tuple):
                    continue
                if len(aper) != len(ap2):
                    continue
                err = 0
                for c1, c2 in zip(aper, ap2):
                    err += (c1[0] - c2[0])**2
                    err += (c1[1] - c2[1])**2
                    if err > 10:
                        break
                else:
                    aper = ap2
                    paths = self._paths[aper]
                    break

        if paths is None:
            paths = Paths()
            self._paths[aper] = paths
        paths.add(*path)

    def _add_region(self, polarity, is_plane_cutout, *path):
        if self._expansion > 0.0:
            s = gerbertools.Shape(1e6)
            s.append_int(aper)
            s = s.offset(self._expansion if polarity else -self._expansion, True)
            if len(s) == 0:
                return
            assert len(s) == 1
            path = tuple(s.get_int(0))
        self._regions.append(Region(path, polarity, is_plane_cutout))

    def add_region(self, polarity, *path):
        self._add_region(polarity, True, *path)

    def add_region_no_cutout(self, polarity, *path):
        self._add_region(polarity, False, *path)

    def get_poly_cutout(self):
        s = gerbertools.Shape(1e6)
        for region in self._regions:
            if region.is_plane_cutout():
                x = gerbertools.Shape(1e6)
                x.append_int(region.get_path())
                if region.get_polarity():
                    s = s + x
                else:
                    s = s - x
        for aper, paths in self._paths.items():
            for path in paths:
                x = gerbertools.Shape(1e6)
                if isinstance(aper, int):
                    x.append_int(path)
                    x = x.render(to_mm(aper), False)
                else:
                    assert len(path) == 1
                    flash = path[0]
                    x.append_int([(ap[0] + flash[0], ap[1] + flash[1]) for ap in list(aper) + [aper[0]]])
                s = s + x
        return s

    def to_file(self, fname):
        fname = '{}.{}'.format(fname, self._name if self._name != 'Mill' else 'GM1')
        with open(fname, 'w') as f:

            # Header. More or less the same as what Altium does.
            f.write('%FSLAX44Y44*%\n%MOMM*%\nG71*\nG01*\nG75*\n')

            # Configure apertures. We write the data out in the same order that
            # the apertures are defined in because that's what Altium does.
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

            # Write the regions.
            polarity = None
            for region in self._regions:
                x = None
                y = None
                pol = region.get_polarity()
                if polarity != pol:
                    if pol:
                        f.write('%LPD*%\n')
                    else:
                        f.write('%LPC*%\n')
                    polarity = pol
                f.write('G36*\n')
                for i, coord in enumerate(region.get_path()):
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
                f.write('D02*\nG37*\n')

            # Write traces and flashes.
            x = None
            y = None
            if polarity is not True:
                f.write('%LPD*%\n')
                polarity = True
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

            # M02 to terminate file.
            f.write('M02*\n')

    def instantiate(self, pcb, transformer, translate, rotate, warpable):
        """Instantiates the contents of this layer onto the given PCB with the
        given transformer and local translation + rotation."""
        assert self._expansion == 0
        for aper, paths in self._paths.items():
            for path in paths:
                if isinstance(aper, int):
                    pcb.add_trace(
                        self._name,
                        aper,
                        *transformer.path_to_global(
                            path,
                            translate,
                            rotate,
                            warpable
                        )
                    )
                else:
                    assert len(path) == 1
                    flash = path[0]
                    path = [(ap[0] + flash[0], ap[1] + flash[1]) for ap in list(aper) + [aper[0]]]
                    path = transformer.path_to_global(path, translate, rotate, warpable)[:-1]
                    pcb.add_flashed_region(
                        self._name,
                        *path
                    )
        for region in self._regions:
            path = transformer.path_to_global(region.get_path(), translate, rotate, warpable)
            pcb.add_region(self._name, region.get_polarity(), *path)

class DrillLayer:
    """Represents a drilling layer."""

    def __init__(self):
        super().__init__()
        self._holes = {}

    def add_hole(self, coord, dia, plated=False):
        """Drills a hole. Dimensions are integer nanometers."""
        for (dia2, _), coords in self._holes.items():
            for coord2 in coords:
                dist = math.hypot(coord[0] - coord2[0], coord[1] - coord2[1])
                if dist < (dia + dia2) / 2 + from_mm(0.5):
                    print('holes too close! {} dia {} and {} dia {}, dist {}, former ignored'.format(
                        coord, to_mm(dia), coord2, to_mm(dia2), to_mm(dist)))
                    return False
        key = (dia, plated)
        points = self._holes.get(key, None)
        if points is None:
            points = []
            self._holes[key] = points
        points.append(coord)
        return True

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

    def instantiate(self, pcb, transformer, translate, rotate, warpable):
        """Instantiates the contents of this layer onto the given PCB with the
        given transformer and local translation + rotation."""
        for (dia, plated), points in self._holes.items():
            for coord in points:
                coord = transformer.to_global(coord, translate, rotate, warpable)
                pcb.add_hole(coord, dia, plated, True)

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
        self._name = name
        self._part = get_part(name)
        self._layer = layer
        self._coord = coord
        self._rotation = rotation

    def get_name(self):
        return self._name

    def get_part(self):
        return self._part

    def get_layer(self):
        return self._layer

    def get_coord(self):
        return self._coord

    def get_rotation(self):
        return self._rotation

class CircuitBoard:
    """Represents (part of) a PCB."""

    def __init__(self, mask_expansion=0.0):
        super().__init__()
        self._layers = {
            layer: GerberLayer(layer, mask_expansion if layer.endswith('S') else 0.0) for layer in [
                'GTO', 'GTS',
                'GTL', 'G1', 'G2', 'GBL',
                'GBS', 'GBO',
                'Mill'
            ]
        }
        self._drill = DrillLayer()
        self._netlist = Netlist()
        self._parts = []
        self._plates = LaseredAcrylic()

    def get_plates(self):
        return self._plates

    def get_netlist(self):
        return self._netlist

    def get_parts(self):
        return self._parts

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

    def add_region(self, layer, polarity, *path):
        """Adds a region. Dimensions are integer nanometers. The path must
        explicitly start and end in the same location. polarity True means
        dark, False means clear. Regions are written to the Gerber file before
        traces and flashes, so a clear region won't remove those, but clear
        regions will make holes in previously added dark regions."""
        assert path[0] == path[-1]
        self._layers[layer].add_region(polarity, *path)

    def add_outline(self, *path):
        """Adds a trace to the outline. Dimensions are integer nanometers."""
        assert path[0] == path[-1]
        self.add_trace('Mill', from_mm(0.1), *path)

    def add_hole(self, coord, dia, plated=False, tented=False):
        """Drills a hole. Dimensions are integer nanometers."""
        if not self._drill.add_hole(coord, dia, plated):
            for i in range(5):
                a = math.pi * i / 2.5
                self.add_trace('GTO', from_mm(0.1), coord, (
                    int(coord[0] + from_mm(3)*math.sin(a)),
                    int(coord[1] + from_mm(3)*math.cos(a))
                ))
        if not tented:
            self.add_flash('GTS', dia, coord)
            self.add_flash('GBS', dia, coord)

    def add_via(self, coord, inner=from_mm(0.35), outer=from_mm(0.65)):
        """Adds a via. Dimensions are integer nanometers."""
        self.add_hole(coord, inner, True, True)
        self.add_flash('GTL', outer, coord)
        self.add_flash('G1', outer, coord)
        self.add_flash('G2', outer, coord)
        self.add_flash('GBL', outer, coord)

    def add_pth_pad(self, coord, inner, outer):
        """Adds a plated through-hole pad. Dimensions are integer nanometers."""
        self.add_via(coord, inner, outer)
        self.add_flash('GTS', outer, coord)
        self.add_flash('GBS', outer, coord)

    def add_net(self, name, layer, coord, mode='passive'):
        """Indicates that the copper at layer/coord is connected to the given
        net. Dimensions are integer nanometers. Mode must be 'passive',
        'driver', 'user', 'in', or 'out'."""
        self._netlist.add(name, layer, coord, mode)

    def add_net_tie(self, master, slave):
        print('TIE', master, slave)
        self._netlist.add_net_tie(master, slave)

    def add_part(self, name, layer, coord, rotation):
        """Adds a soldered part to the PCB."""
        self._parts.append(PartInstance(name, layer, coord, rotation))

    def add_poly_pours(self, clearance=0.2):
        """Adds the polygon pours for the inner layers."""
        outline = gerbertools.Shape(1e6)
        for aperture, paths in self._layers['Mill']._paths.items():
            assert isinstance(aperture, int)
            for path in paths:
                assert path[0] == path[-1]
                outline.append_int(path)

        holes = gerbertools.Shape(1e6)
        for (dia, _), points in self._drill._holes.items():
            x = gerbertools.Shape(1e6)
            for point in points:
                x.append_int([point])
            x = x.render(to_mm(dia), False)
            holes = holes + x

        outline = outline - holes
        outline = outline.offset(-clearance)

        for layer_name in ('G1', 'G2'):
            shape = outline - self._layers[layer_name].get_poly_cutout().offset(clearance)
            for i in range(len(shape)):
                path = shape.get_int(i)
                path = list(path) + [path[0]]
                winding = 0
                for (x1, y1), (x2, y2) in zip(path[1:], path[:-1]):
                    winding += (x2 - x1) * (y2 + y1)
                self.add_region(layer_name, winding > 0, *path)

    def to_file(self, fname):
        pcb_fname = '{}.PCB'.format(fname)
        for layer in self._layers.values():
            layer.to_file(pcb_fname)
        self._drill.to_file(pcb_fname)
        self._netlist.to_file(fname)
        with open('{}.parts.txt'.format(fname), 'w') as f:
            for inst in self._parts:
                f.write('{} {} {} {} {}\n'.format(
                    inst.get_name(),
                    inst.get_layer(),
                    to_mm(inst.get_coord()[0]),
                    to_mm(inst.get_coord()[1]),
                    inst.get_rotation() * 180 / math.pi
                ))
        self._plates.to_file(fname, *sys.argv[1:])

    def instantiate(self, pcb, transformer, translate, rotate, warpable, net_prefix, net_override):
        """Instantiates the contents of this PCB onto the given PCB with the
        given transformer and local translation + rotation. Nets found in the
        net_override map will be renamed accordingly. Local nets not found
        in the map will be prefixed by net_prefix."""

        # Gerber layers.
        for layer in self._layers.values():
            layer.instantiate(pcb, transformer, translate, rotate, warpable)

        # Drill data.
        self._drill.instantiate(pcb, transformer, translate, rotate, warpable)

        # Netlist data.
        for net in self._netlist.iter_physical():
            name = net.get_name().split('~')[0].split('*')[0]
            if name in net_override:
                name = net_override[name]
            elif name.startswith('.'):
                name = net_prefix + name
            for layer, coord, mode in net.iter_points():
                pcb.add_net(
                    name,
                    layer,
                    transformer.to_global(coord, translate, rotate, warpable),
                    mode)

        # Assembly data.
        for part_inst in self._parts:
            pcb.add_part(
                part_inst.get_name(),
                part_inst.get_layer(),
                *transformer.part_to_global(
                    part_inst.get_coord(), part_inst.get_rotation(),
                    translate, rotate, warpable
                )
            )

        # Lasered acrylic plates (if any).
        self._plates.instantiate(pcb.get_plates(), transformer, translate, rotate)
