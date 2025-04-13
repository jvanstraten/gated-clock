

// the current illuminance, stored in 10.6 fixed point
static uint16_t illuminance = 0;

// 100 lux, in 10.6 fixed point.
#define MAX_DIMMING_ILLUMINANCE_FP10_6 6400


/**
 * Scales the given brightness in `max_brightness` depending on the current illuminance.
 * If the current illuminance is larger or equal to `max_illuminance`, it is set to `max_brightness`
 * If it is between `max_illuminance` and `min_illuminance`, it is scaled as
 * brightness = `max_brightness` * (current / `max_illuminance`)
 * The return value is clamped to `min_brightness`.
 * illuminance values are expected in lux, formatted as 10.6 unsigned fixed point.
 */
uint16_t dimmed_brightness_fp(uint16_t max_brightness, uint16_t min_brightness, uint16_t max_illuminance) {
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

#define MAX_ADC_SAMPLES 4096

#define LDR_LOOKUP_TABLE_LENGTH 28

// lookup table, of 10.6 fixed point normalized adc samples to 10.6 fixed point illuminance
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

// convert an ADC reading from the LDR circuit to an illuminance measurement.
// adc_samples is in units of samples (from 0 to `max_samples` - 1)
// output is in 10.6 fixed point, satured at the top.
uint16_t estimate_illuminance_fp(uint32_t samples, uint32_t max_samples) {
    // if samples is 0, this means it's very bright.
    if (adc_samples == 0) {
        return 0xFFFF;
    }

    // calculate (SAMPLE_COUNT - samples) / samples, in 26.6 fixed point
    uint32_t normalized_samples = ((max_samples - adc_samples) << 6) / adc_samples;

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

#define RESISTANCE_AT_10_LUX 14.0e3f

#define PULLUP_RESISTANCE 220.0e3f

#define GAMMA 0.7f

// the same thing, but floating point because the new hardware does support that
float estimate_illuminance(uint32_t adc_samples, uint32_t max_samples) {
    if (adc_samples == 0) {
        return 100000.0f;
    }

    float normalized_samples = ((float)(max_samples - samples)) / (float)adc_samples;
    float resistance = normalized_samples * PULLUP_RESISTANCE;
    return 10.0f * pow(RESISTANCE_AT_10_LUX / resistance, 1.0f / GAMMA);
}

// calculate ambient light level adjusted brightness from the given maximum and minimum brightness
// brightness is linearly dimmed with ambient illuminance from max_brightness to min_brightness,
// when the ambient illuminance drops below max_illuminance.
float dimmed_brightness(float max_brightness, float min_brightness, float max_illuminance) {
    float clamped_illuminance = (float)illuminance;
    if (clamped_illuminance > max_illuminance) {
        clamped_illuminance = max_illuminance;
    }

    float interpolated_brightness = (max_brightness * clamped_illuminance) / max_illuminance;
    if (interpolated_brightness < min_brightness) {
        interpolated_brightness = min_brightness;
    }
    return interpolated_brightness;
}
