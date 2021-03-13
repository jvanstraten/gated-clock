3D-printed parts
================

Aside from the lasercut acrylic plates, all structural parts, buttons, and
switches are 3D-printed. The parts are sized for a Prusa MK3S, so a build
surface of 21x25cm; this is not just the boundary for packing multiple parts
in one print, but the actual part boundary. The clock has a 40cm diameter,
after all. Your mileage may vary with other printers. Hell, your mileage may
vary with the MK3s and the settings. I managed to print the quarter panels with
faster settings, but then my printer started giving me massive trouble, so I
reverted back to stock there.

Anyway, the following parts are needed.

 - The four "quarter panels" that cover the back of the circuit board.
   These are independent prints due to their size.
 - The support board interface; that is, the part that sits between the support
   board and the back of the quarter panels. This is part of misc1.
 - The support board cover; that is, the part that covers the back of the
   support board. This is an independent print due to its size.
 - A small cutout for a panel-mount SMA connector, slid between the support
   board interface and cover. This is a separate part because the shape of the
   SMA connector cutout is pretty important, and the print direction is wrong
   otherwise. This is part of misc1.
 - The high voltage covers (top and bottom). These wrap around the
   mains-referenced part of the support board. They are printed together
   with...
 - The strain relief clasp for the mains input cable, which mounts to the
   bottom high-voltage cover.
 - The display extensions.
 - The user interface components: two slide switches, two singular button
   covers, and one dual button cover. These are part of misc1.

Colors are up to you, I suppose. I have black, white, and clear PETG laying
around, so that's what I printed with: the quarter panels in black as a
backdrop for the LED holes, the high voltage covers in clear so you can sort
of see if everything's okay in there, and everything else in white (mostly
because that's what I had the most of).

Once printed, everything is fastened using 41 M3x12 screws, 25 M3 nuts, and 16
tapped M3 holes in the front acrylic sheet.
