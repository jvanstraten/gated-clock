#include <inttypes.h>

#pragma once

/**
 * FTM2 input capture and repetitive tick interrupt logic.
 */
namespace timer {

// Input capture pin definitions. NOTE: do not change; fixed to timer channels.
static const int PIN_GRID_F     = 3;
static const int PIN_GPS_PPS    = 4;

/**
 * Detected grid cycle period in 48MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
extern volatile uint32_t grid_period;

/**
 * Detected GPS 1PPs period in 48MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
extern volatile uint32_t gps_period;

/**
 * Configures the timer logic.
 */
void setup();

} // namespace timer

/**
 * Declaration for the tick callback function, defined in main().
 */
extern void tick();
