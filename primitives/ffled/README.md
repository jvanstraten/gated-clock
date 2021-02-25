Flipflop LED
============

Dedicated LED for flipflop state. Also includes a 10uF capacitor for bulk
capacitance on the border of the PCB.

```
      Vcc           Vcc           Vcc
     -----         -----         -----
       |             |             |
       |             |             |
       |             |             |
       |             |             |
       |             |       .-._  | 5  SN74LVS1G17DCKR
       |             |       |   `-._
       |             |     2 |     __`-._  4     X
A)-----+-------------+-------|   _||    _:-------.
       |             |       |      _.-'         |
       |             |       |  _.-'            .-.
       |             |       '-'   | 3          | | Depends
       |             |             |            | | on LED
       |             |             |            '-'
       |             |             |             |
       |             |             |             |
       |             |             |             |R
       |             |             |             |
       |             |             |             | 2
       |             |             |             '.  .
       |             |             |               '>| 1
     ----- 10uF    ----- 100nF     |   MMBT4403WT1G  |-----.
     -----         -----           |               .-|     |
       |             |             |             .'  '   -----
       |             |             |             | 3     Vffled
       |             |             |             |
       |             |             |             |L
       |             |             |             |
       |             |             |             | Any T1 (3mm) LED
       |             |             |           -----
       |             |             |           \   / -->
       |             |             |            \ /  -->
       |             |             |           -----
       |             |             |             |
       |             |             |             |
     -----         -----         -----         -----
      Gnd           Gnd           Gnd           Gnd
```
