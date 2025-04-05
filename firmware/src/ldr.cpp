#include "ldr.hpp"
#include <WProgram.h>

/**
 * LDR-based display brightness namespace.
 */
namespace ldr {

/**
 * The current illuminance, stored in 10.6 fixed point
 */
uint16_t illuminance = 0;

/**
 * Sets up pins related to the LDR.
 */
void setup() {
    pinMode(PIN_LDR, INPUT);
    analogReadRes(12);
}

/**
 * ADC sample count
 */
#define MAX_ADC_SAMPLES 4096

// lookup table, of 12.4 fixed point normalized adc samples to 10.6 fixed point illuminance
#define LDR_LOOKUP_TABLE_LENGTH 28
const uint16_t ldr_lookup_table[LDR_LOOKUP_TABLE_LENGTH] = {
    0,     0,
    21,    3,
    64,    13,
    106,   26,
    192,   60,
    448,   202,
    960,   599,
    1984,  1689,
    4032,  4652,
    8128,  12665,
    16320, 34285,
    32704, 65535,
    65472, 65535,
    65535, 65535
};

/**
 * convert an ADC reading from the LDR circuit to an illuminance measurement.
 * adc_samples is in units of samples (from 0 to `max_samples` - 1)
 * output is in 10.6 fixed point, satured at the top.
 */
uint16_t estimate_illuminance(uint32_t samples, uint32_t max_samples) {
    // if samples is 0, this means it's very bright.
    if (samples == 0) {
        return 0xFFFF;
    }

    // calculate (SAMPLE_COUNT - samples) / samples, in 26.6 fixed point
    uint32_t normalized_samples = ((max_samples - samples) << 6) / samples;

    // saturate to 10.6 fixed point
    if (normalized_samples > 0xFFFF) {
        normalized_samples = 0xFFFF;
    }

    // table lookup for normalized_samples
    size_t i;
    for (i = 2; i < LDR_LOOKUP_TABLE_LENGTH; i += 2) {
        if (normalized_samples <= ldr_lookup_table[i]) {
            break;
        }
    }

    // get the linear interpolation boundaries
    uint32_t minx = ldr_lookup_table[i - 2];
    uint32_t maxx = ldr_lookup_table[i];
    uint32_t miny = ldr_lookup_table[i - 1];
    uint32_t maxy = ldr_lookup_table[i + 1];

    // 32-bit interpolation, resulting in a 16-bit value at the end
    uint16_t interpolated = (
        maxy * (normalized_samples - minx) + 
        miny * (maxx - normalized_samples)
    ) / (maxx - minx);

    return interpolated;
}

/**
 * Scales the given brightness in `max_brightness` depending on the current illuminance.
 * If the current illuminance is larger or equal to `max_illuminance`, it is set to `max_brightness`
 * If it is between `max_illuminance` and `min_illuminance`, it is scaled as
 * brightness = `max_brightness` * (current / `max_illuminance`)
 * The return value is clamped to `min_brightness`.
 * illuminance values are expected in lux, formatted as 10.6 unsigned fixed point.
 */
uint16_t dimmed_brightness(uint16_t max_brightness, uint16_t min_brightness, uint16_t max_illuminance) {
    uint16_t clamped_illuminance = illuminance;
    if (clamped_illuminance > max_illuminance) {
        clamped_illuminance = max_illuminance;
    }

    uint16_t interpolated_brightness = (uint32_t(max_brightness) * uint32_t(clamped_illuminance)) / uint32_t(max_illuminance);
    if (interpolated_brightness < min_brightness) {
        interpolated_brightness = min_brightness;
    }
    return interpolated_brightness;
}

/**
 * Updates the LDR readout logic.
 */
void update() {

    // Read the current ADC value.
    uint32_t adc = analogRead(ADC_LDR);

    // Now filter this with a long-duration exponential filter to handle sensor noise and smoothen
    // brightness transitions.
    // We do this before converting to illuminance to ensure a more perceived linear filtering.
    // (idealy we'd filter log(illuminance) but that'd require a lot more math)
    // the time constant of this filter is about 8.2 seconds if evaluated every 2 milliseconds
    // which is the average length of the update loop.

    static int32_t filter;
    static bool first = true;
    static const uint8_t delay = 12;

    if (first) {
        filter = adc << delay;
        first = false;
    } else {
        int32_t error = (adc << delay) - filter;
        filter += (error + (1<<(delay-1))) >> delay;
    }

    // evaluate the current illuminance
    illuminance = estimate_illuminance(filter, MAX_ADC_SAMPLES << delay);
}

/**
 * Debug data: return the current ADC value in samples
 */
uint16_t debug_adc_value() {
    return analogRead(ADC_LDR);
}

/**
 * Debug data: current illuminance in 10.6 fixed point
 */
uint16_t debug_illuminance() {
    return illuminance;
}

} // namespace ldr
