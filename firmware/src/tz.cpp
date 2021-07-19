#include "tz.hpp"

#include <WProgram.h>
#include <EEPROM.h>
#include "clk.hpp"
#include "gps.hpp"

#include "timezones.inc"

/**
 * Timezone/auto-DST/GPS synchronization logic.
 */
namespace tz {

/**
 * Number of locations in the timezone dataset.
 */
static uint16_t num_locs;

/**
 * Current location code, or 0 to disable system.
 */
static uint16_t location_code;

/**
 * DST mode. 0 for DST off (entries with DST flag are ignored), 1 for DST on
 * (entries without DST flag are ignored), 2 for DST auto (all offset entries
 * are considered).
 */
static uint8_t dst_mode;

/**
 * Pointer to the current offset record in the timezone table.
 */
static const uint32_t *offset_record;

/**
 * Returns the number of timezone locations available.
 */
uint16_t num_locations() {
    return num_locs;
}

/**
 * Sets the current timezone location and DST mode. Said mode can be 0 for
 * DST off, 1 for DST on, or 2 for DST auto. The location can be between 0
 * and num_locations() inclusive, where 0 disables automation.
 */
void set_location(uint16_t loc, uint8_t dst) {

    // No-op when nothing changes.
    if (loc == location_code && dst == dst_mode) {
        return;
    }

    // Set the new configuration.
    location_code = loc;
    dst_mode = dst;

    // Look for the first record in the timezone table that corresponds with
    // the current location code. Seeking to the appropriate offset happens
    // in update(), as the offset can change at any time due to its dependence
    // on UTC time.
    offset_record = TIMEZONES;
    while (--loc) {
        if (!*offset_record & 1) break;
        while ((*++offset_record >> 9));
    }

}

/**
 * Initializes the timezone system.
 */
void setup() {

    // Compute the number of locations.
    const uint32_t *ptr = TIMEZONES;
    num_locs = 0;
    while (*ptr & 1) {
        num_locs++;
        while ((*++ptr >> 9));
    }

    // Ensure validity of our variables by explicitly disabling ourselves.
    set_location(0, 0);

}

/**
 * Updates the timezone system. If the time in the clock circuitry is invalid,
 * we have GPS, and a location code is configured, this sets the time. Also,
 * when the computed timezone offset changes, the time in the clock circuitry
 * is invalidated (thus triggering an update).
 */
void update() {

    // Seek forward in our offset records if needed based on the record start
    // times.
    if (gps::year >= 2000 && gps::year <= 2127) {
        const uint32_t *ptr = offset_record;
        const uint32_t compressed_time =
            (((uint32_t)(gps::year - 2000) & 0x7F) << 25) |
            (((uint32_t)(gps::month - 1) & 0x0F) << 21) |
            (((uint32_t)(gps::day - 1) & 0x1F) << 16) |
            (((uint32_t)gps::hours & 0x1F) << 11) |
            (((uint32_t)(gps::minutes / 15) & 0x03) << 9);
        while (*++ptr >> 9) {

            // Seek past records that don't have the DST value we're looking for.
            if ((dst_mode == 0 && (*ptr & 2)) || (dst_mode == 1 && !(*ptr & 2))) {
                continue;
            }

            // If the start time for this record is in the future, stop
            // searching; the previous record is then the valid one.
            if ((*ptr & 0xFFFFFE00) > compressed_time) {
                break;
            }

            // This record starts in the past and matches our DST mode. So
            // update the current record.
            offset_record = ptr;

        }
    }

    // Detect offset changes, and disable the time if there was a change.
    static const uint32_t *prev_offset_record = nullptr;
    if (prev_offset_record != offset_record) {
        if (location_code) {
            clk::valid = false;
        }
        prev_offset_record = offset_record;
    }

    // Set the time if the current time is invalid, we have a valid UTC time
    // via GPS, and we're configured to set the time automatically.
    if (!clk::valid && gps::valid && location_code && (*offset_record & 1)) {
        static uint16_t prev = gps::milliseconds;
        if (gps::milliseconds < prev) {

            // Read timezone offset from UTC.
            uint8_t m = ((*offset_record >> 2) & 3) * 15;
            int8_t h = (*offset_record >> 4) & 0x1F;
            if (h & 0x10) h -= 0x20;

            // Add UTC time to it.
            m += gps::minutes;
            if (m >= 60) {
                m -= 60;
                h++;
            }
            h += gps::hours;
            while (h < 0) h += 24;
            while (h >= 24) h -= 24;

            // Configure the clock.
            clk::configure(h, m, gps::seconds);

        }
    }

}

} // namespace tz
