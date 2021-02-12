3-input NAND for Qn flipflop output
===================================

```
                           Vcc          Vcc
                          -----        -----
                            |            |
                            |            |
                            |            |
                            |            | 5   SN74LVS1G10DCKR
                            |    1 .---------..
A)--------------------------+------|A   Vcc    `.
        ____                |    3 |             \  _  4   X      ____
B)-----[____]-----o---------+------|B           Y |(_)-----o-----[____]-----o-----(Y
         1k       |         |    6 |             /         |      100R      |
C)----------------)---------+------|C   Gnd    ,'         .-.               |
                  |         |      '---------''           | | 680R        ----- 330pF
                  |         |            | 2              | |             -----
                  |         |            |                '-'               |
                  |         |            |                 |                |
                  |         |            |                 |              -----
                  |         |            |                 |R              Gnd
                  |         |            |                 |
                  |         |            |                 | 2
                  |         |            |                 '.  .
                  |         |            |                   '>| 1
         2200pF -----     ----- 100nF    |      MMBT4403WT1G   |-----.
                -----     -----          |                   .-|     |
                  |         |            |                 .'  '   -----
                  |         |            |                 | 3      Vled
                  |         |            |                 |
                  |         |            |                 |L
                  |         |            |                 |
                  |         |            |                 | LTST-C230
                  |         |            |               -----
                  |         |            |               \   / -->
                  |         |            |                \ /  -->
                  |         |            |               -----
                  |         |            |                 |
                  |         |            |                 |
                -----     -----        -----             -----
                 Gnd       Gnd          Gnd               Gnd
```

This is the same as `nand3`, except the B input is delayed considerably. This
delay serves to solve hold timing constraints. By doing this at the input of
the Q and Qn gates, the delay does not affect rise/fall timing of the output,
or of the clock-low latch this gate is part of (A is the latch feedback input,
C is the reset input).
