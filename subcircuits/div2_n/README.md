Divide by 2, no output
======================

This circuit performs a frequency division by 2. It's just a single D flipflop
trivially hooked up as a T flipflop, but the additional routing is such that it
can be placed in the border. This variant only divides; no output is generated
for decoding.

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
  | |   |    P1 |()-o---|1   Qn |()-)-o
  | o---|C     /    | .-|Q     /    | |
  | |   '----''     | | '----''     | |
  | |  _____________| '-----.,------)-'
  | | |               .-----'`------o
  | | | .----..       | .----..     |
  | | '-|1     \      '-|Qn    \    |
  | '---|C   P2 |()-.   |     Q |()-o
  '---o-|4     /    o---|2     /    |
      | '----''     |   '----''     |
      '-----.,------'               |
      .-----'`------.               |
      | .----..     |               |
      '-|2     \    |               |
        |    P4 |()-'               |
      .-|Dn    /                    |
      | '----''                     |
      '-----------------------------'
```

Total width, not including borders, is:

 - 2 gates x 8mm = 16mm;
 - 8 wiring spacers x 1.5mm = 12mm;
 - total 28mm.
