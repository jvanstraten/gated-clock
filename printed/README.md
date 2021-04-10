3D-printed parts
================

Aside from the lasercut acrylic plates, all structural parts, buttons, and
switches are 3D-printed. The parts are sized for a Prusa MK3S, so a build
surface of 21x25cm; this is not just the boundary for packing multiple parts
in one print, but the actual part boundary. The clock has a 40cm diameter,
after all.

Some of the printed parts depend on the actual acrylic thickness that you got.
You can set the sheet thicknesses in the `Makefile` and run `make`, or override
on the command line with
`make FRONT_THICKNESS=... DISPLAY_THICKNESS=... HIGHLIGHT_THICKNESS=...`.
The sizes are set in mm. Note that the generator only tolerates +/-1mm
deviation from nominal; anything more than that will be clamped.

Running this will give you an `stl` directory with a three directories;
`white`, `black`, and `any`. The parts in the `white` directory are visible
from the front of the clock, and should thus be printed in white (assuming
you're using the same color scheme as I did). The parts in the `black`
directory need to be printed black, in order to avoid light bleed between the
segments of the display. The remaining parts can be printed in any color.

Some STL files have `.###` suffixes, with a shared filename as prefix. This
just means the part with the shared filename needs to be printed more than
once. So if you print all the STL files once, you should have exactly the
amount of parts you need.

Here's a list of the parts:

 - `StrainRelief`: mounts to the `HighVoltageBottom` part to clamp down on the
   mains cable.
 - `QP.Grid`, `QP.Seconds`, `QP.Minutes`, and `QP.Hours`: the "quarter panels"
   that, together with the acrylic sheets, sandwich the mainboard for
   protection and slightly improved structural integrity (the prints themselves
   are super flimsy though, they only become somewhat rigid when the clock is
   fully assembled). The screw head recess depths of this part depend on the
   thickness of the acrylic sheets.
 - `WallMountBracket`: a bracket that mounts to the top of the back of the
   clock, providing something that the clock can be hung from. A nail or screw
   will work, but to be safe, you might want to use the following part;
 - `WallMountBracketB`: a bracket that mounts to a wall and mates nicely with
   its counterpart. It's mounted to the wall with two up-to 4mm thick screws,
   spaced 75mm+/-2mm apart.
 - `SupportBoardInterface`: the part that the support board mounts to. It
   itself mounts to the back of the quarter panels.
 - `SupportBoardCover`: the protective cover for the support board.
 - `SMAInsert` OR `NoSMAInsert`: these slot into the square hole formed when
   mating the support board cover and interface parts. The former has a cutout
   for a panel-mount SMA connector; the latter is a blind insert. You only need
   one of these; which you use depends on whether you intend to populate the
   clock with a GPS module or not.
 - `HighVoltageBottom` and `HighVoltageTop`: plastic shielding for the
   mains-referenced parts of the support board. When these are mounted to the
   board, you *SHOULD* not be able to touch any live metal accidentally. But
   be careful anyway when the thing is plugged in! This is just an extra
   precaution.
 - `DisplayExtender`: a printed light guide for the 7-segment displays that
   sits immediately behind the acrylic. The dimensions of this part depend on
   the acrylic thickness.
 - `DisplayLightGuide`: counterpart of the above part, that mounts to the
   support board. Its dimensions do not depend on the acrylic.
 - `SingleButton`, `DualButton`, and `SlideSwitch`: these form the caps for the
   four pushbuttons and two slide switches. `SingleButton` and `SlideSwitch`
   need to be printed twice. These parts heavily depend on the thickness of the
   acrylic, and relatively difficult to print compared to the other parts due
   to their shape; they rely heavily on build plate supports. You'll probably
   need to do some post-processing on these to make them work; this goes
   especially for the slide switches.
 - `HeaderSpacer`: a small part that you can slide over the extra-tall headers
   to give the plastic part the right height. Needs to be printed five times.
   You'll probably need to post-process these with a small drill to make the
   holes large enough for the headers; they're so small that the printer tends
   to clog them.
 - `LedBendBottomDie` and `LedBendTopDie`: these parts aid in bending the leads
   of the 3mm flipflop LEDs. They are not part of the actual clock.

I printed everything with the Prusa defaults for PETG and the
default 0.20mm SPEED setting for the stock 0.4mm nozzle, aside from enabling
build-plate supports for the parts that need it; that worked for me. Your
mileage may vary with other printers or settings.
