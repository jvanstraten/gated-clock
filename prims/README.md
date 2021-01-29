Circuit primitives
==================

These represent the primitive components for as far as the netlist and PCB
generator is concerned.

Each component consists of a readme file with the circuit, a VHDL model for
simulation, and a .blend file for everything else.

"A .blend file? What?"
----------------------

Yes.

I'm used to working with Altium, but for performance and legal/fiscal reasons
that it just wouldn't cut it for this project. Too many arcs/primitives for it
to reach workable FPS while editing, polar grids are terrible to work with as
I've learned, and ultimately, even if it would have worked, the license I have
access to is not meant for random hobby projects.

I tried KiCad, but started questioning life choices and was ready to ragequit
the whole project within two hours. So I took a step back. "What do I actually
need?"

Well, since the circuit and most of the placement data is generated, and I
worked out the schematics and routing largely in ASCII art, I would at least
want a way to import the bulk of that into whatever PCB design program I'd
use. Like, make "symbols" for the various subcircuits and routing repeated all
over, and then copypaste orientation and coordinate data into the design. Then
do the global routing, stare at 3D models, run DRC, generate gerbers, and
that's basically it.

So, I thought, why go through the trouble of finding a new free or cheap PCB
design tool that might not even exist (at least not to my liking) and then
spend the trouble actually learning to use it sufficiently to make the final
result look nice, when I can just cut out the middle man and generate the damn
Gerber files myself?

This had a few snags of itself, of course.

 - I need DRC of some kind; this PCB is way too expensive for me to want to
   fuck up. Mere electrical DRC (clearance/short circuit, unconnected net) is
   sufficient though, since JLCPCB (and most other fabs) do an online
   manufacturing DRC before you can even place an order. That's just a few
   cleverly chosen boolean operations on polygons; surely there's
   [a library for that?](http://www.angusj.com/delphi/clipper.php)
 - I need a way to visualize the result in 3D to judge how it looks, for the
   same reasons as above.
 - Above things should be done from purely the Gerber files I output (not from
   some internal representation) to check the export process. I can test the
   DRC/3D conversion with known-good stuff that I've already ordered in the
   past, so then everything is checked at least once.
 - I need some way to input coordinate data, because manually calculating
   everything, even procedurally, would be an absolute pain in the ass
   otherwise.

The first few points are handled by the tool in the gerber directory (unnamed
as of the time I'm writing this). It reads Gerber files, can (or will be able
to) output SVGs for quick verification and OBJ files for 3D verification in
Blender, and can do the basic DRC I mentioned. That just leaves coordinate
entry, and, well... I'm used to Blender, and Blender is super easy to script.
So why not.

Blend file data extraction
--------------------------

The data can be extracted from the `.blend` files by just running `make` here.
This runs `blend-export.py` within Blender for all primitives. That generates
`.blend.dat` files, which are straightforward, easy-to-parse text files.

Since these files are just glorified coordinate entry, a couple of rules need
to be adhered to for the scripts to make sense of them.

 - The function of a Blender object depends on the collection it is in. These
   collections roughly correspond to the Gerber layers of a PCB. These layers
   are:

    - `Ctop`: top-side components.
    - `GTO`: top overlay.
    - `GTS`: top soldermask opening.
    - `GTL`: top copper.
    - `G1`: inner copper, just below top.
    - `G2`: inner copper, just above bottom.
    - `GBL`: bottom copper.
    - `GBS`: bottom soldermask openings.
    - `GBO`: bottom overlay.
    - `Cbottom`: bottom-side components.
    - `Mill`: mill data & board outline.
    - `Drill`: drill data.

   An object may be linked in multiple collections at once to easily get the
   same shape on multiple Gerber layers.

 - The following object types are supported:

    - Linear interpolations & flashes (i.e. traces). These may be placed in all
      layers except Drill, Ctop, and Cbottom. They are represented as mesh
      objects. The object center must be at the origin, with no transformation
      applied. A single solidify operator must be present, with mode complex,
      boundary round, offset 0, and the thickness set to the desired trace
      thickness. The exporter only uses vertices and edges with Z=0, but these
      verts/edges are extruded downward to make the thickness operator work,
      allowing you to see more-or-less what you're doing in Blender.

    - Polygonal apertures to represent pads. These may be placed in all layers
      except Drill, Ctop, Cbottom, and Mill. They are represented as mesh
      objects as well, with the same requirements, except without the solidify
      operator. Each polygon becomes an aperture flash on the circuit board.
      The center for the flash is just the median. Note that these regions do
      not automatically receive soldermask openings; for that, the shape must
      be present on both the copper and respective soldermask layer. Soldermask
      expansion is post-processed for all shapes on the soldermask layer,
      however, so the shape can be the same on both.

    - Via/hole objects. These are represented as mesh objects in the Drill
      layer. The mesh data must consist of one or two circular polygons,
      centered around the object origin; the location of the origin is used for
      the drill center. The smaller of the two polygons, or the only polygon,
      represents the (finished) hole size. If there is a second polygon, the
      hole will be plated, and receive a circular pad of its size on all layers
      to form a via. Vias are tented unless a soldermask opening is manually
      added for them. If there is only one polygon, a non-plated hole is made.

    - Text objects. These may be placed in copper, mask, and component layers.
      Text should be centered; the object origin and orientation around Z are
      used for the location data. Rotation around the other axes should be 0.
      Text objects on the copper layers represent ports for the primitives,
      to be connected via routing traces (note that the three plane-based
      global signals do not receive such ports). Text objects on mask layers
      represent net labels for component pins, intended for electrical DRC.
      Text objects on the component layers represent references to components,
      to be placed in the 3D model and used for BOM generation.

 - Objects not within the classes above are ignored, and may thus be used for
   notes.

 - Four type of net labels are distinguished by a symbol prefix:

    - no prefix: global net. The name will appear in the final netlist as
      written.
    - `.` prefix: local net. The name will be prefixed with the instance name
      to make it unique.
    - `>` prefix: input port. Same as `.`, but the net is treated as an input
      of this primitive. A similarly-named input is expected in the VHDL model.
    - `<` prefix: output port. Same as `.`, but the net is treated as an output
      of this primitive. A similarly-named output is expected in the VHDL
      model.
