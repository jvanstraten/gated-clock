
from paths import Paths
from coordinates import from_mm, to_mm
import gerbertools
import subprocess
import os

class LaseredAcrylicPlate:

    def __init__(self, material, thickness, flipped=False):
        super().__init__()
        self._cuts = Paths()
        self._lines = Paths()
        self._regions = []
        self._material = material
        self._thickness = thickness
        self._flipped = flipped

    def add_cut(self, *path):
        self._cuts.add(*path)

    def add_line(self, *path):
        self._lines.add(*path)

    def add_region(self, *path):
        assert path[-1] == path[0]
        assert len(path) > 2
        self._regions.append(path)

    def get_material(self):
        return self._material

    def get_thickness(self):
        return self._thickness

    def is_flipped(self):
        return self._flipped

    def iter_cuts(self):
        return iter(self._cuts)

    def iter_lines(self):
        return iter(self._lines)

    def iter_regions(self):
        return iter(self._regions)

    def get_bounds(self):
        x_min = None
        x_max = None
        y_min = None
        y_max = None
        for paths in (self._cuts, self._lines, self._regions):
            for path in paths:
                for x, y in path:
                    if x_max is None:
                        x_min = x
                        x_max = x
                        y_min = y
                        y_max = y
                    else:
                        x_min = min(x_min, x)
                        x_max = max(x_max, x)
                        y_min = min(y_min, y)
                        y_max = max(y_max, y)
        if x_min is None:
            return 0, 0, 0, 0
        return x_min, x_max, y_min, y_max

    def instantiate(self, plate, transformer, translate, rotate):
        for path in self._cuts:
            plate.add_cut(*transformer.path_to_global(path, translate, rotate, True))
        for path in self._lines:
            plate.add_line(*transformer.path_to_global(path, translate, rotate, True))
        for path in self._regions:
            plate.add_region(*transformer.path_to_global(path, translate, rotate, True))


