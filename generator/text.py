from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties
from coordinates import from_mm, transrot
import math

class Label:
    def __init__(
        self,
        text,
        translate=(0, 0),
        rotate=0.0,
        scale=1.0,
        halign=0.5,
        valign=None,
        layer='GTO',
        family='Montserrat',
        style='normal',
        weight='bold'
    ):
        super().__init__()
        self._text = text
        self._translate = translate
        self._rotate = rotate
        self._scale = scale
        self._halign = halign
        self._valign = valign
        self._layer = layer
        self._family = family
        self._style = style
        self._weight = weight

    def get_text(self):
        return self._text

    def instantiate(self, pcb, transformer, translate, rotate):

        # Determine scale.
        ref_coord = transrot(self._translate, translate, rotate)
        ref_rot = rotate + self._rotate
        scale_x, scale_y = transformer.get_scale(ref_coord, ref_rot)
        scale_x = self._scale * 0.1 / scale_x
        scale_y = self._scale * 0.1 / scale_y

        # Determine whether the text needs to be flipped to be readable.
        _, angle = transformer.part_to_global((0, 0), 0, ref_coord, ref_rot)
        angle += 0.5 * math.pi
        while angle >= 2*math.pi:
            angle -= 2*math.pi
        while angle < 0:
            angle += 2*math.pi
        flip_x = -1 if angle > math.pi else 1
        flip_y = -1 if angle > math.pi else 1

        # Render an overbar if the text ends in a backslash, sort of like
        # Altium (except not on character-basis).
        overbar = self._text.endswith('\\')
        if overbar:
            text = self._text[:-1]
        else:
            text = self._text

        # Abuse matplotlib to render some text.
        fp = FontProperties(self._family, self._style, weight=self._weight)
        path = TextPath((0, 0), text, 12, prop=fp)
        polys = [[tuple(x) for x in poly] for poly in path.to_polygons()]

        # Determine extents.
        x_min = 0
        y_min = 0
        x_max = 0
        y_max = 0
        for poly in polys:
            for coord in poly:
                x_min = min(x_min, coord[0])
                x_max = max(x_max, coord[0])
                #y_min = min(y_min, coord[1])
                #y_max = max(y_max, coord[1])
        for poly in TextPath((0, 0), 'jf', 12, prop=fp).to_polygons():
            for _, y in poly:
                y_min = min(y_min, y)
                y_max = max(y_max, y)

        # Render the overbar.
        if overbar:
            polys.append([
                (x_min, y_max + 1.5),
                (x_min, y_max + 3),
                (x_max, y_max + 3),
                (x_max, y_max + 1.5),
                (x_min, y_max + 1.5)
            ])
            y_max += 3

        # Flip if needed.
        for poly in polys:
            for i in range(len(poly)):
                poly[i] = (poly[i][0] * flip_x, poly[i][1] * flip_y)
        x_min *= flip_x
        x_max *= flip_x
        y_min *= flip_y
        y_max *= flip_y

        # Shift based on alignment and apply transformation.
        ox = (x_min + (x_max - x_min) * (self._halign if flip_x > 0 else 1.0 - self._halign)) if self._halign is not None else 0
        oy = (y_min + (y_max - y_min) * (self._valign if flip_y > 0 else 1.0 - self._valign)) if self._valign is not None else 0
        for poly in polys:
            for i in range(len(poly)):
                poly[i] = transrot((
                    from_mm((poly[i][0] - ox) * scale_x),
                    from_mm((poly[i][1] - oy) * scale_y),
                ), self._translate, self._rotate)

        # Determine winding order to detect whether to render as dark or clear.
        dark = []
        clear = []
        for poly in polys:
            poly = [tuple(x) for x in poly]
            winding = 0
            for (x1, y1), (x2, y2) in zip(poly[1:], poly[:-1]):
                winding += (x2 - x1) * (y2 + y1)
            if winding < 0:
                dark.append(poly)
            else:
                clear.append(poly)

        # Add the paths to the PCB.
        for path in dark:
            path = transformer.path_to_global(path, translate, rotate, True)
            pcb.add_region(self._layer, True, *path)
        for path in clear:
            path = transformer.path_to_global(path, translate, rotate, True)
            pcb.add_region(self._layer, False, *path)
