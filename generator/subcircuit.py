import os
import math
from coordinates import from_mm, to_mm, transrot
from pin_map import Pins, PinMap
from netlist import Netlist
from primitive import get_primitive
from text import Label

class GridDimension:
    """Represents one of the two dimensions of the table grid."""

    def __init__(self, mirror):
        super().__init__()
        self._positions = []
        self._mirror = mirror

    def _convert_mm(self, pos):
        """Converts a grid position to millimeters."""
        if pos < 0 or pos >= len(self._positions):
            raise ValueError('invalid grid position')
        idx1 = int(pos)
        if idx1 == len(self._positions) - 1:
            return self._positions[idx1]
        idx2 = idx1 + 1
        f2 = pos - idx1
        f1 = 1 - f2
        return self._positions[idx1] * f1 + self._positions[idx2] * f2

    def convert(self, pos):
        """Converts a grid position to internal units."""
        return from_mm(self._convert_mm(float(pos)))

    def configure(self, *args):
        """Parses a grid layout command. The first N-1 arguments must be of the
        form `<count>x<length><aligment>`, where count is used to set N
        rows/columns at once, length sets the size of each row/column, and
        alignment is L/T/C/R/B to specify where in relation to the row/column
        the placed part centers should be. The last argument specifies where
        in the specified layout the subcircuit origin should end up."""
        self._positions = []
        pos = 0.0
        for arg in args[:-1]:
            count, length = arg[:-1].split('x')
            count = int(count)
            length = float(length)
            align = {
                'L': 0.0, 'T': 0.0,
                'C': 0.5,
                'R': 1.0, 'B': 1.0
            }[arg[-1]]
            for _ in range(count):
                self._positions.append(pos + length * align)
                pos += length
        ref = self._convert_mm(float(args[-1]))
        if self._mirror:
            for i in range(len(self._positions)):
                self._positions[i] = ref - self._positions[i]
        else:
            for i in range(len(self._positions)):
                self._positions[i] = self._positions[i] - ref

class Instance:
    """Represents a primitive or subcircuit instance."""

    def __init__(self, is_primitive, typ, name, coord, rotation, *mappings):
        super().__init__()
        self._name = name
        self._is_primitive = is_primitive
        self._data = get_primitive(typ) if is_primitive else get_subcircuit(typ)
        self._coord = coord
        self._rotation = rotation
        self._pinmap = PinMap(self._data.get_pins(), *mappings)

    def get_name(self):
        return self._name

    def is_primitive(self):
        return self._is_primitive

    def get_data(self):
        return self._data

    def get_coord(self):
        return self._coord

    def get_rotation(self):
        return self._rotation

    def get_pinmap(self):
        return self._pinmap

    def instantiate(self, pcb, transformer, translate, rotate, net_prefix, net_override):
        """Instantiate this instance to the given PCB. The transformation and
        net overrides are treated as being for the parent subcircuit -- the
        transformations for this instance are applied on top of it. Note that
        the parent is assumed to be warpable."""

        # Figure out net prefix for the child instance.
        child_net_prefix = '{}.{}'.format(net_prefix, self.get_name())

        # Figure out net override for the child instance.
        child_net_override = dict(net_override)
        for pin, net in self._pinmap:
            pin = pin.get_name()
            if net in net_override:
                net = net_override[net]
            elif net.startswith('.'):
                net = net_prefix + net
            child_net_override['.{}'.format(pin)] = net

        self.get_name() if not net_prefix else '{}.{}'.format(net_prefix, self.get_name())
        self._data.instantiate(
            pcb,
            transformer,
            transrot(self._coord, translate, rotate),
            self._rotation + rotate,
            child_net_prefix,
            child_net_override)

