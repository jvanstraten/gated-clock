#include "clk.hpp"

#include <WProgram.h>
#include "gpio.hpp"
#include "timer.hpp"

/**
 * Clock control namespace.
 */
namespace clk {

/**
 * Whether the auto-increment logic is enabled.
 */
bool enable_auto_inc;

/**
 * Whether the clock is considered to be valid. This is cleared when the grid
 * frequency is missing and at startup, and set when the user increments the
 * time or the time was configured automatically.
 */
volatile bool valid;

/**
 * Overrides the clock's reset signal to the given state.
 */
void override_reset(bool state) {
    gpio::mcp_iodir |= gpio::PIN_RESET_MASK;
    if (state) {
        gpio::mcp_gpio_out |= gpio::PIN_RESET_MASK;
    } else {
        gpio::mcp_gpio_out &= ~gpio::PIN_RESET_MASK;
    }
    gpio::update();
}

/**
 * Releases the clock's reset signal, giving control to the reset button.
 */
void release_reset() {
    gpio::mcp_iodir &= ~gpio::PIN_RESET_MASK;
    gpio::update();
}

/**
 * Configures the time.
 */
void configure(uint8_t h, uint8_t m, uint8_t s) {

    // Reset.
    timer::override_clk(LOW);
    override_reset(LOW);
    digitalWrite(gpio::PIN_REN, LOW);
    digitalWrite(gpio::PIN_MIN_IEN, LOW);
    digitalWrite(gpio::PIN_MIN_INC, HIGH);
    digitalWrite(gpio::PIN_HR_IEN, LOW);
    digitalWrite(gpio::PIN_HR_INC, HIGH);

    // Release reset. Clock should be at 0:00:00.
    override_reset(HIGH);

    // Increment the individual time components as requested.
    while (h || m || s) {
        if (h) {
            digitalWrite(gpio::PIN_HR_INC, LOW);
            h--;
        }
        if (m) {
            digitalWrite(gpio::PIN_MIN_INC, LOW);
            m--;
        }
        if (s) {
            uint8_t c = timer::grid_frequency();
            while (c--) {
                timer::override_clk(true);
                delayMicroseconds(2);
                timer::override_clk(false);
                delayMicroseconds(2);
            }
            s--;
        }
        digitalWrite(gpio::PIN_MIN_INC, HIGH);
        digitalWrite(gpio::PIN_HR_INC, HIGH);
        delayMicroseconds(2);
    }

    // Release control.
    digitalWrite(gpio::PIN_REN, HIGH);
    digitalWrite(gpio::PIN_MIN_IEN, HIGH);
    digitalWrite(gpio::PIN_HR_IEN, HIGH);
    timer::release_clk();
    release_reset();

    // Assert that the time is now valid.
    valid = true;
}

/**
 * Sends the given amount of clock pulses to the clock circuitry, while
 * disabling carry to minutes.
 */
static void send_clk_pulses(uint16_t count) {
    digitalWrite(gpio::PIN_REN, LOW);
    while (count--) {
        timer::override_clk(true);
        delayMicroseconds(2);
        timer::override_clk(false);
        delayMicroseconds(2);
    }
    timer::release_clk();
    delayMicroseconds(2);
    digitalWrite(gpio::PIN_REN, HIGH);
}

/**
 * Increments seconds value without carry.
 */
void increment() {
    send_clk_pulses(timer::grid_frequency());
}

/**
 * Decrements seconds value without carry.
 */
void decrement() {
    send_clk_pulses(timer::grid_frequency() * 59);
}

/**
 * Initializes the clock control logic.
 */
void setup() {
    enable_auto_inc = true;
    valid = false;
}

/**
 * Updates the clock control logic.
 */
void update() {
    uint32_t now = millis();

    // Auto-increment logic for minutes configuration.
    static uint32_t min_inc_start;
    if (digitalRead(gpio::PIN_MIN_ISW)) {
        valid = true;
        if (enable_auto_inc) {
            uint32_t d = now - min_inc_start;
            if (d < 1024) {
                digitalWrite(gpio::PIN_MIN_IEN, LOW);
            } else {
                digitalWrite(gpio::PIN_MIN_IEN, (d & 64) ? HIGH : LOW);
            }
        } else {
            digitalWrite(gpio::PIN_MIN_IEN, HIGH);
        }
    } else {
        min_inc_start = now;
        digitalWrite(gpio::PIN_MIN_IEN, HIGH);
    }

    // Auto-increment logic for hours configuration. Yes, I know I'm repeating
    // myself.
    static uint32_t hr_inc_start;
    if (digitalRead(gpio::PIN_HR_ISW)) {
        valid = true;
        if (enable_auto_inc) {
            uint32_t d = now - hr_inc_start;
            if (d < 1024) {
                digitalWrite(gpio::PIN_HR_IEN, LOW);
            } else {
                digitalWrite(gpio::PIN_HR_IEN, (d & 64) ? HIGH : LOW);
            }
        } else {
            digitalWrite(gpio::PIN_HR_IEN, HIGH);
        }
    } else {
        hr_inc_start = now;
        digitalWrite(gpio::PIN_HR_IEN, HIGH);
    }

}

} // namespace clk
