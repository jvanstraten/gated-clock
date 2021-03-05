Manually placed features of the main PCB
========================================

Includes the board outline, screw holes, etc., and everything else that isn't
generated. This also includes the microcontroller-controlled circuitry, i.e.
the Vled routing, the buttons (including the manual reset button), the
microcontroller status LED, and the synchroscope LEDs.

Mechanical notes
----------------

The mainboard primitives define the shapes of four things: the PCB (of course),
a 5+/-0.9mm thick white acrylic sheet named "Highlight", a 3+/-0.7mm black
acrylic sheet named "Display", and a 3+/-0.7mm transparent acrylic sheet named
"Front". The design is specifically engineered for a local laser cutting shop,
laserbeest.nl. To have them cut elsewhere, you probably need to do some file
conversion work, and might have to change some dimensions here and there (the
2.35mm holes in particular).

They PCB and acrylic sheets are layered as follows:

```
      ⌀ 2.35+0.2                                            ⌀ 2.35+0.2
       |<--->|                   Outside                     |<--->|
       |     |                                               |     |
       |     |                                               |     |
.------. - - .-----------------------------------------------. - - .-----------  ------
|      |     |                                               |     |                 ^
|      |     |              Front (transparant)              |     |              3.0±0.7
|      |     |                              Engraving --> ___|     |___________      v
:------' - - '.----------------.-----------.----------..--==.' - - '.==========  ----------------
| \ \ |       | \ \ \ \ \ \ \ \|           |\ \ \ \ \ ||X X |       |X X X X X       ^         ^
|\ \ \|       |\ \ \ \ \ \ \ \ |           | \ \ \ \ \|| X X|       | Display X   3.0±0.7      |
| \ \ |       | \ \Highlight\ \|           |\ \ \ \ \ ||X X |       |X X X X X       v      5.0±0.9
|\ \ \|       |\ \ \ \ \ \ \ \ | Top side  | \ \ \ \ \|'----' - - - '----------  ------        |
| \ \ |       | \ \ \ \ \ \ \ \|   .--.    |\ \ \ \ \ |     |       |                          v             v
:-----: - - - :-----------------------------------------. - | - - - | - - - - -  ------------------------------
| / / |       | / / / / / PCB / / / / / / / / / / / / / |   |       |                                     1.6±0.1
'-----' - - - '-----------------------------------------' - | - - - | - - - - -  ------------------------------
      |       |   '--'        '--'           '--'           |       |                                      ^
      |       |                Bottom side                  |       |
      |<----->|                                             |<----->|
      ⌀ 3.2±0.2                  Inside                     ⌀ 3.2±0.2
        (14x)                                                  (2x)
```

The highlight sheet serves as a spacer between the front sheet and the PCB, and
to highlight the borders around the many subcircuits. The tallest component on
the front side of the PCB is 4mm high (the 50/60Hz jumpers), so the spacing
must be at least 4mm. The tolerances on sheet thickness at Laserbeest are quite
abysmal; a nominally 5mm thick sheet is just barely thick enough in the worst
case.

The front sheet serves to protect the system from dust and the likes, and allows
it to be cleaned easily. It is also used to form good-looking displays through
engraved surfaces: these surfaces become opaque but translucent, scattering the
LED light and making the segment shapes almost invisible when the LEDs are off.
Note however that the engraved side must be facing inside for this to work,
thus the drawing for the front sheet is mirrored.

The display sheet serves as a black backing for the engraved surfaces on the
front to increase contrast, and the display sheet is intentionally a bit larger
than the engraved surface, thus outlining the display with a thick, black line.

It'd be great if the display and highlight sheets would have a nice press fit,
but this is not doable with a laser. Instead, there is a gap between them of
the thickness of the laser, which seems to be about 0.1 to 0.2mm for
Laserbeest. The 3D-printed part underneath the display might be tweakable to
fit snugly, however.

