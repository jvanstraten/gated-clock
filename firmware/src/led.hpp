#include <inttypes.h>

#pragma once

/**
 * TLC6C5748 LED controller namespace.
 */
namespace led {

// Pin number definitions.
static const int PIN_SIN  =  0;
static const int PIN_SOUT =  1;
static const int PIN_LAT  =  6;
static const int PIN_OVER = 13;
static const int PIN_SCLK = 20;

/**
 * A single RGB channel of a TLC6C5748.
 */
struct Channel {

    /**
     * PWM-based brightness configuration, 0..65535.
     */
    uint16_t pwm_r;
    uint16_t pwm_g;
    uint16_t pwm_b;

    /**
     * Analog brightness configuration, ranges from 0..127 for 25..100%.
     */
    uint8_t dc_r;
    uint8_t dc_g;
    uint8_t dc_b;

    /**
     * Whether to enable this segment when display override is active. That is,
     * PWM is overridden to zero when display_override is set and this flag is
     * cleared.
     */
    bool enable;

    /**
     * LED failure detection. When a LED is turned off by discrete logic, it
     * reports as open.
     */
    bool open_r;
    bool open_g;
    bool open_b;
    bool short_r;
    bool short_g;
    bool short_b;

};

/**
 * State data structure for a complete TLC6C5748.
 */
struct Controller {

    /**
     * Channel configuration.
     */
    Channel ch[16];

    /**
     * Maximum current, 0..7. Design point is 1.
     */
    uint8_t mc_r;
    uint8_t mc_g;
    uint8_t mc_b;

    /**
     * Brightness control for a complete color group, essentially multiplied
     * with MC, ranges from 0..127 for 10..100%.
     */
    uint8_t bc_r;
    uint8_t bc_g;
    uint8_t bc_b;

    /**
     * When set, Automatically repeats the 488Hz grayscale cycle, instead of
     * turning the LEDs off after a single cycle.
     */
    bool dsprpt;

    /**
     * When latched, resets the grayscale timing.
     */
    bool tmgrst;

    /**
     * When set, brightness latch update is postponed to the next 488Hz
     * grayscale cycle.
     */
    bool rfresh;

    /**
     * When set, enables enhanced-spectrum PWM, raising it to about 60kHz.
     * Prevents audible whine.
     */
    bool espwm;

    /**
     * Controls whether LEDs are considered open at 70% or 90% Vcc.
     */
    bool lsdvlt;

};

/**
 * LED controller configuration structures.
 */
extern Controller config[3];

/**
 * Whether to enable the display override signal.
 */
extern bool display_override;

/**
 * Sets up pins related to LED control.
 */
void setup();

/**
 * Updates the above LED config structure. This takes about 18ms when there
 * are no interrupts in between.
 */
void update();

} // namespace led
