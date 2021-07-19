#include "led.hpp"

#include <WProgram.h>
#include "pwr.hpp"
#include "clk.hpp"
#include "sine.hpp"

/**
 * TLC6C5748 LED controller namespace.
 */
namespace led {

/**
 * LED controller configuration structures.
 */
Controller config[3];

/**
 * Whether to enable the display override signal.
 */
bool display_override;

/**
 * Displayed hours in UTC.
 */
uint8_t displayed_hours;

/**
 * Displayed minutes in UTC.
 */
uint8_t displayed_minutes;

/**
 * Displayed seconds in UTC.
 */
uint8_t displayed_seconds;

/**
 * Displayed time validity.
 */
bool displayed_time_valid;

/**
 * Returns whether the LED driven by the given controller/channel pair is on.
 */
static bool is_on(uint8_t ctrl, uint8_t ch) {
    const auto &c = config[ctrl].ch[ch];
    if (c.open_r || c.open_g || c.open_b) {
        return false;
    } else {
        return true;
    }
}

/**
 * Tries to determine what digit is being displayed, given the controller index
 * and the segment indices within the controller. Returns 10 for empty and 255
 * for unknown.
 */
static uint8_t detect_digit(uint8_t ctrl, const uint8_t *ch) {
    uint8_t val = 0;
    for (uint8_t i = 0; i < 7; i++) {
        if (is_on(ctrl, ch[i])) {
            val |= 1u << i;
        }
    }
    switch (val) {
        case 0b0111111: return 0;
        case 0b0000110: return 1;
        case 0b1011011: return 2;
        case 0b1001111: return 3;
        case 0b1100110: return 4;
        case 0b1101101: return 5;
        case 0b1111101: return 6;
        case 0b0000111: return 7;
        case 0b1111111: return 8;
        case 0b1101111: return 9;
        case 0b0000000: return 10;
    }
    return 255;
}

/**
 * Tries to determine the displayed time using the above routines.
 */
static bool detect_time() {
    if (display_override) return false;
    uint8_t ht = detect_digit(HOURS_CTRL,   TENS_CH);
    if (ht != 1 && ht != 2 && ht != 10) return false;
    if (ht == 10) ht = 0;
    uint8_t hu = detect_digit(HOURS_CTRL,   UNITS_CH);
    if (hu > 9) return false;
    uint8_t mt = detect_digit(MINUTES_CTRL, TENS_CH);
    if (mt > 9) return false;
    uint8_t mu = detect_digit(MINUTES_CTRL, UNITS_CH);
    if (mu > 9) return false;
    uint8_t st = detect_digit(SECONDS_CTRL, TENS_CH);
    if (st > 9) return false;
    uint8_t su = detect_digit(SECONDS_CTRL, UNITS_CH);
    if (su > 9) return false;
    displayed_hours   = ht * 10 + hu;
    displayed_minutes = mt * 10 + mu;
    displayed_seconds = st * 10 + su;
    displayed_time_valid = true;
    return true;
}

/**
 * Sets the override for a digit to the specified (representable) character.
 * Supported are alphanumerics except k, m, v, w, x, and z, as well as
 * space, dash, and underscore. Any unrecognized character becomes a dash on
 * the display.
 */
static void set_digit(uint8_t ctrl, const uint8_t *ch, char c) {
    uint8_t val = 0;
    if (c) {
        switch (c) {
            case 'a':
            case 'A': val = 0b1110111; break;
            case 'b':
            case 'B': val = 0b1111100; break;
            case 'c': val = 0b1011000; break;
            case 'C': val = 0b0111001; break;
            case 'd':
            case 'D': val = 0b1011110; break;
            case 'e':
            case 'E': val = 0b1111001; break;
            case 'f':
            case 'F': val = 0b1110001; break;
            case 'g':
            case 'G': val = 0b0111101; break;
            case 'h': val = 0b1110100; break;
            case 'H': val = 0b1110110; break;
            case 'i': val = 0b0000100; break;
            case 'I': val = 0b0000110; break;
            case 'j':
            case 'J': val = 0b0011110; break;
            case 'l':
            case 'L': val = 0b0111000; break;
            case 'n':
            case 'N': val = 0b1010100; break;
            case 'o': val = 0b1011100; break;
            case 'O': val = 0b0111111; break;
            case 'p':
            case 'P': val = 0b1110011; break;
            case 'q':
            case 'Q': val = 0b1100111; break;
            case 'r':
            case 'R': val = 0b1010000; break;
            case 's':
            case 'S': val = 0b1101101; break;
            case 't':
            case 'T': val = 0b1111000; break;
            case 'u': val = 0b0011100; break;
            case 'U': val = 0b0111110; break;
            case 'y':
            case 'Y': val = 0b1101110; break;
            case '_': val = 0b0001000; break;
            case ' ': val = 0b0000000; break;
            case '0': val = 0b0111111; break;
            case '1': val = 0b0000110; break;
            case '2': val = 0b1011011; break;
            case '3': val = 0b1001111; break;
            case '4': val = 0b1100110; break;
            case '5': val = 0b1101101; break;
            case '6': val = 0b1111101; break;
            case '7': val = 0b0000111; break;
            case '8': val = 0b1111111; break;
            case '9': val = 0b1101111; break;
            default:  val = 0b1000000; break;
        }
    }
    for (uint8_t i = 0; i < 7; i++) {
        config[ctrl].ch[ch[i]].enable = (val >> i) & 1;
    }
}

/**
 * Sets the override for a digit to the specified (representable) character.
 * Supported are alphanumerics except k, m, v, w, x, y, and z, as well as
 * space, dash, and underscore. Any unrecognized character becomes a dash on
 * the display.
 */
static void set_digit_index(uint8_t i, char c) {
    switch (i) {
        case 0: set_digit(HOURS_CTRL,   TENS_CH,  c); break;
        case 1: set_digit(HOURS_CTRL,   UNITS_CH, c); break;
        case 2: set_digit(MINUTES_CTRL, TENS_CH,  c); break;
        case 3: set_digit(MINUTES_CTRL, UNITS_CH, c); break;
        case 4: set_digit(SECONDS_CTRL, TENS_CH,  c); break;
        case 5: set_digit(SECONDS_CTRL, UNITS_CH, c); break;
    }
}


/**
 * Sets the text on the display, enabling override. Specify an empty string or
 * nullptr to disable override.
 */
void set_text(const char *text) {
    if (text == nullptr || text[0] == 0) {
        display_override = false;
        return;
    }
    for (uint8_t i = 0; i < 6; i++) {
        set_digit_index(i, *text);
        if (*text) text++;
    }
    display_override = true;
}

/**
 * Computes the PWM value for the red channel for our simplistic HDL color
 * model (hue, dark value, light value). Green is computed by adding 43690
 * to h, and blue by adding 21845.
 */
static uint16_t compute_hdl(uint16_t h, uint16_t d, uint16_t l) {
    if (h > 43690) return d;
    h += h >> 1;
    h -= 16384;
    h = (uint16_t)sine::sine(h);
    h += 32768;
    uint32_t val = (uint32_t)h * l + (65536 - (uint32_t)h) * d;
    val += 32768;
    return val >> 16;
}

/**
 * Internal call for set_color() that handles a particular segment.
 */
static void set_segment_color(Channel &ch, uint16_t h, uint16_t d, uint16_t l, uint8_t dc) {
    ch.pwm_r = compute_hdl(h +     0, d, l);
    ch.pwm_g = compute_hdl(h + 43690, d, l) >> 1;
    ch.pwm_b = compute_hdl(h + 21845, d, l) >> 1;
    ch.dc_r = dc;
    ch.dc_g = dc;
    ch.dc_b = dc;
}

/**
 * Sets the color of the display with hue, dark PWM level, light PWM level,
 * and hue delta per X coord and per Y coord (for a rainbow-y effect, because
 * why not?).
 */
void set_color(uint16_t h, uint16_t d, uint16_t l, uint8_t dc, bool es, int16_t hx, int16_t hy) {
    for (uint8_t i = 0; i < 7; i++) {
        set_segment_color(
            config[HOURS_CTRL].ch[TENS_CH[i]],
            h + (uint16_t)((int32_t)hx * (SEG_X[i] + 0) + (int32_t)hy * SEG_Y[i]), d, l, dc
        );
        set_segment_color(
            config[HOURS_CTRL].ch[UNITS_CH[i]],
            h + (uint16_t)((int32_t)hx * (SEG_X[i] + 3) + (int32_t)hy * SEG_Y[i]), d, l, dc
        );
        set_segment_color(
            config[MINUTES_CTRL].ch[TENS_CH[i]],
            h + (uint16_t)((int32_t)hx * (SEG_X[i] + 7) + (int32_t)hy * SEG_Y[i]), d, l, dc
        );
        set_segment_color(
            config[MINUTES_CTRL].ch[UNITS_CH[i]],
            h + (uint16_t)((int32_t)hx * (SEG_X[i] + 10) + (int32_t)hy * SEG_Y[i]), d, l, dc
        );
        set_segment_color(
            config[SECONDS_CTRL].ch[TENS_CH[i]],
            h + (uint16_t)((int32_t)hx * (SEG_X[i] + 14) + (int32_t)hy * SEG_Y[i]), es ? d : 0, es ? l : 0, dc
        );
        set_segment_color(
            config[SECONDS_CTRL].ch[UNITS_CH[i]],
            h + (uint16_t)((int32_t)hx * (SEG_X[i] + 17) + (int32_t)hy * SEG_Y[i]), es ? d : 0, es ? l : 0, dc
        );
    }
    for (uint8_t i = 0; i < 2; i++) {
        set_segment_color(
            config[COLON_CTRL[0]].ch[COLON_CH[i]],
            h + (uint16_t)((int32_t)hx * 6 + (int32_t)hy * COLON_Y[i]), d, l, dc
        );
        set_segment_color(
            config[COLON_CTRL[1]].ch[COLON_CH[i]],
            h + (uint16_t)((int32_t)hx * 13 + (int32_t)hy * COLON_Y[i]), es ? d : 0, es ? l : 0, dc
        );
    }
}

/**
 * Sets up pins related to LED control.
 */
void setup() {

    // Configure the pins.
    pinMode(PIN_SIN,  OUTPUT);
    pinMode(PIN_SOUT, INPUT);
    pinMode(PIN_LAT,  OUTPUT);
    pinMode(PIN_OVER, OUTPUT);
    pinMode(PIN_SCLK, OUTPUT);

    // Load sane initial values for the configuration structure.
    for (uint8_t dev = 0; dev < 3; dev++) {
        config[dev].mc_r = 1;
        config[dev].mc_g = 1;
        config[dev].mc_b = 1;
        config[dev].bc_r = 0x7F;
        config[dev].bc_g = 0x7F;
        config[dev].bc_b = 0x7F;
        config[dev].dsprpt = true;
        config[dev].tmgrst = false;
        config[dev].rfresh = false;
        config[dev].espwm = true;
        config[dev].lsdvlt = false;
        for (uint8_t ch = 0; ch < 16; ch++) {
            /*config[dev].ch[ch].pwm_r = 0x4000;
            config[dev].ch[ch].pwm_g = 0x4000;
            config[dev].ch[ch].pwm_b = 0x4000;
            config[dev].ch[ch].dc_r = 0x0F;
            config[dev].ch[ch].dc_g = 0x0F;
            config[dev].ch[ch].dc_b = 0x0F;*/
            config[dev].ch[ch].pwm_r = 0;
            config[dev].ch[ch].pwm_g = 0;
            config[dev].ch[ch].pwm_b = 0;
            config[dev].ch[ch].dc_r = 0;
            config[dev].ch[ch].dc_g = 0;
            config[dev].ch[ch].dc_b = 0;
            config[dev].ch[ch].enable = true;
        }
    }
    /*config[1].ch[13].pwm_r = 0xFFFF;
    config[1].ch[13].pwm_g = 0xFFFF;
    config[1].ch[13].pwm_b = 0xA000;
    config[1].ch[13].dc_r = 0x1F;
    config[1].ch[13].dc_g = 0x10;
    config[1].ch[13].dc_b = 0x00;
    config[1].ch[14].pwm_r = 0x0000;
    config[1].ch[14].pwm_g = 0x0000;
    config[1].ch[14].pwm_b = 0x0000;
    config[1].ch[14].dc_r = 0x10;
    config[1].ch[14].dc_g = 0x10;
    config[1].ch[14].dc_b = 0x10;*/
    display_override = false;
    displayed_time_valid = false;

    // Send update twice during initialization to configure the max current
    // latch.
    delay(1);
    while (!update());
    while (!update());

}


/**
 * Shifts a bit into and out of the LED controllers.
 */
static inline bool shift_bit(bool d = false) {
    digitalWrite(PIN_SIN, d);
    digitalWrite(PIN_SCLK, HIGH);
    digitalWrite(PIN_SCLK, LOW);
    return digitalRead(PIN_SOUT);
}

/**
 * Shifts an n-bit word into the LED controllers.
 */
static inline void shift_word(uint16_t d, uint8_t nb) {
    for (int8_t i = nb - 1; i >= 0; i--) {
        shift_bit(d & (1 << i));
    }
}

/**
 * Updates the continuous bit-banged data transfer between the LED controllers
 * and the configuration structure. Returns true when a full sequence was
 * completed (this takes a while, so it's divided up into multiple updates).
 */
bool update() {
    static uint8_t state = 0;
    static uint32_t last_gs_write = 0;
    static bool time_blank;

    switch (state) {

        // Send control data while reading fault config from previous cycle.
        case 0:
            time_blank = (millis() & 512) ? !clk::valid : false;
            if ((uint32_t)millis() - last_gs_write < 5) {
                // Wait for a grayscale cycle to complete for sure before
                // starting the next transfer.
                return false;
            }
            digitalWrite(PIN_LAT, LOW);
        case 2:
        case 4:
        {
            auto &d = config[2 - (state >> 1)];
            d.ch[15].open_b = shift_bit(true);  // write 768 (select control latch), read 767
            d.ch[15].open_g = shift_bit(true);  // write 767 (control config write command in next 8 bits, 0x96), read 766
            d.ch[15].open_r = shift_bit(false); // write 766, read 765
            d.ch[14].open_b = shift_bit(false); // write 765, read 764
            d.ch[14].open_g = shift_bit(true);  // write 764, read 763
            d.ch[14].open_r = shift_bit(false); // write 763, read 762
            d.ch[13].open_b = shift_bit(true);  // write 762, read 761
            d.ch[13].open_g = shift_bit(true);  // write 761, read 760
            d.ch[13].open_r = shift_bit(false); // write 760, read 759
            // next shift is write 759, read 758
            for (int8_t channel = 12; channel >= 0; channel--) {
                auto &c = d.ch[channel];
                c.open_b = shift_bit();
                c.open_g = shift_bit();
                c.open_r = shift_bit();
            }
            // next shift is write 720, read 719
            for (int8_t channel = 15; channel >= 0; channel--) {
                auto &c = d.ch[channel];
                c.short_b = shift_bit();
                c.short_g = shift_bit();
                c.short_r = shift_bit();
            }
            // next shift is write 672, (read 671)
            for (uint16_t i = 0; i < 302; i++) {
                shift_bit();
            }
            // next shift is write 370
            state++;
            return false;
        }
        case 1:
        case 3:
        case 5:
        {
            auto &d = config[2 - (state >> 1)];
            if (pwr::power_bad) {
                // next shift is write 370
                shift_bit(0);
                shift_bit(0);
                shift_bit(0);
                shift_bit(1);
                shift_bit(0);
                // next shift is write 365
                shift_word(0, 21);
                // next shift is write 344
                shift_word(0, 9);
            } else {
                // next shift is write 370
                shift_bit(d.lsdvlt);
                shift_bit(d.espwm);
                shift_bit(d.rfresh);
                shift_bit(d.tmgrst);
                shift_bit(d.dsprpt);
                // next shift is write 365
                shift_word(d.bc_b, 7);
                shift_word(d.bc_g, 7);
                shift_word(d.bc_r, 7);
                // next shift is write 344
                shift_word(d.mc_b, 3);
                shift_word(d.mc_g, 3);
                shift_word(d.mc_r, 3);
            }
            // next shift is write 335
            for (int8_t channel = 15; channel >= 0; channel--) {
                const auto &c = d.ch[channel];
                shift_word(c.dc_b, 7);
                shift_word(c.dc_g, 7);
                shift_word(c.dc_r, 7);
            }
            // full shift complete
            if (state == 5) {
                digitalWrite(PIN_LAT, HIGH);
            }
            state++;
            return false;
        }

        // Send grayscale data.
        case 6:
            digitalWrite(PIN_LAT, LOW);
        case 7:
        case 8:
        case 9:
        case 10:
        case 11:
        {
            uint8_t ctrl = 5 - (state >> 1);
            auto &d = config[ctrl];
            int8_t start, stop;
            if (!(state & 1)) {
                shift_bit(false);
                start = 15;
                stop = 8;
            } else {
                start = 7;
                stop = 0;
            }
            for (int8_t channel = start; channel >= stop; channel--) {
                const auto &c = d.ch[channel];
                bool segment_blank = pwr::power_bad;
                if (display_override) {
                    if (!c.enable) {
                        segment_blank = true;
                    }
                } else {
                    if (time_blank) {
                        if (!(ctrl == STATUS_CTRL && channel == STATUS_CH)) {
                            if (!(ctrl == BRIGHTNESS_CTRL && channel == BRIGHTNESS_CH)) {
                                segment_blank = true;
                            }
                        }
                    }
                }
                if (segment_blank) {
                    shift_word(0, 48);
                } else {
                    shift_word(c.pwm_b, 16);
                    shift_word(c.pwm_g, 16);
                    shift_word(c.pwm_r, 16);
                }
            }
            if (state == 11) {
                digitalWrite(PIN_LAT, HIGH);
                last_gs_write = millis();
            }
            state++;
            return false;
        }

        // Detect displayed time.
        default:
        {
            digitalWrite(PIN_OVER, display_override);
            displayed_time_valid = detect_time();
            state = 0;
            return true;
        }

    }

}

} // namespace led
