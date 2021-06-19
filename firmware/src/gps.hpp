#include <inttypes.h>

#pragma once

/**
 * GPS time readout.
 */
namespace gps {

// Pin number definitions. NOTE: do not change, fixed to hardware serial port.
static const int PIN_RX   =  7;
static const int PIN_TX   =  8;

/**
 * GPS year (UTC).
 */
extern uint16_t year;

/**
 * GPS month, 1..12 (UTC).
 */
extern uint8_t month;

/**
 * GPS day, 1..31 (UTC).
 */
extern uint8_t day;

/**
 * GPS hours in UTC.
 */
extern uint8_t hours;

/**
 * GPS minutes in UTC.
 */
extern uint8_t minutes;

/**
 * GPS seconds in UTC.
 */
extern uint8_t seconds;

/**
 * GPS milliseconds.
 */
extern int16_t milliseconds;

/**
 * GPS time validity; nonzero means valid.
 */
extern uint16_t valid;

/**
 * Sets up stuff related to GPS readout.
 */
void setup();

/**
 * Updates the GPS readout logic.
 */
void update();

} // namespace gps
