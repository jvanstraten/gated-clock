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

It's based on the following circuit. Note that Q and Qn are swapped to make
the D input inverted. Note that in the dual the asynchronous reset is actually
an asynchronous set; hence the difference.

![Flip flop circuit](flipflop.jpg?raw=true "Flip flop circuit")

The data input and output pins are placed such that they can be routed with
vertical columns in the divider subcircuits. The reset and clock pins are
to be routed using horizontal routing outside the divider circuits.

```
Clk ArnA          ArnB
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
