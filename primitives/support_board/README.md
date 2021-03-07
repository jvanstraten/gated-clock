Support PCB
===========

The support PCB is done entirely in Blender with a single primitive. So, this
comprises the entire board. Its tasks are:

 - supply 5V power (4A) from mains with soft-start, proper UVLO/OVLO, and
   monitoring;
 - detect, isolate, and filter the grid frequency as a clock source for the
   discrete clock circuit;
 - drive the LEDs for the 7-segment displays and colons;
 - control LED PWM and voltage for the gate LEDs, flipflop LEDs, two
   synchroscope channels, and the microcontroller status LED;
 - provide support for a GPS module;
 - control everything using a microcontroller (Teensy LC).

Power supply and grid frequency
-------------------------------

### Mains circuitry

The mains circuitry is as follows.

```
   Screw terminals
       .-----.                5x20 T1A                                       class X 100nF
       |  _  |         L    .----------.     Lp                                  . .    Lc    ____   Lt    ____   Lo
 L ====| (-) |--------------|----------|-----o-------------o----------------o----| |-----o---|____|---o---|____|---.
       |  _  |              '----------'     |             |                |    ' '     |    47R     |    470R    |
 N ====| (-) |---------.                     |             | .-------~      |    ____    |            |            | LTV-816
       |  _  |         |                    .-._           '-|L             '---|____|---'            |         .--|-----~
PE ====| (-) |----.    |                    | / 275VAC       |  RAC20           1Meg HV              ---        | ---
       |     |    |    |                   _|/| 430VDC       |  -05SK            0.5W        SMBJ3V3 \ /        | / \ -->
       '-----'    |    |                    '-'            .-|N                                     .---'       | ---
                -----  |                     |             | '-------~                                |         '--|-----~
                 Gnd   |                     |             |                                          |            |
                       '---------------------o-------------o------------------------------------------o------------'
                       N
```

Between the following groups, minimum creepage is 4mm and minimum clearance is
1mm (TODO, verify):

 - L;
 - Lp;
 - Lc, Lt, Lo, and N;
 - everything else.

The 430V varistor and 3V3 transzorb aim to protect the power supply and
optocoupler against spikes when the clock is plugged in. The fuse prevents a
failed-short varistor or safety capacitor from burning the house down. The
power supply has its own fuse built in, but that one's next to impossible to
get to. The 1Meg resistor acts as a bleed resistor for the 100nF capacitor,
draining it to ~30V within about 260ms.

Depending on input voltage and to some extent frequency (designed for
100-250VAC, 50-60Hz), the current through the capacitive dropper will peak at
somewhere between 3mA and 8mA.

The PE connection is kind of optional, since the clock does not have any
exposed metal that doesn't float. I'd always recommend connecting it anyway,
however. Especially while testing it's good not to blow everything up when you
touch something (non-live), regardless of whether it electrocutes you or not.

### Power supply