The whole thing is assembled using a few M3 screws. They screw in from the
back, mating with tapped holes in the front sheet. Being able to see the end
of the screws isn't ideal, but doesn't look *too* too bad, and it beats gluing
everything together. The correct drill size for an M3 tap is 2.5mm, but we need
to account for laser thickness; experimentally, a 2.3mm hole was found to be
uncomfortably tight to tap (lots of squeeking and mild cracking noises, though
the sheet remained visibly intact), while a 2.4mm hole was still slightly
oversized. Thus, 2.35mm was chosen.

The PCB (and the 3D-printed shell structure on the back) screws into the front
panel using 14 screws; 12 on the border, and 2 diagonally across the display.
The highlight sheet is probably quite weak due to all the cutouts, so it's
important for structural integrity that it's firmly clamped between the front
sheet and the PCB. The display sheet and 3D-printed spacer between it and the
support PCB are mounted to the front directly 2 more screws, and are only
fixed this way; this is necessary to clamp everything down to the front sheet
properly despite the large sheet thickness tolerances, which in turn is
necessary for aforementioned structural integrity and to minimize any gap
between the engraved surface on the front sheet and the display sheet.

Support board interface
-----------------------

The mainboard connects to the support board through five extra tall but
otherwise standard 2.54mm 16-pin headers; TSW-108-12-T-S-RA headers on the
mainboard, mating with SSQ-108-01-T-D sockets on the support board, leading
to a board-to-board distance of about 27.5mm when the headers are soldered
flush to the board. The headers surround the display area, so they are just
barely covered by the display sheet, but can still be through-hole.

The headers carry the following signals:

 - 5V power and ground;
 - the 50/60Hz grid-based clock signal;
 - display data (as the LEDs for the time display are on the support board);
 - SPI/I2C+IRQ interface to a 16-bit I/O expander on the mainboard;
 - microcontroller interface for the hours and minutes configuration; and
 - LED control voltages for the flipflop LEDs, NAND gate LEDs, synchroscope,
   and microcontroller status RGB LED.

I/O expander
------------

To limit the amount of signals that need to pass through the headers, an I/O
expander is added to the mainboard. This can be either an MCP23017T (I2C) or an
MCP23S17T (SPI). The SPI/I2C pins are pulled high by 10k resistors to allow the
mainboard to work without support board while testing, without noise causing
all kinds of stuff to happen. The address and reset pins are pulled up via a 1k
resistor. Only the INTA pin is forwarded to the support board. The GPIO pinout
is as follows:

 - GPA0: mode button, active low with no hardware debouncing.
 - GPA1: down button, active low with no hardware debouncing.
 - GPA2: up button, active low with no hardware debouncing.
 - GPA3: synchroscope H6.
 - GPA4: synchroscope H4.
 - GPA5: synchroscope H2.
 - GPA6: synchroscope H5.
 - GPA7: synchroscope H3.
 - GPB0: synchroscope L6.
 - GPB1: synchroscope L5.
 - GPB2: synchroscope L4.
 - GPB3: synchroscope L3.
 - GPB4: synchroscope L2.
 - GPB5: synchroscope L1.
 - GPB6: synchroscope H1.
 - GPB7: reset readout/override.

Reset circuit
-------------

The mainboard includes the following reset conditioning circuit.

```
                    Vcc          Vcc                                           Vcc
                   -----        -----        100nF                  100nF     -----
                     |            |           . .                    . .        |
                    .-.           o-----------| |-----------o--------| |--------o
               100k | |           |           ' '           |        ' '        |
                    | |     .-._  | 5  SN74LVC1G17DCKR      |             .-._  | 5  SN74LVC1G17DCKR
                    '-'     |   `-._                        |             |   `-._
          ____       |    2 |     __`-._  4  B   ____       |      O    2 |     __`-._  4  B   ____
  .------|____|------o------|   _||    _:-------|____|------)------o------|   _||    _:-------|____|------o------ Arn
  |        1k        |      |      _.-'          10k        |      |      |      _.-'          100        |
  o                  |      |  _.-'                         |      |      |  _.-'                         |
   \  Manual   1uF -----    '-'   | 3                       |      |      '-'   | 3                     ----- 330pF
  o \ reset        -----          |                         |      |            |                       -----
  |                  |            |                         |      |            |                         |
  |                  |            |                         |      |            |                         |
-----              -----        -----                     -----    |          -----                     -----
 Gnd                Gnd          Gnd                       Gnd     |           Gnd                       Gnd
                                                                   |
                                                           From GPIO expander
```

