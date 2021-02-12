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

Note that the above unfortunately doesn't work out of the box (at least not
with excessive pessimism about load capacity and process variations in the
NAND gates). To make timing work, special instances of the NAND gates are used:

 - P3 and P4 are normal NAND gates, with a latency between 13 and 80 ns over
   process and load capacity variation (100R/330pF output filter);
 - P1 and P2 are slow NAND gates, with with a latency between 83 and 420 ns
   over process and load capacity variation (100R/2200pF output filter);
 - Q and Qn are normal NAND gates in terms of speed, but with an extra
   1k/2200pF RC filter for the P1/P2 input, adding between 699 and 2943 ns
   latency.

P1 and P2 are slowed down because for some reason this helped with stability
when there is clock uncertainty; this may or may not be an artifact of an
overly simplistic simulation, but better safe than sorry. With just that and
normal Q/Qn gates however, a minimum datapath length of a few hundred
nanoseconds is needed to satisfy hold timing. Because we're using flipflops
almost or completely back-to-back in our counters, that wouldn't fly. The
easiest way to add this "datapath" latency everywhere is by sticking it between
the latch preprocessing circuit and the actual Q/Qn latch; the latch is
transparent while clock is high, so the latency here is effectively added to
the datapath as long as it's in the first half of the clock period.

All of the above of course limits the maximum clock frequency considerably. But
we hardly need a fast clock frequency; under normal operation, the highest
frequency is 60Hz, while this flipflop, along with the bare-minimum datapaths,
can probably pull about 250kHz easily. That allows a self-test to be performed
at ~4000x real-time, which means we need about 21 seconds to cycle through an
entire day for 60Hz division or a little over 18 seconds for 50Hz division. The
microcontroller can configure the time much faster however, by pulsing the
minute and hour increment inputs directly. It could do that easily in under a
millisecond. If it also wants to set the seconds counter, it would take maybe
20 milliseconds -- still way faster than the eye can see, so that's more than
good enough.
