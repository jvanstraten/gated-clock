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
}

void update() {
    pwr::update();
    clk::update();
    led::update();
    gps::update();
    synchro::update();
    gpio::update();
    ldr::update();
}

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

    if (!clk::valid && gps::valid) {
        static uint16_t prev = gps::milliseconds;
        if (gps::milliseconds < prev) {
            clk::configure((gps::hours + 2) % 24, gps::minutes, gps::seconds);
        }
    }

    if (gpio::event != gpio::Event::NONE) {
        if (gpio::event == gpio::Event::RESET) {
            clk::valid = false;
        }
        Serial.printf("Event: %d\n", (int)gpio::event);
        gpio::event = gpio::Event::NONE;
    }

    /*led::set_text("888888");
    led::set_color(ldr::brightness * 64, 0, ldr::brightness*32, 3276, 3276);*/

    /*auto x = (millis() / 200) % 10;
    if (x < 1) {
        led::set_text("888888");
        led::set_color(ldr::brightness*4, ldr::brightness*4, ldr::brightness*4);
    } else if (x < 4) {
        //led::set_text(nullptr);
        led::set_color(ldr::brightness*64, 0, 0);
    } else if (x < 7) {
        //led::set_text(nullptr);
        led::set_color(0, ldr::brightness*64, 0);
    } else {
        //led::set_text(nullptr);
        led::set_color(0, 0, ldr::brightness*64);
    }*/

}