class RoutingColumn:
    """Represents a routing column."""

    def __init__(self, x, net, primary_layer, secondary_layer):
        """Creates a routing column at the given x coordinate for the given
        net. The primary layer and secondary layer are used for routing. They
        must be the same for all routing columns in the subcircuit. The primary
        layer is used for horizontal traces, as well as vertical traces that do
        not cross a horizontal trace. The secondary layer is used for vertical
        traces that bridge horizontal traces."""
        super().__init__()
        self._net = net
        self._x = x
        self._targets = []
        self._bridges = []
        self._pl = primary_layer
        self._sl = secondary_layer
        assert primary_layer != secondary_layer

    def get_x_coord(self):
        return self._x

    def register(self, net, router_x, coord, layer):
        """Registers a connection point (aka pin) for the given net, coordinate,
        and layer, to be connected to the routing column at router_x."""
        if net == self._net:

            # Connection point is to be connected to this column, so add it to
            # our target list. Targets are always connected to the column using
            # the primary layer, so if the connection point is on another layer,
            # a via will be inserted at that point.
            assert router_x == self._x
            self._targets.append((coord, layer))

        else:

            # Connection point is for a different net. If it crosses our
            # column, register a bridge. Targets are always connected to their
            # column using the primary layer, so a bridge implies that our
            # column must duck under the primary layer using the secondary
            # layer (in addition to depicting the bridge on the silkscreen).
            min_x = min(router_x, coord[0])
            max_x = max(router_x, coord[0])
            if self._x >= min_x and self._x <= max_x:
                self._bridges.append(coord[1])

    def generate(self, pcb, transformer, translate, rotate):
        if len(self._targets) < 2:
            return

        def glob(coord):
            return transformer.to_global(coord, translate, rotate, True)

        def get_scale(coord, r=from_mm(1)):
            a = glob((coord[0] + r, coord[1]))
            b = glob((coord[0] - r, coord[1]))
            x = 2*r / math.hypot(a[0] - b[0], a[1] - b[1])
            a = glob((coord[0], coord[1] + r))
            b = glob((coord[0], coord[1] - r))
            y = 2*r / math.hypot(a[0] - b[0], a[1] - b[1])
            return (x, y)

        def trace(path, layer, t=0.2):
            path = transformer.path_to_global(path, translate, rotate, True)
            pcb.add_trace(layer, from_mm(t), *path)

        # First, turn the bridge points into ranges: both the arc for the
        # visual representation and potential vias/knots right next to it cost
        # space. We can move the vias/knots slightly, but we can't move the
        # bridges, because the horizontal traces they cross are generated by
        # other routing columns. Note that we might have bridges registered
        # with us that lie beyond the actual column; we ignore those here.
        # The final result is an ordered list of four-tuples representing
        # non-overlapping ranges of local Y coordinates (first and second
        # element being the lower and upper coordinate) of at least 2ry in
        # length, where rx/ry is the local radius of the graphic needed to
        # get the desired radius in global coordinates, as stored in the third
        # and fourth tuple element.
        def get_bridge_r(y):
            sx, sy = get_scale((self._x, y))
            rx = int(round(sx * from_mm(0.3))) # <-- desired global X radius
            ry = int(round(sy * from_mm(0.5))) # <-- desired global Y radius
            return rx, ry
        all_y_targets = [y for (_, y), _ in self._targets]
        min_y = min(all_y_targets)
        max_y = max(all_y_targets)
        bridge_reqs = []
        for y in self._bridges:
            if y < min_y or y > max_y:
                continue
            rx, ry = get_bridge_r(y)
            bridge_reqs.append((y - ry, y + ry, rx, ry))
        bridge_reqs.sort()
        combined_bridges = []
        for a, b, rx, ry in bridge_reqs:
            if not combined_bridges or combined_bridges[-1][1] < a:
                combined_bridges.append((a, b, rx, ry))
            else:
                combined_bridges[-1] = (combined_bridges[-1][0], b, None, None)
        bridges = []
        for a, b, rx, ry in combined_bridges:
            if rx is None or ry is None:
                rx, ry = get_bridge_r((a + b) / 2)
            if b - a < 2 * ry:
                ry = int(b - a) // 2
            bridges.append((a, b, rx, ry))

        for i in range(len(bridges)-1):
            assert bridges[i+1][0] >= bridges[i][1]

        # Let's call the bits before, between, and after the bridges spans
        # (note that by definition there is at least one of these). Two Y
        # coordinate ranges are involved in a span; the outer range specifies
        # which connection points are mapped to which span, while the inner
        # range specifies the outermost coordinates that a knot may exist at.
        # Let's set up those ranges first.
        spans = []
        min_y -= from_mm(10)
        max_y += from_mm(10)
        for i in range(len(bridges) + 1):
            spans.append((
                min_y if i == 0            else (bridges[i-1][0] + bridges[i-1][1]) / 2,
                max_y if i == len(bridges) else (bridges[i  ][0] + bridges[i  ][1]) / 2,
                min_y if i == 0            else bridges[i-1][1],
                max_y if i == len(bridges) else bridges[i  ][0],
                []
            ))

        # Spans consist of zero or more knots. A knot is a point in the routing
        # column where the column meets with one or more connection points;
        # depending on the amount, and where the knot is in the column, the
        # point will be rendered as a bend or as a thick dot, and may or may
        # not receive a via at its centerpoint. While it's possible that there
        # are two connection points with the same Y coordinate on either side
        # of the column, multiple connection points on the same side may also
        # be routed to the same knot if they are too close. In this case the
        # final stretch of the horizontal trace will bend toward the
        # centerpoint of the knot.
        class Knot:
            def __init__(self, x, y):
                super().__init__()
                self._x = x
                self._y = y
                self._r = None
                self._targets = [] # (x, y), layer
                self._min_y = y
                self._max_y = y
                self._type = 'knot' # or 'upper', 'lower', or 'single' for endpoints
                self.prev_layer = None
                self.next_layer = None

            def get_coord(self):
                return (self._x, self._y)

            def get_y(self):
                return self._y

            def set_y(self, y):
                self._y = y
                self._r = None

            def recenter_y(self):
                self.set_y(int(round((self._min_y + self._max_y) / 2)))

            def add_target(self, coord, layer):
                self._targets.append((coord, layer))
                self._min_y = min(self._min_y, coord[1])
                self._max_y = max(self._max_y, coord[1])

            def iter_targets(self):
                for target in self._targets:
                    yield target

            def get_r(self):
                if self._r is None:
                    sx, sy = get_scale((self._x, self._y))
                    rx = int(round(sx * from_mm(0.4))) # <-- desired global X radius
                    ry = int(round(sy * from_mm(0.4))) # <-- desired global Y radius
                    self._r = (rx, ry)
                return self._r

            def mark_constrained(self):
                self._constrained = True

            def mark_endpoint(self, typ, limit=None):
                if len(self._targets) > (2 if typ == 'single' else 1):
                    return
                self._type = typ
                if typ == 'upper':
                    self.set_y(max(self._y - self.get_r()[1], limit))
                elif typ == 'lower':
                    self.set_y(min(self._y + self.get_r()[1], limit))
                else:
                    self.recenter_y()

            def get_layers(self):
                layers = set()
                for _, layer in self._targets:
                    layers.add(layer)
                if self.prev_layer is not None:
                    layers.add(self.prev_layer)
                if self.next_layer is not None:
                    layers.add(self.next_layer)
                return layers

            def layer_preference(self):
                layers = self.get_layers()
                if len(layers) == 1:
                    return next(iter(layers))
                return None

            def needs_via(self, primary_layer):
                return len(self.get_layers()) > 1

            def needs_dot(self):
                return int(self.prev_layer is not None) + int(self.next_layer is not None) + len(self._targets) > 2

            def bend_90(self):
                return self._type in ('upper', 'lower')

        # Now lets assign connection points to the spans. Initially, we'll just
        # give each point its own knot. We'll also immediately place vias for
        # points that don't connect on the primary layer.
        for (tx, ty), layer in sorted(self._targets, key=lambda x: x[0][1]):
            for a, b, _, _, knots in spans:
                if ty >= a and ty < b:
                    k = Knot(self._x, ty)

                    # If the point is not on the primary layer and it's close
                    # enough to our column, we'll actually route the horizontal
                    # on that layer, to prevent vias from getting too close.
                    # But otherwise, place a via at the connection point now
                    # and route on primary.
                    if layer != self._pl:
                        a = glob((tx, ty))
                        b = glob((self._x, ty))
                        if math.hypot(a[0] - b[0], a[1] - b[1]) > from_mm(0.5):
                            layer = self._pl
                            pcb.add_via(a)

                    k.add_target((tx, ty), layer)
                    knots.append(k)
                    break
            else:
                # This should never happen; if it does, min_y and max_y are not
                # correct or the outer spans do not properly extend to those
                # limits.
                assert False

        # The first and last span should each have at least one knot.
        if not spans[0][4] or not spans[-1][4]:
            print('spans for net {}:'.format(self._net))
            for oa, ob, ia, ib, knots in spans:
                print(' - span from {} to {} ({} to {}) has {} knots'.format(
                    to_mm(oa), to_mm(ob), to_mm(ia), to_mm(ib), len(knots)))
            assert False

        # Now combine knots that are too close together, starting with the
        # closest ones.
        for _, _, _, _, knots in spans:
            done = False
            while not done:
                i = -1
                done = True
                while i < len(knots) - 2:
                    i += 1
                    k1 = knots[i]
                    k2 = knots[i+1]
                    d12 = k2.get_y() - k1.get_y()
                    assert d12 >= 0
                    if i+2 < len(knots):
                        k3 = knots[i+2]
                        d23 = k3.get_y() - k2.get_y()
                        assert d23 >= 0
                        if d23 < d12:

                            # The next two knots are closer together than
                            # these two; try combining those first.
                            continue

                    min_d = k1.get_r()[1] + k2.get_r()[1]
                    if d12 < min_d:

                        # Knots k1 and k2 are too close, combine.
                        del knots[i+1]
                        for target in k2.iter_targets():
                            k1.add_target(*target)
                        k1.recenter_y()
                        done = False

        # The knots at the start and end of the span may interfere with
        # bridges. Combine any knots that interfere this way for the
        # lower end of the column...
        for _, _, a, _, knots in spans:
            ka = Knot(self._x, a)
            endpt_min_y = a + ka.get_r()[1]
            ka.set_y(endpt_min_y)
            ka.mark_constrained()
            a = ka.get_y()
            any_merged = False
            while knots:
                k = knots[0]
                if k.get_y() - k.get_r()[1] < a:
                    del knots[0]
                    any_merged = True
                    for target in k.iter_targets():
                        ka.add_target(*target)
                    a = ka.get_y() + ka.get_r()[1] * 2
                else:
                    break
            if any_merged:
                knots.insert(0, ka)

        # ...and for the upper end.
        for _, _, _, b, knots in reversed(spans):
            kb = Knot(self._x, b)
            endpt_max_y = b - kb.get_r()[1]
            kb.set_y(endpt_max_y)
            kb.mark_constrained()
            b = kb.get_y()
            any_merged = False
            while knots:
                k = knots[-1]
                if k.get_y() + k.get_r()[1] > b:
                    del knots[-1]
                    any_merged = True
                    for target in k.iter_targets():
                        kb.add_target(*target)
                    b = kb.get_y() - kb.get_r()[1] * 2
                else:
                    break
            if any_merged:
                knots.append(kb)

        # We don't need the span ranges anymore now, so we can simplify the
        # data structure for them.
        spans = [knots for _, _, _, _, knots in spans]

        # Mark the last knots at each end as endpoints. This may move their
        # "center" inwards to make way for a bend, but no further than the
        # constraint for the next bridge.
        if len(spans) == 1 and len(spans[0]) == 1:
            # Special case for just one knot.
            spans[0][0].mark_endpoint('single')
        else:
            # Multiple knots, mark endpoints.
            spans[0][0].mark_endpoint('lower', endpt_max_y)
            spans[-1][-1].mark_endpoint('upper', endpt_min_y)

        # Now we have our topology mostly worked out. The only thing that
        # remains is to figure out what layers to place the vertical components
        # of the traces on. We'll actually draw the traces as we do so.
        kp = None
        ks = None
        force_nonprimary = False
        for knots in spans:
            for k in knots:
                if kp is not None:

                    # We have two knots that need to be connected on a layer.
                    # Figure out what the best layer would be.
                    preference = kp.layer_preference()
                    if preference is not None:
                        layer = preference
                    else:
                        preference = k.layer_preference()
                        if preference is not None:
                            layer = preference
                        else:
                            layer = self._pl
                    if force_nonprimary and layer == self._pl:
                        layer = self._sl

                    # Store the layers in the knots.
                    kp.next_layer = layer
                    k.prev_layer = layer

                    # Don't render the trace immediately; optimize by drawing
                    # contiguous lines with one path.
                    if ks is not None and ks.next_layer != layer:

                        # Draw from ks to k.
                        trace([ks.get_coord(), kp.get_coord()], ks.next_layer)
                        ks = kp

                if ks is None:
                    ks = k

                kp = k

                # Next knot in this span (if any remain) will not cross
                # bridges, and thus can be routed on the primary layer.
                force_nonprimary = False

            # Next knot (if any) will cross bridges. So we need to route
            # on secondary.
            force_nonprimary = True

        if ks is not None and ks is not kp:
            trace([ks.get_coord(), kp.get_coord()], ks.next_layer)

        # Place vias for the knots that need one.
        for knots in spans:
            for knot in knots:
                if knot.needs_via(self._pl):
                    pcb.add_via(glob(knot.get_coord()))

        # Render the connections from the column to the connection points.
        for knots in spans:
            for knot in knots:
                kx, ky = knot.get_coord()
                rx, ry = knot.get_r()
                for (tx, ty), layer in knot.iter_targets():
                    if ty == ky and tx == kx:

                        # No trace necessary, we're already there.
                        continue

                    elif ty == ky or tx == kx:

                        # No curvature necessary.
                        path = [(kx, ky), (tx, ty)]

                    else:

                        bend_90 = knot.bend_90()

                        # X coordinate for the bend.
                        if bend_90:
                            bx = min(max(kx - rx, tx), kx + rx)
                        else:
                            bx = min(max(kx - rx * 1.5, tx), kx + rx * 1.5)

                        path = []
                        N = 3
                        for i in range(N+1):
                            f = i / N
                            if bend_90:
                                a = f * math.pi / 2
                                c = 1 - math.cos(a)
                                s = math.sin(a)
                            else:
                                a = (1 + f) * math.pi / 4
                                c = 1 - math.cos(a) * math.sqrt(2)
                                s = (math.sin(a) - 1/math.sqrt(2)) * 3.4142135623730945
                            x = kx + (bx - kx) * c
                            y = ky + (ty - ky) * s
                            path.append((int(x), int(y)))
                        path.append((tx, ty))

                    path = transformer.path_to_global(path, translate, rotate, True)
                    pcb.add_trace(layer, from_mm(0.2), *path)
                    pcb.add_trace('GTO', from_mm(0.2), *path)

        # Place dots on the knots that need one.
        for knots in spans:
            for knot in knots:
                if knot.needs_dot():
                    trace([knot.get_coord()], 'GTO', 0.65)

        # Finally, draw the top overlay path for the vertical column.
        path = [spans[0][0].get_coord()]
        if spans[-1][-1].get_coord() != path[0]:
            N = 3
            for a, b, rx, ry in bridges:
                for i in range(N+1):
                    f = i / N
                    th = f * math.pi / 2
                    c = 1 - math.cos(th)
                    s = math.sin(th)
                    x = self._x + s * rx
                    y = a + c * ry
                    path.append((int(x), int(y)))
                for i in reversed(range(N+1)):
                    f = i / N
                    th = f * math.pi / 2
                    c = 1 - math.cos(th)
                    s = math.sin(th)
                    x = self._x + s * rx
                    y = b - c * ry
                    path.append((int(x), int(y)))
            path.append(spans[-1][-1].get_coord())
            trace(path, 'GTO')

