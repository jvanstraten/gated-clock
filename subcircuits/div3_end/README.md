Last divide by 3
================

This circuit performs a frequency division by 3. Specifically, it is used for
the most significant digit of the hours, so there is no further divider that
this circuit must generate a clock for. Therefore, the clock output is omitted
entirely. Furthermore, the layout is 0.75mm wider to make everything line up
at the top of the clock, and d3ap is omitted because it is never used.

Order:

```
    .-----.-----.---------.
    | d3b | d3a | decimal |
.---+-----+-----+---------|
| 0 |  0  |  0  |    0    |
| 1 |  0  |  1  |    1    |
| 2 |  1  |  0  |    2    |
'---'-----'-----'---------'
```

Circuit:

```
ClkIn~1 Arn~1         Arn~2           ClkIn~2 Arn~3         Arn~4
      | | .----..       |                   | | .----..       |
      | '-|A     \      |      ,-.          | '-|A     \      |      ,-.
    .-)---|4   P3 |()-. |     |   |---.   .-)---|4   P3 |()-. |     |   |---.
    | | .-|1     /    | |      `-'    |   | | .-|1     /    | |      `-'    |
    | | | '----''     | |             |   | | | '----''     | |             |
    | | '-----.,------' |             |   | | '-----.,------' |             |
    | | .-----'`------. |             |   | | .-----'`------. |             |
    | | | .----..     | | .----..     |   | | | .----..     | | .----..     |
    | | '-|3     \    | '-|A     \    |   | | '-|3     \    | '-|A     \    |
    | |   |    P1 |()-o---|1   Qn |()-)-. | |   |    P1 |()-o---|1   Qn |()-)-o
    | o---|C     /    | .-|Q     /    | | | o---|C     /    | .-|Q     /    | |
    | |   '----''     | | '----''     | | | |   '----''     | | '----''     | |
    | |  _____________| '-----.,------)-o | |  _____________| '-----.,------)-o
    | | |               .-----'`------o | | | |               .-----'`------o |
    | | | .----..       | .----..     | | | | | .----..       | .----..     | |
    | | '-|1     \      '-|Qn    \    | | | | '-|1     \      '-|Qn    \    | |
    | '---|C   P2 |()-.   |     Q |()-' | | '---|C   P2 |()-.   |     Q |()-o |
    '---o-|4     /    o---|2     /      | '---o-|4     /    o---|2     /    | |
        | '----''     |   '----''       |     | '----''     |   '----''     | |
        '-----.,------'                 |     '-----.,------'               | |
        .-----'`------.                 |     .-----'`------.               | |
        | .----..     |                 |     | .----..     |               | |
        '-|2     \    |                 |     '-|2     \    |               | |
          |    P4 |()-'                 |       |    P4 |()-'               | |
        .-|Dn    /          ..----.     o-------|Dn    /                    | |
        | '----''          /  d3an|-----o       '----''                     | |
        '---------------()| fb    |     |                                   | |
                           \  d3bn|-----)-----------------------------------)-o
                            ''----'     |                                   | |
                                        d3an                             d3bp d3bn
```

Total width, not including borders, is:

 - 4 gates x 8mm = 32mm;
 - 17 wiring spacers x 1.5mm = 25.5mm;
 - total 57.5mm.
