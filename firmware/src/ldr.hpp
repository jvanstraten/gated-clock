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
 * The current ambient brightness, 0..1023.
 */
extern uint16_t brightness;

/**
 * Sets up pins related to the LDR.
 */
void setup();

/**
 * Updates the LDR readout logic.
 */
void update();

} // namespace ldr
