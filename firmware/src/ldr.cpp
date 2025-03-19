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

/**
 * The ambient illuminance at which we start dimming. 
 * 100 lux, in 10.6 fixed point.
 */
#define MAX_DIMMING_ILLUMINANCE_FP10_6 6400

// lookup table, of 12.4 fixed point normalized adc samples to 10.6 fixed point illuminance
#define LDR_LOOKUP_TABLE_LENGTH 30
const uint16_t ldr_lookup_table[LDR_LOOKUP_TABLE_LENGTH] = {
    0,     0,
    5,     3,
    16,    14,
    26,    29,
    48,    66,
    112,   222,
    240,   661,
    496,   1864,
    1008,  5134,
    2032,  13977,
    4080,  37836,
    8176,  65535,
    16368, 65535,
    32752, 65535,
    65535, 65535
};

/**
 * convert an ADC reading from the LDR circuit to an illuminance measurement.
 * adc_samples is in units of samples (from 0 to MAX_ADC_SAMPLES)
 * output is in 10.6 fixed point, satured at the top.
 */
uint16_t estimate_illuminance(uint16_t adc_samples) {
    // if samples is 0, this means it's very bright.
    if (adc_samples == 0) {
        return 0xFFFF;
    }

    // calculate (SAMPLE_COUNT - samples) / samples, in 12.4 fixed point
    uint16_t normalized_samples = ((MAX_ADC_SAMPLES - adc_samples) << 4) / adc_samples;

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
        maxy * ((uint32_t)normalized_samples - minx) + 
        miny * (maxx - (uint32_t)normalized_samples)
    ) / (maxx - minx);

    return interpolated;
}
/**
 * calculate ambient light level adjusted brightness from the given maximum and minimum brightness
 * brightness is linearly dimmed with ambient illuminance from max_brightness to min_brightness,
 * when the ambient illuminance drops below MAX_DIMMING_ILLUMINANCE.
 */
uint16_t dimmed_brightness(uint16_t max_brightness, uint16_t min_brightness) {
    uint16_t clamped_illuminance = illuminance;
    if (clamped_illuminance > MAX_DIMMING_ILLUMINANCE_FP10_6) {
        clamped_illuminance = MAX_DIMMING_ILLUMINANCE_FP10_6;
    }

    uint16_t diff_brightness = max_brightness - min_brightness;
    uint16_t interpolated_brightness = ((uint32_t)diff_brightness * (uint32_t)clamped_illuminance) / MAX_DIMMING_ILLUMINANCE_FP10_6 + min_brightness;
    return interpolated_brightness;
}

/**
 * Updates the LDR readout logic.
 */
void update() {

    // Read the current ADC value.
    uint32_t adc = analogRead(ADC_LDR);

    // Filter it a lot.
    static uint8_t counter;
    static uint32_t accum;
    accum += adc;
    if (counter++ < 64) {
        return;
    }

    // evaluate the current illuminance
    int32_t current_illuminance = estimate_illuminance(accum >> 6);

    // Reset the initial box filter.
    accum = 0;
    counter = 0;

    // current_luminance is in 10.6 fp format, lower values being brighter. Now filter with
    // an IIR to smoothen brightness transitions.
    static int32_t filter;
    static bool first = true;
    static const uint8_t delay = 6;
    current_illuminance <<= delay;

    if (first) {
        filter = current_illuminance;
        first = false;
    }
    int32_t error = current_illuminance - filter;
    filter += (error + (1<<(delay-1))) >> delay;

    // convert back to 10.6 fp and write it to the global
    illuminance = (filter + (1 << (delay - 1))) >> delay;
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
