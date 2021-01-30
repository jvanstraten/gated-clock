import math

def from_mm(x):
    """Converts millimeters into internal dimension format."""
    return int(round(float(x) * 1e5) * 1e1)

def to_mm(x):
    """Converts internal dimension format into millimeters."""
    return float(x / 1e6)

def to_grb_int(x):
    """Converts internal dimension format into a Gerber integer."""
    return str(x // 100)

def to_grb_mm(x):
    """Converts internal dimension format into a Gerber float."""
    return '{:0.4f}'.format(x / 1e6)

def to_ncd_int(x):
    """Converts internal dimension format into an NC drill integer."""
    s = '{:+010.4f}'.format(x / 1e6)
    s = s[0:5] + s[6:10]
    while len(s) > 2 and s[-1] == '0':
        s = s[:-1]
    if s[0] == '+':
        s = s[1:]
    return s

def to_ncd_mm(x):
    """Converts internal dimension format into an NC drill float."""
    return '{:0.4f}'.format(x / 1e6)

def transrot(coord, translate, rotate):
    """Rotates and then translates a coordinate."""
    return (
        int(round(coord[0] * math.cos(rotate) - coord[1] * math.sin(rotate) + translate[0])),
        int(round(coord[0] * math.sin(rotate) + coord[1] * math.cos(rotate) + translate[1]))
    )

class Transformer:
    """Represents a potentially nonlinear transformation from some local
    coordinate system to a global coordinate system and back. The transformer
    guarantees that every global coordinate maps to exactly one local
    coordinate, but due to roundoff error, multiple local coordinates may
    map to the same global coordinate.

    We're talking PCBs here, so nonlinear transformations are a bit
    problematic; we should never warp or scale any footprints! Therefore, when
    globalizing a coordinate that's part of a primitive, the transformation is
    first linearized around the primitive origin to just a translation and
    rotation, and that translation/rotation is used to transform every local
    coordinate for that primitive. Due to the above guarantees however, the
    resulting global coordinates can be transformed back to true (warped) local
    coordinates without roundoff error when later converting that coordinate
    back to global."""

    def __init__(self):
        super().__init__()
        self._forward_lookup = {}
        self._reverse_lookup = {}

    def to_global(self, origin, rotation=0.0, delta=(0, 0), warpable=False):
        """When one argument is specified, treat it as a simple local
        coordinate. When four arguments are specified, treat the first two as
        origin/rotation of an instance, the third as the coordinate in the
        subcircuit/primitive coordinate system, and the fourth as a boolean
        indicating whether the subcircuit/primitive coordinate system may be
        warped or not."""

        # If we're allowed to warp the subcoordinate, transform it to a simple
        # local coordinate first. If not, we still have to rotate first.
        if delta != (0, 0):
            if warpable:
                origin = transrot(delta, origin, rotation)
                delta = (0, 0)
            else:
                delta = transrot(delta, (0, 0), rotation)

        # If this is a simple translation, see if we've done it before, and
        # return exactly what we returned then if so.
        if delta == (0, 0):
            global_coord = self._forward_lookup.get(origin, None)
            if global_coord is not None:
                return global_coord

        # Get the transformation at the origin point.
        translate, rotate = self._get_transform(origin)

        # We get our global coord by transforming the delta coordinate with the
        # transformation we got for the origin point. But in order to ensure
        # that there is a one-to-one mapping between local and global
        # coordinates (in the presence of roundoff error), we must transform
        # that coordinate back to local first. That transformation is the
        # master, so to speak. Then we should have a mapping in our
        # transformation cache that we can use.
        global_coord = transrot(delta, translate, rotate)
        local_coord = self.to_local(global_coord)
        return self._forward_lookup[local_coord]

    def to_local(self, global_coord):
        """Converts a global coordinate to its corresponding local
        coordinate."""
        local_coord = self._reverse_lookup.get(global_coord, None)
        if local_coord is None:
            local_coord = self._reverse_transform(global_coord)
            self._forward_lookup[local_coord] = global_coord
            self._reverse_lookup[global_coord] = local_coord
        return local_coord

    def path_to_global(self, path):
        """Transforms a path (list of coordinates, open unless first=last) in
        the local coordinate system to a path in the global coordinate system,
        taking nonlinearity into consideration."""
        global_path = [path[0]]
        for i in range(1, len(path)):
            n = self._num_segments(path[i-1], path[i])
            for j in reversed(range(n)):
                global_path.append((
                    path[i][0] + (j / n) * (path[i-1][0] - path[i][0]),
                    path[i][1] + (j / n) * (path[i-1][1] - path[i][1])
                ))
        return global_path

    def _get_transform(self, local_coord):
        """Transforms the local coordinate to a global coordinate, and also
        return the local rotation at that coordinate for linearizations."""
        raise NotImplementedError()

    def _reverse_transform(self, global_coord):
        """Transforms the global coordinate to a local coordinate."""
        raise NotImplementedError()

    def _num_segments(self, c1, c2):
        """Returns the number of line segments needed to make a path between
        local coordinates c1 and c2."""
        return 1

class LinearTransformer(Transformer):
    """A simple linear transformation, based on rotation followed by
    translation."""

    def __init__(self, translate=(0, 0), rotate=0.0):
        super().__init__()
        self._translate = translate
        self._rotate = rotate

    def _get_transform(self, local_coord):
        """Transforms the local coordinate to a global coordinate, and also
        return the local rotation at that coordinate for linearizations."""
        return transrot(local_coord, self._translate, self._rotate), self._rotate

    def _reverse_transform(self, global_coord):
        """Transforms the global coordinate to a local coordinate."""
        return transrot(
            (global_coord[0] - self._translate[0], global_coord[1] - self._translate[1]),
            (0, 0), -self._rotate)

class CircularTransformer(Transformer):
    """Treats local coordinates as polar coordinates, such that (x, y) ends
    up at transrot((0, radius + y), translate, rotate - x / radius)."""

    def __init__(self, translate, radius, rotate=0.0, epsilon=from_mm(0.1)):
        super().__init__()
        self._translate = translate
        self._radius = radius
        self._rotate = rotate
        self._epsilon = epsilon

    def _get_transform(self, local_coord):
        """Transforms the local coordinate to a global coordinate, and also
        return the local rotation at that coordinate for linearizations."""
        return transrot(
            (0, self._radius + local_coord[1]),
            self._translate,
            self._rotate - local_coord[0] / self._radius
        ), self._rotate - local_coord[0] / self._radius

    def _reverse_transform(self, global_coord):
        """Transforms the global coordinate to a local coordinate."""
        coord = (
            global_coord[0] - self._translate[0],
            global_coord[1] - self._translate[1]
        )
        rot = -math.atan2(coord[1], coord[0]) + math.pi/2 + self._rotate
        while rot < -math.pi:
            rot += 2 * math.pi
        while rot > math.pi:
            rot -= 2 * math.pi
        return (
            int(round(rot * self._radius)),
            int(round(math.hypot(coord[1], coord[0]) - self._radius))
        )

    def _num_segments(self, c1, c2):
        """Returns the number of line segments needed to make a path between
        local coordinates c1 and c2."""
        r = (c1[1] + c1[2]) * 0.5 + self._radius
        x = (1.0 - self._epsilon / r) if r > self._epsilon else 0.0
        th = math.acos(2.0 * x * x - 1.0) + 1e-3;
        dx = th * self._radius
        return int(math.ceil(abs(c1[0] - c2[0]) / dx))


if __name__ == '__main__':
    t1 = CircularTransformer((0, 0), 100000, 0)
    t2 = CircularTransformer((0, 0), 100000, 0)
    a = t1.to_global((100000*math.pi/2, 0), math.pi/2, (10000, 0))
    print(a)
    b = t1.to_local(a)
    print(b)
    c = t2.to_global(b)
    print(c)

    t1 = LinearTransformer((3000, 2000), math.pi/2)
    t2 = LinearTransformer((3000, 2000), math.pi/2)
    a = t1.to_global((10000, 1000), 0, (0, 0))
    print(a)
    b = t1.to_local(a)
    print(b)
    c = t2.to_global(b)
    print(c)
