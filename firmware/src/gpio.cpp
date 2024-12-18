#include "gpio.hpp"

#include <WProgram.h>
#include "pwr.hpp"
#include "sine.hpp"

/**
 * Regular GPIO & MCP23S17 logic.
 */
namespace gpio {

/**
 * Starts a SPI transaction by pulling SS low.
 */
static inline void spi_start() {
    digitalWrite(PIN_EXP_CS, LOW);
}

/**
 * Synchronously transfers a byte using the SPI.
 */
static uint8_t spi_xfer(uint8_t val) {
    while (!(SPI0_S & (1ul << 5)));
    SPI0_DL = val;
    while (!(SPI0_S & (1ul << 7)));
    return SPI0_DL;
}

/**
 * Drains the receive buffer and asserts SS, returning the last byte read.
 */
static void spi_stop() {
    digitalWrite(PIN_EXP_CS, HIGH);
}

/**
 * Starts a SPI transaction to the given MCP23S17 register.
 */
static void mcp_start(bool write, uint8_t reg) {
    spi_start();
    spi_xfer(write ? 0b01001110 : 0b01001111);
    spi_xfer(reg);
}

/**
 * Synchronously writes a byte to the MCP23S17.
 */
static void mcp_write_byte(uint8_t reg, uint8_t val) {
    mcp_start(true, reg);
    spi_xfer(val);
    spi_stop();
}

/**
 * Synchronously writes two bytes to the MCP23S17.
 */
static void mcp_write_word(uint8_t reg, uint16_t val) {
    mcp_start(true, reg);
    spi_xfer(val & 0xFF);
    spi_xfer(val >> 8);
    spi_stop();
}

/**
 * Synchronously reads two bytes from the MCP23S17.
 */
static uint16_t mcp_read_word(uint8_t reg) {
    mcp_start(false, reg);
    uint16_t val = spi_xfer(0);
    val |= (uint16_t)spi_xfer(0) << 8;
    spi_stop();
    return val;
}

/**
 * The latest value read from the I/O expander's GPIO port.
 */
uint16_t mcp_gpio_in = 0;

/**
 * The value to write to the I/O expander's GPIO port.
 */
uint16_t mcp_gpio_out = 0;

/**
 * The value to write to the I/O expander's IODIR register. 1 means output,
 * 0 means input (so this value is inverted w.r.t. the IODIR register; who
 * the hell makes 1 mean input?)
 */
uint16_t mcp_iodir = 0;

/**
 * Synchroscope LED position. ranges from 0 to 30*256-1.
 */
uint16_t synchro = 0;

/**
 * Whether the synchroscope should be enabled.
 */
bool synchro_enable = false;

/**
 * Button event code for the UI logic to use. Must be cleared to NONE by the UI
 * logic.
 */
Event event = Event::NONE;

/**
 * Configures the GPIO logic.
 */
void setup() {

    // Initial I/O configuration with Arduino.
    pinMode(PIN_EXP_CS, OUTPUT);    digitalWrite(PIN_EXP_CS, HIGH);
    pinMode(PIN_EXP_MOSI, OUTPUT);  digitalWrite(PIN_EXP_MOSI, HIGH);
    pinMode(PIN_EXP_MISO, INPUT);
    pinMode(PIN_EXP_SCK, OUTPUT);   digitalWrite(PIN_EXP_SCK, HIGH);
    pinMode(PIN_EXP_IRQ, INPUT);

    analogWriteResolution(16);
    pinMode(PIN_SYNCHRO_A, OUTPUT); analogWrite(PIN_SYNCHRO_A, 65535);
    pinMode(PIN_SYNCHRO_B, OUTPUT); analogWrite(PIN_SYNCHRO_B, 65535);

    pinMode(PIN_MIN_ISW, INPUT);
    pinMode(PIN_MIN_IEN, OUTPUT);   digitalWrite(PIN_MIN_IEN, HIGH);
    pinMode(PIN_MIN_INC, OUTPUT);   digitalWrite(PIN_MIN_INC, HIGH);
    pinMode(PIN_HR_ISW, INPUT);
    pinMode(PIN_HR_IEN, OUTPUT);    digitalWrite(PIN_HR_IEN, HIGH);
    pinMode(PIN_HR_INC, OUTPUT);    digitalWrite(PIN_HR_INC, HIGH);
    pinMode(PIN_REN, OUTPUT);       digitalWrite(PIN_REN, HIGH);

    // Configure the SPI unit.
    SIM_SCGC4  |= (1ul << 22);  // enable SPI clock
    SPI0_C1     = (0ul << 7)    // disable SPI interrupt
                | (1ul << 6)    // enable SPI system
                | (0ul << 5)    // disable transmit interrupt
                | (1ul << 4)    // select SPI master mode
                | (0ul << 3)    // SPI clock polarity idle low
                | (0ul << 2)    // SPI clock phase 0
                | (0ul << 1)    // slave select pin config is don't care
                | (0ul << 0);   // MSB first
    SPI0_C2     = (0ul << 7)    // disable match interrupt
                | (0ul << 6)    // use 8-bit SPI
                | (0ul << 5)    // disable transmit DMA
                | (0ul << 4)    // disable mode-fault function, whatever that is
                | (0ul << 3)    // disable bidirectional mode
                | (0ul << 2)    // disable receive DMA
                | (0ul << 1)    // no need for low power stuff
                | (0ul << 0);   // normal SPI pin directions
    SPI0_BR     = (0ul << 4)    // disable prescaler
                | (2ul << 0);   // divide by 8

    // Connect the hardware-controlled SPI pins to the SPI unit.
    CORE_PIN11_CONFIG = PORT_PCR_MUX(2) | PORT_PCR_SRE | PORT_PCR_DSE;
    CORE_PIN12_CONFIG = PORT_PCR_MUX(2) | PORT_PCR_SRE | PORT_PCR_DSE;
    CORE_PIN14_CONFIG = PORT_PCR_MUX(2) | PORT_PCR_SRE | PORT_PCR_DSE;

    // Initialize the I/O expander.
    delay(1);
    mcp_write_byte(0x0A,        // configure IOCON
                  (0ul << 7)    // sequential registers for 16-bit access
                | (1ul << 6)    // interrupt is currently unused, but mirroring makes the most sense
                | (1ul << 5)    // enable address auto increment
                | (0ul << 3)    // don't use the address pins
                | (0ul << 2)    // interrupt is unused
                | (0ul << 1));  // interrupt is unused

    // Reset the clock.
    mcp_iodir |= PIN_RESET_MASK;
    mcp_gpio_out &= ~PIN_RESET_MASK;
    update();
    mcp_iodir &= ~PIN_RESET_MASK;

}

/**
 * Updates the GPIO logic.
 */
void update() {

    // Update synchroscope LEDs.
    mcp_gpio_out &= ~PIN_SYNCHRO_H_MASK;
    mcp_iodir &= ~PIN_SYNCHRO_L_MASK;
    uint16_t tab = PIN_SYNCHRO_TAB[(synchro >> 8) % 30];
    mcp_gpio_out |= tab & PIN_SYNCHRO_H_MASK;
    mcp_iodir |= tab & PIN_SYNCHRO_L_MASK;
    mcp_iodir |= PIN_SYNCHRO_H_MASK;
    uint32_t sync_pwm = (synchro & 0xFF) << 8;
    if (synchro & 0x100) sync_pwm = 65535 - sync_pwm;
    sync_pwm = sine::sine(sync_pwm / 2 - 16384) + 32768;
    uint32_t sync_pwm_a = sync_pwm;
    uint32_t sync_pwm_b = 65535 - sync_pwm;
    if (!synchro_enable) {
        sync_pwm_a = 0;
        sync_pwm_b = 0;
    } else {
        /*sync_pwm_a = (powf(sync_pwm_a / 65535.0f, 1.5f) * 65535);
        sync_pwm_b = (powf(sync_pwm_b / 65535.0f, 1.5f) * 65535);*/
    }
    analogWrite(PIN_SYNCHRO_A, 65535 - sync_pwm_a);
    analogWrite(PIN_SYNCHRO_B, 65535 - sync_pwm_b);

    // Override the reset output pin if power is bad.
    auto actual_gpio_out = mcp_gpio_out;
    auto actual_iodir = mcp_iodir;
    if (pwr::power_bad) {
        actual_gpio_out &= ~PIN_RESET_MASK;
        actual_iodir |= PIN_RESET_MASK;
    }

    // Perform the data transfer with the MCP23S17.
    mcp_gpio_in = mcp_read_word(0x12);
    mcp_write_word(0x12, actual_gpio_out);
    mcp_write_word(0x00, ~actual_iodir);

    // Detect time since last update.
    static unsigned long prev_time = millis();
    unsigned long time = millis();
    unsigned long delta = time - prev_time;
    prev_time = time;

    // Detect mode button presses.
    static uint16_t mode_timer = 0;
    bool mode = !(mcp_gpio_in & PIN_BTN_MODE_MASK);
    if (mode) {
        if (mode_timer < 1000) {
            mode_timer += delta;
            if (mode_timer >= 1000) {
                event = Event::LONG;
            }
        }
    } else {
        if (mode_timer > 20 && mode_timer < 1000) {
            event = Event::SHORT;
        }
        mode_timer = 0;
    }

    // Handle up & down buttons.
    bool up = !(mcp_gpio_in & PIN_BTN_UP_MASK);
    bool dn = !(mcp_gpio_in & PIN_BTN_DOWN_MASK);
    static bool both = false;
    if (up && dn) {
        if (!both) {
            event = Event::CANCEL;
        }
        both = true;
    }
    if (!up && !dn) {
        both = false;
    }
    if (!both) {

        // Handle up button.
        static uint16_t up_timer = 0;
        if (up) {
            if (up_timer < 1000) {
                if (up_timer < 20 && (up_timer + delta) >= 20) {
                    event = Event::UP_INIT;
                }
                up_timer += delta;
                if (up_timer >= 1000) {
                    event = Event::UP_AUTO;
                    up_timer -= 128;
                }
            }
        } else {
            up_timer = 0;
        }

        // Handle down button.
        static uint16_t dn_timer = 0;
        if (dn) {
            if (dn_timer < 1000) {
                if (dn_timer < 20 && (dn_timer + delta) >= 20) {
                    event = Event::DN_INIT;
                }
                dn_timer += delta;
                if (dn_timer >= 1000) {
                    event = Event::DN_AUTO;
                    dn_timer -= 128;
                }
            }
        } else {
            dn_timer = 0;
        }

    }

    // Detect reset button press+releases.
    static uint8_t auto_reset = 0;
    static bool resetting_prev = false;
    bool resetting = !(mcp_gpio_in & PIN_RESET_MASK);
    if (actual_iodir & PIN_RESET_MASK) {
        auto_reset = 100;
    } else if (auto_reset) {
        auto_reset--;
    }
    if (!resetting && resetting_prev && !auto_reset) {
        event = Event::RESET;
    }
    resetting_prev = resetting;

    // Detect UI inactivity.
    static uint16_t inactivity_timer = 0;
    if (event != Event::NONE) {
        inactivity_timer = 60000;
    } else if (inactivity_timer) {
        inactivity_timer--;
        if (!inactivity_timer) {
            event = Event::INACTIVE;
        }
    }

}

} // namespace gpio
