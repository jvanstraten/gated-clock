Microcontroller configuration interface
=======================================

```
              Vcc                                                Vcc
             -----                                              -----
               |                                                  |
               | LTST-C230TBKT                                    | LTST-C230TBKT
             -----      (blue)                                  -----      (blue)
             \   / -->                                          \   / -->
              \ /  -->                                           \ /  -->
             -----                                              -----
               |                                                  |
               |IenR               TE-2328702-4                   |IncR
               |              .--------------------.              |
              .-.             |      FPC-0.5mm     |             .-.
              | | 100R        |                    |             | | 100R
              | |             |  1    2    3    4  |             | |
              '-'             '--------------------'             '-'
               |                 |    |    |    |                 |
      Ien <----o-----------------'    |    |    '-----------------o----> Inc
                                      |    |
                                      |    |
      Isw >----o----------------------'    '----------------------o----> Ren
               |                                                  |
              .-.                                                .-.
              | | 680R                                           | | 100R
              | |                                                | |
              '-'                                                '-'
               |                                                  |
               |IswR                                              |RenR
               |                                                  |
               | 2                                                | LTST-C230TBKT
               '.  .                                            -----      (blue)
                 '>| 1                                           / \  -->
    MMBT4403WT1G   |-----.                                      /   \ -->
                 .-|     |                                      -----        Vcc
               .'  '   -----                                      |         -----
               | 3      Vled                                      |           |
               |                                                  '-----------'
               |IswL
               |
               | LTST-C230
             -----
             \   / -->
              \ /  -->
             -----
               |
               |
             -----
              Gnd
```

The LED for the Isw input is active-high. It lights up when the user pushes the
configuration switch into the momentary increment position. It uses the same
circuit as the gate LEDs, so it should have (roughly) the same, dimmable
brightness.

The blue LEDs for the microcontroller outputs are active-low, as the
microcontroller idles high. These LEDs are intentionally much brighter as the
other LEDs, because it should be clearly visible when the microcontroller is
intervening. The LEDs and resistors also effectively pull the outputs high
(assuming no static load besides CMOS input pin leakage), so the circuit works
entirely without microcontroller connection.

The microcontroller board is connected via a 4-conductor, 0.5mm pitch flat-flex
cable.