The main component of the power supply is an off-the-shelf module, the Recom
[RAC20-05SK](https://recom-power.com/pdf/Powerline_AC-DC/RAC20-K.pdf). This
module takes 85-264VAC at its input to provide an isolated 5V at 4A. It seemed
like a safe idea to me to use a module rather than to try to design a live SMPS
myself, especially for something that will be on for long periods of time.

To be safe, however, the module isn't directly connected to the power rail: it
goes through a [TPS26631](https://www.ti.com/lit/ds/symlink/tps2663.pdf)
hot-swap controller that provides undervoltage, overvoltage, and overcurrent
protection, soft-starts the power supply to prevent excessive capacitor inrush
current, and has a current monitor output that's tied to an ADC of the
microcontroller. Furthermore, the output of the module is kind of noisy, so
we'll add an LC filter.

```
                                                _ _ R_ser
                                   . - - - - - . _ _'- - - - - .
                                   .                31mΩ       .                                   Vcc
                                   .         TPS26631          .                                  -----
~------.    I                 L    .   .-------------------.   .                                    |
    V+ |---------^^^^^--------o--------| In            Out |-------o------------------------o-------o-------------o---------------------------o----------.
       |         100nH        |   1,2,3| ____              |18,    |                        |       |             |             '             |          |
       |         15mΩ         |     X--| Shdn              |19,   .-.                       |       | +           | +           '             |          |
 RAC20 |                      |      13|                   |20    | | 16k9                -----   -----         -----         - - - C_load    |        ----- 100nF
 -05SK |           .----------o--------| In_sys            |      | |                10uF -----    .-.  100uF    .-.  100uF   - - - ~340uF    |        -----
       |           |          |       6|                   |      '-'                       |     ' | `         ' | `           .             |          |
       |   100nF -----       .-.    X--| B_gate            |       |     ____      ____     |       |             |             .             |          |
    V- |--.      -----  16k9 | |      4|              Pgth |-------o----|____|----|____|----o-------o-------------o---------------------------)----------'
~------'  |        |         | |    X--| Drv               |16   Pgth    680  Pgl  5k11             |                                         |
          |        |         '-'      5|                   |                                        |                              .----------)----------.
          |        |          |        |                   |                                        |                              |          |          |
          |        |     UVLO o--------| UVLO              |                                        |                              |  4 .-._  | 5        |
          |        |          |       7|             Pgood |-------> Pgood                          |                              '----| - `-._         |
          |        |         .-.       |               ___ |17                                      |                                   |       `-._  1  |     ____
          |        |    1k27 | |       |               Flt |--X                                     |                                   | MCP6#01  _:----o----|____|----o----> Imon
          |        |         | |       |                   |15                        Imon.I        |                                 3 |      _.-'   Imon.B    1k      |
          |        |         '-'       |              Imon |-----------------------------o----------)-----------------------------------| +_.-'                         |
          |        |          |        |                   |14                           |          |                                   '-'   | 2                       |
          |        |      OVP o--------| OVP          Ilim |------------------.          |          |                                         |                         |
          |        |          |       8|                   |11         Ilim   |          |          |                                         |                       ----- 1uF
          |        |         .-.       |             dV/dT |-------.         .-.        .-.         |                                         |                       -----
          |        |    5k11 | |       |                   |10 dVdT| 100nF   | |        | |         |                                         |                         |
          |        |         | |    X--| Mode   Gnd        |     -----       | | 5k11   | | 16k9    |                                         |                         |
          |        |         '-'     12'-------------------'     -----       '-'        '-'         |                                         |                         |
          |        |          |                  |9,EP             |          |          |          |                                         |                         |
        -----    -----      -----              -----             -----      -----      -----      -----                                     -----                     -----
         Gnd      Gnd        Gnd                Gnd               Gnd        Gnd        Gnd        Gnd                                       Gnd                       Gnd
```

The LED controllers draw quite a bit of quiescent current. While the total
current drawn is still less than the maximum that the Teensy board can provide,
it's cutting it close. Therefore, a dedicated 3.3V LDO was added.

```
      Vcc                   3V3
     -----                 -----
       |    .-----------.    |
       o----| In    Out |----o
       |    | BD33FC0FP |    |
       |    |    Gnd    |    |
10uF -----  '-----------'  ----- 10uF
     -----       |         -----
       |         |           |
       |         |           |
     -----     -----       -----
      Gnd       Gnd         Gnd
```

This regulator is overkill; it should supply about 90mA, and can do 1A. The
footprint should be large enough that it shouldn't get too warm.

#### Noise filter

The LC filter is formed by the 100nH inductor, its 15mΩ series resistance,
the 31mΩ equivalent series resistance of the TPS26631's internal FET, the
electrolytic 100uF bulk capacitor, and the ~350uF total capacitive load on
the Vcc rail due to the decoupling capacitors all over the place. This gives
a cutoff frequency of 23.7kHz and a damping ratio of ~1.51.

