#include <inttypes.h>

#pragma once

/**
 * Timezone/auto-DST/GPS synchronization logic.
 */
namespace tz {

/**
 * Returns the number of timezone locations available.
 */
uint16_t num_locations();

/**
 * Sets the current timezone location and DST mode. Said mode can be 0 for
 * DST off, 1 for DST on, or 2 for DST auto. The location can be between 0
 * and num_locations() inclusive, where 0 disables automation. Calling this
 * invalidates the time if the configuration changed.
 */
void set_location(uint16_t loc, uint8_t dst);

/**
 * Initializes the timezone system.
 */
void setup();

/**
 * Updates the timezone system. If the time in the clock circuitry is invalid,
 * we have GPS, and a location code is configured, this sets the time. Also,
 * when the computed timezone offset changes, the time in the clock circuitry
 * is invalidated (thus triggering an update).
 */
void update();

} // namespace tz