class LaseredAcrylic:

    def __init__(self):
        super().__init__()
        self._plates = {}

    def add(self, name, material, thickness, flipped=False):
        assert name not in self._plates
        plate = LaseredAcrylicPlate(material, thickness, flipped)
        self._plates[name] = plate
        return plate

    def get(self, name):
        return self._plates[name]

    def has_plate(self, name):
        return name in self._plates

    def instantiate(self, plates, transformer, translate, rotate):
        for name, data in self._plates.items():
            plate = plates._plates.get(name, None)
            if plate is None:
                plate = plates.add(name, data.get_material(), data.get_thickness(), data.is_flipped())
            data.instantiate(plate, transformer, translate, rotate)

    def to_file(self, fname, name='...', email='...', telephone='...'):
        cutting_layer = []
        engrave_line_layer = []
        engrave_region_layer = []
        outline_layer = []
        notes_layer = []

        drawing_w = 0
        drawing_h = 0

        def to_svg(x):
            # 90 DPI for some reason
            return to_mm(x) * 90 / 25.4

        ident_counter = [0]
        def ident(prefix=''):
            ident_counter[0] += 1
            return '{}{}'.format(prefix, ident_counter[0])

        for index, plate in enumerate(self._plates.values()):
            sizes = list(map(from_mm, [200, 300, 450, 600, 900]))
            x_min, x_max, y_min, y_max = plate.get_bounds()
            w = x_max - x_min
            h = y_max - y_min
            if w == 0 or h == 0:
                continue
            cx = (x_max + x_min) / 2
            cy = (y_max + y_min) / 2
            flipped = plate.is_flipped()
            for idx, (w_total, h_total) in enumerate(zip(sizes[1:], sizes[:-1])):
                if w < w_total - from_mm(10) and h < h_total - from_mm(10):
                    swap_xy = False
                    break
                if h < w_total - from_mm(10) and w < h_total - from_mm(10):
                    swap_xy = True
                    flipped = not flipped
                    break
            else:
                assert False

            def coord_to_svg(coord):
                x, y = coord
                x -= cx
                y -= cy
                if swap_xy:
                    x, y = y, x
                if flipped:
                    x = -x
                y = -y
                x += w_total / 2 + from_mm(50) + drawing_w
                y += h_total / 2 + from_mm(400)
                return to_svg(x), to_svg(y)

            def svg_path(path):
                closed = path[0] == path[-1] and len(path) > 2
                if closed:
                    path = path[:-1]
                data = []
                for coord in path:
                    if not data:
                        data.append('M')
                    else:
                        data.append('L')
                    data.append('{},{}'.format(*coord_to_svg(coord)))
                if closed:
                    data.append('Z')
                return ' '.join(data)

            for path in plate.iter_cuts():
                cutting_layer.append((
                    '<path inkscape:connector-curvature="0" id="{}" ' +
                    'style="display:inline;fill:none;stroke:#ff0000;' +
                    'stroke-width:{};stroke-linecap:square;stroke-linejoin:miter;' +
                    'stroke-miterlimit:10;stroke-dasharray:none;stroke-opacity:1" ' +
                    'd="{}" />').format(
                        ident('path'),
                        to_svg(from_mm(0.05)),
                        svg_path(path)
                    )
                )

            for path in plate.iter_lines():
                engrave_line_layer.append((
                    '<path inkscape:connector-curvature="0" id="{}" ' +
                    'style="display:inline;fill:none;stroke:#0000ff;' +
                    'stroke-width:{};stroke-linecap:square;stroke-linejoin:miter;' +
                    'stroke-miterlimit:10;stroke-dasharray:none;stroke-opacity:1" ' +
                    'd="{}" />').format(
                        ident('path'),
                        to_svg(from_mm(0.05)),
                        svg_path(path)
                    )
                )

            for path in plate.iter_regions():
                engrave_region_layer.append((
                    '<path inkscape:connector-curvature="0" id="{}" ' +
                    'style="fill:#000000;fill-opacity:1;stroke:none;' +
                    'stroke-width:0.5;stroke-linecap:square;stroke-linejoin:miter;' +
                    'stroke-miterlimit:10;stroke-dasharray:none;stroke-opacity:1" ' +
                    'd="{}" />').format(
                        ident('path'),
                        svg_path(path)
                    )
                )

            outline_layer.append((
                '<rect id="{}" x="{}" y="{}" width="{}" height="{}" ' +
                'style="display:inline;opacity:1;fill:none;stroke:#00ff00;' +
                'stroke-width:{};stroke-miterlimit:4;stroke-dasharray:none;' +
                'stroke-dashoffset:0;stroke-opacity:1" />').format(
                    ident('rect'),
                    to_svg(from_mm(50) + drawing_w), to_svg(from_mm(400)),
                    to_svg(w_total), to_svg(h_total),
                    to_svg(from_mm(1))
                )
            )

            notes_layer.append((
                '<rect id="{}" x="{}" y="{}" width="{}" height="{}" ' +
                'style="display:inline;fill:none;fill-rule:evenodd;stroke:#000000;' +
                'stroke-width:{};stroke-linecap:butt;stroke-linejoin:miter;' +
                'stroke-miterlimit:4;stroke-dasharray:14.17885439, 28.35770877999999939;' +
                'stroke-dashoffset:0;stroke-opacity:1;" />').format(
                    ident('rect'),
                    to_svg(from_mm(55) + drawing_w), to_svg(from_mm(405)),
                    to_svg(w_total - from_mm(10)), to_svg(h_total - from_mm(10)),
                    to_svg(from_mm(1))
                )
            )

            notes_layer.append("""<flowRoot
                transform="translate({},{})"
                style="font-style:normal;font-weight:normal;line-height:0.01%;font-family:roboto;letter-spacing:0px;word-spacing:0px;display:inline;fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;-inkscape-font-specification:roboto;font-stretch:normal;font-variant:normal;"
                id="flowRoot{}"
                xml:space="preserve"><flowRegion
                style="-inkscape-font-specification:roboto;font-family:roboto;font-weight:normal;font-style:normal;font-stretch:normal;font-variant:normal;"
                id="flowRegion{}"><rect
                    style="font-size:68.75px;-inkscape-font-specification:roboto;font-family:roboto;font-weight:normal;font-style:normal;font-stretch:normal;font-variant:normal;"
                    y="-1000.7537"
                    x="-265.16504"
                    height="1199.8718"
                    width="2079.3359"
                    id="rect{}" /></flowRegion><flowPara
                style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:141.732px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;"
                id="flowPara{}">PLAAT#: {:02d}</flowPara><flowPara
                id="flowPara{}"
                style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:88.5827px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;">{}X{}mm</flowPara><flowPara
                id="flowPara{}"
                style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:88.5827px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;"> </flowPara><flowPara
                id="flowPara{}"
                style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:88.5827px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;">MATERIAAL: {}</flowPara><flowPara
                id="flowPara{}"
                style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:88.5827px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;">DIKTE: {}</flowPara></flowRoot>""".format(
                    to_svg(from_mm(125) + drawing_w), to_svg(from_mm(500)),
                    ident(), ident(), ident(), ident(), index+1,
                    ident(), int(round(to_mm(w_total))), int(round(to_mm(h_total))),
                    ident(), ident(), plate.get_material(), ident(), plate.get_thickness()
                )
            )

            drawing_w += w_total + from_mm(300)
            drawing_h = max(drawing_h, h_total + from_mm(450))

        if drawing_w == 0:
            if os.path.isfile('{}.svg'.format(fname)):
                os.unlink('{}.svg'.format(fname))
            if os.path.isfile('{}.pdf'.format(fname)):
                os.unlink('{}.pdf'.format(fname))
            return

        svg = []
        svg.append((
            '<svg xmlns:dc="http://purl.org/dc/elements/1.1/" ' +
            'xmlns:cc="http://creativecommons.org/ns#" ' +
            'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" ' +
            'xmlns:svg="http://www.w3.org/2000/svg" ' +
            'xmlns="http://www.w3.org/2000/svg" ' +
            'xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd" ' +
            'xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" ' +
            'sodipodi:docname="Inkscape-Template-V2-0-NL.svg" ' +
            'inkscape:version="1.0 (4035a4fb49, 2020-05-01)" ' +
            'viewBox="0 0 {} {}" width="{}mm" height="{}mm">').format(
                to_svg(drawing_w), to_svg(drawing_h),
                to_mm(drawing_w), to_mm(drawing_h)
            )
        )
        svg.append((
            '<sodipodi:namedview  inkscape:document-rotation="0" ' +
            'inkscape:window-maximized="1" inkscape:window-y="-8" ' +
            'inkscape:window-x="-8" inkscape:window-height="987" ' +
            'inkscape:window-width="1680" inkscape:snap-global="false" ' +
            'inkscape:guide-bbox="true" showguides="true" showgrid="false" ' +
            'inkscape:current-layer="layer1" inkscape:document-units="mm" ' +
            'inkscape:cy="{}" inkscape:cx="{}" inkscape:zoom="1" ' +
            'inkscape:pageshadow="2" inkscape:pageopacity="0.0" ' +
            'borderopacity="1.0" bordercolor="#666666" pagecolor="#ffffff" ' +
            'id="base" />').format(to_svg(drawing_w / 2), to_svg(drawing_h / 2))
        )
        svg.append('<g style="display:inline" inkscape:label="01_SNIJLIJNEN" id="layer1" inkscape:groupmode="layer">')
        svg.extend(cutting_layer)
        svg.append('</g>')
        svg.append('<g style="display:inline" inkscape:label="02_GRAVEERLIJNEN" id="layer2" inkscape:groupmode="layer">')
        svg.extend(engrave_line_layer)
        svg.append('</g>')
        svg.append('<g style="display:inline" inkscape:label="03_GRAVEERVLAKKEN" id="layer3" inkscape:groupmode="layer">')
        svg.extend(engrave_region_layer)
        svg.append('</g>')
        svg.append('<g style="display:inline" inkscape:label="04_WERKBLAD" id="layer4" inkscape:groupmode="layer">')
        svg.extend(outline_layer)
        svg.append('</g>')
        svg.append('<g style="display:inline" inkscape:label="05_TEKSTEN_INSTRUCTIES" id="layer5" inkscape:groupmode="layer">')
        svg.extend(notes_layer)
        svg.append("""<flowRoot
          transform="translate({},{})"
          style="font-style:normal;font-weight:normal;line-height:0.01%;font-family:roboto;letter-spacing:0px;word-spacing:0px;display:inline;fill:#000000;fill-opacity:1;stroke:none;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1;-inkscape-font-specification:roboto;font-stretch:normal;font-variant:normal;"
          id="flowRoot{}"
          xml:space="preserve"><flowRegion
            style="-inkscape-font-specification:roboto;font-family:roboto;font-weight:normal;font-style:normal;font-stretch:normal;font-variant:normal;"
            id="flowRegion{}"><rect
              style="font-size:68.75px;-inkscape-font-specification:roboto;font-family:roboto;font-weight:normal;font-style:normal;font-stretch:normal;font-variant:normal;"
              y="-1000.7537"
              x="-265.16504"
              height="1199.8718"
              width="2079.3359"
              id="rect{}" /></flowRegion><flowPara
            id="flowPara{}"
            style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:141.732px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;">NAAM: {}</flowPara><flowPara
            id="flowPara{}"
            style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:141.732px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;">E-MAIL: {}</flowPara><flowPara
            id="flowPara{}"
            style="font-style:normal;font-variant:normal;font-weight:normal;font-stretch:normal;font-size:141.732px;line-height:1.25;font-family:roboto;-inkscape-font-specification:roboto;">TELEFOON: {}</flowPara></flowRoot>""".format(
                to_svg(from_mm(125)), to_svg(from_mm(300)),
                ident(), ident(), ident(), ident(), name, ident(), email, ident(), telephone
            )
        )
        svg.append('</g>')
        svg.append('</svg>')

        with open('{}.svg'.format(fname), 'w') as f:
            f.write('\n'.join(svg) + '\n')

        subprocess.run(['inkscape', '-C', '-A', '{}.pdf'.format(fname), '{}.svg'.format(fname)], check=True)

if __name__ == '__main__':
    import math
    plates = LaseredAcrylic()
    plate = plates.add('driehoek', 'kek', 'banaan')
    plate.add_cut(*((from_mm(100*math.sin(x/120*math.pi)), from_mm(200*math.cos(x/120*math.pi))) for x in range(241)))
    plate.add_line(*((from_mm(50*math.sin(x/120*math.pi)), from_mm(50*math.cos(x/120*math.pi))) for x in range(241)))
    plate.add_region(*((from_mm(25*math.sin(x/120*math.pi)+25), from_mm(25*math.cos(x/120*math.pi)+25)) for x in range(241)))
    plate = plates.add('driehoek2', 'kek2', 'banaan2')
    plate.add_line(*((from_mm(50*math.sin(x/120*math.pi)), from_mm(50*math.cos(x/120*math.pi))) for x in range(241)))
    plate.add_region(*((from_mm(25*math.sin(x/120*math.pi)+25), from_mm(25*math.cos(x/120*math.pi)+25)) for x in range(241)))
    plates.to_file('test')
