Divide-by-3 to 7-segment decoder
================================

This takes the (complementary) output of a divide-by-3 as input, and outputs
active-low 7-segment controls for the following "font." The overall input to
output table is shown below.

```
d3b      0      0      1
d3a      0      1      0

  A      .      · .   ===.
F   B  .   .  ·   |  ·   |
  G      ·      · |  .==='
E   C  .   .  ·   |  |   ·
  D      .      · '  '===

An       x      x           = d3bn
Bn       x                  = not (d3an nand d3bn)
Cn       x             x    = d3an
Dn       x      x           = d3bn
En       x      x           = d3bn
Fn       x      x      x    = 1
Gn       x      x           = d3bn
```

This results in the following possible routing.

```
    d3b  d3a
    p n  p n
    | |  | |
    '-)--)-)---------------------------------- An Dn En Gn
      |  | |   ____                  ____
      |  | '--|    \                |    \
      |  |    | B   )O--------------| Bn  )O-- Bn
      '--|----|____/                |____/
         |
         '------------------------------------ Cn
```
