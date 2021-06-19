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
 * consecutive edges are detected, cleared when processed by the syncroscope
 * logic.
 */
extern volatile uint32_t grid_period;

/**
 * Detected GPS 1PPs period in 48MHz ticks. Set by an ISR when two
 * consecutive edges are detected.
 */
extern volatile uint32_t gps_period;

/**
 * The value of micros() when the PPS input last rose.
 */
extern volatile unsigned long gps_pulse_micros;

/**
 * The number of PPS input rising edges detected, incremented when gps_period
 * and gps_pulse_micros are updated.
 */
extern volatile uint32_t gps_edges;

/**
 * Overrides the clock's clk signal to the given state.
 */
void override_clk(bool state);

/**
 * Releases the clock's clk signal, giving control to the power grid.
 */
void release_clk();

/**
 * Returns the detected grid frequency (either 50 or 60Hz).
 */
uint8_t grid_frequency();

/**
 * Configures the timer logic.
 */
void setup();

} // namespace timer
