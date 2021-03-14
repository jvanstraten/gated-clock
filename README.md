Gated Clock
===========

Hi! Looks like you stumbled upon this project before it's completely finished.
Maybe one of JLCPCB's engineers decided to scan the QR code? :D

Anyway, the point of this project is to:

 - build a functional digital clock out of only discrete logic gates (74LVC1G10
   3-input NANDs to be specific) and passives;
 - make sure the entire circuit for as far as this is needed to make it work is
   visible on the front, with LEDs for (almost) all digital signals;
 - actually make it look pretty; and
 - actually make it useful.

Note that none of the above include anything about BOM cost. See the section on
cost below.

License
-------

Let's get the fine print out of the way first. The license for this stuff is
[Creative Commons BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
See also the LICENSE file for the full plaintext.

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
    - Blender. I'm using version 2.91. Blender is good with compatibility, but
      with all the scripting going on, you might want to get that exact version.
      The makefiles look for `blender-2.91` in your `PATH` first if it exists,
      before defaulting to just `blender`.
    - Python 3.x. I'm using 3.6 because I'm too lazy to upgrade my OpenSUSE
      install. But it probably doesn't matter too much if it's newer than that.
    - [Gerbertools](https://github.com/jvanstraten/gerbertools). Depending on how
      lazy I am you might have to build it yourself, but that should be pretty
      easy.
    - The following regular Python modules: `matplotlib` (I'm using 3.1.0, but
      it's only used to render text, so probably doesn't matter) and `qrcode`
      (6.1, may or may not matter).
    - ImageMagick for the `convert` command.
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
   should be relatively easy.

 - A 3D-printer with at least 21x25cm build area. I'm using a Prusa MK3s with
   a stock 0.4mm nozzle and print in PETG. I'm not sure how much filament is
   used exactly.

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
   out entirely if you don't care enough about GPS sync).

 - An appropriately filled wallet, because this is not a cheap project. But we
   went over that already.

If you're ordering via laserbeest and want to use the existing pipeline, you
will want to set the following environment variables:

 - `ACRYLIC_NAME`: your full name;
 - `ACRYLIC_EMAIL`: your e-mail address; and
 - `ACRYLIC_PHONE`: your phone number.

These are added to the SVG/PDF files that are generated for Laserbeest for
their reference, as per their instructions.

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

You should start by ordering the parts, obviously: the PCBs, Mouser/TinyTronics
electronics parts, and the acrylic sheets.

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

For the acrylic sheets, three sheets are needed:

 - `Front`: clear, 3mm, at least 40x40cm. Includes engraving instructions in
   addition to cuts.
 - `Highlight`: opaque white, 5mm, at least 40x40cm.
 - `Display`: opaque black, 3mm, at least 23x6cm.

The thickness tolerance of Laserbeest's acrylic source is abysmal, apparently
due to how the sheets are made. So everything is designed with about +/-1mm
thickness tolerance in mind. However, you may need to adjust some 3D-printed
parts here and there.

You may also need to adjust the hole sizes in the `Front` sheet based on laser
width and how gutsy you're feeling. They need to be threaded, so the finished
hole size should be 2.5mm. They are 2.35mm in the design files for Laserbeest,
based on experimentation.

The thing is assembled with 41 M3x12mm screws with at most 6.2mm diameter, 2mm
thick heads, and 25 M3 hex nuts of standard 2.5mm thickness. **These are not**
**in any ordering list, because I had them all in stock!** If you can't be
bothered to adjust the 3D-printed parts too much based on acrylic plate
thickness, you may want to get M3x15mm instead and cut the screws to size with
a thread cutter where applicable.

**Also not in any ordering list is a mains cable with plug.** The 3D-printed
files assume an outer diameter of at most 7-8mm or so, allowing for an earthed
cable to be used. This shouldn't be strictly necessary because it should be
properly isolated, but better safe than sorry, right?

Assembly notes TODO. I'm not that far into the process yet. It should be pretty
obvious if everything works out, though.
