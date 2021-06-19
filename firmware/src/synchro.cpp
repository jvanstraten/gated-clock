#include "synchro.hpp"
#include "timer.hpp"
#include "gpio.hpp"
#include "led.hpp"
#include "gps.hpp"
#include <WProgram.h>

/**
 * Synchroscope logic namespace.
 */
namespace synchro {

/**
 * Current synchroscope mode.
 */
Mode mode = Mode::LEAD_LAG;

/**
 * Updates the power management logic.
 */
void update() {
    static bool overriding_clk = false;

    // Compute number of GPS-referenced milliseconds passed since last call.
    // Used for generating 50Hz/60Hz in override mode.
    static int16_t prev;
    int16_t gps_ms_passed = gps::milliseconds - prev;
    prev = gps::milliseconds;
    if (gps_ms_passed < 0) {
        gps_ms_passed += 1000;
    }
    static uint8_t f_gen_state;

    // Update based on current mode.
    switch (mode) {
        case Mode::SYNCHRO: {

            // Don't override the grid clock input.
            if (overriding_clk) {
                timer::release_clk();
                overriding_clk = false;
            }

            // Update whenever we receive a tick from the grid.
            if (!timer::grid_period) return;

            // If we have no GPS fix, or we're getting a fucky PPS pulse, default
            // to using the microcontroller crystal frequency as a reference.
            if (timer::gps_period < 47000000 || timer::gps_period > 49000000) {
                timer::gps_period = 48000000;
            }

            // Compute the frequency the grid is running at in microhertz.
            int64_t f_uhz = ((int64_t)timer::gps_period * 1000000 / timer::grid_period);

            // We're interested in the beat frequency you'd get when multiplying
            // the grid phasor and a perfect 50Hz or 60Hz (w.r.t. our reference,
            // and whichever is closer) phasor. That's just subtracting
            // frequencies.
            if (f_uhz < 55000000) {
                f_uhz -= 50000000;
            } else {
                f_uhz -= 60000000;
            }

            // So, every second, the phase difference we want to visualize varies
            // by 2 pi f_uhz / 1000000. But this routine isn't called every second;
            // it's called every grid period. So let's compute that period.
            int64_t t_us = ((int64_t)timer::grid_period * 1000000 / timer::gps_period);

            // Now we can update the phase, expressed in trillionths of the unit
            // circle.
            static int64_t phase_ppt = 0;
            phase_ppt += f_uhz * t_us;

            // The LEDs are spaced 2.8 degrees apart, and there are 30 of them.
            // That boils down to 7/30th of the unit circle. The LED logic has
            // 30*256 steps, so every step is 7/230400th of the unit circle. Put
            // differently, 1 trillion steps for phase_ppt equates to 230400/7
            // steps. So, to convert, we have to divide phase_ppt by
            // 1e12 / (230400/7) = 30381944 + 4/9. But let's add another factor
            // 256 precision to that for now, to use for some modest filtering.
            // That makes the divisor around 118679. We can use this logic here
            // for an IIR filter directly: phase_ppt tracks the current error
            // between the correct synchroscope position and what's already been
            // transferred to the synchroscope via synchro_micro_delta, so if
            // we just make synchro_micro_delta artificially lower, and also add
            // a dead zone, the display will lag behind the real value but will
            // never lag too far.
            int32_t synchro_micro_delta = phase_ppt / (int64_t)(118679ll * 5); // <- IIR ratio
            if (synchro_micro_delta < -256) { // dead zone
                synchro_micro_delta += 256;
            } else if (synchro_micro_delta > 256) {
                synchro_micro_delta -= 256;
            } else {
                synchro_micro_delta = 0;
            }
            phase_ppt -= (int64_t)synchro_micro_delta * 118679ll;

            // Track the actual position in 256th microsteps.
            static int32_t synchro_micro_pos = 0;
            synchro_micro_pos += synchro_micro_delta;

            // Roll over with period 30*256*256.
            if (synchro_micro_pos < 0) {
                synchro_micro_pos += 1966080;
            } else if (synchro_micro_pos >= 1966080) {
                synchro_micro_pos -= 1966080;
            }

            // Hand the data over to the synchroscope LED logic.
            gpio::synchro = synchro_micro_pos >> 8;
            gpio::synchro_enable = true;

            break;
        }
        case Mode::LEAD_LAG: {

            // Don't override the grid clock input.
            if (overriding_clk) {
                timer::release_clk();
                overriding_clk = false;
            }

            // Only enable display when we know both the GPS and displayed
            // time.
            if (led::displayed_time_valid && gps::valid) {

                // Update only when the displayed time just changed.
                static uint8_t prev;
                if (led::displayed_seconds != prev) {
                    prev = led::displayed_seconds;

                    // Compute the current delta using only seconds.
                    int32_t delta = ((int32_t)led::displayed_seconds - (int32_t)gps::seconds) * 1000 - gps::milliseconds;

                    // Convert delta to the 30*256 steps used by the
                    // synchroscope LED logic.
                    delta *= 128;
                    delta /= 1000;

                    // A delta of 0 should read as the middle two LEDs being on
                    // at the halfway point. So let's deal with that already,
                    // and then wrap delta such that it falls within 0..30*256.
                    delta += 3712;
                    if (delta < 0) {
                        delta += 7680;
                    } else if (delta >= 7680) {
                        delta -= 7680;
                    }

                    // Hand the data over to the synchroscope LED logic.
                    gpio::synchro = delta;
                    gpio::synchro_enable = led::displayed_time_valid;

                }

            } else {

                // Insufficient information available. Disable display.
                gpio::synchro_enable = false;

            }

            break;
        }
        case Mode::EXT: {

            // Don't override the grid clock input.
            if (overriding_clk) {
                timer::release_clk();
                overriding_clk = false;
            }

            // Position is controlled externally. Only enable the LEDs.
            gpio::synchro_enable = true;

            break;
        }
        case Mode::OFF: {

            // Don't override the grid clock input.
            if (overriding_clk) {
                timer::release_clk();
                overriding_clk = false;
            }

            // Disable the sychroscope LEDs.
            gpio::synchro_enable = false;

            break;
        }
        case Mode::GPS_50: {

            // Generate 50Hz.
            while (gps_ms_passed--) {
                f_gen_state++;
                if (f_gen_state == 10) {
                    timer::override_clk(false);
                } else if (f_gen_state >= 20) {
                    timer::override_clk(true);
                    f_gen_state = 0;
                }
            }
            overriding_clk = true;

            // Disable the sychroscope LEDs.
            gpio::synchro_enable = false;

            break;
        }
        case Mode::GPS_60: {

            // Generate 60Hz.
            while (gps_ms_passed--) {
                f_gen_state++;
                if (f_gen_state == 8) { // 8.3
                    timer::override_clk(false);
                } else if (f_gen_state == 17) { // 16.7
                    timer::override_clk(true);
                } else if (f_gen_state == 25) {
                    timer::override_clk(false);
                } else if (f_gen_state == 33) { // 33.3
                    timer::override_clk(true);
                } else if (f_gen_state == 42) { // 41.6
                    timer::override_clk(false);
                } else if (f_gen_state >= 50) {
                    timer::override_clk(true);
                    f_gen_state = 0;
                }
            }
            overriding_clk = true;

            // Disable the sychroscope LEDs.
            gpio::synchro_enable = false;

            break;
        }
    }

    // Reset the grid period timer, so we know when the timer logic updates it
    // again.
    timer::grid_period = 0;

}

} // namespace synchro
