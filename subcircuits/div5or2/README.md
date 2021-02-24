Divide by 5 or 2
================

This circuit divides by 5 in the same way div5 does, but has logic to stop at
2 instead based on an external input. This is used to achieve division by 24 in
a way that a regular d5d2 decoder can be used for the lower digit.

Order:

```
      .-----.-----.-----.---------.-----.--------.
      | d5c | d5b | d5a | decimal | con | ClkOut |
.-----+-----+-----+-----+---------+-----+--------|
|  0  |  0  |  0  |  0  |    0    |  0  |   1    |
|  1  |  0  |  0  |  1  |    1    |  1  |   0    |
| (2) |  0  |  1  |  1  |    3    |  1  |   0    |
| (3) |  1  |  1  |  0  |    6    |  1  |   0    |
| (4) |  1  |  0  |  0  |    4    |  1  |   0    |
'-----'-----'-----'-----'---------'-----'--------'
```

Circuit:

```
ClkIn~1 Arn~1         Arn~2           ClkIn~2 Arn~3         Arn~4           ClkIn~3 Arn~5         Arn~6             ClkOut
1     | | .----..       |                   | | .----..       |                   | | .----..       |                 |
      | '-|A     \      |      ,-.          | '-|A     \      |      ,-.          | '-|A     \      |      ,-.        |
    .-)---|4   P3 |()-. |     |   |---.   .-)---|4   P3 |()-. |     |   |---.   .-)---|4   P3 |()-. |     |   |---.   |
    | | .-|1     /    | |      `-'    |   | | .-|1     /    | |      `-'    |   | | .-|1     /    | |      `-'    |   |
    | | | '----''     | |             |   | | | '----''     | |             |   | | | '----''     | |             |   |
    | | '-----.,------' |             |   | | '-----.,------' |             |   | | '-----.,------' |             |   |
    | | .-----'`------. |             |   | | .-----'`------. |             |   | | .-----'`------. |             |   |
    | | | .----..     | | .----..     |   | | | .----..     | | .----..     |   | | | .----..     | | .----..     |   |
    | | '-|3     \    | '-|A     \    |   | | '-|3     \    | '-|A     \    |   | | '-|3     \    | '-|A     \    |   |
    | |   |    P1 |()-o---|1   Qn |()-)-. | |   |    P1 |()-o---|1   Qn |()-)-. | |   |    P1 |()-o---|1   Qn |()-)-. |
    | o---|C     /    | .-|Q     /    | | | o---|C     /    | .-|Q     /    | | | o---|C     /    | .-|Q     /    | | |
    | |   '----''     | | '----''     | | | |   '----''     | | '----''     | | | |   '----''     | | '----''     | | |
2   | |  _____________| '-----.,------)-o | |  _____________| '-----.,------)-o | |  _____________| '-----.,------)-o |
    | | |               .-----'`------o | | | |               .-----'`------o | | | |               .-----'`------o | |
    | | | .----..       | .----..     | | | | | .----..       | .----..     | | | | | .----..       | .----..     | | |
    | | '-|1     \      '-|Qn    \    | | | | '-|1     \      '-|Qn    \    | | | | '-|1     \      '-|Qn    \    | | |
    | '---|C   P2 |()-.   |     Q |()-o | | '---|C   P2 |()-.   |     Q |()-o | | '---|C   P2 |()-.   |     Q |()-' | |
    '---o-|4     /    o---|2     /    | | '---o-|4     /    o---|2     /    | | '---o-|4     /    o---|2     /      | |
        | '----''     |   '----''     | |     | '----''     |   '----''     | |     | '----''     |   '----''       | |
        '-----.,------'               | |     '-----.,------'               | |     '-----.,------'                 | |
        .-----'`------.               | |     .-----'`------.               | |     .-----'`------.                 | |
        | .----..     |               | |     | .----..     |               | |     | .----..     |                 | |
        '-|2     \    |               | |     '-|2     \    |               | |     '-|2     \    |                 | |
      .---|daan P4|()-'               | |       |    P4 |()-'               | |       |    P4 |()-'                 | |
      | .-|dabn  /          ..----.   | |     .-|dbn   /        ..----.     | o-------|Dn    /                      | |
      | | '----''          /    an|---)-o     | '----''        /   Di5|---. | |       '----''                       | |
3     | '---------------()|dabn   |   | |     '-------------()| dbn   |   | | |                                     | |
4     |     ..----.        \   Di2|-. | |                      \    ap|-. | | |       .----..         .----..       | |
5     |    /    bn|------.  ''----' | | |                       ''----' | | | o-------|bn    \        |      \      | |
6     '-()daan  cn|----. |          | o-)-------------------------------' | | |   .---|an  con|()-----|con  co|()---)-'
7          \   Di5|--. | |          | | o---------------------------------)-)-)---' .-|cn    /        |      /      |
8           ''----'  | | '----------)-)-)---------------------------------)-)-o     | '----''         '----''       |
9                    | '------------)-)-)---------------------------------)-)-)-----o-------------------------------o
10                   |              | | |                                 | | |                                     |
                   div5          div2 | d5an                           div5 | d5bn                                  d5cn
                                     d5ap                                  d5bp
    0 1 2    3    4 5 6 7 8  9  0 1 2 3 4 0 1 2      3           4      5 6 7 8 0 1 2      3      4 5      6      7 8 9
                                1 1 1 1 1 2 2 2      2           2      2 2 2 2 3 3 3      3      3 3      3      3 3 3
```

Total width, not including borders, is:

 - 6 gates x 8mm = 48mm;
 - 27 wiring spacers x 1.5mm = 40.5mm;
 - total 88.5mm.

A note on the clock output circuit
----------------------------------

Unlike all the other dividers, we can't just use the Qn output of the last
flipflop, because that flipflop never toggles in div2 mode.

One way to do it instead is to output high when the *next* output for the first
flipflop is high. This can be accomplished with just a 2-input NAND on `dabn`
and `daan`, and, in fact, this is what I originally did. However, this causes a
hazard when switching between div2 and div5! Hazards in clock signals = bad.

Instead, we make the clock output 1 only when the register is at 0. This
guarantees a rising edge transition at the right time, and has no hazards: the
only state transition where two flipflops change state at once is between state
2 and 3, but output B remains set throughout this transition, keeping the
clock output low. The only downside is that it doesn't route as nicely.
