#include "gps.hpp"
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
 * GPS time validity; nonzero means valid.
 */
uint16_t valid;

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
    valid = 0;
    fix_valid = 0;
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
                valid = 1100;
            }
        }
    }
}

/**
 * Updates the GPS readout logic.
 */
void update() {

    // Update time record validity.
    uint32_t now = millis();
    static uint32_t then;
    uint32_t delta = now - then;
    then = now;
    while (delta--) {
        if (valid) valid--;
        if (fix_valid) fix_valid--;
    }

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
