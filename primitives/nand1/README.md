1-input NAND (so, an inverter)
==============================

```
      Vcc          Vcc
     -----        -----
       |            |
       |            |
       |            |
       |            | 5   SN74LVC1G10DCKR
       |    1 .---------..
A)-----+------|A   Vcc    `.
       |    3 |             \  _  4   X      ____
       o------|B           Y |(_)-----o-----[____]-----o-----(Y
       |    6 |             /         |      100R      |
       o------|C   Gnd    ,'         .-.               |
       |      '---------''           | | 680R        ----- 330pF
       |            | 2              | |             -----
       |            |                '-'               |
       |            |                 |                |
       |            |                 |              -----
       |            |                 |R              Gnd
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

All gates use the 74LVC1G10 triple-input NAND gate for simplicity; the unused
inputs are simply tied to Vcc.

The 100R/330pF RC circuit should effectively reduce ringing due to long traces
to zero, and also serves to control the propagation time of the gate, as
opposed to this varying wildly based on routing and fanout. Specifically, the
propagation time is at least 13ns and at most (roughly) 80ns. This is based on
process corners for the source and sink gate, 1% resistor tolerance, 10%
capacitor tolerance, and capacitive loading of up to 30cm of PCB trace and 10
gate inputs.

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

The 74LVC1G10 and MMBT4403 both use SC-70 footprint (a.k.a. DCK for Texas
Instruments). The capacitor and resistors are 0603. The LED is a through-PCB
mounted 1206.

Propagation delay should be somewhere between 1ns and 15ns. This is modeled in
the VHDL entity.

Total footprint of the circuit is about 9x5mm. The gate symbol itself is 8x5.
