#include <inttypes.h>

#pragma once

/**
 * Clock control namespace.
 */
namespace clk {

/**
 * Whether the auto-increment logic is enabled.
 */
extern bool enable_auto_inc;

/**
 * Whether the clock is considered to be valid. This is cleared when the grid
 * frequency is missing and at startup, and set when the user increments the
 * time or the time was configured automatically.
 */
extern volatile bool valid;

/**
 * Overrides the clock's reset signal to the given state.
 */
void override_reset(bool state);

/**
 * Releases the clock's reset signal, giving control to the reset button.
 */
void release_reset();

/**
 * Configures the time.
 */
void configure(uint8_t h, uint8_t m, uint8_t s);

/**
 * Initializes the clock control logic.
 */
void setup();

/**
 * Updates the clock control logic.
 */
void update();

} // namespace clk