#### Voltage-based protection

The UVLO, OVP, and Pgth thresholds in the TPS26631 are 1.2V rising, 1.12V
falling. With the selected resistors, this puts the trigger points at:

 - turn on above 4.38V, below 5.00V;
 - power good above 4.71V;
 - power bad below 4.30V;
 - turn off below 4.00V, above 5.47V.

The system may or may not recover from overvoltage, because the 5V happens to
end up at exactly the nominal voltage. However, it shouldn't need to, because
overvoltage should never happen in the first place. The power good signal is
just an I/O signal for the microcontroller, informing it that it should
probably reset everything if it's been low. The microcontroller's internal
pullup will be used.

Note that the resistor values were chosen to limit unique part count, with
minor sacrifices in the trip points. Hence also the usage of 680R and 5k11 in
series; both were already used elsewhere, but the desired resistance value
was not.

#### Current-based protection and monitoring

The 5k11 resistor programs the current limit of the TPS26631 to 3.52A. The
devices allows momentary overcurrent of 2x the set current (so 7.04A) for up
to 25ms, after which it will limit current at the set current for 162ms more.
When that timer expires, it will latch off until a power cycle. At 3x the set
current (10.56A), the device will ignore the timers, and latch off within
3.2us. Finally, at 45A or more, it will latch off within 1us.

