#include "pwr.hpp"
#include <WProgram.h>

/**
 * Power management namespace.
 */
namespace pwr {

/**
 * The current approximate current consumption in mA.
 */
uint16_t current;

/**
 * Nonzero means power is bad, zero means power is good.
 */
uint16_t power_bad;

/**
 * Sets up pins related to power management.
 */
void setup() {
    pinMode(PIN_IMON, INPUT);
    pinMode(PIN_PGOOD, INPUT_PULLUP);
    analogReadRes(12);
    power_bad = 250;
}

/**
 * Updates the power management logic.
 */
void update() {

    // Update power_bad.
    uint32_t now = millis();
    static uint32_t then;
    uint32_t delta = now - then;
    then = now;
    while (power_bad && delta--) {
        power_bad--;
    }
    if (!digitalRead(PIN_PGOOD)) {
        power_bad = 250;
    }

    // Update current consumption.
    current = analogRead(ADC_IMON) * 1709 / 1000;

}

} // namespace pwr