The circuit provides a reset pulse at least 35ms in length at powerup, assuming
Vcc rises fast enough. The circuit can be reset manually by pushing the manual
reset button. Furthermore, the microcontroller can read the state of the reset
circuit and override it in either direction using the GPIO expander. The RC
circuit at the end is a copy of the one used for "fast" NAND gates; it limits
the slew rate to prevent ringing.

The reset signal is not synchronized with the incoming clock in any way.
Therefore, weird stuff might happen when the reset is released at the wrong
time. However, all flipflop circuitry should automatically recover from
invalid states, and the odds of the reset being timed this way are extremely
low during normal operation, as the incoming clock frequency is only 50/60 Hz.

The reset circuit is depicted on the silkscreen as well, although the
decoupling capacitors, switch current limit resistor, and RC filer are omitted.

Clock circuit
-------------

While a clock generation circuit is depicted on the silkscreen, this circuit
is not implemented on the mainboard for the following reasons:

 - the required anti-creepage slots would be ugly;
 - the high-voltage components are large and through-hole, which would again be
   ugly;
 - strong electric fields and the relatively high temperatures of some of the
   parts might cause the circuit board to blacken; and
 - when the cover is off, you don't want surprise electric shocks.

Instead, the clock signal comes straight from the support board. It does
however have a 10k pullup resistor to properly define the signal when the
support board is not connected.

Microcontroller user interface
------------------------------

The microcontroller is controlled using three pushbuttons, and can provide
visual feedback using a dedicated RGB LED next to these buttons. It can of
course also override the value displayed on the synchroscope, and it can
override all display segments on, at which point it can control them
individually using the LED controllers. Thus, a menu structure can be
programmed into it.

The buttons are marked Up, Down, and Mode, the former sharing a single
3D-printed cap. A short press of mode should cycle through the various
configuration parameters, such as time zone and DST setup for GPS
synchronization and LED color/brightness. When any configuration parameter
is active, the display content is overridden to show an abbreviation of the
parameter name and its value; this override is visible by way of the four
colon LEDs turning off (this should be hardwired). The clock should always
return to normal operation after a timeout.

The configuration parameters might be:

 - `br   0`..`br 100` for overall LED brightness control;
 - `GPS  0`..`GPS  1` for enabling or disabling daily GPS synchronization at
   3:00;
 - `nS xxx` depicts number of GPS satellites in view (up/down does nothing);
 - `utc-12`..`utc 12` for timezone setup;
 - `dSt  0`..`dSt  1` to enable/disable automatic DST switching (the DST
   switching date logic would need to be programmed into it via Arduino
   however);
 - `Fb   0`..`Fb 100` for flipflop LED brightness;
 - `Gb   0`..`Gb 100` for NAND gate LED brightness;
 - `Sb   0`..`Sb 100` for synchroscope LED brightness;
 - `db   0`..`dB 100` for setting display and status LED brightness;
 - `dh   0`..`dB 359` for setting display hue;
 - `dS   0`..`dB 100` for setting display saturation.

Letters on 7-segment displays are a bit awkward, but (most) are possible:

```
  b      c      d      F      G      h      n      P      r     S      t      u
                      ---    ---                  ---          ---
|                 |  |      |      |             |   |        |      |
 ---    ---    ---    ---           ---    ---    ---    ---   ---    ---
|   |  |      |   |  |      |   |  |   |  |   |  |      |         |  |      |   |
 ---    ---    ---           ---                               ---    ---    ---
```

