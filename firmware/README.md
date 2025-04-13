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

### Updating timezone definitions

You can automatically update the timezone database that the clock uses for
auto-DST by running `src/timezones.py`. The database is based on data provided
by [timezonedb.com](https://timezonedb.com/).

User interface and configuration
--------------------------------

The clock has three software-only buttons (labelled up, down, and mode), one
hardware reset button, and two slide switches. To the right of the mode button
there is also a dedicated RGB LED for status information. These elements,
combined with the main 7-segment display and the synchroscope bar, are used to
configure the clock.

Under normal circumstances, the 7-segment display displays the time, the status
LED is off, and the synchroscope display behaves as configured (by default, the
LEDs act like the needle of a electromechanical synchroscope). But there are a
few exceptional cases:

 - If the GPS module is not locked and GPS time synchronization is enabled, the
   status LED turns red.
 - If the time is invalid (for example, after a power cycle), the 7-segment
   display blinks.

The buttons and switches have the following functions in this state.

 - The hardware reset button resets the time. This also "invalidates" the time,
   making the display blink. If GPS synchronization is enabled, you can press
   this button to force resynchronization.
 - The slide switches may be used to manually configure the clock. The left
   switch controls the hours, the bottom switch controls minutes. To configure
   the time, you can use the following procedure.
    - Move both switches to the center position. This prevents the minutes and
      hours counters from updating when the seconds and minutes counters
      overflow.
    - Optionally, press the reset button when you want the seconds counter to
      read zero. There's no way to configure the seconds otherwise. Note that
      you'll want to disable GPS synchronization if you do this, or the clock
      may try to automatically configure itself instead.
    - Configure hours and minutes independently by pushing the respective slide
      switches into their clockwise position. If auto-increment is enabled in
      the clock's settings, the microcontroller will make this process more
      convenient: the counters will then increment when you push the button
      towards the clockwise position and will auto-increment if you keep
      holding it. If you disable this setting, the counters will instead
      increment only when you release the respective switches, but everything
      is handled by the discrete NAND circuit.
    - Move both switches back to the anti-clockwise position.
 - Pressing the down button enables "distraction-free" mode. In this mode, all
   LEDs except for the hours and minutes 7-segment displays and the status LED
   (if the GPS signal is used and lost) are disabled. Press the up button to
   exit this mode.
 - Briefly pressing the mode button will display the date in YYMMDD format, if
   GPS is currently available or has been available at some point since the
   last power cycle. The status LED will turn green to indicate that the clock
   isn't displaying time; also, the colons are turned off. Press mode again to
   return to normal operation.
 - Hold mode down for at least one second to enter the setup menu.

The setup menu consists of a number of configuration parameters, that you can
cycle through using the up and down buttons. You can leave the menu by holding
down the mode button again, by pressing up and down simultaneously, or simply
by waiting. When you leave the menu, any changes made to the configuration are
written to non-volatile memory, so the configuration survives a power cycle.

While in the menu, the current parameter is shown on the left side of the
7-segment display via an abbreviation. Its current value is shown on the right.
The status LED turns dark blue to indicate that you can cycle through the
values with up and down. The behavior of the synchroscope display depends on
the selected parameter.

The mode button is used to change the value of the current parameter. For
"enumerated" values, pressing mode simply advances to the next value. For
numeric values, the status LED will instead turn light blue, at which point
you can change the value by means of the up and down buttons. For most
parameters, the value will also blink to indicate that you can change it;
the only exception is the "display brightness" parameter. Instead, the display
will read `888888` while you're adjusting it, to give you a better idea of what
the brightness looks like, and also such that the clock can better monitor the
worst-case effect of the brightness on its own power consumption. For all
numeric options, pressing mode again confirms the new value, and allows you to
select a different parameter again.

The following parameters are available.

 - Flipflop LED brightness (`Fb`).
 - NAND gate LED brightness (`Gb`).
 - Synchroscope LED brightness (`Sb`).
 - 7-segment display brightness (`db`).
 - 7-segment display color saturation (`dS`).
 - 7-segment display color hue (`dh`).
 - Whether the 7-segment display brightness is automatically adjusted based on
   ambient lighting conditions. This requires an LDR to be installed. When
   enabled, the display brightness setting controls the maximum brightness.
 - Whether the seconds digits should be shown (`Sd`).
 - Configuration of the timing source of the clock and the synchroscope
   (`SYn`). Five modes are available.
    - Normal synchroscope operation (`1`). The clock is timed via the 50Hz or
      60Hz utility frequency, and the synchroscope shows whether the grid (and
      thus the clock itself!) is running slow or fast. Every 360-degree
      revolution of a real synchroscope represents a full 50/60Hz cycle lost
      or gained, which the display tries to model (despite not being a full
      circle) by moving with the same angular rate as a real synchroscope
      would, and rolling over every 84 degrees.
    - Lead-lag mode (`LL`). Like above, but instead, the synchroscope display
      shows the current offset of the seconds counter compared to GPS time.
      When the two center LEDs are both on, the clock is synchronized. When the
      outermost LEDs are both on, the clock is running exactly 30 seconds fast
      or slow. Note that this mode is not available when the seconds display
      is turned off.
    - Synchroscope display off, but still using the utility frequency as the
      clock source (`0`).
    - Synchroscope display off, using an internally-generated 50Hz timing
      source (`50`). When GPS is available, the frequency is referenced to it,
      so long-term stability should be extremely good. When GPS is not
      available, the crystal oscillator of the microcontroller takes over,
      making stability similar to a normal digital clock.
    - As above, but generating 60Hz (`60`).
 - Whether the software-controlled auto-increment logic is enabled for manually
   configuring the clock (`AInc`).
 - The [location code](timezones.md) corresponding to your timezone for GPS
   synchronization and automatic daylight-saving time adjustment (`LC`). Set to
   0 to disable automatic time synchronization.
 - Daylight-saving time configuration (`dSt`). This option is only available
   when automatic time synchronization is enabled. You can set it to `A` (auto)
   to have the clock update the time automatically when DST changes, or you can
   manually enable or disable daylight-saving time using values `1` and `0`.
   This is of course particularly relevant if your region decides to get rid of
   DST, or change its implementation. You can also choose to update the
   firmware in that case; you don't have to change any code to do this, but
   you will need to open the clock back up to attach a USB cable, and of course
   you need a computer that meets the system requirements for building and
   uploading the firmware.

For some of the options, the synchroscope display will show additional
information while the option is selected.

 - When LED brightness/color options are active, the synchroscope depicts the
   current power consumption of the clock. Full-scale is about 2.5A at 5V. When
   you somehow end up drawing too much current by making the displays too
   bright, software and/or hardware will kick in to reduce power consumption;
   at 3A or above brightness levels are automatically reduced across the board.
   Furthermore, if 3.5A or more is sustained, hardware protection circuitry
   will kick in and disable the clock until the next power cycle to prevent
   damage.
 - When the LDR option is selected, the synchroscope depicts the current
   (low-pass-filtered) value of the ambient light sensor.
 - When the location code option is selected, the synchroscope gives a rough
   indication of the GPS signal strength, which may help you find a good place
   for the antenna.

If necessary, you can do a "factory reset" of all options by holding down the
mode button while the clock powers up.

Debugging / Development notes
-----------------------------

### Listening to the serial port

When connected via USB, the board acts as a serial device, and can print some
debug data over serial. It will however only do so after being sent any
character from the host first. In a linux terminal, you can for instance use
the `screen` command to read this data. Note that the device file name may
differ depending on your setup.

- run `screen /dev/ttyUSB0`
- press any character

### Programming using Windows

While the default build process is gearded towards linux, it is possible to
program and debug the board from windows, using WSL. You will need to use
`usbipd-win` to forward the USB connection from windows to the WSL instance.
The workflow is as follows:

- install `usbipd-win` on the host computer.
- start your WSL instance on the host computer.
- in a windows terminal, run `usbipd list` before connecting the Teensy board.
- connect the Teensy board
- run `usbipd list` again to identify the bus id of the Teensy board
- run `usbipd bind --busid=BUSID`, where BUSID is the bus id of the Teensy board
- run `usbipd attach --wsl --busid=BUSID`, to attach the Teensy board to the wsl
  instance
- in WSL, install the required dependencies as stated above, and manually start
  the docker service if needed.
- run `make build` to build the firmware
- run `make program` to start the programming process. This will put the Teensy
  board in programming mode, which will cause it to reconnect.
- run `usbipd attach --wsl --busid=BUSID` again from the windows side to reattach
  the teensy board to WSL
- the programming process should now continue to completion.
- the board will detach again after programming is finished. If you want to
  debug it using the serial connection, simply reattach it again with the same
  command as before.

Note: while developing using WSL, the device will likely show up with a different
name like `/dev/ttyACM0`.