class Subcircuit:
    """Represents a subcircuit for PCB composition."""

    def __init__(self, name):
        super().__init__()
        print('loading subcircuit {}...'.format(name))
        if not os.path.isdir(os.path.join('subcircuits', name)):
            raise ValueError('subcircuit {} does not exist'.format(name))
        if not os.path.isfile(os.path.join('subcircuits', name, '{}.circuit.txt'.format(name))):
            raise ValueError('missing .circuit.txt file for subcircuit {}'.format(name))
        cols = GridDimension(False)
        rows = GridDimension(True)
        self._name = name
        self._pins = Pins()
        self._net_insns = []
        self._instances = []
        self._routers = []
        self._labels = []
        forwarded_pins = []
        with open(os.path.join('subcircuits', name, '{}.circuit.txt'.format(name)), 'r') as f:
            for line in f.read().split('\n'):
                line = line.split('#', maxsplit=1)[0].strip()
                if not line:
                    continue
                args = line.split()

                if args[0] == 'columns':
                    cols.configure(*args[1:])
                    continue

                if args[0] == 'rows':
                    rows.configure(*args[1:])
                    continue

                if args[0] in ('in', 'out'):
                    coord = (cols.convert(args[3]), rows.convert(args[4]))
                    self._pins.add(args[1], args[0], args[2], (0, 0), coord, 0.0)
                    name = '.{}'.format(args[1])
                    self._net_insns.append((name, args[2], (0, 0), coord, 0.0, args[0]))
                    continue

                if args[0] in ('fwd_in', 'fwd_out'):
                    forwarded_pins.append((args[0][4:], args[1]))
                    continue

                if args[0] in ('prim', 'subc'):
                    coord = (cols.convert(args[4]), rows.convert(args[5]))
                    rotation = float(args[3]) / 180 * math.pi
                    instance = Instance(
                        args[0] == 'prim', args[1], args[2],
                        coord, rotation, *args[6:]
                    )
                    for pin, net in instance.get_pinmap():
                        if pin.is_output():
                            mode = 'driver' if args[0] == 'prim' else 'in'
                        else:
                            mode = 'user' if args[0] == 'prim' else 'out'
                        self._net_insns.append((
                            net,
                            pin.get_layer(),
                            pin.get_coord(),
                            transrot(pin.get_translate(), coord, rotation),
                            pin.get_rotate() + rotation,
                            mode
                        ))
                    self._instances.append(instance)
                    continue

                if args[0] == 'route':
                    self._routers.append((cols.convert(args[1]), ['.{}'.format(x) for x in args[2:]]))
                    continue

                if args[0] == 'text':
                    text = args[1].replace('~', ' ')
                    coord = (cols.convert(args[3]) + from_mm(args[5]), rows.convert(args[4]) + from_mm(args[6]))
                    rotation = float(args[2]) / 180 * math.pi
                    scale = float(args[7]) if len(args) > 7 else 1.0
                    halign = float(args[8]) if len(args) > 8 else 0.5
                    valign = float(args[9]) if len(args) > 9 else None
                    self._labels.append(Label(text, coord, rotation, scale, halign, valign))
                    continue

                print('warning: unknown subcircuit construct: {}'.format(line))

        forwarded_pin_nets = set()
        for direction, name in forwarded_pins:
            insns = []
            for insn in self._net_insns:
                if insn[0] == '.' + name:
                    insns.append(insn)
            if not insns:
                raise ValueError('cannot forward pins for nonexistant net {}'.format(name))
            if len(insns) != 1:
                raise ValueError('multiple pins exist for forwarded pin {}; this is not supported'.format(name))
            net, layer, coord, translate, rotate, mode = insns[0]
            self._pins.add(name, direction, layer, coord, translate, rotate)
            self._net_insns.append((net, layer, coord, translate, rotate, direction))
            forwarded_pin_nets.add(net)

        print('doing basic DRC for subcircuit {}...'.format(self._name))
        netlist = Netlist()
        for net, layer, coord, translate, rotate, mode in self._net_insns:
            netlist.add(net, layer, transrot(coord, translate, rotate), mode)
        good = netlist.check_subcircuit()
        unrouted = set(map(lambda x: x.get_name(), netlist.iter_logical()))
        routed = set()
        for x, nets in self._routers:
            ranges = []
            for net in nets:
                if net in routed:
                    print('net {} is routed multiple times'.format(net))
                    good = False
                elif net not in unrouted:
                    print('net {} cannot be routed because it does not exist'.format(net))
                    good = False
                routed.add(net)
                unrouted.remove(net)
                y_min = None
                y_max = None
                for _, (_, y), _ in netlist.get_logical(net).iter_points():
                    if y_min is None or y < y_min:
                        y_min = y
                    if y_max is None or y > y_max:
                        y_max = y
                assert y_min is not None
                assert y_max is not None
                ranges.append((y_min, y_max, net))
            ranges.sort()
            for i in range(len(ranges) - 1):
                if ranges[i+1][0] - from_mm(0.5) < ranges[i][1]:
                    print('nets {} and {} overlap in routing column;'.format(ranges[i][2], ranges[i+1][2]))
                    print('  {} goes down to Y{} and {} up to Y{} at X{}'.format(
                        ranges[i+1][2], to_mm(ranges[i+1][0]),
                        ranges[i][2], to_mm(ranges[i][1]),
                        to_mm(x)))
                    good = False
        for net in forwarded_pin_nets:
            if net in routed:
                print('net {} is routed multiple times'.format(net))
                good = False
            elif net not in unrouted:
                print('net {} cannot be routed because it does not exist'.format(net))
                good = False
            routed.add(net)
            unrouted.remove(net)
        for net in unrouted:
            print('net {} is not routed'.format(net))
            good = False
        if not good:
            raise ValueError('basic DRC failed for subcircuit {}'.format(self._name))
        print('finished loading subcircuit {}, basic DRC passed'.format(self._name))

        # Write VHDL for the netlist.
        with open(os.path.join('subcircuits', self._name, '{}.gen.vhd'.format(self._name)), 'w') as f:
            f.write('library ieee;\nuse ieee.std_logic_1164.all;\n\nentity {} is\n  port (\n'.format(self._name))

            pin_directions = {}
            for pin in self._pins:
                direction = pin.get_direction()
                pin = pin.get_name().split('~')[0].split('*')[0]
                if pin in pin_directions:
                    if direction == 'out':
                        pin_directions[pin] = 'out'
                else:
                    pin_directions[pin] = direction

            first = True
            nets = set()
            for pin in self._pins:
                pin = pin.get_name().split('~')[0].split('*')[0]
                direction = pin_directions[pin]
                if pin in nets:
                    continue
                nets.add(pin)
                if first:
                    first = False
                else:
                    f.write(';\n')
                f.write('    {} : {} std_logic'.format(pin, direction))
            f.write('\n  );\nend entity;\n\narchitecture model of {} is\n'.format(self._name))
            for net, *_ in self._net_insns:
                if not net.startswith('.'):
                    continue
                net = net[1:].split('~')[0].split('*')[0]
                if net in nets:
                    continue
                f.write('  signal {} : std_logic;\n'.format(net))
                nets.add(net)
            f.write('begin\n\n')
            for instance in self._instances:
                name = instance.get_name().replace('*', '').replace('~', '')
                f.write('  {}_inst: entity work.{}\n    port map (\n'.format(name, instance.get_data().get_name()))
                pins = set()
                first = True
                for pin, net in instance.get_pinmap():
                    pin = pin.get_name().split('~')[0].split('*')[0]
                    if pin in pins:
                        continue
                    pins.add(pin)
                    net = net[1:].split('~')[0].split('*')[0]
                    if first:
                        first = False
                    else:
                        f.write(',\n')
                    f.write('      {} => {}'.format(pin, net))
                f.write('\n    );\n\n')
            f.write('end architecture;\n')

    def get_name(self):
        return self._name

    def get_pins(self):
        return self._pins

    def instantiate(self, pcb, transformer, translate, rotate, net_prefix, net_override):
        """Instantiates this subcircuit on the given PCB with the given
        transformer and local coordinate + rotation. Nets found in the
        net_override map will be renamed accordingly. Local nets not found
        in the map will be prefixed by net_prefix."""

        # Rebuild netlist with the correct transformations.
        netlist = Netlist()
        for net, layer, coord, trans, rot, mode in self._net_insns:
            trans = transrot(trans, translate, rotate)
            rot += rotate
            netlist.add(net, layer, transformer.to_global(coord, trans, rot, False), mode)

        # Handle primitive artwork and netlist.
        for instance in self._instances:
            instance.instantiate(pcb, transformer, translate, rotate, net_prefix, net_override)
        for net in netlist.iter_physical():
            name = net.get_name()
            if name in net_override:
                name = net_override[name]
            elif name.startswith('.'):
                name = net_prefix + name
            for layer, coord, mode in net.iter_points():
                pcb.add_net(name, layer, coord, mode)

        # Perform routing.
        routers = [RoutingColumn(x, net, 'GTL', 'GBL') for x, nets in self._routers for net in nets]
        x_coords = {net: x for x, nets in self._routers for net in nets}
        for net in netlist.iter_logical():
            name = net.get_name()
            router_x = x_coords.get(name, None)
            if router_x is None:
                continue
            for layer, coord, _ in net.iter_points():
                coord = transformer.to_local(coord)
                coord = transrot(coord, (-translate[0], -translate[1]), 0.0)
                coord = transrot(coord, (0, 0), -rotate)
                for router in routers:
                    router.register(name, router_x, coord, layer)
        for router in routers:
            router.generate(pcb, transformer, translate, rotate)

        # Add labels.
        for label in self._labels:
            label.instantiate(pcb, transformer, translate, rotate)


