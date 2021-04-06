#include <Arduino.h>
#include "led.hpp"
#include "timer.hpp"

void setup() {
    Serial.begin(115200);
    pinMode(2, INPUT);    // minutes Isw
    pinMode(5, OUTPUT);   // minutes Ien
    digitalWrite(5, HIGH);
    pinMode(7, INPUT);    // GPS RX
    pinMode(8, OUTPUT);   // GPS TX
    digitalWrite(8, HIGH);
    pinMode(9, OUTPUT);   // minutes Inc
    digitalWrite(9, HIGH);
    pinMode(10, OUTPUT);  // I/O CS
    digitalWrite(10, HIGH);
    pinMode(11, OUTPUT);  // I/O MOSI
    digitalWrite(11, LOW);
    pinMode(12, INPUT);   // I/O MISO
    pinMode(14, OUTPUT);  // I/O SCK
    digitalWrite(14, LOW);
    pinMode(15, INPUT);   // I/O IRQ
    pinMode(16, OUTPUT);  // synchroscope PWM A
    digitalWrite(16, LOW);
    pinMode(17, OUTPUT);  // synchroscope PWM B
    digitalWrite(17, LOW);
    pinMode(18, OUTPUT);  // hours Inc
    digitalWrite(18, HIGH);
    pinMode(19, INPUT);   // hours Isw
    pinMode(20, OUTPUT);  // LED driver SCLK
    pinMode(21, OUTPUT);  // hours Ien
    digitalWrite(21, HIGH);
    pinMode(22, INPUT);   // power Imon
    pinMode(23, INPUT);   // power good
    pinMode(26, OUTPUT);  // minutes/hours Ren
    digitalWrite(26, HIGH);
    led::setup();
    delay(2000);
    timer::setup();
}

int cycle_count = 0;
uint32_t cycle_accum = 0;

void loop() {
    // put your main code here, to run repeatedly:
//     unsigned long x = micros();
    led::update();
//     unsigned long y = micros();
//     Serial.printf("micros: %lu\n", y - x);
    if (timer::gps_period & timer::grid_period) {
        cycle_accum += timer::grid_period;
        cycle_count++;
        if (cycle_count == 50) {
            Serial.printf("grid: %u mHz\n", (uint64_t)timer::gps_period * 50000 / cycle_accum);
            cycle_accum = 0;
            cycle_count = 0;
        }
        timer::grid_period = 0;
    }
    delay(4);
}
