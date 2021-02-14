User configuration interface
============================

```
                         Vcc                            Vcc              Vcc
                        -----                          -----            -----
                          |                              |                |
                          |                              |                |
                         .-.                             |                |
                         | | 22k                         |                |
                         | |                             |                |
                         '-'                             |                | 5   SN74LVS1G10DCKR
                          |      ____                    |        1 .---------..
                    .-----o-----[____]-----o-------------)---o------|A   Vcc    `.
                    |    RunS    22k       |     RunC    |   |    3 |             \  _  4
     Run            |                      |             |   '------|B           Y |(_)----- Run
 (retaining)        |                      |             |        6 |             /
                    |                      |             o----------|C   Gnd    ,'
     :'''''''': 1   |                      |             |          '---------''
     :    <---------'                      |             |                | 2
  ^  '   .    : 2                          |             |                |
  |    .-|<---------o----------.         ----- 1uF     ----- 100nF        |
.------| '    :     |          |         -----         -----              |
|      |  <-. :     |          |           |             |                |
'------| .  | : 3   |          |           |             |                |
  |    '-|<-o-------'          |           |             |                |
  v  .   '    : 4            -----       -----         -----            -----
     :    <---------.         Gnd         Gnd           Gnd              Gnd
     :........:     |
                    |
  Increment         |
 (momentary)        |    Vcc                            Vcc              Vcc
                    |   -----                          -----            -----
JSM07011SAQNL       |     |                              |                |
   switch           |     |                              |                |
                    |    .-.                             |                |
                    |    | | 22k                         |                |
                    |    | |                             |                |
                    |    '-'                             |                | 5   SN74LVS1G10DCKR
                    |     |      ____                    |        1 .---------..
                    '-----o-----[____]-----o-------------)---o------|A   Vcc    `.
                         IncS    22k       |     IncC    |   |    3 |             \  _  4
                                           |             |   '------|B           Y |(_)----- Inc
                                           |             |        6 |             /
                                           |             o----------|C   Gnd    ,'
                                           |             |          '---------''
                                           |             |                | 2
                                           |             |                |
                                         ----- 1uF     ----- 100nF        |
                                         -----         -----              |
                                           |             |                |
                                           |             |                |
                                           |             |                |
                                         -----         -----            -----
                                          Gnd           Gnd              Gnd
```

This is just a 3-way switch with a debouncing circuit for either position,
using the Schmitt-trigger inputs of the 74LVC1G10 NAND gates. The final output
is active high. Assertion latency is ~15ms, release latency is ~30ms.
