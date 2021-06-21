#include "ldr.hpp"
#include <WProgram.h>

/**
 * LDR-based display brightness namespace.
 */
namespace ldr {

/**
 * The current ambient brightness, 0..1023.
 */
uint16_t brightness;

/**
 * Sets up pins related to the LDR.
 */
void setup() {
    pinMode(PIN_LDR, INPUT);
    analogReadRes(12);
}

/**
 * Updates the LDR readout logic.
 */
void update() {

    // Read the current ADC value.
    int32_t adc = analogRead(ADC_LDR);

    // Filter it a lot.
    static uint8_t counter;
    static int32_t accum;
    accum += adc;
    if (counter++ < 64) {
        return;
    }

    // Value 0..262144 (18 bits), lower values being brighter. Now filter with
    // an IIR to smoothen brightness transitions.
    static int32_t filter;
    static bool first = true;
    if (first) {
        filter = accum;
        first = false;
    }
    int32_t error = accum - filter;
    static const uint32_t delay = 6;
    filter += (error + (1<<(delay-1))) >> delay;

    // Reset the initial box filter.
    accum = 0;
    counter = 0;

    // Compute brightness.
    brightness = 1023 - (filter >> 8);
    if (brightness > 300) {
        brightness -= 200;
    } else {
        brightness = 100;
    }

}

} // namespace ldr
