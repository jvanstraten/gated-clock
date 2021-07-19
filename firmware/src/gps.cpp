#include "gps.hpp"
#include "timer.hpp"
#include <WProgram.h>

/**
 * GPS time readout.
 */
namespace gps {

/**
 * GPS fix validity.
 */
static uint16_t fix_valid;

/**
 * GPS year (UTC).
 */
uint16_t year;

/**
 * GPS month, 1..12 (UTC).
 */
uint8_t month;

/**
 * GPS day, 1..31 (UTC).
 */
uint8_t day;

/**
 * GPS hours in UTC.
 */
uint8_t hours;

/**
 * GPS minutes in UTC.
 */
uint8_t minutes;

/**
 * GPS seconds in UTC.
 */
uint8_t seconds;

/**
 * GPS time validity down to seconds; nonzero means valid.
 */
static uint16_t seconds_valid;

/**
 * GPS milliseconds.
 */
int16_t milliseconds;

/**
 * GPS time validity down to milliseconds; nonzero means valid.
 */
uint16_t valid;

/**
 * Maximum number of entries in the GSV list.
 */
#define GSV_MAX 5

/**
 * Number of valid entries in GSV list.
 */
static uint8_t gsv_count = 0;

/**
 * SNRs of the 5 best-received satellites. Only the first gsv_count entries
 * are valid.
 */
static uint8_t gsv_data[GSV_MAX];

/**
 * Signal strength indicator. This is the sum of the SNRs in dB of the 5 best
 * satellites being tracked. SNR is max 99 per satellite, so the maximum value
 * is 495.
 */
uint16_t signal_strength = 0;

/**
 * Sets up stuff related to GPS readout.
 */
void setup() {
    pinMode(PIN_RX, INPUT);
    pinMode(PIN_TX, OUTPUT);
    digitalWrite(PIN_TX, HIGH);
    Serial3.begin(9600, SERIAL_8N1);
    Serial3.setRX(PIN_RX);
    Serial3.setTX(PIN_TX);
    fix_valid = 0;
    seconds_valid = 0;
    valid = 0;
}

/**
 * Handles a field of an NMEA sentence.
 */
static void handle_field(const char *sentence, uint8_t field, const char *value) {
    if (!strcmp(sentence + 2, "GGA")) {
        if (field == 5) {
            if (!strcmp(value, "1")) {
                fix_valid = 1100;
            } else {
                fix_valid = 0;
            }
        } else if (field == 0) {
            signal_strength = 0;
            for (uint8_t i = 0; i < gsv_count; i++) {
                signal_strength += gsv_data[i];
            }
            gsv_count = 0;
        }
    } else if (!strcmp(sentence + 2, "ZDA")) {
        if (field == 0) {
            hours   = (value[0] - '0') * 10 + (value[1] - '0');
            minutes = (value[2] - '0') * 10 + (value[3] - '0');
            seconds = (value[4] - '0') * 10 + (value[5] - '0');
        } else if (field == 1) {
            day     = (value[0] - '0') * 10 + (value[1] - '0');
        } else if (field == 2) {
            month   = (value[0] - '0') * 10 + (value[1] - '0');
        } else if (field == 3) {
            year    = (value[0] - '0') * 1000 + (value[1] - '0') * 100
                    + (value[2] - '0') * 10 + (value[3] - '0');
            if (fix_valid) {
                seconds_valid = 1100;
            }
        }
    } else if (!strcmp(sentence + 2, "GSV")) {
        if ((field == 6 || field == 10 || field == 14 || field == 18) && value[0] && value[1]) {
            uint8_t snr = (value[0] - '0') * 10 + (value[1] - '0');
            if (gsv_count < GSV_MAX) {
                gsv_data[gsv_count++] = snr;
            } else {
                uint8_t lowest_value = 100;
                uint8_t lowest_index = 0;
                for (uint8_t i = 0; i < GSV_MAX; i++) {
                    if (gsv_data[i] < lowest_value) {
                        lowest_value = gsv_data[i];
                        lowest_index = i;
                    }
                }
                if (snr > gsv_data[lowest_index]) {
                    gsv_data[lowest_index] = snr;
                }
            }
        }
    }
}

/**
 * Increments the current GPS time by the given number of milliseconds.
 */
static void increment_time(uint16_t amt = 1) {
    while (amt > 1000) {
        increment_time(1000);
        amt -= 1000;
    }
    milliseconds += amt;
    if (milliseconds >= 1000) {
        milliseconds -= 1000;
        seconds++;
        if (seconds >= 60) {
            seconds = 0;
            minutes++;
            if (minutes >= 60) {
                minutes = 0;
                hours++;
                if (hours >= 24) {
                    hours = 0;
                    day++;
                    uint8_t days = 30 + month % 2;
                    if (month == 2) {
                        if (((year % 4 == 0) && !(year % 100 == 0)) || (year % 400 == 0)) {
                            days = 29;
                        } else {
                            days = 28;
                        }
                    }
                    if (day > days) {
                        day = 1;
                        month++;
                        if (month > 12) {
                            month = 1;
                            year++;
                        }
                    }
                }
            }
        }
    }
}

/**
 * Updates the GPS readout logic.
 */
void update() {

    // Update validity counters.
    uint32_t now = millis();
    static uint32_t then;
    int32_t delta = now - then;
    then = now;
    if (valid > (uint16_t)delta) {
        valid -= (uint16_t)delta;
    } else {
        valid = 0;
    }
    if (seconds_valid > (uint16_t)delta) {
        seconds_valid -= (uint16_t)delta;
    } else {
        seconds_valid = 0;
    }
    if (fix_valid > (uint16_t)delta) {
        fix_valid -= (uint16_t)delta;
    } else {
        fix_valid = 0;
    }

    // Align the time to the PPS pulse.
    static int32_t adjust = 0;
    static uint32_t last_edges;
    if (last_edges != timer::gps_edges) {
        last_edges = timer::gps_edges;
        auto millis_passed = (micros() - timer::gps_pulse_micros) / 1000;
        adjust = (int32_t)millis_passed - (int32_t)milliseconds;
        if (adjust < -500) adjust += 1000;
        if (adjust > 500) adjust -= 1000;
        if (adjust > -5 && adjust < 5 && seconds_valid) {
            valid = 1100;
        }
    }
    if (adjust > -delta) {
        delta += adjust;
        adjust = 0;
    } else {
        adjust += delta;
        delta = 0;
    }
    increment_time(delta);

    // Update NMEA sentence parsing.
    while (Serial3.available()) {

        // Parse the next character.
        char c = Serial3.read();
        static uint8_t state = 0;
        static char sentence[6];
        static uint8_t buf_idx = 0;
        static char buf[32];
        if (c == '$') {

            // Found sentence identifier, start processing.
            state = 1;

        } else if (c == '*') {

            // Parse current field data (if any), then stop processing.
            // Checksum is ignored.
            if (buf_idx > 0 && buf_idx < 32) {
                buf[buf_idx] = 0;
                sentence[5] = 0;
                handle_field(sentence, state - 7, buf);
            }
            buf_idx = 0;
            state = 0;

        } else if (state == 0) {

            // Discard garbage and unused stuff between start of checksum and
            // start of next message.

        } else if (state < 6) {

            // Load the NMEA sentence identifier.
            sentence[state-1] = c;
            state++;

        } else if (c == ',') {

            // Parse current field data (if any), then advance to next field.
            if (buf_idx > 0 && buf_idx < 32) {
                buf[buf_idx] = 0;
                sentence[5] = 0;
                handle_field(sentence, state - 7, buf);
            }
            buf_idx = 0;
            state++;

        } else if (buf_idx < 32) {

            // Update field buffer if we're not out of room.
            buf[buf_idx++] = c;

        }

    }

}

} // namespace gps
