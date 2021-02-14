Configuration circuit
=====================

This circuit intercepts a clock line to allow the user (or the microcontroller
subsystem) to block transmission of regular clock pulses or to add introduce
additional clock pulses.

Circuit:

```
ClkIn_n                          ClkOut
  | .-----------------------------. |
  | |                             | |    .
  | |           Switch            | |    |
  | |                             | |    |
  | '---.                     .---' |    |
  | .---|Run               Isw|---. |    '
  | |   '---------------------'   | |    -
  | | .---------------------------' |    -
  | | | .----..         .----..     |    .
  | '-)-|Run   \        |      \    |    |
  '---)-|Cin  X |()-. .-|Con  Co|()-'    |
  .---)-|Ren   /    | | |      /         |
  |   | '----''     | | '----''          '
  |  _|             | |_____________     - /__ r=160mm
  | |               |               |    - \   reference
  | |   .----..     |   .----..     |    .
  | o---|Isw   \    '---|X     \    |    |
  | |   |     Y |()-----|Y   Con|()-'    |
  | | .-|Ien   /    .---|Inc   /         |
  | | | '----''     |   '----''          '
  | | |             '---------------.    -
  | | | .-------------------------. |    -
  | | '-|Ien  .- - - - - - -.  Inc|-'    .
  | |   |     :             :     |      |
  | |   |     :  4 pin FPC  :     |      |
  | |   |     :             :     |      |
  | '---|Isw  '- - - - - - -'  Ren|-.    '
  |     '-------------------------' |
  '---------------------------------'
```

Total width, not including borders, is:

 - 2 gates x 8mm = 16mm;
 - 8 wiring spacers x 1.5mm = 12mm;
 - total 28mm.

Theory of operation
-------------------

The switch primitive consists of a sliding ON-OFF-(ON) switch that outputs
active-high through a basic RC debounce circuit. The microcontroller interface
primitive at the bottom allows the microcontroller to override the switch and
output clock pulses of its own.

The input to the circuit is an *inverted* clock; the inversion necessary there
is pushed to the previous output circuit. This is always a div3, and the div3
isn't used in any other context where its clock should not be inverted, so we
don't need an alternative circuit there.

The default behavior of the switch is to pass the clock through in run mode,
output clock high in the neutral position, and output clock low in the
momentary increment position. While simple, this is not entirely intuitive:

 - the action of moving from the run to the neutral position may or may not
   spuriously increment the driven dividers; and
 - the action of moving from the momentary increment position back to neutral
   is what increments the driven dividers, not the other way around.

The former can only be solved with an XOR gate, which we don't have enough
room for (especially because the microcontroller would need an input as well,
so we'd have to make a 3-input XOR). So we just have to deal with it. It
shouldn't be too bad, because when you want to reconfigure the time, you by
definition want to increment the time at least once.

The microcontroller's override signals can be used to solve the latter, hence
why the microcontroller can detect whether the switch is in the momentary
increment position. Almost immediately after detecting this, it may disable
the increment switch by pulling its Ie (increment enable) output low. Doing
so causes the increment action to happen immediately, as the circuit behaves
as if the switch has already been released. Furthermore, auto-repeat can be
accomplished by pulsing the Ie pin periodically while the user continues to
hold the switch in the increment position.

The microcontroller may also configure the clock autonomously, in conjunction
with the global Arn (asynchronous reset) signal. The procedure is as follows:

 - pull Arn, Ie, and Re low to clear all registers (i.e. set the time to
   00:00:00), block clock propagation, and override user input;
 - release Arn at the 0-second synchronization point;
 - strobe In (active-low increment) low up to 59 times for the minute
   configuration circuit and up to 23 times for hours to load the hours
   configuration circuit; and
 - pull Ie, Re, and In high again to return to normal operation.
