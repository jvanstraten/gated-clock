#include <inttypes.h>

#pragma once

/**
 * Power management namespace.
 */
namespace pwr {

// Pin number definitions.
static const int PIN_PGOOD  = 23;
static const int PIN_IMON   = 22;
static const int ADC_IMON   =  8;

/**
 * The current approximate current consumption in mA.
 */
extern uint16_t current;

/**
 * Nonzero means power is bad, zero means power is good.
 */
extern uint16_t power_bad;

/**
 * Sets up pins related to power management.
 */
void setup();

/**
 * Updates the power management logic.
 */
void update();

} // namespace pwr
