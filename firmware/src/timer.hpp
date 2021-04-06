#include <inttypes.h>

#pragma once

/**
 * FTM2 input capture and repetitive tick interrupt logic.
 */
namespace timer {

/**
 * Detected grid cycle period in 24MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
extern volatile uint32_t grid_period;

/**
 * Detected GPS 1PPs period in 24MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
extern volatile uint32_t gps_period;

/**
 * Configures the timer logic.
 */
void setup();

} // namespace led
