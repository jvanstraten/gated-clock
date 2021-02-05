D flipflop, negated input
=========================

This represents a rising-edge-sensitive D flipflop with asynchronous reset,
single negated input, and complementary output. Logic function:

```
.-----.-----.-----.       .-----.-----.
|  C  | Arn | Dn  |       |  Q  | Qn  |
|=====+=====+=====+=======+=====+=====|
|  -  |  0  |  -  | reset |  0  |  1  |
|-----+-----+-----+-------+-----+-----|
| _/‾ |  1  |  0  | load  |  1  |  0  |
| _/‾ |  1  |  1  |       |  0  |  1  |
|-----+-----+-----+-------+-----+-----|
|  0  |  -  |  -  |       | Q'  | Qn' |
|  1  |  -  |  -  | keep  | Q'  | Qn' |
| ‾\_ |  -  |  -  |       | Q'  | Qn' |
'-----'-----'-----'-------'-----'-----'
```

The data input and output pins are placed such that they can be routed with
vertical columns in the divider subcircuits. The reset and clock pins are
to be routed using horizontal routing outside the divider circuits.

```
Clk Arn~1         Arn~2
  | | .----..       |
  | '-|A     \      |      ,-.
.-)---|4   P3 |()-. |     |   |- Q~1
| | .-|1     /    | |      `-'
| | | '----''     | |
| | '-----.,------' |
| | .-----'`------. |
| | | .----..     | | .----..
| | '-|3     \    | '-|A     \
| |   |    P1 |()-o---|1   Qn |()- Qn~1
| o---|C     /    | .-|Q     /
| |   '----''     | | '----''
| |  _____________| '-----.,- Qn~2
| | |               .-----'`- Q~2
| | | .----..       | .----..
| | '-|1     \      '-|Qn    \
| '---|C   P2 |()-.   |     Q |()- Q~3
'---o-|4     /    o---|2     /
    | '----''     |   '----''
    '-----.,------'
    .-----'`------.
    | .----..     |
    '-|2     \    |
      |    P4 |()-'
  Dn -|Dn    /
      '----''
```
