Circuit descriptions
====================

This directory describes the subcircuits built with the primitive NAND gates to
form the components of the clock. This is done via a netlist, annotated with
the information to do local routing as well.

Local placement and routing can only be done in an axis-aligned grid layout, of
which the gridpoints are described via the `columns` and `rows` directives.
These directives have a list of arguments of which each has the form
`<count>x<length><alignment>`, followed by one argument of the form `<ref>`,
where:

 - `<count>` indicates a number of rows/columns which are specified at once;
 - `<length>` specifies the width/height of the row/column in mm;
 - `<align>` specifies the alignment of the components w.r.t. the column/row,
   where `C` is centered, `L`/`T` is at the lower end of the axis, and `R`/`B`
   is at the upper end; and
 - `<ref>` is the grid position that should be at the subcircuit origin.

Note that columns and rows are specified from top-left to bottom-right, as you
would read a table. That means the Y axis is flipped as the grid coordinates
are converted to PCB coordinates. Note also that fractional grid positions can
be used, which will then be linearly interpolated.

Input and output pins of the subcircuit are placed using
`<in|out> <net> <col> <row>`, where `<net>` is a local netname and `<col>` and
`<row>` are zero-referenced grid coordinates.

Primitives or subcircuits are placed using
`prim <ref> <name> <angle> <col> <row> <pin>=<net> [...]`. Here:

 - `<ref>` is the name of the referenced primitive or subcircuit;
 - `<name>` is the instance name;
 - `<angle>` is a counterclockwise orientation of the primitive/subcircuit
   around its reference point in degrees;
 - `<col>` and `<row>` are zero-referenced grid coordinates;
 - `<pin>` is the name of a pin in the referenced primitive or subcircuit;
 - `<net>` is the net it should be connected to.

Finally, routing is instantiated using `route <col> <net> [...]`, where
`<col>` is the column for the (vertical) routing, and the nets are a list of
local nets routed in that column. Vertical routing is placed on the bottom
layer; horizontal routing is placed on the top layer. All routing is made
visible on the top overlay, using bridges for crossings and thick points for
connection points. Horizontal routing is placed from every pin in a net to
the column, and vertical routing is placed between the topmost and bottommost
connection.

In order to route between columns, special feedthrough primitives are needed.
These are placed as if they are gates. However, this implies that multiple
net names are needed for the same logical net; if both columns have the same
net name, too much horizontal routing would be placed; if they have a
different net name, the electrical DRC would start screaming. Therefore, nets
in subcircuits may be suffixed with an `*` followed by whatever. The router
will consider nets with different suffixes as different, but electrical DRC
will consider them to be aliases for the same electrical net.

During generation, all subcircuits are checked for basic DRC violations. These
are:

 - all true nets must have exactly one driver (either an input pin or a
   subcircuit/primitive output);
 - all true nets must drive at least one thing (either an output pin or a
   subcircuit/primitive input);
 - all net aliases must be associated with exactly one routing column;
 - different nets routed in a single column must not overlap.

Besides the regular Cartesian grid, subcircuits can also be placed on a polar
grid. In this case, the horizontal axis will be treated as an angle, and the
vertical access becomes the radius. The reference radius (along which the
horizontal coordinates are properly millimeters) is configured along with the
polar coordinate system. In polar coordinate systems, primitives are only
rotated around their reference; they are never warped. Subcircuits of
subcircuits however *are* warped.
