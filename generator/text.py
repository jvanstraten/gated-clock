from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from coordinates import from_mm, transrot

class Label:
    def __init__(
        self,
        text,
        translate=(0, 0),
        rotate=0.0,
        scale=1.0,
        halign=0.5,
        valign=None,
        warpable=True,
        layer='GTO',
        family='Montserrat',
        style='normal',
        weight='bold'
    ):
        super().__init__()
        self._text = text
        self._warpable = warpable
        self._layer = layer

        # Render an overbar if the text ends in a backslash, sort of like
        # Altium (except not on character-basis).
        overbar = text.endswith('\\')
        if overbar:
            text = text[:-1]

        # Abuse matplotlib to render some text.
        fp = FontProperties(family, style, weight=weight)
        path = TextPath((0, 0), text, 12, prop=fp)
        polys = [[tuple(x) for x in poly] for poly in path.to_polygons()]

        # Apply scale.
        scale *= 0.1
        for poly in polys:
            for i in range(len(poly)):
                poly[i] = (from_mm(poly[i][0] * scale), from_mm(poly[i][1] * scale))

        # Determine extents.
        self._x_min = 0
        self._y_min = 0
        self._x_max = 0
        self._y_max = 0
        for poly in polys:
            for coord in poly:
                self._x_min = min(self._x_min, coord[0])
                self._x_max = max(self._x_max, coord[0])
                self._y_min = min(self._y_min, coord[1])
                self._y_max = max(self._y_max, coord[1])

        # Render the overbar.
        if overbar:
            polys.append([
                (self._x_min, self._y_max + from_mm(1.5 * scale)),
                (self._x_min, self._y_max + from_mm(3 * scale)),
                (self._x_max, self._y_max + from_mm(3 * scale)),
                (self._x_max, self._y_max + from_mm(1.5 * scale)),
                (self._x_min, self._y_max + from_mm(1.5 * scale))
            ])

        # Shift based on alignment and apply transformation.
        ox = int(round(self._x_min + (self._x_max - self._x_min) * halign)) if halign is not None else 0
        oy = int(round(self._y_min + (self._y_max - self._y_min) * valign)) if valign is not None else 0
        self._x_min -= ox
        self._x_max -= ox
        self._y_min -= oy
        self._y_max -= oy
        for poly in polys:
            for i in range(len(poly)):
                poly[i] = transrot((poly[i][0] - ox, poly[i][1] - oy), translate, rotate)

        # Determine winding order to detect whether to render as dark or clear.
        self._dark = []
        self._clear = []
        for poly in polys:
            poly = [tuple(x) for x in poly]
            winding = 0
            for (x1, y1), (x2, y2) in zip(poly[1:], poly[:-1]):
                winding += (x2 - x1) * (y2 + y1)
            if winding < 0:
                self._dark.append(poly)
            else:
                self._clear.append(poly)

    def get_text(self):
        return self._text

    def get_extents(self):
        return self._x_min, self._x_max, self._y_min, self._y_max

    def iter_regions(self):
        for poly in self._dark:
            yield True, poly
        for poly in self._clear:
            yield False, poly

    def instantiate(self, pcb, transformer, translate, rotate):
        for polarity, path in self.iter_regions():
            path = transformer.path_to_global(path, translate, rotate, self._warpable)
            pcb.add_region(self._layer, polarity, *path)


# TODO removeme
if __name__ == '__main__':
    from coordinates import LinearTransformer
    from circuit_board import CircuitBoard
    import math
    import gerbertools
    pcb = CircuitBoard()
    pcb.add_outline(
        (from_mm(-50), from_mm(-1)),
        (from_mm(50), from_mm(-1)),
        (from_mm(50), from_mm(3)),
        (from_mm(-50), from_mm(3)),
        (from_mm(-50), from_mm(-1)),
    )
    t = LinearTransformer()
    Label('hello').instantiate(pcb, t, (0, 0), 0.0)
    pcb.to_file('kek')
    gerbertools.read('./kek').write_svg('kek.svg', 12.5, gerbertools.color.mask_white(), gerbertools.color.silk_black())
