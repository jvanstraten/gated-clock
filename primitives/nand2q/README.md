2-input NAND for Q flipflop output
==================================

```
                           Vcc          Vcc
                          -----        -----
                            |            |
                            |            |
                            |            |
                            |            | 5   SN74LVC1G10DCKR
        ____                |    1 .---------..
A)-----[____]-----o---------+------|A   Vcc    `.
         1k       |         |    3 |             \  _  4   X      ____
                  |         o------|B           Y |(_)-----o-----[____]-----o-----(Y
                  |         |    6 |             /         |      100R      |
B)----------------)---------+------|C   Gnd    ,'         .-.               |
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

This is the same as `nand2`, except the A input is delayed considerably. This
delay serves to solve hold timing constraints. By doing this at the input of
the Q and Qn gates, the delay does not affect rise/fall timing of the output,
or of the clock-low latch this gate is part of (B is the latch feedback input).