The microcontroller can get a reading of the total current draw through the
Imon signal. At 3V3 ADC full scale, the current will be around 7A. The
datasheet mentions vaguely that the Imon signal should not have a capacitor,
but doesn't mention if this is because it prevents the frequency response of
the monitoring signal (duh, that's the point), or if it affects internal
behavior. Therefore, to be safe, it's buffered by an opamp before it's
filtered. The microcontroller wants at most 5k source impedance anyway.

### Grid frequency filter

The following circuit is used to filter and amplify the grid frequency signal
from the optocoupler.

```
        3V3                     3V3        3V3                                                      Vcc
       -----                   -----      -----                                                    -----
         |                       |          |   100nF                                                |   100nF
        .-.                     .-.         |    . .                                                 |    . .
        | | 10k                 | | 10k     o----| |----.                                            o----| |----.
        | |                     | |         |    ' '    |                                            |    ' '    |
        '-'                     '-'         |         -----                                74LV1T125 |         -----
         |    ____    F1         |  4 .-._  | 5        Gnd                                     .-._  | 5        Gnd
       I o---|____|---o----------)----| - `-._                                                 |   `-._
         |    100k    |          |    |       `-._  1     F2    ____   F3    ____    O       2 |       `-._  4  ____
         |            |          |    | MCP6#01  _:--------o---|____|---o---|____|---o---------|A        Y_:---|____|---o---> f50hz
 LTV-816 |            |          |  3 |      _.-'          |    100R    |     10k    |       1 |__    _.-'   B  100R    |
~--------|--.         |        H o----| +_.-'              |            |            |      .--|OE_.-'                  |
     .  .'  |         |          |    '-'   | 2    ____    |            |            |      |  '-'   | 3                |
     |-'    |       ----- 100n   o----------)-----|____|---'    100nF -----      Readout/   |        |                ----- 330pF
 --> |      |       -----        |          |      16k9               -----      override   |        |                -----
     |>.    |         |         .-.         |                           |                   |        |                  |
     '  '.  |         |         | | 10k     |                           |                   |        |                  |
~--------|--'         |         | |         |                           |                   |        |                  |
         |            |         '-'         |                           |                   |        |                  |
         |            |          |          |                           |                   |        |                  |
       -----        -----      -----      -----                       -----               -----    -----              -----
        Gnd          Gnd        Gnd        Gnd                         Gnd                 Gnd      Gnd                Gnd
```

The circuit uses the 3V3 rail because it should be less noisy than Vcc, and to
prevent complexity for the readout & override signal to/from the
microcontroller.

The first RC filter stage combined with the Schmitt-trigger configuration of
the opamp should get rid of essentially all transients, and the second RC
filter should get rid of any remaining noise. The resulting signal can be
read by the microcontroller using the readout/override GPIO signal; the 10k
resistor limits current in case it wants to override. What follows is a basic
level shifter to 5V, with a slew-rate limiter similar to those used for the
NAND gates.

LED controllers
---------------

LED brightness and color control is managed by three excessively overpowered
[TLC6C5748QDCARQ1](https://www.ti.com/lit/ds/symlink/tlc6c5748-q1.pdf) LED
controllers. In a nutshell, each of these has 3x16 channels with independent
16-bit enhanced-spectrum PWM output, using a current sink with configurable
current (the product of 3x3-bit max current selection from 3.2mA to 31.9mA,
3x7-bit @ 10-100% per color group, and 48x7-bit @ ~26-100% per channel), with
stuck-at-high and stuck-at-low fault detection per channel.

Most of the 3x48 channels are used for the RGB LEDs of the 7-segment display;
it has 46 RGB LEDs, to be specific. The 47th channel is used for the
microcontroller status LED on the mainboard. Finally, the 48th channel controls
LED brightness of the synchrometer (current only), the gate LEDs
(current + PWM), and the flipflop LEDs (current + PWM) with its red, green, and
blue channels. This means that the color group dimming feature can't really be
used, but the current can still be set between 26% and 100% of the maximum
current.

The design point for the maximum current is 8.0mA (configuration 0b001): 6mA
for just the red color channel was found to be enough to read the display in
sunlight. Thus, the LED current can be configured between about 2mA and 8mA.
The rest is done via the also rather overkill 16-bit PWM.

### 7-segment display channel circuit

The regular 7-segment display LEDs are driven as follows. This circuit is
instanced 6 x 7 = 42 times.

```
               Vcc     Vcc          Vcc
              -----   -----        -----
                |       |            |
               .-.      |            |
      header   | | 100k |            |
         |     | |      |            |
         v     '-'      |            | 5   SN74LVC1G10DCKR
 _______        |       |    1 .---------..
 Segment )------o-------)------|A   Vcc    `.
________                |    3 |             \  _  4   A
Override ---------------)------|B           Y |(_)-----.
                        |    6 |             /         |
                        o------|C   Gnd    ,'          |
                        |      '---------''            | ASMB-KTF0-0A306
                        |            | 2        - - - -|- - - -
                        |            |         :   .---o---.   :
                        |            |         :   |   |   |   :
                        |            |         :  --- --- ---  :
                      ----- 100nF    |         :  \R/ \G/ \B/  :
                      -----          |         :  --- --- ---  :
                        |            |         :   |   |   |   :
                        |            |          - -|- -|- -|- -
                        |            |             |   |   |
                        |            |             |R  |G  |B
                        |            |             |   |   |
                      -----        -----        ---------------
                       Gnd          Gnd          1 RGB channel
                                                  (TLC6C5748)
```

The segment is thus controlled directly by the (active-low) signal from the
discrete circuit without microcontroller involvement, as long as override (an
output from the microcontroller) is inactive (high). When override is activated
however, all high-side segment drivers are on, regardless of the state of the
discrete circuit. The LEDs can then be individually controlled by the
microcontroller using the TLC6C5748.

The SN74LVC1G10DCKR can source up to 32mA (recommended) at 5V. As long as the
maximum current is configured correctly, at maximum brightness this current
would be 24mA, so that's fine.

This circuit should also allow the microcontroller to read out the state of the
segment signal, as long as override is inactive and at least one RGB channel
is on at the 33rd GSCLK cycle. This state is reflected in the LED open
detection flags.

The pullup resistor on the segment line ensures that the segment is off when
the support board is not connected to the mainboard, allowing it to be tested
independently.

Some segments share a single control line (ADn for seconds and minutes tens,
ADEGn for hours tens). For these segments, only one pullup resistor exists, but
the rest of the circuit is repeated. "Logically" speaking the NAND gates could
be "optimized away" because they perform the same logic function, but
electrically this would put too much load on them in the worst case.

### Colon LED circuit

The four colon dots are driven as follows.

```
              Vcc          Vcc
             -----        -----
               |            |
               |            |
               |            |
               |            |
               |      .-._  | 5  SN74LVC1G17DCKR
               |      |   `-._
________       |    2 |     __`-._  4     A
Override )-----)------|   _||    _:-----------.
               |      |      _.-'             |
               |      |  _.-'                 |
               |      '-'   | 3               | MB-KTF0-0A306
               |            |          - - - -|- - - -
               |            |         :   .---o---.   :
               |            |         :   |   |   |   :
               |            |         :  --- --- ---  :
             ----- 100nF    |         :  \R/ \G/ \B/  :
             -----          |         :  --- --- ---  :
               |            |         :   |   |   |   :
               |            |          - -|- -|- -|- -
               |            |             |   |   |
               |            |             |R  |G  |B
               |            |             |   |   |
             -----        -----        ---------------
              Gnd          Gnd          1 RGB channel
                                         (TLC6C5748)
