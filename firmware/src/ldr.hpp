#include <inttypes.h>

#pragma once

/**
 * LDR-based display brightness namespace.
 */
namespace ldr {

// Pin number definitions.
static const int PIN_LDR    = 24;
static const int ADC_LDR    = 10;

/**
 * Sets up pins related to the LDR.
 */
void setup();

/**
 * Updates the LDR readout logic.
 */
void update();

/**
 * Scale the brightness given in `max_brightness` linearly with the current illuminance.
 * At `max_illuminance` or above the brightness matches `max_brightness`.
 * The return value is clamped to `min_brightness`.
 */
uint16_t dimmed_brightness(uint16_t max_brightness, uint16_t min_brightness, uint16_t max_illuminance);

/**
 * Debug data: return the current ADC value in samples
 */
uint16_t debug_adc_value();

/**
 * Debug data: current illuminance in 10.6 fixed point
 */
uint16_t debug_illuminance();

} // namespace ldr
