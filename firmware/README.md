Firmware
========

By design, the clock can operate entirely without any microcontroller firmware.
After all, the whole point is to demonstrate that you can make a useful circuit
with only NAND gates and some discretes. Nevertheless, some auxiliary functions
are handled by a microcontroller:

 - LED brightness and color control;
 - automatically configuring the time using GPS after a blackout;
 - blinking the display before a time is set (either manually or automatically)
   after a blackout;
 - automatic DST changes;
 - the synchroscope display; and
 - handling UI stuff for configuring all of the above.

Build process
-------------

The microcontroller (board) in question is a Teensy LC. I opted for such a
board versus a "discrete" microcontroller primarily because you don't need a
programmer for them, and because Arduino makes it so easy to set something up
quickly. Arduino is however hardly a platform for distributing a reproducible
build with: the user has to manually set options like board, operating
frequency, and USB mode, and many times for Teensy you end up changing system
files to change a buffer size somewhere or something. Therefore, to try to make
things a little better, a docker-based build is provided.

When you run `make` in this directory, the following things will happen:

 - docker will be used to do a build using exactly the Teensy core library
   version I use;
 - the [Teensy loader CLI](https://github.com/PaulStoffregen/teensy_loader_cli)
   will be downloaded and compiled;
 - an attempt will be made to put the first Teensy connected to your system in
   programming mode (this only works when it has a program on it that uses the
   USB for serial communication); and
 - an attempt will be made to program the Teensy (if aforementioned fails,
   you'll have to press the programming button).

So, before running `make`, make sure that you have a working Docker, working
dev essentials (GCC, make, etc), and the libusb 0.1 development headers that
the Teensy loader CLI uses.

Firmware details
----------------

TODO

 - measure 1PPS and 50Hz frequency -> interrupt-driven using timer input
   capture
 - update LED drivers and synchroscope at ~50fps, also UI loop -> not
   timing-critical; bitbang LED driver in main loop
 - read buttons/update I/O on I/O expander at 500Hz -> 1ms-tick-driven: read
   result of previous transaction from the FIFO, then prepare the next
   transaction, cycling between read GPIO, write GPIO (and latch direction
   simultaneously), read GPIO, write IODIR. If previous transaction was a read,
   update button debounce states. Also read the increment switch states at this
   time and update the auto-increment logic.
 - read GPS time, and possibly perform time sync: interrupt-driven on UART RX
