1-input NAND (so, an inverter)
==============================

```
      Vcc          Vcc
     -----        -----
       |            |
       |            |
       |            |
       |            | 5   SN74LVS1G10DCKR
       |    1 .---------..
A)-----+------|A   Vcc    `.
       |    3 |             \  _  4   X      ____
       o------|B           Y |(_)-----o-----[____]-----(Y
       |    6 |             /         |      47R
B)-----+------|C   Gnd    ,'         .-.
       |      '---------''           | | 680R
       |            | 2              | |
       |            |                '-'
       |            |                 |
       |            |                 |
       |            |                 |R
       |            |                 |
       |            |                 | 2
       |            |                 '.  .
       |            |                   '>| 1
     ----- 100nF    |      MMBT4403WT1G   |-----.
     -----          |                   .-|     |
       |            |                 .'  '   -----
       |            |                 | 3      Vled
       |            |                 |
       |            |                 |L
       |            |                 |
       |            |                 | LTST-C230
       |            |               -----
       |            |               \   / -->
       |            |                \ /  -->
       |            |               -----
       |            |                 |
       |            |                 |
     -----        -----             -----
      Gnd          Gnd               Gnd
```

Vcc to Gnd design voltage is 5V.

All gates use the 74LVS1G10 triple-input NAND gate for simplicity; the unused
inputs are simply tied to Vcc.

The 47R series resistance is an extreme-prejudice precaution against ringing.
LTspice shows that it's probably not an issue at these slew rates and trace
lengths, but whatever. Better safe than sorry.

The LED circuit is such that the LEDs can be dimmed both via PWM and to some
degree via DAC. For Vled > Vf, the LED current will be approximately
(Vcc - Vled - 0.6) / 680R, giving a range of about 0 to 3mA theoretically for
red/orange/amber LEDs. The range is lower for green/blue/white due to the
higher forward voltage of those LEDs. However, the matching of the Vbe voltage
of the transistors determines how dim the LEDs can be made this way; at some
point some LEDs will be fully off while others are still on. Note that Vled
should not be brought below LED Vf, or the LED will start dimming again as the
current through the 680R resistor starts flowing through the base instead of
the collector. This shouldn't be immediately damaging, but wastes power.

For further dimming, PWM between Vcc (off) and the DAC voltage can be used.
If the transistor matching is so poor that analog dimming is unfeasible, then
pure-PWM dimming is of course an option.

3mA is expected to be enough; LEDs are way too bright usually. But the 680R
resistor can just be changed to a different value.

The 100nF capacitor effectively decouples both the gate and the LED PWM
circuit.

The 74LVS1G10 and MMBT4403 both use SC-70 footprint (a.k.a. DCK for Texas
Instruments). The capacitor and resistors are 0603. The LED is a through-PCB
mounted 1206.

Propagation delay should be somewhere between 1ns and 15ns. This is modeled in
the VHDL entity.

Total footprint of the circuit is about 9x5mm. The gate symbol itself is 8x5.