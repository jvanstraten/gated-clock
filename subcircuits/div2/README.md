Divide by 2
===========

This circuit performs a frequency division by 2. It's just a single D flipflop
trivially hooked up as a T flipflop, but the additional routing is such that it
can be placed in the border.

Order:

```
    .----.---------.
    | d2 | decimal |
.---+----+---------|
| 0 | 0  |    0    |
| 1 | 1  |    1    |
'---'----'---------'
```

Circuit:

```
ClkIn Arn~1         Arn~2          ClkOut
    | | .----..       |               |
    | '-|A     \      |      ,-.      |
  .-)---|4   P3 |()-. |     |   |---. |
  | | .-|1     /    | |      `-'    | |
  | | | '----''     | |             | |
  | | '-----.,------' |             | |
  | | .-----'`------. |             | |
  | | | .----..     | | .----..     | |
  | | '-|3     \    | '-|A     \    | |
  | |   |    P1 |()-o---|1   Qn |()-)-o Qn~1
  | o---|C     /    | .-|Q     /    | |
  | |   '----''     | | '----''     | |
  | |  _____________| '-----.,------)-o
  | | |               .-----'`------o |
  | | | .----..       | .----..     | |
  | | '-|1     \      '-|Qn    \    | |
  | '---|C   P2 |()-.   |     Q |()-o |
  '---o-|4     /    o---|2     /    | |
      | '----''     |   '----''     | |
      '-----.,------'               | |
      .-----'`------.               | |
      | .----..     |               | |
      '-|2     \    |               | |
        |    P4 |()-'               | |
      .-|Dn    /                    | |
      | '----''                     | |
      '-----------------------------o |
                                    | |
                                  d2p d2n
```

Total width, not including borders, is:

 - 2 gates x 8mm = 16mm;
 - 8 wiring spacers x 1.5mm = 12mm;
 - total 28mm.