A long press of the mode switch should toggle the microcontroller altogether.
When the microcontroller is powered down, all outputs to the clock circuit
are high, the microcontroller status LED is off, and the synchroscope is off.
Only LED brightness setup is retained. The former also means that
auto-increment control of the hours/minute configuration circuit is disabled.
Thus, in this state, the discrete clock circuit is operating without any
"cheating" going on.

Synchroscope
------------

A sort of synchroscope is included (mostly as filler) to show the difference
between the grid frequency and the supposedly much more stable GPS clock.
Hopefully it'll be possible to see load fluctuations in the electrical grid by
this means. For those unaware, the electrical grid "communicates" the current
discrepancy between power consumption and production via minute frequency
fluctuations. When consumption is greater than production, all synchronous
generators physically slow down, thus reducing grid frequency, which is then
detected and results in an increase in production in all power plants
simultaneously merely by regularing the RPM of the generators (and vice versa).
In Europe, the nominal instantaneous frequency is about +/-0.05Hz. That means
the clock will run 1ms slow or fast each second, thus one "revolution" of the
synchrometer per ms of phase shift between the grid and GPS signal is probably
good.

The synchroscope is built using 30 LEDs arranged in an unusual multiplexing
circuit that allows these LEDs to be controlled with only 12 slow GPIO pins and
two DAC/PWM channels, such that any two (modulo) consecutive LEDs can be on
simultaneously with independent dimming for antialiasing and brightness control.
The circuit for this is as follows.

```
         H1                      H2                      H3                      H4                      H5                      H6
          |                       |                       |                       |                       |                       |
          |                       |                       |                       |                       |                       |
         .-.                     .-.                     .-.                     .-.                     .-.                     .-.
         | | Depends             | | Depends             | | Depends             | | Depends             | | Depends             | | Depends
         | | on LED              | | on LED              | | on LED              | | on LED              | | on LED              | | on LED
         '-'                     '-'                     '-'                     '-'                     '-'                     '-'
          |                       |                       |                       |                       |                       |
          |                       |                       |                       |                       |                       |
          |H1R                    |H2R                    |H3R                    |H4R                    |H5R                    |H6R
          |                       |                       |                       |                       |                       |
          | 2                     | 2                     | 2                     | 2                     | 2                     | 2
          '.  .                   '.  .                   '.  .                   '.  .                   '.  .                   '.  .
            '>| 1                   '>| 1                   '>| 1                   '>| 1                   '>| 1                   '>| 1
MMBT4403WT1G  |-----.   MMBT4403WT1G  |-----.   MMBT4403WT1G  |-----.   MMBT4403WT1G  |-----.   MMBT4403WT1G  |-----.   MMBT4403WT1G  |-----.
            .-|     |               .-|     |               .-|     |               .-|     |               .-|     |               .-|     |
          .'  '     |             .'  '     |             .'  '     |             .'  '     |             .'  '     |             .'  '     |
          | 3       |             | 3       |             | 3       |             | 3       |             | 3       |             | 3       |
          |         |             |         |             |         |             |         |             |         |             |         |
V1 -------)---------o-------------)---------)-------------)---------o-------------)---------)-------------)---------'             |         |
V2 -------)-----------------------)---------o-------------)-----------------------)---------o-------------)-----------------------)---------'
          |                       |                       |                       |                       |                       |
          |H1L                    |H2L                    |H3L                    |H4L                    |H5L                    |H6L
          |                       |                       |                       |                       |                       |
          '-o---------------------)-o---------------------)-o---------------------)-o---------------------)-.                     |
            |   .-----------------o-)---o-----------------)-)---o-----------------)-)---o-----------------)-)---.                 |
            |   |   .---------------)---)---o-------------o-)---)---o-------------)-)---)---o-------------)-)---)---.             |
            |   |   |   .-----------)---)---)---o-----------)---)---)---o---------o-)---)---)---o---------)-)---)---)---.         |
            |   |   |   |   .-------)---)---)---)---o-------)---)---)---)---o-------)---)---)---)---o-----o-)---)---)---)---.     |
            |   |   |   |   |   .---)---)---)---)---)---o---)---)---)---)---)---o---)---)---)---)---)---o---)---)---)---)---)---o-'
            |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
            |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
           --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
           \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ / \ /
           --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- --- ---
           1|  2|  3|  4|  5|  6|  7|  8|  9| 10| 11| 12| 13| 14| 15| 16| 17| 18| 19| 20| 21| 22| 23| 24| 25| 26| 27| 28| 29| 30|
            |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
            '---o---o---o---'   '---o---o---o---'   '---o---o---o---'   '---o---o---o---'   '---o---o---o---'   '---o---o---o---'
                    |                   |                   |                   |                   |                   |
                    |                   |                   |                   |                   |                   |
                   L1                  L2                  L3                  L4                  L5                  L6
```

