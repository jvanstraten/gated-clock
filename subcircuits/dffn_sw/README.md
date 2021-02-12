D flipflop, negated input, with switch for clock
================================================

Exactly the same as `dffn`, except the clock enters in a different place and
via the center of a 3-way jumper header.

```
            ArnA          ArnB
            | .----..       |
            '-|A     \      |      ,-.
        .-----|4   P3 |()-. |     |   |- Q~1
        |   .-|1     /    | |      `-'
ClkA |O||   | '----''     | |
     |O|)-. '-----.,------' |
ClkB |O|| | .-----'`------. |
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