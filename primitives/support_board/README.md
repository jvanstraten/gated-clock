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

### Power entry

TODO: terminal block, fuse

### Power supply

The main component of the power supply is an off-the-shelf module, the Recom
[RAC20-05SK](https://recom-power.com/pdf/Powerline_AC-DC/RAC20-K.pdf). This
module takes 85-264VAC at its input to provide an isolated 5V at 4A.

To be safe, however, the module isn't directly connected to the power rail: it
first goes through a [TPS26631PWPR](https://www.ti.com/lit/ds/symlink/tps2663.pdf)
hot-swap controller that provides undervoltage, overvoltage, and overcurrent
protection, soft-starts the power supply to prevent excessive capacitor inrush
current, and has a current monitor output that's tied to an ADC of the
microcontroller.

TODO circuit

### Grid frequency monitor

TODO

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
