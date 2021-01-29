4-bit binary to 7-segment decoder
=================================

This takes a regular 4-bit binary value as complementary signals as input, and
outputs active-low 7-segment controls for the following "font."

```
  A    .===.    · .   ===.   ===.  . · .  .===   .===    ===.  .===.  .===.
F   B  |   |  ·   |  ·   |  ·   |  |   |  |   ·  |   ·  ·   |  |   |  |   |
  G    | · |    · |  .==='   ===|  '===|  '===.  |===.    · |  |===|  '===|
E   C  |   |  ·   |  |   ·  ·   |  ·   |  ·   |  |   |  ·   |  |   |  ·   |
  D    '==='    · '  '===    ==='    · '   ==='  '==='    · '  '==='   ==='

b3       0      0      0      0      0      0      0      0      1      1
b2       0      0      0      0      1      1      1      1      0      0
b1       0      0      1      1      0      0      1      1      0      0
b0       0      1      0      1      0      1      0      1      0      1
```

Other input is treated as don't-care. This results in the following table
(`x` marks output high = segment *off*):

```
    .---------.---------.-----.
    |    X    |    Y    | (Z) |
    |---------+---------+-----|
    | 0 1 2 3 | 4 5 6 7 | 8 9 |
.---+---------+---------+-----)-------------------.
| A |   x     | x       |     | X01 or Y00        |
| B |         |   x x   |     | Y01 or Y10        |
| C |     x   |         |     | X10               |
| D |   x     | x     x |     | X01 or Y00 or Y11 |
| E |   x   x | x x   x |   x | --1 or Y00        |
| F |   x x x |       x |     | X01 or X1- or Y11 |
| G | x x     |       x |     | X0- or Y11        |
'---'---------'---------'-----'-------------------'
```

where `X`, `Y`, `Z` represent regions. `Y` is simply the `b2` input, and `Z`
would simply be the `b3` input if it were used, but `X` needs to be generated
with as `b2 nor b3`, which, unfortunately, requires two gates.

The rest is simply the and-or-invert network shown on the right.

We need a helper signal to indicate the 0..3 state, which we'll call X. Then
we can use an and-or-invert circuit using only up-to 3-input NANDs to produce
our desired outputs. Note that some of the intermediate signals can be reused.

```
  b0n   b1n
b0 |  b1 |  b2                                     b2n  b3n
|  |  |  |  |                                        |  |
|  o--)--)--)---------------------------.            |  |
|  |  |  |  |        ____               |     ____   |  |
|  |  |  |  |       /    |              |    /    |--'  |
|  |  |  |  |  .--O(  X  |--------------)--O(  Xn |     |
|  |  |  |  |  |    \____|              |    \____|-----'
|  |  |  |  |  |                        |
|  |  |  |  |  |                        |
|  |  |  |  |  |   ____                 |
|  |  |  |  |  o--|    \                |
|  |  |  |  |  |  | X0u )O-----.        |
|  |  |  o--)--)--|____/       |        |   ____
|  |  |  |  |  |               '--------)--|    \
|  |  |  |  |  |                        |  | Gn  )O--
|  |  |  |  |  |   ____        .--------)--|____/
|  |  |  |  |  o--|    \       |        |
|  |  |  o--)--)--| X01 )O--.  |        |
o--)--)--)--)--)--|____/    |  |        |   ____
|  |  |  |  |  |            |  o--------)--|    \
|  |  |  |  |  |            o--)--------)--| Fn  )O--
|  |  |  |  |  |   ____     |  |  .-----)--|____/
|  |  |  |  |  o--|    \    |  |  |     |
|  |  o--)--)--)--| X10 )O--)--)--)--.  |
|  o--)--)--)--)--|____/    |  |  |  |  |   ____
|  |  |  |  |  |            |  |  |  |  '--|    \
|  |  |  |  |  |            |  |  |  |     | En  )O--
|  |  |  |  |  |   ____     |  |  |  |  .--|____/
|  |  |  |  |  '--|    \    |  |  |  |  |
|  |  |  |  |     | X1u )O--)--)--'  |  |
|  |  o--)--)-----|____/    |  |     |  |   ____
|  |  |  |  |               |  o-----)--)--|    \
|  |  |  |  |               |  |     |  o--| Dn  )O--
|  |  |  |  |      ____     o--)-----)--)--|____/
|  |  |  |  o-----|    \    |  |     |  |
|  |  |  o--)-----| Y00 )O--)--)-----)--o
|  o--)--)--)-----|____/    |  |     |  |   ____
|  |  |  |  |               |  |     |  |  |    \
|  |  |  |  |               |  |     '--)--| Cn  )O--
|  |  |  |  |      ____     |  |        |  |____/
|  |  |  |  o-----|    \    |  |        |
|  |  |  '--)-----| Y01 )O--)--)--.     |
o--)--)-----)-----|____/    |  |  |     |   ____
|  |  |     |               |  |  '-----)--|    \
|  |  |     |               |  |        |  | Bn  )O--
|  |  |     |      ____     |  |  .-----)--|____/
|  |  |     o-----|    \    |  |  |     |
|  |  o-----)-----| Y10 )O--)--)--'     |
|  '--)-----)-----|____/    |  |        |   ____
|     |     |               |  |        '--|    \
|     |     |               |  |           | An  )O--
|     |     |      ____     '--)-----------|____/
|     |     '-----|    \       |
|     '-----------| Y11 )O-----'
'-----------------|____/
```
