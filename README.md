Gated Clock
===========

A clock suitable for electronics nerds, built out of 3-input NAND gates.

![Clock](assets/finished-clock.jpg?raw=true "Clock")

The point of this project is to:

 - build a functional digital clock out of only discrete logic gates (74LVC1G10
   3-input NANDs to be specific) and passives;
 - make sure the entire circuit for as far as this is needed to make it work is
   visible on the front, with LEDs for (almost) all digital signals;
 - actually make it look pretty; and
 - actually make it useful.

Note that none of the above include anything about BOM cost. See the section on
cost below.

The status of the project is that I've manufactured a total of nine clocks for
myself, friends, and family at this point. There's some renewed interest, so a
second run might happen; however, the Teensy LC that the old design used for
misc UI tasks is now EoL. Work is in progress to replace it with a Raspberry Pi
Pico W.

License
-------

Let's get the fine print out of the way first. The license for this stuff is
[Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
See also the LICENSE file for the full plaintext.

Note: if anyone out there would like to commercialize this somehow and needs a
different license, I'm all ears. I mostly just want to know about it if someone
does. See also: "why not build a bunch of them and sell them?"

The only exceptions to the license are the 3D models of the electrical parts I
used for the renders (basically, any of the .blend files in the `models`
directory); some of these are converted directly from the STEP files provided
by the part manufacturers and are thus licensed under different terms. I'm
honestly not too sure what these terms are, since most of the legalese they try
to make you read is about limitation of warranty with regards to model
accuracy.

How does it work
----------------

The short version is as follows.

 - The electricity grid oscillates at 50Hz or 60Hz depending on where you live,
   with stipulations about long-term accuracy by law in most places. So, while
   synchronizing clocks to the grid frequency is old-fashioned, it's actually a
   supported use case.

 - A circuit based on a capacitive dropper, an optocoupler, and some active
   filtering translates the high-voltage AC signal to a logic-level clock
   source.

 - A bunch of NAND-gate-based D-flipflops divide this frequency down to
   increasingly lower frequencies. Divider circuits exist for a factor 2,
   factor 3, and factor 5. The chain used is as follows:

    - divide by 5 to get 10Hz or 12.5Hz;
    - divide by 5 or 2x3 (jumper-configurable) to get to 2Hz;
    - divide by 2 to get to 1Hz;
    - divide by 2 to get to 1/2Hz (= 2 seconds);
    - divide by 5 to get to 1/10Hz (= 10 seconds);
    - divide by 2 to get to 1/20Hz (= 20 seconds);
    - divide by 3 to get to 1/60Hz (= 1 minute);
    - divide by 2 to get to 1/120Hz (= 2 minutes);
    - divide by 5 to get to 1/600Hz (= 10 minutes);
    - divide by 2 to get to 1/1200Hz (= 20 minutes);
    - divide by 3 to get to 1/3600Hz (= 1 hour);
    - divide by 2 to get to 1/7200Hz (= 2 hours);
    - divide by 5 or 2 based on the last divider to get to an average of
      1/28800Hz (= 8 hours);
    - divide by 3 to get to 1/86400Hz (= 1 day).

   Note that the division works very different than how you would do it in an
   FPGA. In an FPGA you'd probably have binary counters with a clock-enable
   signal on the registers and call it a day. But that requires *considerably*
   more logic to do. The dividers here are all clocked based on the previous
   output, which omits the clock enable requirement, and they are based on
   shift registers rather than regular binary counters. Note also that the
   dividers are chosen such that each decimal digit of the time it represents
   has its own set of counters, with states independent from the counters for
   the other digits.

 - A bunch more NAND gates in an and-or-invert configuration take the state
   signals and convert them to (active-low) 7-segment display signals for the
   clock readout. These drive the LEDs more-or-less directly.

 - A clock needs to be configurable, of course. It'd be a bit inconvenient if
   you'd have to turn it on at midnight exactly. Therefore, the clock signal
   for the minutes and for the hours passes through a configuration circuit
   with a three-way switch that allows you to override it: the circuit either
   forwards the clock signal in one extreme position of the switch, overrides
   it high in the middle position, and overrides it low in the non-latching,
   opposite position. The subsequent dividers increment on the rising edge of
   the clock signal, so releasing the switch from its non-latching position
   always increments the time, and going from the passthrough position to the
   middle position *may* increment the time (this is an unwanted side effect
   that would require an XOR to avoid, which would take more gates than I had
   room for).

 - Flipflops require a reset signal to be put in a well-defined state. A
   power-on reset circuit asserts this global reset line to do this at powerup,
   and a button allows you to override. This button could also be used to
   synchronize the seconds counter, as the clock starts at 00:00.

 - Because I don't like manually configuring clocks, and especially setting the
   time with the above interface would be annoying, there's also a
   microcontroller in here somewhere. This microcontroller can also override
   the minutes and hours clock signals, so it can also set the time. It can
   also read and override the non-latching position of the manual configuration
   switch, allowing it to convert its function to increment the time when
   you're pushing it outward rather than when you release it, and to
   auto-increment it when you hold it in the extreme position. Different-color
   LEDs are used to indicate the state of these override signals, so it's clear
   when the microcontroller is doing something. The microcontroller can
   synchronize itself using a GPS module (GPS is about the most accurate time
   reference you can get in your home that isn't a literal atomic clock!).

 - Because I had some room left on the board visually, I added a sort of
   synchroscope to it for showing the speed difference between the
   GPS-referenced and grid-referenced time signals. This is completely
   unnecessary for the operation of the clock, but I'm generally also
   interested in seeing the grid frequency fluctuations, so it's kind of a
   two-projects-in-one thing for me.

 - The microcontroller can also override the reset signal, read and override
   the grid frequency clock signal, and read and override the state of the
   7-segment display. This allows it to do fancy stuff like a self-test of the
   circuit (so you don't have to wait a day for it to pass through all states),
   and to override the display with a menu structure in conjunction with three
   soft buttons.

 - Finally, the microcontroller controls LED brightness and (in case of the
   7-segment display) color using not only PWM but also analog dimming.
   Basically, I hate flickering LEDs and LEDs that are way too bright, and
   couldn't make up my mind about the display color so I rammed some RGB LEDs
   in there.

For more details, check out the `primitives` and `subcircuits` directories.
Most of the circuitry is ASCII-art'ed in there, with more elaborate
descriptions.

How did you design it
---------------------

Yeah, about that. I'm used to working in Altium, but didn't want to use it for
this because:

 - arcs, arcs everywhere;
 - it's ridiculously slow nowadays;
 - I only have access to a sponsored license through a student association
   which has nothing to do with this project, and their licenses are
   unaffordable when you're not designing PCBs for profit full-time.

I heard KiCad is good and tried it, but started hating my life within a few
hours. Altium has spoiled me.

So, I did what any reasonable person would do and ~~abandoned the project~~
built my own PCB design flow from scratch using Blender and Python. More
details on this are in the README file of the `primitives` directory.

The practical upshot of doing everything from scratch however is that I could
hook into it wherever I wanted. For example, the Python scripts also generate
VHDL to test the actual circuit logically, with some best-effort timing
estimates even. After generating everything, you can just run `vhdeps ghdl`
or `vhdeps vsim` (see the [vhdeps](https://github.com/abs-tudelft/vhdeps)
for more info) and it will check everything (GHDL is super slow for the
main test case however). It also allowed me to make proper no-compromises 3D
models of the PCBs, something that I always wished Altium would let me do. I
don't just want the holes and outline, damnit, I want the copper traces and
silkscreen and soldermask and whatever as well! Seeing as part of the goals
is for it to be pretty, being able to make proper renders in advance was pretty
important for me.

How do I get one
----------------

tl;dr: I do not sell these, nor do I plan to do so personally. You're free to
build one yourself though (and I'd love to hear about it if you do!), and I'm
open for discussion on commercializing it if that's your cup of tea.

### BOM cost

I personally didn't care too much about this. I mentally give myself an
approximate monthly allowance for hobby stuff, and because this project has
taken so long already, I'm actually way under budget. That means I did
basically *no* cost-optimization.

I can't put an accurate price tag on the thing because I split everything over
multiple orders while prototyping, but I would expect the whole thing to set
you back somewhere around **€500-€800**, assuming you already have the
necessary equipment for SMD soldering and a 3D printer with sufficient build
area.

A lot of that is startup cost though. For example, the main PCB is ~€200 for
the minimum quantity of five even at insanely cheap places like JLCPCB. One
does not simply a 40x40cm four-layer PCB with white soldermask, I guess. The
acrylic lasercutting also has a significant startup cost, and of course part
cost at Mouser or whatever distributor you prefer will go down for higher
volumes as well. The price per clock probably drops off to around €300 or so
per clock for five of them.

### But if it's so much cheaper at scale, why not build a bunch of them and sell them?

I can't believe I'm writing this; it feels so "full-of-myself". The only reason
I'm putting this here is because multiple people have asked me to make one for
them.

No, I won't personally be commercializing these. I honestly can't be bothered
dealing with things like shipping, managing payments, taxes, supply chain,
redesigning the whole thing for pick & placing rather than manual soldering,
and so on. I'm the kind of person to hand perfectly resellable stuff over to a
local goodwill or whatever for free because trying to do anything more stresses
me out so much that it's just not even close to worth it.

*However.*

I love the idea of this thing hanging on someone else's wall as well.
Therefore, I made sure not to use any software or whatever that does not allow
commercial usage, and I did make sure that the thing should work worldwide
(50/60Hz selection, 100-250VAC input voltage, and using GPS instead of DCF77
for time sync). So, in case someone with a more entrepreneurial spirit than I
have wants to pick things up from where I left off to sell these for a profit,
it should be no problem aside from the things I mentioned above. I would expect
*some* compensation (hence why I've slapped a noncommercial license on this
thing for now), but ultimately this is just a hobby project for me. Mostly I
just want to know about it if someone does this. You can contact me at
![e](assets/e.png?raw=true "e").

Above does not apply if you just want to build one yourself and sell the other
four to friends to recoup some of the one-off costs, like I might do. If that's
all you want to do, go for it; I'd still like to know out of curiosity, but I
don't expect anything in return. The limit for me would be when you start making
profit.

Okay, then how do I build one
-----------------------------

You're going to need the following things.

 - A Linux computer or VM, probably. Some or all of it may work on Windows/Mac
   too, but your mileage may vary. The following software is needed:
    - Blender. Scripts updated for blender 4.2. Blender is good with
      compatibility, but with all the scripting going on, you might want to get
      that exact version. The makefiles look for `blender-4.2` in your `PATH`
      first if it exists, before defaulting to just `blender`.
    - Python 3.x. It used to work back on 3.6, nothing has meaningfully changed
      since, and it still works on 3.13 now that I'm writing this update. It
      probably doesn't matter too much if your version is newer than that.
    - [Gerbertools](https://github.com/jvanstraten/gerbertools). Depending on how
      lazy I am you might have to build it yourself, but that should be pretty
      easy.
    - The following regular Python modules: `matplotlib` (3.10) and `qrcode`
      (worked with 6.1 initially, still works with 8.0 without changes).
    - ImageMagick for converting huge SVGs that take forever to render to
      big-enough PNGs.
    - Inkscape for making PDFs out of SVGs (part of the acrylic plate pipeline,
      you'll probably have to customize/redo this though).
    - `git`, as in the commandline version, should exist. It's used by the
      generator to tag the generated boards with the current revision.
    - `make` is abused for some things.
    - `7z` (7zip) is used for packing the generated gerber files into a zip
      file.
    - You may also want [`vhdeps`](https://github.com/abs-tudelft/vhdeps) and a
      compatible simulator, if you intend to change any circuitry.

 - Soldering equipment. If you've never soldered (SMD) before, this might not
   be the best project to start with. The LED drivers in particular are 0.5mm
   pitch TSSOPs with a thermal pad. The boards are designed to be hand-soldered
   though, so the pads are relatively long, and I took care to only connect
   traces to the end that you stuff the soldering iron into, so heating them up
   should be relatively easy. Unless you like to live dangerously, you should
   also have anti-ESD gear and actually use it during assembly.

 - A current-limited lab power supply, multimeter, waveform generator, and
   oscilloscope are very much nice-to-have. I don't think it's humanly possible
   to solder everything correctly the first time, so you will be doing some
   debugging.

 - A 3D-printer with at least 21x25cm build area. I'm using a Prusa MK3s with
   a stock 0.4mm nozzle and print in PETG. I'm not sure how much filament is
   used exactly. You'll want some 3D-print post-processing stuff as well, which
   I'm assuming you'll have if you have a printer.

 - An M3 tap for inner thread.

 - A source for the lasercut acrylic plates. I'm using a local Dutch shop
   ([laserbeest.nl](https://www.laserbeest.nl/)). Unfortunately I'm not sure if
   they ship internationally. Their ordering instructions are a bit "custom",
   so you'll probably have to change the pipeline or do some manual conversion
   work of the generated PDF/SVG files.

 - A source for the two PCBs. I'm used to ordering from JLCPCB, but there are
   more of them out there.

 - A source for the components. I'm using Mouser for everything now, so the
   generated ordering information is for them.

 - A source for the Teensy LC, the GPS module, and the antenna. I got those
   from [TinyTronics](https://www.tinytronics.nl/shop/en); a local shop again,
   but I'm pretty sure they ship internationally, or at least within Europe.
   Either way, the Teensy in particular shouldn't be hard to get your hands on,
   and you can probably jury-rig any GPS module you want in there (or leave it
   out entirely if you don't care enough about GPS sync). The headers you'd
   probably want to mount the Teensy to the support board are not included in
   any ordering list; you can do anything between proper male/female headers
   and just sticking wires through the holes and soldering them.

 - Some miscellaneous parts not in any ordering list because I had them laying
   around:

    - 41 M3x12mm screws with a domed head of at most 6.2mm diameter and about
      2mm thickness, though if you don't have a bunch of screws in stock you
      might want to get longer ones and cut them to size with a thread cutting
      tool;
    - 25 standard M3 hex nuts, 2.5mm thick;
    - a long M3 screw is nice to have to help pull the nuts into the printed
      parts;
    - a screwdriver for the above, obviously;
    - calipers are very useful to have lying around, if only to measure the
      thickness of the acrylic you got;
    - a mains power cord to mount to screw terminals on the support board
      (preferably with grounding lead, though this is technically not necessary
      due to the lack of exposed metal);
    - stuff to clean the acrylic with when you're done (I used "wasbenzine,"
      but that stuff doesn't seem to have a proper English translation for some
      reason. The best translation I suppose would be pure gasoline. Contrary
      to what Google et al will tell you it is *not* white spirit, which would
      be "terpentine" in Dutch, and would be likely to mess up your acrylic).

 - An appropriately filled wallet, because this is not a cheap project. But we
   went over that already.

### 1) File generation

If you're ordering via laserbeest and want to use the existing pipeline, you
will want to set the following environment variables:

 - `ACRYLIC_NAME`: your full name;
 - `ACRYLIC_EMAIL`: your e-mail address; and
 - `ACRYLIC_PHONE`: your phone number.

These are added to the SVG/PDF files that are generated for Laserbeest for
their reference, as per their instructions.

You'll also want to update the header of `generator/orderlist.py` to select
the LED color you want. Seven color schemes are predefined. At the time of
writing I've only tried orange; your mileage may vary with the resistor values
for other colors. LED brightness differs a lot based on color.

Once you have all that, or the computer part at least, run `make` in the root
directory and go get coffee. It takes 20 minutes or so to generate everything
on my fairly beefy computer, though most of it is single-threaded because I'm
lazy, so the beefyness of your computer might not make too much of a
difference.

Note that the root makefile is *not at all* intelligent, and may as well be a
shell script. You may therefore want to comment out part of the `make` recipe
manually while iterating to not regenerate literally everything each time.
There's also `generator/config.py`; if you set the `LAYOUT_ONLY` constant,
things will be way faster, but won't generate any copper, and use
reduced-complexity routing for the circuit on the silkscreen.

Anyway, the pipeline generates the `output` directory, with about a GB's worth
of files in it (hence why I don't try putting the generated files on github).
The filenames should be fairly self-explanatory, at least in conjunction with
the documentation scattered about this repo in the form of README files.
Nevertheless, the most important ones are:

 - `mainboard.zip`: Gerber production files for the main PCB;
 - `support_board.zip`: Gerber production files for the support PCB;
 - `*.*.traces.png`: circuit board assembly instructions (and copper layout);
 - `mainboard.laserbeest.pdf`/`.svg`: acrylic plate production files;
 - `mouser.txt`: Mouser ordering list; and
 - `tinytronics.txt`: TinyTronics ordering list (the Teensy, GPS, and antenna).

### 2) Ordering

You should start by ordering the parts, obviously: the Mouser/TinyTronics
electronics parts, the PCBs, the acrylic sheets, and the consumables if you
don't have them laying around like I do.

As stated, the build process generates `mouser.txt` for the mouser ordering
list, usable [here](https://nl.mouser.com/Tools/part-list-import.aspx). If
things are not in stock, you'll either have to wait or look for alternatives
yourself; you can specify these alternatives in `generator/orderlist.py`, after
which you can regenerate by just running `python3 generator/orderlist.py`. If
you (have to) go for the backorder route, I strongly recommend the "ship items
as they become available" option; in my experience, Mouser doesn't reserve
anything for your order, so by the time the originally problematic part is
finally back in stock, something else might be out of stock again.

After you copy the part list into your basket, make sure to round up the part
count, especially for uncommonly used resistor values and such: Mouser levies
what I can only describe as an "asshole tax" for people who order small amounts
of these, as ordering more will often cost *less*. I've seen an extreme case
where the price break for 10+ was so much cheaper than the price break for 1+
that buying ten was cheaper than buying one! The ordering system does not
notify you of this. In general, by the way, it's good practice to over-order
the tiny parts a little bit, so you don't have to place a new order if you
misplace or break a few of them.

As for the Tinytronics parts, the actual parts are a Teensy LC (which you can
get just about anywhere), and any GPS module with a VCC|GND|TX|RX|PPS pinout
using a standard 2.54mm header. You can probably source both from wherever if
Tinytronics doesn't work for you. Don't forget to buy an antenna with a long
lead as well; they're commonly available for use in cars. Headers to mount
these are not included in the Mouser order either, so you'll need to get them
yourself.

For the PCBs, everything assumes standard 1.6mm 4-layer PCBs with 1oz copper on
the outer layers and something around .5oz on the inner layers. The mainboard
is visible and is assumed to be built with a white soldermask and black
silkscreen, but it's up to you; the support board is not visible and thus the
color does not matter. Stackup was designed with 0.1mm between the outer and
inner layers in mind, but I later found out that JLC only does this for green
soldermask PCBs, so I ended up with 0.2mm separation. Doesn't really matter;
nothing is explicitly impedance-matched. The only thing is that the trace
capacitance calculations I did assume .1mm separation, but that would be the
worse case anyway.

The footprints are designed for conventional soldering by hand. If you want to
use solder paste with an oven or hot air, you might want to rework some
footprints here and there. In particular, the support board has four components
with a thermal pad (the LED drivers and the hot-swap controller), which have a
large hole under the pad to provide access to a conventional soldering iron;
you'll probably want to remove those holes when using solder paste.

As for the acrylic, three sheets are needed:

 - `Front`: clear, 3mm, at least 40x40cm. Includes engraving instructions in
   addition to cuts.
 - `Highlight`: opaque white, 5mm, at least 40x40cm.
 - `Display`: opaque black, 3mm, at least 23x6cm.

The thickness tolerance of Laserbeest's acrylic source is abysmal, apparently
due to how the sheets are made. So everything is designed with about +/-1mm
thickness tolerance in mind. However, you may need to adjust some 3D-printed
parts here and there, or you may need slightly shorter or longer M3 screws.
Of particular importance is that the button and slide switch caps have the
right height,

You may also need to adjust the hole sizes in the `Front` sheet based on laser
width and how gutsy you're feeling. They need to be threaded, so the finished
hole size should be 2.5mm. They are 2.35mm in the design files for Laserbeest,
which worked well based on experimentation.

When you receive the acrylic, don't throw the bubble wrap it undoubtedly comes
wrapped in away! It'll be useful during assembly.

### 3) 3D-printing

I would recommend to wait with this until you have the acrylic, because some of
the parts depend on its thickness to various degrees. I was far too impatient
for this, myself; just be aware that you may need to reprint parts later if you
don't wait. The following parts depend on the thickness of the acrylic:

 - the four quarter panels of the back shell have the clamping surface for the
   screw heads at just the right size for the bottom of the M3x12 screws that
   mate with the clear acrylic sheet to be flush with the front, so this
   recess depends on the thickness of the white and clear acrylic sheets;
 - likewise for the "display extender" part, of which both the total height and
   mounting flange thickness depends on the thickness of the black and clear
   acrylic parts;
 - the button and slide switch caps depend on the thickness of the white
   acrylic sheet.

The Blender sources for the parts are in the `printed` folder, the main one
being `assembly.blend`. When you open it (give it time, the boolean operations
and geometry involved are considerable) you will be presented with some text
and a few "empties;" the axis-looking things in the middle. Their negative-Z
position represents the thickness of the three acrylic sheets. You can select
them by right-clicking (or left-clicking I think, if you're using the 2.8+
keybinds), and then use the transform panel on the top-right of the viewport to
change the Z coordinate to negative the thickness.

Once you've done that, note the note the panel on the top-right of the screen,
listing the assembly steps. You can disable visibility of all the steps except
the first by clicking the eye icons, then work from there. Use numpad 7 to view
the clock from the back (as you will be assembling it), or numpad 9 to view it
from the front. Dragging the middle mouse button will drag the view around,
holding shift as well will pan, and scrolling zooms in and out.

STL files can be generated by selecting the object you want (right/left-click
as before), selecting File -> Export -> STL, ticking the "Selection Only"
checkbox on the right, and picking a nice filename. You'll have to orient them
onto the build plate (most parts have an obvious flat side) using the slicer
for your printer.

I use PETG for everything. PLA might be fine as well, but be careful that in
particular the mounting bracket is strong enough -- wouldn't want the clock to
break off your wall in the middle of the night. I don't exactly consider myself
to be a very experienced 3D-printer, so your mileage may vary.

Some of the parts need build plate supports, so some post-processing is
involved. The slide switch caps in particular needed some TLC for me before
they would slide properly, and I had to drill out the holes in the spacers for
the extra-long headers. If you don't have a 1mm drill and a drill press to do
this with, you can probably mess with the part and print settings until that
one works straight out of the printer though, or you could probably also just
eyeball the correct insertion depth for the headers when soldering.

### 4) Mechanical assembly (dry run)

Once you have the 3D-printed parts, acrylic, and bare PCBs, I would suggest a
dry run of assembling the thing, so you know what goes where and you can be
sure everything fits before all the delicate parts are populated.

 - Carefully clean the clear acrylic sheet. There will be debris from the
   engraving; make sure it doesn't cause scratches! I personally messed up here
   because I assumed there would be protective foil on both sides; there was
   not.

 - Carefully tap the holes in the clear acrylic sheet. Be patient; acrylic
   cracks if you're too rough. Don't use power tools!

 - Place the clear acrylic sheet on bubblewrap, to avoid causing scratches and
   allow the button and slide switch caps to stick out slightly. The rough,
   engraved side should be facing up.

 - Place the black acrylic sheet on top. It is *not* symmetrical in any
   direction: make sure that the colons are off-center *away* from the side
   with the synchroscope and pushbutton cutouts, and of course that the
   screw holes align.

 - Place the printed display extender part on top of the display, again
   ensuring that it is oriented correctly.

 - Mount the black acrylic sheet and display extender using two M3x12 screws.
   Be careful not to exert too much torque; threaded holes in acrylic are
   quite fragile!

 - Place the white acrylic sheet on top. The cutout for the display should
   constrain it in roughly the right place aside from 180deg rotation symmetry;
   align based on the synchroscope engraving and/or button cutouts to avoid
   mounting the plate upside down.

 - Place the three button caps (2x round, 1x oblong) and the two slide switch
   caps in the appropriate cutouts.

 - Carefully place the mainboard on top. First align the slide switch caps with
   the slots in the PCB (and the slide switches themselves if you already
   soldered then), then align the pins on the bottom of the button caps with
   the holes in the PCB, and finally align the holes.

 - If you haven't already, insert nuts in the hex recesses of the four quarter
   panels. There are eleven of these. Pull them in with a screw if necessary,
   and make sure they're all the way in (they should be flush or slightly
   recessed into the bosses. If your print is undersized and they fall out, you
   might want to glue them in.

 - Slot the quarter panels together. They are all different, so there's only
   one way to do this. Secure them by placing screws in the four shared screw
   holes; the assembly shouldn't fall apart anymore after you do this, although
   it will still be quite floppy.

 - Carefully place the panels over the rest of the assembly. The triangular
   screw hole pattern should be at the top of the clock, i.e. the side with the
   synchroscope and buttons.

 - Start by tightening the four screws that hold the quarters together. Again,
   be careful not to exert too much force. Be especially careful if you're
   impatient and are doing this before you have the PCBs: you can easily break
   the 3D-printed parts by tightening the screws without the 1.6mm spacing
   provided by the PCB. Once these four screws are in, screw the remaining ten
   in in any order.

 - Flip the clock over and make sure that the slide switches and buttons move
   freely. If not, disassemble in reverse order and file them down a bit.
   Repeat ad nauseum until they work right. Once done, place the clock down
   on its front again on the bubble wrap.

 - Mount the wall mount bracket to the assembly with three screws. The screws
   mate with the triangular-pattern nuts in the top quarter panel. Be careful
   when tightening these the first time; the screws should be too short to
   reach the PCB, but if they do, you can easily damage the PCB.

 - If you haven't already, insert nuts in the hex recesses of the support board
   interface part. There are four of these. Pull them in with a screw if
   necessary. If your print is undersized and they fall out, you might want to
   glue them in.

 - Mount the panel-mount SMA antenna connector end of the SMA to uFL adapter
   cable that comes with the GPS antenna to the small square SMA insert part,
   making sure to align the flat side of the panel-mount connector with the
   flat side of the hole.

 - Slide the above assembly into the corresponding retaining structure of the
   support board interface part. Note that this might require some "gentle
   persuasion" the first time; it should be more-or-less press-fit.

 - Mount the support board interface assembly onto the main assembly with eight
   screws. They mate in the same way as the wall mount bracket, so be careful
   if the screws may be too long.

 - If you haven't already, insert nuts in the hex recesses of the display light
   guide. There are six of these. Pull them in with a screw if necessary. If
   your print is undersized and they fall out, you might want to glue them in.

 - Mount the display light guide to the support board using six screws. Be
   careful not to place it upside down; follow the silkscreen on the PCB.

 - If you haven't already, insert nuts in the hex recesses of the high-voltage
   top cover and strain relief. There are two of these in either part. You
   know the drill by now.

 - Mount the top and bottom high-voltage covers to the support board using two
   screws. There should only be one way to do this.

 - Mount the strain relief to the bottom high-voltage cover.

 - Place the support board onto the main assembly, making sure to align the
   screw holes. The upright flanges inside the support board interface part
   should constrain it.

 - Place the support board cover on top. Again, some "gentle persuasion" may be
   needed for the SMA connector insert the first time. Finally, clamp it down
   with four screws, that should mate with the four nuts in the support board
   interface part.

 - Carefully lift the clock up by the wall mount. Make sure it's strong enough
   to hold the weight with ease.

 - Find a nice place to mount it to a wall! You can just use a nail or screw to
   do it, or you could print a part that mates with the wall mount bracket if
   you're worried about the strength of the part.

Disassemble in the reverse order as usual. The wall mount can stay mounted to
its quarter panel, but note that you can't remove the quarter panels from the
acrylic without removing the support board assembly, because it hides one of
the fourteen screws that mate with the acylic.

### 5) Electronic assembly

Some preprocessing is required:

 - The 3D-printed parts include a small lead bending tool for the 3mm LEDs. It
   consists of two square printed parts, and is completed using four M3 nuts
   and four M3x12 screws. To use it, push the LED into the hole, bend the leads
   outward far enough for the screws to reach the recesses for the nuts on the
   other side, then carefully tighten the screws while guiding the leads into
   the cutouts for them. Once tightened, cut the exposed part of the leads off
   with pliers. Finally, disassemble everything again to retrieve the LED. I've
   found that two screws on opposite sides is enough.

 - The trace connecting the USB bus voltage to the 5V rail on the Teensy LC
   must be cut, to prevent the power supply on the support board from trying to
   power your PC.

 - The mainboard to support board connectors are slightly too short right out
   of the box: the male side should be soldered flush to the opposite side of
   the PCB rather than having it stick through slightly as usual.

Ultimately, the order in which you solder the parts is up to you. Here's some
tips and recommendations, however.

 - I couldn't be bothered to add part designators to the board generation
   scripts and design entry file formats, so you'll have to use the
   `*.*.traces.png` output files to figure out what to solder where. However,
   the circuitry is so repetitive that you won't need it most of the time.

 - The mainboard circuitry is highly linear, which means you can solder one or
   a few subcircuits at a time and then test whether everything works. Start
   with the reset circuit and the clock pulldown resistor (the 10k resistor
   near the TSSOP I/O expander), then work your way around clockwise for the
   dividers, and finally solder the decoders. You can test using the staggered
   receptable for a standard 2.54mm 5-pin header (push it in upside-down; the
   spring force of the pins will friction-lock it in place). The `f50Hz` signal
   should receive a 0V..5V clock signal, `Vled` and `Vffled` should be pulled
   *down* to somewhere between 2.5V (max brightness) and 4.5V (least
   brightness) to turn the LEDs on, and `0V`/`5V` should be self-explanatory.
   A two-channel waveform generator is ideal for the `f50Hz` and
   `Vled`/`Vffled` signals, the latter because a waveform generator can pull
   down as well (unless you have a super-fancy power supply, it won't be able
   to). If you don't have a waveform generator or only have a single-channel
   generator however, you can probably get the LEDs to light up with a 1:1
   voltage divider using 100R resistors as well, and you can strobe the clock
   by just pushing a 5V wire into the `f50Hz` signal (it will bounce though,
   so this won't be very controlled). Use a properly current-limited power
   supply (somewhere around 400mA should be enough for the whole clock with
   the default LEDs), such that you don't fry something if you accidentally
   short-circuited something. Being able to see the current is also very
   useful, because then you'll see the current rise when a gate output is
   shorted. Other than that, ensure that all LEDs blink when you apply enough
   clock pulses. Some common symptoms:

    - Current shoots up by about 40mA for some flipflop states: there's
      probably a short-circuit to 0V or 5V *after* a 100R filter resistor.

    - Current shoorts up by about 150-200mA for some flipflop states: there's
      probably a short-circuit to 0V or 5V between a gate output and the
      100R filter resistor.

    - Current limit kicks in at around 1.0V to 1.5V: you probably mounted a
      gate rotated 180-degrees.

    - Current limit kicks in immediately: you have a dead short somewhere. You
      can trace this by measuring the voltage across the decoupling capacitors
      while the power supply is on. I got about 2.7mV over the decoupling
      capacitors serving good circuits and less than 2mV for the one that had
      the short, for only 200mA supply current.

    - No unexpected current (the current should be <1mA when the `f50Hz` input
      is idle and the LEDs are off), but one or more flipflops/decoder outputs
      don't work right: usually this is due to a bad soldering joint for one
      of the gates. You'll have to debug this by finding the gate that doesn't
      perform its logic function properly.

    - The circuit works, but a LED doesn't light up: check for bad soldering
      joints in the LED circuitry.

    - Everything is fine in steady-state, but a flipflop doesn't work: I didn't
      personally encounter this, but this is what I'd expect to see if you
      misplaced a capacitor or resistor somewhere in the RC filter circuits.
      The filters are there to solve worst-case hold timing, so the flipflops
      might misbehave with improper filters. I've found that leaving the 330pF
      and 2.2nF capacitors out entirely also works, however (with a sample size
      of only 1 flipflop, though).

 - While soldering the mainboard, put short screws in the screw holes that
   prevent you from accidentally exerting force on the 3mm LEDs or 1.27mm
   jumpers when the board is upside-down. Otherwise, you can easily bend the
   headers, or push the SMD pads for the LEDs right off the board.

 - For the support board, first solder the hot-swap controller circuit and test
   it. There's a lot of critical resistor values there, and if they're wrong,
   the board won't do anything or won't be as protected against
   over/undervoltage and overcurrent as it can be. I would furthermore suggest
   leaving the mains stuff for last, because it's large, and because you'll
   then lose the ability to power the board with a better-protected lab power
   supply.

