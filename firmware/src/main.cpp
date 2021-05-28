#include <Arduino.h>
#include "pwr.hpp"
#include "clk.hpp"
#include "led.hpp"
#include "gps.hpp"
#include "gpio.hpp"
#include "timer.hpp"
#include "sine.hpp"

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
    //led::set_text("  LL_ ");
}

void update() {
    pwr::update();
    clk::update();
    led::update();
    gps::update();
    gpio::update();
}

int cycle_count = 0;
uint32_t cycle_accum = 0;

/**
 * Main loop, called by Arduino's main().
 */
void loop() {
    unsigned long t1 = micros();
    update();
    unsigned long t2 = micros();
    
    /*uint16_t color = millis() * 100;
    uint16_t r = sine::sine(color) + 32768;
    uint16_t g = sine::sine(color + 21845) + 32768;
    uint16_t b = sine::sine(color + 43691) + 32768;
    led::set_color(r, g >> 1, b >> 1);*/
    if (timer::grid_period) {
        if (timer::gps_period < 47000000 || timer::gps_period > 49000000) {
            timer::gps_period = 48000000;
        }
        uint32_t f_mhz = (uint64_t)timer::gps_period * 1000 / timer::grid_period;
        int32_t x = (int32_t)f_mhz - 50000;
        if (x < -1000) x = -1000;
        if (x > 1000) x = 1000;
        x += gpio::synchro;
        if (x > 30*256) x -= 30*256;
        if (x < 0) x += 30*256;
        gpio::synchro = x;

        cycle_accum += timer::grid_period;
        cycle_count++;
        if (cycle_count == 50) {
            Serial.printf("grid: %u mHz\n", (uint64_t)timer::gps_period * 50000 / cycle_accum);
            Serial.printf("update micros: %lu\n", t2 - t1);
            Serial.printf("gpio exp: %04X\n", gpio::mcp_gpio_in);
            if (gps::valid) {
                Serial.printf(
                    "gps time: %04d-%02d-%02d %02d:%02d:%02d\n",
                    gps::year, gps::month, gps::day,
                    gps::hours, gps::minutes, gps::seconds
                );
            } else {
                Serial.printf("gps time: no fix\n");
            }
            if (led::displayed_time_valid) {
                Serial.printf(
                    "displayed time: %02d:%02d:%02d\n",
                    led::displayed_hours, led::displayed_minutes, led::displayed_seconds
                );
            } else {
                Serial.printf("displayed time: unknown\n");
            }
            Serial.printf("pgood: %d\n", digitalRead(23));
            Serial.printf("current: %d mA\n", analogRead(8) * 1709 / 1000);
            Serial.println("");
            cycle_accum = 0;
            cycle_count = 0;
        }
        timer::grid_period = 0;
    }
    if (!clk::valid && gps::valid) {
        clk::configure((gps::hours + 2) % 24, gps::minutes, gps::seconds);
    }
}