```

This means that they are hardwired to always be on when the clock circuit is
in control of the display, and always off when the microcontroller is in
control. Off course the microcontroller can always turn individual segments
*off*, but it can't turn them on without also turning the colons off.
Basically, this is a hardwired anti-cheating measure.

### Microcontroller status LED circuit

The microcontroller status LED is driven trivially.

```
       Vcc
      -----
        |
        ~   <-- header
        |
        |
        | MB-KTF0-0A306
 - - - -|- - - -
:   .---o---.   :
:   |   |   |   :
:  --- --- ---  :
:  \R/ \G/ \B/  :
:  --- --- ---  :
:   |   |   |   :
 - -|- -|- -|- -
    |   |   |
    ~   ~   ~   <-- header
    |   |   |
    |R  |G  |B
    |   |   |
 ---------------
  1 RGB channel
   (TLC6C5748)
```

### Gate and flipflop LED drive voltage circuits

The control voltage for the gate and flipflop LEDs is generated as follows.

```
       Vcc              Vcc                                Vcc
      -----            -----                              -----
        |                |                                  |
        |                |     . .                          |
        |                o-----| |------.                  .-.
        |                |     ' '      |                  | | 10k
        |                |    100nF   -----                | |
       .-.               |             Gnd                 '-'
  470R | |               |                                  |
       | |               |          F         ____          |
       '-'    .----------)--------------o----|____|---------o-----( Vled
        |     |          |              |     10k           |
        |     |  4 .-._  | 5    100nF -----               2 |
        |     '----| - `-._           -----             .  .'
        |          |       `-._  1  O   |     ____    1 |<'
        |          | MCP6#01  _:--------o----|____|-----|   MMBT4403WT1G
        |   A    3 |      _.-'                 1k    C  |-.
        o----------| +_.-'                              '  '.
        |          '-'   | 2                              3 |R
        |                |                                  |
 ---------------         |       # = 0 or L                .-.
 1 color channel         |                                 | | 100R
   (TLC6C5748)           |                                 | |
                         |                                 '-'
                         |                                  |
                         |                                  |
                       -----                              -----
                        Gnd                                Gnd
```

The current from the TLC6C5748 channel is converted to a voltage by the 470R
resistor, varying between about 1.2V and 4.1V when the channel is on based on
the dot correction value, and 5V when the channel is off. The remainder of
the circuit simply serves to mirror this voltage at Vled, regardless of the
amount of current drawn from it. The transistor is in a voltage follower
configuration, with the base and collector resistors only serving to limit
currents in fault conditions, and the 10k resistor only serving to define the
Vled voltage when the mainboard is not connected. The MCP6001 combined with
the 10k/100nF RC circuit serves to calibrate the Vbe voltage drop of the
transistor out; this voltage drop depends somewhat on the amount of current
drawn otherwise, which in turn would depend on the amount of LEDs that are
on. The RC circuit serves mostly to ensure stability of the opamp. It's
entirely possible that the circuit will work just fine in practice without
any of the 100R/1k/10k resistors or the 100nF capacitor in the filter, in
which case they can just be omitted/bridged.

### Synchroscope drive voltage circuits

Because only one (color) channel remains, while we need two synchroscope
control voltages, some shenanigans are needed here.

```
                     Vcc                Vcc           Vcc                Vcc
                    -----              -----         -----              -----
                      |                  |             |                  |
                      |                  |             |                  |
                     .-.                .-.           .-.                .-.
                     | | 10k            | | 10k       | | 10k            | | 10k
                     | |                | |           | |                | |
                     '-'                '-'           '-'                '-'
                      |                  |             |                  |          _
                      |                  |             o------------------)-----( V1  \_ Output
     PWM A @ 5V ------o A                o-------------)------------------)-----( V2 _/  voltages
 (microcontroller)    |                  |             |                  |
                      |                2 |             | 2                |
                      |              .  .'             '.  .              |
      Vcc             |    ____    1 |<'                 '>| 1    ____    |
     -----            '---|____|-----|   2x MMBT4403WT1G   |-----|____|---o------ PWM B @ 5V
       |                   100k   AR |-.                 .-| BR   100k         (microcontroller)
       |                             '  '.             .'  '
      .-.                              3 |             | 3
 470R | |                                '------o------'
      | |                                       |M
      '-'                                     2 |
       |                                    .  .'
       |   C                              1 |<'
       o------------------------------------|   MMBT4403WT1G
       |                                    |-.
       |                                    '  '.
---------------                               3 |R
1 color channel                                 |
  (TLC6C5748)                                  .-.
                                               | | 100R
                                               | |
                                               '-'
                                                |
                                                |
                                              -----
                                               Gnd
```

The intended mode of operation is that the TLC6C5748 output is always on; it is
only used as a current-mode DAC. As in the Vled circuit, a 470R resistor is
used to convert it to a voltage between 1.2V and 4.1V. The bottom transistor
mirrors this voltage at the M net, with a 100R series resistor for protection.
The remaining two transistors are configured as switches controlled by the
microcontroller; they allow the microcontroller to PWM the two channels
individually. The 10k pullup resistors only serve to define the output voltages
when the mainboard is not connected.

Note that an opamp isn't necessary for the synchrometer, because during normal
operation, there is always only one LED on per channel. Therefore, the current
sourced by V1 and V2 is approximately constant for a given voltage.

### GSCLK and other support circuitry

The three LED controllers are connected as follows.

```
                          3V3       Vcc                            3V3       Vcc                            3V3       Vcc
                         -----     -----                          -----     -----                          -----     -----
                           |         |                              |         |                              |         |
                           |         |                              |         |                              |         |
                           |       ----- 10uF                       |       ----- 10uF                       |       ----- 10uF
                           |       -----                            |       -----                            |       -----
                           |         |                              |         |                              |         |
             .       . .   |   . .   |   .            .       . .   |   . .   |   .            .       . .   |   . .   |   .
         Gnd |---o---| |---o---| |---o---| Gnd    Gnd |---o---| |---o---| |---o---| Gnd    Gnd |---o---| |---o---| |---o---| Gnd
             '   |   ' '   |   ' '   |   '            '   |   ' '   |   ' '   |   '            '   |   ' '   |   ' '   |   '
                 |  100nF  |  100nF  |                    |  100nF  |  100nF  |                    |  100nF  |  100nF  |
                 |29       |54       |56                  |29       |54       |56                  |29       |54       |56
              .-------------------------.              .-------------------------.              .-------------------------.
              | Gnd       Vcc       Gnd |              | Gnd       Vcc       Gnd |              | Gnd       Vcc       Gnd |
            1 |                         | 28         1 |                         | 28         1 |                         | 28
         .----| SIN    TLC6C5748   SOUT |--------------| SIN    TLC6C5748   SOUT |--------------| SIN    TLC6C5748   SOUT |-----.
         |    |                         |     SIO1     |                         |     SIO2     |                         |     |
         |    | SCLK      LAT     GSCLK |              | SCLK      LAT     GSCLK |              | SCLK      LAT     GSCLK |     |
         |    '-------------------------'              '-------------------------'              '-------------------------'     |
 SIN ----'        |2       |3       |55                    |2       |3       |55                    |2       |3       |55       |
SCLK -------------o--------)--------)----------------------o--------)--------)----------------------'        |        |         |
 LAT ----------------------o--------)-------------------------------o--------)-------------------------------'        |         |
SOUT -------------------------------)----------------------------------------)----------------------------------------)---------'
                                    |                                        |                                        |
             3V3         Hours      |                            Minutes     |                            Seconds     |
            -----                   |                                        |                                        |
              |                     |                                        |                                        |
              o-----------.         |                                        |                                        |
              |           |         |                                        |                                        |
        100nF |       .-------.     |                                        |                                        |
            -----     | 32MHz |-----o----------------------------------------o----------------------------------------'
            -----     '-------' ECS-3225MV-320-BN-TR
              |           |
              o-----------'
              |
            -----
             Gnd
```

Note that they run on 3V3 rather than the standard Vcc (5V). The current sinks
can handle voltages up to 10V regardless of supply voltage, so this is fine. It
saves a few level shifters for the microcontroller and allows a standard
oscillator to be used.

### Connection table

First TLC6C5748 in daisy chain:

 - OUTx0: hours, tens, segment F
 - OUTx1: hours, tens, segment A
 - OUTx2: hours, units, segment A
 - OUTx3: hours, units, segment B
 - OUTx4: hours, tens, segment G
 - OUTx5: hours, tens, segment B
 - OUTx6: hours, units, segment F
 - OUTx7: hours, units, segment G
 - OUTx8: hours, tens, segment E
 - OUTx9: hours, tens, segment D
 - OUTx10: hours, units, segment D
 - OUTx11: hours, units, segment C
 - OUTx12: hours, tens, segment C
 - OUTx13: colon between minutes and hours, upper segment
 - OUTx14: colon between minutes and hours, lower segment
 - OUTx15: hours, units, segment E

Second TLC6C5748 in daisy chain:

 - OUTx0: minutes, tens, segment F
 - OUTx1: minutes, tens, segment A
 - OUTx2: minutes, units, segment A
 - OUTx3: minutes, units, segment B
 - OUTx4: minutes, tens, segment G
 - OUTx5: minutes, tens, segment B
 - OUTx6: minutes, units, segment F
 - OUTx7: minutes, units, segment G
 - OUTx8: minutes, tens, segment E
 - OUTx9: minutes, tens, segment D
 - OUTx10: minutes, units, segment D
 - OUTx11: minutes, units, segment C
 - OUTx12: minutes, tens, segment C
 - OUTR13: brightness control for flipflop status LEDs
 - OUTB13: brightness control for gate status LEDs
 - OUTG13: brightness control for synchroscope LEDs (analog only, PWM done by
   microcontroller)
 - OUTx14: microcontroller status LED
 - OUTx15: minutes, units, segment E

Third TLC6C5748 in daisy chain:

 - OUTx0: seconds, tens, segment F
 - OUTx1: seconds, tens, segment A
 - OUTx2: seconds, units, segment A
 - OUTx3: seconds, units, segment B
 - OUTx4: seconds, tens, segment G
 - OUTx5: seconds, tens, segment B
 - OUTx6: seconds, units, segment F
 - OUTx7: seconds, units, segment G
 - OUTx8: seconds, tens, segment E
 - OUTx9: seconds, tens, segment D
 - OUTx10: seconds, units, segment D
 - OUTx11: seconds, units, segment C
 - OUTx12: seconds, tens, segment C
 - OUTx13: colon between seconds and minutes, upper segment
 - OUTx14: colon between seconds and minutes, lower segment
 - OUTx15: seconds, units, segment E

Microcontroller and GPS
-----------------------

The clock is controlled using a [Teensy LC](https://www.pjrc.com/teensy/teensyLC.html)
microcontroller board. This is a little more expensive than just using a
discrete microcontroller, but the builtin USB programming circuitry makes it
vastly more user-friendly.

The Teensy LC is powered by 5V, but internally converts this down to 3.3V, and
its pins are not 5V-tolerant. Therefore, signals going to and coming from the
5V clock circuitry need to be translated up and down. This is done using
74LV1T125s, with the /OE pin tied to Gnd. The Teensy's VUSB trace is to be cut,
so it will operate from the local 5V rail rather than USB power. The circuitry
is otherwise trivial.

GPS connectivity is also achieved with a daughterboard. The connector uses the
pinout of an ATGM336H: 5V, Gnd, TX, RX, PPS. Similar to the Teensy, this board
has its own 3V3 LDO that the I/Os are referenced to. Therefore, no level
shifters are included here.

The Teensy's pinout is as follows.

 - Arduino 0, used as MOSI1: display data input (`disp.SIN`)
 - Arduino 1, used as MISO1: display fault data output (`disp.SOUT`)
 - Arduino 2: minutes configuration increment switch readout (`mcfg.Isw.L`)
 - Arduino 3, usable as PWM or input capture for FTM2: 50/60Hz readback &
   override (`f50hz.O`)
 - Arduino 4, usable as input capture for FTM2: PPS signal from the GPS
   (`gps.PPS`)
 - Arduino 5: minutes configuration increment switch enable (`mcfg.Ien.L`)
 - Arduino 6, possibly used as CS1: display data latch control (`disp.LAT`)
 - Arduino 7, RX3: GPS data input (`gps.G2U`)
 - Arduino 8, TX3: GPS configuration output (`gps.U2G`)
 - Arduino 9: automatic configuration, increment minutes (`mcfg.Inc.L`)
 - Arduino 10, possibly used as CS0: mainboard I/O expander chip select
   (`uc.CS.L`)
 - Arduino 11, used as MOSI0: mainboard I/O expander write data (`uc.MOSI.L`)
 - Arduino 12: used as MISO0: mainboard I/O expander read data (`uc.MISO.L`)
 - Arduino 13 (LED): display override (non-inverted, `override.L`)
 - Arduino 14, used as SCK0: mainboard I/O expander clock (`uc.SCK.L`)
 - Arduino 15: mainboard I/O expander interrupt request (`uc.IRQ.L`)
 - Arduino 16, used as FTM1 PWM: synchroscope PWM channel B (`sync.BL`)
 - Arduino 17, used as FTM1 PWM: synchroscope PWM channel A (`sync.AL`)
 - Arduino 18, automatic configuration, increment hours (`hcfg.Inc.L`)
 - Arduino 19, hours configuration increment switch readout (`hcfg.Isw.L`)
 - Arduino 20, used as SCK1: display clock (`disp.SIN`)
 - Arduino 21: hours configuration increment switch enable (`mcfg.Ien.L`)
 - Arduino 22, used as analog 8: current monitor ADC (`pwr.Imon`)
 - Arduino 23: power good input, GPIO pullup needed (`pwr.Pgood`)
 - Arduino 26: automatic configuration, enable (`cfg.Ren.L`)