_subcircuits = {}

def get_subcircuit(name):
    """Loads a subcircuit from the subcircuits directory."""
    subcirc = _subcircuits.get(name, None)
    if subcirc is None:
        subcirc = Subcircuit(name)
        _subcircuits[name] = subcirc
    return subcirc

# TODO removeme
if __name__ == '__main__':
    from coordinates import LinearTransformer, CircularTransformer
    from circuit_board import CircuitBoard
    import math
    import gerbertools
    pcb = CircuitBoard(mask_expansion=0.05)
    path = [(from_mm(math.sin(x/50*math.pi)*190), from_mm(math.cos(x/50*math.pi)*190)) for x in range(101)]
    pcb.add_outline(*path)
        #(from_mm(-45), from_mm(-45)),
        #(from_mm(50), from_mm(-45)),
        #(from_mm(50), from_mm(45)),
        #(from_mm(-45), from_mm(45)),
        #(from_mm(-45), from_mm(-45)),
    #)
    t = LinearTransformer()
    t = CircularTransformer((0, 0), from_mm(160), math.pi/2)
    get_subcircuit('decode_d2d5').instantiate(pcb, t, (from_mm(0), from_mm(-10)), -math.pi/2, 'x', {})
    get_subcircuit('decode_d2d3').instantiate(pcb, t, (from_mm(60), from_mm(-10)), -math.pi/2, 'y', {})
    get_subcircuit('div2').instantiate(pcb, t, (from_mm(90), from_mm(0)), 0, 'y', {})
    get_subcircuit('div3').instantiate(pcb, t, (from_mm(120), from_mm(0)), 0, 'y', {})
    get_subcircuit('div5').instantiate(pcb, t, (from_mm(180), from_mm(0)), 0, 'y', {})
    pcb.get_netlist().check_composite()
    pcb.to_file('kek')
    gerbertools.read('./kek').write_svg('kek.svg', 12.5, gerbertools.color.mask_white(), gerbertools.color.silk_black())
