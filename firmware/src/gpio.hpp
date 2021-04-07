#include <inttypes.h>

#pragma once

/**
 * Regular GPIO & MCP23S17 logic.
 */
namespace gpio {

// I/O expander pin number definitions (Arduino). NOTE: do not change, fixed
// to hardware SPI ports.
static const int PIN_EXP_CS                 = 10;
static const int PIN_EXP_MOSI               = 11;
static const int PIN_EXP_MISO               = 12;
static const int PIN_EXP_SCK                = 14;
static const int PIN_EXP_IRQ                = 15;

// Synchroscope PWM pin number definitions (Arduino).
static const int PIN_SYNCHRO_A              = 16;
static const int PIN_SYNCHRO_B              = 17;

// Synchroscope selection pin number definitions (MCP23S17).
static const uint16_t PIN_SYNCHRO_H_MASK    = 0b0100000011111000;
static const uint16_t PIN_SYNCHRO_L_MASK    = 0b0011111100000000;
static const uint16_t PIN_SYNCHRO_TAB[30]   = {
    0b0110000000100000, // 1-2
    0b0010000010100000, // 2-3
    0b0010000010010000, // 3-4
    0b0010000001010000, // 4-5
    0b0011000001001000, // 5-6
    0b0101000000001000, // 6-7
    0b0101000000100000, // 7-8
    0b0001000010100000, // 8-9
    0b0001000010010000, // 9-10
    0b0001100001010000, // 10-11
    0b0000100001001000, // 11-12
    0b0100100000001000, // 12-13
    0b0100100000100000, // 13-14
    0b0000100010100000, // 14-15
    0b0000110010010000, // 15-16
    0b0000010001010000, // 16-17
    0b0000010001001000, // 17-18
    0b0100010000001000, // 18-19
    0b0100010000100000, // 19-20
    0b0000011010100000, // 20-21
    0b0000001010010000, // 21-22
    0b0000001001010000, // 22-23
    0b0000001001001000, // 23-24
    0b0100001000001000, // 24-25
    0b0100001100100000, // 25-26
    0b0000000110100000, // 26-27
    0b0000000110010000, // 27-28
    0b0000000101010000, // 28-29
    0b0000000101001000, // 29-30
    0b0110000100001000  // 30-1
};

// Microcontroller button pin number definitions (MCP23S17).
static const int PIN_BTN_MODE               = 0;
static const int PIN_BTN_DOWN               = 1;
static const int PIN_BTN_UP                 = 2;
static const uint16_t PIN_BTN_MASK          = 0b0000000000000111;

// Clock configuration pin number definitions (Arduino).
static const int PIN_MIN_ISW                = 2;
static const int PIN_MIN_IEN                = 5;
static const int PIN_MIN_INC                = 9;
static const int PIN_HR_ISW                 = 19;
static const int PIN_HR_IEN                 = 21;
static const int PIN_HR_INC                 = 18;
static const int PIN_REN                    = 26;

// Clock reset pin number definition (MCP23S17).
static const int PIN_RESET                  = 15;
static const uint16_t PIN_RESET_MASK        = 0b1000000000000000;

/**
 * The latest value read from the I/O expander's GPIO port.
 */
extern uint16_t mcp_gpio_in;

/**
 * The value to write to the I/O expander's GPIO port.
 */
extern uint16_t mcp_gpio_out;

/**
 * The value to write to the I/O expander's IODIR register. 1 means output,
 * 0 means input (so this value is inverted w.r.t. the IODIR register; who
 * the hell makes 1 mean input?)
 */
extern uint16_t mcp_iodir;

/**
 * Synchroscope LED position. ranges from 0 to 30*256-1.
 */
extern uint16_t synchro;

/**
 * Configures the GPIO logic.
 */
void setup();

/**
 * Updates the GPIO logic.
 */
void update();

} // namespace timer