Here, H1..6 and L1..6 are outputs of an MCP23S17T GPIO expander, and V1/V2 are
LED control voltages generated on the support board. The control scheme is as
follows.

```
.-------..----.----.----.----.----.----..----.----.----.----.----.----..----.----..------.
| LEDs  || H1 | H2 | H3 | H4 | H5 | H6 || L1 | L2 | L3 | L4 | L5 | L6 || V1 | V2 ||  x   |
|-------++----+----+----+----+----+----++----+----+----+----+----+----++----+----++------|
|  1-2  || 1  | 1  | 0  | 0  | 0  | 0  || 0  | Z  | Z  | Z  | Z  | Z  || 1  | 2  ||  0.* |
|  2-3  || 0  | 1  | 1  | 0  | 0  | 0  || 0  | Z  | Z  | Z  | Z  | Z  || 3  | 2  ||  1.* |
|  3-4  || 0  | 1  | 1  | 1  | 0  | 0  || 0  | Z  | Z  | Z  | Z  | Z  || 3  | 4  ||  2.* |
|  4-5  || 0  | 0  | 0  | 1  | 1  | 0  || 0  | Z  | Z  | Z  | Z  | Z  || 5  | 4  ||  3.* |
|  5-6  || 0  | 0  | 0  | 0  | 1  | 1  || 0  | 0  | Z  | Z  | Z  | Z  || 5  | 6  ||  4.* |
|  6-7  || 1  | 0  | 0  | 0  | 0  | 1  || Z  | 0  | Z  | Z  | Z  | Z  || 7  | 6  ||  5.* |
|  7-8  || 1  | 1  | 0  | 0  | 0  | 0  || Z  | 0  | Z  | Z  | Z  | Z  || 7  | 8  ||  6.* |
|  8-9  || 0  | 1  | 1  | 0  | 0  | 0  || Z  | 0  | Z  | Z  | Z  | Z  || 9  | 8  ||  7.* |
|  9-10 || 0  | 1  | 1  | 1  | 0  | 0  || Z  | 0  | Z  | Z  | Z  | Z  || 9  | 10 ||  8.* |
| 10-11 || 0  | 0  | 0  | 1  | 1  | 0  || Z  | 0  | 0  | Z  | Z  | Z  || 11 | 10 ||  9.* |
| 11-12 || 0  | 0  | 0  | 0  | 1  | 1  || Z  | Z  | 0  | Z  | Z  | Z  || 11 | 12 || 10.* |
| 12-13 || 1  | 0  | 0  | 0  | 0  | 1  || Z  | Z  | 0  | Z  | Z  | Z  || 13 | 12 || 11.* |
| 13-14 || 1  | 1  | 0  | 0  | 0  | 0  || Z  | Z  | 0  | Z  | Z  | Z  || 13 | 14 || 12.* |
| 14-15 || 0  | 1  | 1  | 0  | 0  | 0  || Z  | Z  | 0  | Z  | Z  | Z  || 15 | 14 || 13.* |
| 15-16 || 0  | 1  | 1  | 1  | 0  | 0  || Z  | Z  | 0  | 0  | Z  | Z  || 15 | 16 || 14.* |
| 16-17 || 0  | 0  | 0  | 1  | 1  | 0  || Z  | Z  | Z  | 0  | Z  | Z  || 17 | 16 || 15.* |
| 17-18 || 0  | 0  | 0  | 0  | 1  | 1  || Z  | Z  | Z  | 0  | Z  | Z  || 17 | 18 || 16.* |
| 18-19 || 1  | 0  | 0  | 0  | 0  | 1  || Z  | Z  | Z  | 0  | Z  | Z  || 19 | 18 || 17.* |
| 19-20 || 1  | 1  | 0  | 0  | 0  | 0  || Z  | Z  | Z  | 0  | Z  | Z  || 19 | 20 || 18.* |
| 20-21 || 0  | 1  | 1  | 0  | 0  | 0  || Z  | Z  | Z  | 0  | 0  | Z  || 21 | 20 || 19.* |
| 21-22 || 0  | 1  | 1  | 1  | 0  | 0  || Z  | Z  | Z  | Z  | 0  | Z  || 21 | 22 || 20.* |
| 22-23 || 0  | 0  | 0  | 1  | 1  | 0  || Z  | Z  | Z  | Z  | 0  | Z  || 23 | 22 || 21.* |
| 23-24 || 0  | 0  | 0  | 0  | 1  | 1  || Z  | Z  | Z  | Z  | 0  | Z  || 23 | 24 || 22.* |
| 24-25 || 1  | 0  | 0  | 0  | 0  | 1  || Z  | Z  | Z  | Z  | 0  | Z  || 25 | 24 || 23.* |
| 25-26 || 1  | 1  | 0  | 0  | 0  | 0  || Z  | Z  | Z  | Z  | 0  | 0  || 25 | 26 || 24.* |
| 26-27 || 0  | 1  | 1  | 0  | 0  | 0  || Z  | Z  | Z  | Z  | Z  | 0  || 27 | 26 || 25.* |
| 27-28 || 0  | 1  | 1  | 1  | 0  | 0  || Z  | Z  | Z  | Z  | Z  | 0  || 27 | 28 || 26.* |
| 28-29 || 0  | 0  | 0  | 1  | 1  | 0  || Z  | Z  | Z  | Z  | Z  | 0  || 29 | 28 || 27.* |
| 29-30 || 0  | 0  | 0  | 0  | 1  | 1  || Z  | Z  | Z  | Z  | Z  | 0  || 29 | 30 || 28.* |
| 30-1  || 1  | 0  | 0  | 0  | 0  | 1  || 0  | Z  | Z  | Z  | Z  | 0  || 1  | 30 || 29.* |
'-------''----'----'----'----'----'----''----'----'----'----'----'----''----'----''------'
```

That is:

 - Hi = 1 if ⌊x+i⌋ % 6 < 2 else 0
 - Li = 0 if ⌊x/5⌋ == i-1 or ⌊(x+1)/5⌋ == i-1 else Z
 - V1_pwm = x-⌊x⌋ if ⌊x/2⌋ == 1 else 1-x+⌊x⌋
 - V2_pwm = x-⌊x⌋ if ⌊x/2⌋ == 0 else 1-x+⌊x⌋

where x is a real number in [0,30> (or any real modulo 30).

Li could probably be driven high when disabled as well, and Hi could probably
be Z when disabled as well. This configuration is mostly gut feeling; it makes
sure that the base-emitter junction of the transistors always has a defined
voltage, but prevents the LEDs from ever being reverse-biased without at least
another forward-biased LED in the path to drop the voltage. In theory, some
slight ghosting might occur this way if the reverse leakage current is high
enough, but with the engraved panel in front there's no way you'd see that.

Also, yes, 30 LEDs with antialiasing is ridiculously overkill for a gimmick
like the synchroscope. Just wait until you see the 7-segment display drivers.

The current sinked by V1/V2 is approximately constant during normal operation,
because they always drive only one LED. Therefore, they can be driven directly
by a LED control channel with pullup resistor.
