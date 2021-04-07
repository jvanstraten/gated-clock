#include <Arduino.h>
#include "led.hpp"
#include "timer.hpp"
#include "gpio.hpp"

/**
 * Initialization function called by Arduino's main().
 */
void setup() {
    Serial.begin(115200);
    pinMode(7, INPUT);    // GPS RX
    pinMode(8, OUTPUT);   // GPS TX
    digitalWrite(8, HIGH);
    pinMode(22, INPUT);   // power Imon
    pinMode(23, INPUT);   // power good
    led::setup();
    gpio::setup();
    timer::setup();
}

int cycle_count = 0;
uint32_t cycle_accum = 0;
volatile uint32_t ticks = 0;

/**
 * Main loop, called by Arduino's main().
 */
void loop() {
    // put your main code here, to run repeatedly:
    unsigned long t1 = micros();
    gpio::update();
    led::update();
    unsigned long t2 = micros();
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
            Serial.printf("ticks: %u\n", ticks);
            Serial.printf("update micros: %lu\n", t2 - t1);
            Serial.printf("gpio exp: %04X\n", gpio::mcp_gpio_in);
            cycle_accum = 0;
            cycle_count = 0;
        }
        timer::grid_period = 0;
    }
    delay(4);
}

/**
 * 1 kHz tick, called from a low-priority timer interrupt (from timer.cpp).
 */
void tick() {
    ticks++;
}
