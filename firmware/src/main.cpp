#include <Arduino.h>
#include "pwr.hpp"
#include "clk.hpp"
#include "led.hpp"
#include "gps.hpp"
#include "gpio.hpp"
#include "timer.hpp"
#include "sine.hpp"
#include "synchro.hpp"
#include "ldr.hpp"
#include "ui.hpp"
#include "tz.hpp"

/**
 * Initialization function called by Arduino's main().
 */
void setup() {
    Serial.begin(115200);
    pwr::setup();
    clk::setup();
    led::setup();
    gps::setup();
    gpio::setup();
    timer::setup();
    ldr::setup();
    tz::setup();
    ui::setup();
}

/**
 * Main loop, called by Arduino's main().
 */
void loop() {

    // Update everything.
    unsigned long t1 = micros();
    pwr::update();
    clk::update();
    led::update();
    gps::update();
    synchro::update();
    gpio::update();
    ldr::update();
    tz::update();
    ui::update();
    unsigned long t2 = micros();

    // Write debug output via USB serial if enabled.
    static bool debugging = false;
    if (Serial.available()) {
        debugging = true;
    }
    if (debugging) {
        static uint32_t grid_period;
        if (timer::grid_period) {
            grid_period = timer::grid_period;
        }
        static unsigned long debug_timer;
        unsigned long now = millis();
        if (now - debug_timer > 1000) {
            int32_t f_mhz = ((int64_t)48000000 * 1000 / grid_period);
            Serial.printf("update micros: %lu\n", t2 - t1);
            Serial.printf("grid: %d mHz\n", f_mhz);
            Serial.printf("gpio exp: %04X\n", gpio::mcp_gpio_in);
            if (gps::valid) {
                Serial.printf(
                    "gps time: %04d-%02d-%02d %02d:%02d:%02d.%04d\n",
                    gps::year, gps::month, gps::day,
                    gps::hours, gps::minutes, gps::seconds, gps::milliseconds
                );
            } else {
                Serial.printf("gps time: no fix\n");
            }
            Serial.printf("gps signal: %d\n", gps::signal_strength);
            if (led::displayed_time_valid) {
                Serial.printf(
                    "displayed time: %02d:%02d:%02d\n",
                    led::displayed_hours, led::displayed_minutes, led::displayed_seconds
                );
            } else {
                Serial.printf("displayed time: unknown\n");
            }
            Serial.printf("pgood: %d\n", digitalRead(23));
            Serial.printf("current: %d mA\n", pwr::current);
            Serial.printf("LDR: %d\n", ldr::brightness);
            Serial.println("");
            debug_timer = now;
        }
    }

}
