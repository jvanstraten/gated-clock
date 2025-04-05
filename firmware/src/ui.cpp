/*

When mode is held while the clock is powered on, factory settings are loaded
into the EEPROM.

Normal operation:
 - status LED is red when GPS sync is enabled but there is no GPS fix, off
   otherwise;
 - synchroscope is in normal operation;
 - down enables distraction-free mode (only minutes+hours, all other LEDs off);
 - up disables distraction-free mode;
 - short mode press enters date screen;
 - long mode press enters menu screen.

When in date screen:
 - status LED is green;
 - synchroscope is disabled;
 - short mode press or inactivity leaves date screen.

When in menu screen:
 - status LED is blue;
 - synchroscope state depends on selected entry;
 - long mode, cancel, or inactivity leaves menu;
 - up/down selects between configuration values;
 - for numeric values, mode selects configuration value;
 - for enum values, mode advances to next state.

When a value is selected:
 - status LED is light blue;
 - synchroscope state depends on selected entry;
 - the value either blinks or (for display color config) the display shows 88888;
 - up/down changes value (with auto-inc for non-enum values);
 - short mode, long mode, or cancel confirms new value (value -> eeprom);
 - inactivity confirms new value (value -> eeprom) and leaves menu.

Pressing the reset button at any time causes resynchronization with GPS, if
automatic synchronization is enabled. Otherwise it just makes the time blink
until manual configuration.

Menu items and values:

Fb ###      flipflop LED brightness (0..100)                        |
                                                                    |
Gb ###      gate LED brightness (0..100)                            |
                                                                    |
Sb ###      synchroscope LED brightness (0..100)                    | synchroscope shows
                                                                    | current consumption
db ###      display brightness (0..100)                             |
                                                                    |
dS ###      display saturation value (0..100)                       |
                                                                    |
dh ###      display hue value (0..359, wraparound)                  |

Ldr  1      enable LDR-based dimming (main display only)            | synchroscope shows
Ldr  0      disable LDR-based dimming                               | LDR value

Sd   1      enable seconds display                                  |
Sd   0      disable seconds display                                 |
                                                                    |
SYn  1      enable synchroscope (not avail. w/o seconds)            |
SYn LL      lead-lag synchroscope mode (not avail. w/o seconds)     | synchroscope
SYn  0      disable synchroscope                                    | is disabled
SYn 50      disable grid time, use XTAL/GPS for 50Hz square wave    |
SYn 60      disable grid time, use XTAL/GPS for 60Hz square wave    |
                                                                    |
AInc 1      enable auto-increment                                   |
AInc 0      disable auto-increment                                  |

LC ###      location code for GPS synchronization (0..num_codes)    | synchroscope shows
            (0 to disable synchronization)                          | GPS signal strength

dSt  A      auto DST                                                | synchroscope is disabled;
dSt  1      DST on                                                  | menu entry is not shown
dSt  0      DST off                                                 | when GPS sync is disabled

*/

#include "ui.hpp"

#include <WProgram.h>
#include <EEPROM.h>
#include "clk.hpp"
#include "led.hpp"
#include "gpio.hpp"
#include "synchro.hpp"
#include "ldr.hpp"
#include "gps.hpp"
#include "pwr.hpp"
#include "tz.hpp"

/**
 * User interface logic.
 */
namespace ui {

/**
 * Current screen.
 */
enum class Screen {
    NORMAL,
    DATE,
    MENU,
    VALUE
};
Screen screen;

/**
 * The currently selected config entry for MENU and VALUE screens.
 */
enum class ConfigEntry {
    FF_BRIGHTNESS,
    FF_BRIGHTNESS_MIN,
    GATE_BRIGHTNESS,
    GATE_BRIGHTNESS_MIN,
    SYNCHRO_BRIGHTNESS,
    SYNCHRO_BRIGHTNESS_MIN,
    DISPLAY_BRIGHTNESS,
    DISPLAY_BRIGHTNESS_MIN,
    DISPLAY_SATURATION,
    DISPLAY_HUE,
    LDR_DIMMING,
    SECONDS_SHOWN,
    SYCHRO_MODE,
    AUTO_INC_ENABLE,
    LOCATION_CODE,
    DST_MODE,
    END
};
ConfigEntry config_entry;

/**
 * Configuration data structure.
 */
struct Config {

    /**
     * EEPROM checksum field. Currently just set to the size of the structure.
     */
    uint16_t checksum;

    /**
     * Flipflop LED brightness level, 0..100. 37..100 maps to DC, below that
     * maps to PWM control with factor 1771. Default 40.
     */
    uint8_t ff_brightness;

    /**
     * Minimum flipflop LED brightness level, used when dimming is enabled, same encoding as above.
     */
    uint8_t ff_brightness_min;

    /**
     * Gate LED brightness level, 0..100. 37..100 maps to DC, below that maps
     * to PWM control with factor 1771. Default 40.
     */
    uint8_t gate_brightness;

    /**
     * Minimum gate LED brightness level, used when dimming is enabled, same encoding as above.
     */
    uint8_t gate_brightness_min;

    /**
     * Synchroscope LED brightness level, 0..100. 37..100 maps to DC, below
     * that maps to PWM control with factor 1771. Default 40.
     */
    uint8_t synchro_brightness;

    /**
     * Minimum synchroscope LED brightness level, used when dimming is enabled, same encoding as above.
     */
    uint8_t synchro_brightness_min;

    /**
     * Display brightness level, 0..100. 37..100 maps to DC, below that maps
     * to PWM control with factor 1328 and minimum 16384. Default 40.
     */
    uint8_t display_brightness;

    /**
     * Minimum display brightness level, used when dimming is enabled, same encoding as above.
     */
    uint8_t display_brightness_min;

    /**
     * Display saturation level, 0..100. Controls PWM only; specifically, this
     * inversely controls the dark PWM level with respect to the bright level.
     * Default 0.
     */
    uint8_t display_saturation;

    /**
     * Display hue, 0..359. Controls PWM only. Default 0.
     */
    uint16_t display_hue;

    /**
     * Whether LDR-based dimming is enabled on all leds. Disabled if 0. If enabled, the value
     * controls the illuminance cutoff below which dimming is enabled. It is in units of ~ 0.5lux.
     */
    uint8_t ldr_dimming;

    /**
     * Whether the seconds digits and second colon are shown. Default true.
     */
    bool seconds_shown;

    /**
     * Synchroscope configuration. Default SYNCHRO. The synchroscope is not
     * available when seconds_shown is false.
     */
    synchro::Mode synchro_mode;

    /**
     * Whether the auto-increment system is enabled. Default true.
     */
    bool auto_inc_enable;

    /**
     * Location code for GPS synchronization. Default 0.
     */
    uint16_t location_code;

    /**
     * 0 for DST off, 1 for on, 2 for auto DST. Ignored when location code is
     * 0. Default 2.
     */
    uint8_t dst_mode;

};
Config config;

/**
 * Whether distraction-free mode is enabled.
 */
bool distraction_free;

/**
 * Computes the correct checksum value for the current configuration.
 */
static uint16_t compute_checksum() {
    return sizeof(Config);
}

/**
 * Writes default values to the config structure.
 */
static void load_defaults() {
    config.ff_brightness = 40;
    config.ff_brightness_min = 10;
    config.gate_brightness = 40;
    config.gate_brightness_min = 25;
    config.synchro_brightness = 40;
    config.synchro_brightness_min = 10;
    config.display_brightness = 40;
    config.display_brightness_min = 10;
    config.display_saturation = 0;
    config.display_hue = 0;
    config.ldr_dimming = 0;
    config.seconds_shown = true;
    config.synchro_mode = synchro::Mode::SYNCHRO;
    config.auto_inc_enable = true;
    config.location_code = 0;
    config.dst_mode = 0;
}

/**
 * Reads the EEPROM data into the config structure.
 */
static void read_eeprom() {
    for (uint16_t i = 0; i < sizeof(Config); i++) {
        ((uint8_t*)&config)[i] = EEPROM.read(i);
    }
}

/**
 * Writes the config structure into EEPROM. Bytes are written lazily to reduce
 * wear.
 */
static void write_eeprom() {
    config.checksum = compute_checksum();
    for (uint16_t i = 0; i < sizeof(Config); i++) {
        uint8_t value = ((const uint8_t*)&config)[i];
        if (value != EEPROM.read(i)) {
            EEPROM.write(i, value);
        }
    }
}

/**
 * Updates everything based on the current configuration and the given
 * overrides. text specifies the text shown on the display, status_color
 * specifies a 24-bit hex color code for the status LED, and status_synchro
 * overrides the synchroscope position if non-negative, ranging from 0 to
 * 30*256-1.
 */
static void commit_config(
    const char *text = "",
    uint32_t status_color = 0,
    int32_t status_synchro = -1
) {

    // Configure brightness of the mainboard LEDs.
    auto &brightness = led::config[led::BRIGHTNESS_CTRL].ch[led::BRIGHTNESS_CH];
    if (distraction_free) {
        brightness.pwm_r = 0;
        brightness.pwm_g = 0;
        brightness.pwm_b = 0;
    } else {
        // brightness settings are stored in the range 0 to 100 inclusive
        // expand the range of these guys so we can dim them smoothly in the lower range
        uint16_t ff_brightness_dimmed      = uint16_t(config.ff_brightness) << 8;
        uint16_t gate_brightness_dimmed    = uint16_t(config.gate_brightness) << 8;
        uint16_t synchro_brightness_dimmed = uint16_t(config.synchro_brightness) << 8;

        if (config.ldr_dimming) {
            uint16_t max_illuminance = config.ldr_dimming * 32;

            ff_brightness_dimmed      = ldr::dimmed_brightness(ff_brightness_dimmed, uint16_t(config.ff_brightness_min) << 8, max_illuminance);
            gate_brightness_dimmed    = ldr::dimmed_brightness(gate_brightness_dimmed, uint16_t(config.gate_brightness_min) << 8, max_illuminance);
            synchro_brightness_dimmed = ldr::dimmed_brightness(synchro_brightness_dimmed, uint16_t(config.synchro_brightness_min) << 8, max_illuminance);
        }

        if (ff_brightness_dimmed < 9363) {
            brightness.pwm_r = ff_brightness_dimmed * 7;
            brightness.dc_r = 0;
        } else {
            brightness.pwm_r = 0xFFFF;
            brightness.dc_r = uint8_t((ff_brightness_dimmed - 9363) >> 7) + 1;
        }
        if (gate_brightness_dimmed < 9363) {
            brightness.pwm_b = gate_brightness_dimmed * 7;
            brightness.dc_b = 0;
        } else {
            brightness.pwm_b = 0xFFFF;
            brightness.dc_b = uint8_t((gate_brightness_dimmed - 9363) >> 7) + 1;
        }
        // synchroscope doesn't support PWM, so just map the brightness to DC
        brightness.pwm_g = 0xFFFF;
        brightness.dc_g = (uint32_t(synchro_brightness_dimmed) * 126) / 25600 + 1;
    }

    // Configure brightness and color of the 7-segment displays.
    uint8_t display_dc;
    uint16_t display_bright;
    uint16_t display_dark;
    uint16_t display_hue;
    bool enable_seconds;

    // brightness settings are stored in the range 0 to 100 inclusive
    // expand the range of these guys so we can dim them smoothly in the lower range
    uint16_t display_brightness_dimmed = uint16_t(config.display_brightness) << 8;
    if (config.ldr_dimming) {
        uint16_t max_illuminance = config.ldr_dimming * 32;

        display_brightness_dimmed = ldr::dimmed_brightness(display_brightness_dimmed, uint16_t(config.display_brightness_min) << 8, max_illuminance);
    }
    if (display_brightness_dimmed < 9363) {
        display_bright = ((display_brightness_dimmed * 3) >> 2) * 7 + 16384;
        display_dc = 0;
    } else {
        display_bright = 0xFFFF;
        display_dc = uint8_t((display_brightness_dimmed - 9363) >> 7) + 1;
    }
    display_dark = ((uint32_t)display_bright * (uint32_t)(100 - config.display_saturation)) / 100;
    display_hue = config.display_hue * 182;
    enable_seconds = (config.seconds_shown & !distraction_free) || (text && text[0]);
    led::set_color(display_hue, display_dark, display_bright, display_dc, enable_seconds);

    // Set the text on the display.
    led::set_text(text);

    // Set the color of the status LED.
    auto &status = led::config[led::STATUS_CTRL].ch[led::STATUS_CH];
    status.pwm_r = ((status_color >> 16) & 0xFF) << 5;
    status.pwm_g = ((status_color >>  8) & 0xFF) << 5;
    status.pwm_b = ((status_color >>  0) & 0xFF) << 5;

    // Configure the synchroscope.
    auto mode = config.synchro_mode;
    if (status_synchro >= 0) {
        mode = synchro::Mode::EXT;
        gpio::synchro = status_synchro;
    } else if (text && text[0]) {
        if (mode == synchro::Mode::LEAD_LAG || mode == synchro::Mode::SYNCHRO) {
            mode = synchro::Mode::OFF;
        }
    } else if (!config.seconds_shown) {
        if (mode == synchro::Mode::LEAD_LAG) {
            mode = synchro::Mode::OFF;
        }
    }
    synchro::mode = mode;

    // Configure auto-increment logic.
    clk::enable_auto_inc = config.auto_inc_enable;

    // Configure location and DST system.
    tz::set_location(config.location_code, config.dst_mode);

}

/**
 * Initializes the UI system. Also loads configuration from EEPROM.
 */
void setup() {

    // Figure out the state of the mode button.
    gpio::update();
    auto mode = !(gpio::mcp_gpio_in & gpio::PIN_BTN_MODE_MASK);

    // Read the configuration from EEPROM. If the checksum mismatches or the
    // mode button is held down, load default settings and write those to
    // EEPROM.
    read_eeprom();
    if (mode || config.checksum != compute_checksum()) {
        load_defaults();
        write_eeprom();
    }
    commit_config();

    // Load UI default values.
    screen = Screen::NORMAL;
    distraction_free = false;

}

/**
 * Updates the UI system.
 */
void update() {

    // Handle blink timer.
    static auto prev = millis();
    auto now = millis();
    auto delta = now - prev;
    prev = now;
    static uint16_t blink_timer;
    blink_timer += delta;

    // Handle UI events.
    if (gpio::event != gpio::Event::NONE) {

        switch (screen) {

            case Screen::NORMAL:
                switch (gpio::event) {
                    case gpio::Event::DN_INIT:
                        distraction_free = true;
                        break;
                    case gpio::Event::UP_INIT:
                        distraction_free = false;
                        break;
                    case gpio::Event::SHORT:
                        distraction_free = false;
                        screen = Screen::DATE;
                        break;
                    case gpio::Event::LONG:
                        distraction_free = false;
                        screen = Screen::MENU;
                        config_entry = ConfigEntry::FF_BRIGHTNESS;
                        break;
                    default:
                        break;
                }
                break;

            case Screen::DATE:
                switch (gpio::event) {
                    case gpio::Event::SHORT:
                    case gpio::Event::INACTIVE:
                        screen = Screen::NORMAL;
                        break;
                    default:
                        break;
                }
                break;

            case Screen::MENU:
                switch (gpio::event) {
                    case gpio::Event::CANCEL:
                    case gpio::Event::LONG:
                    case gpio::Event::INACTIVE:
                        screen = Screen::NORMAL;
                        write_eeprom();
                        break;
                    case gpio::Event::UP_INIT:
                        config_entry = ConfigEntry((int)config_entry + 1);
                        if (config_entry == ConfigEntry::END || (config_entry == ConfigEntry::DST_MODE && !config.location_code)) {
                            config_entry = ConfigEntry(0);
                        }
                        break;
                    case gpio::Event::DN_INIT:
                        if ((int)config_entry != 0) {
                            config_entry = ConfigEntry((int)config_entry - 1);
                        } else if (config.location_code) {
                            config_entry = ConfigEntry::DST_MODE;
                        } else {
                            config_entry = ConfigEntry::LOCATION_CODE;
                        }
                        break;
                    case gpio::Event::SHORT:
                        switch (config_entry) {
                            case ConfigEntry::FF_BRIGHTNESS:
                            case ConfigEntry::FF_BRIGHTNESS_MIN:
                            case ConfigEntry::GATE_BRIGHTNESS:
                            case ConfigEntry::GATE_BRIGHTNESS_MIN:
                            case ConfigEntry::SYNCHRO_BRIGHTNESS:
                            case ConfigEntry::SYNCHRO_BRIGHTNESS_MIN:
                            case ConfigEntry::DISPLAY_BRIGHTNESS:
                            case ConfigEntry::DISPLAY_BRIGHTNESS_MIN:
                            case ConfigEntry::DISPLAY_SATURATION:
                            case ConfigEntry::DISPLAY_HUE:
                            case ConfigEntry::LOCATION_CODE:
                            case ConfigEntry::LDR_DIMMING:
                                screen = Screen::VALUE;
                                break;

                            case ConfigEntry::SECONDS_SHOWN:
                                config.seconds_shown = !config.seconds_shown;
                                if (!config.seconds_shown) {
                                    if (config.synchro_mode == synchro::Mode::LEAD_LAG) {
                                        config.synchro_mode = synchro::Mode::SYNCHRO;
                                    }
                                }
                                break;

                            case ConfigEntry::SYCHRO_MODE:
                                if (config.synchro_mode != synchro::Mode::GPS_60) {
                                    config.synchro_mode = synchro::Mode((int)config.synchro_mode + 1);
                                } else if (!config.seconds_shown) {
                                    config.synchro_mode = synchro::Mode::SYNCHRO;
                                } else {
                                    config.synchro_mode = synchro::Mode::LEAD_LAG;
                                }
                                break;

                            case ConfigEntry::AUTO_INC_ENABLE:
                                config.auto_inc_enable = !config.auto_inc_enable;
                                break;

                            case ConfigEntry::DST_MODE:
                                config.dst_mode++;
                                if (config.dst_mode == 3) config.dst_mode = 0;
                                break;

                            default:
                                break;
                        }
                    default:
                        break;
                }
                break;

            case Screen::VALUE:
                switch (gpio::event) {
                    case gpio::Event::SHORT:
                    case gpio::Event::LONG:
                    case gpio::Event::CANCEL:
                        screen = Screen::MENU;
                        break;
                    case gpio::Event::INACTIVE:
                        write_eeprom();
                        screen = Screen::NORMAL;
                        break;
                    default:
                        break;
                }
                uint8_t *value8;
                uint16_t *value16;
                uint16_t max;
                switch (config_entry) {
                    case ConfigEntry::FF_BRIGHTNESS:
                        value8 = &config.ff_brightness;
                        goto handle8;
                    case ConfigEntry::FF_BRIGHTNESS_MIN:
                        value8 = &config.ff_brightness_min;
                        goto handle8;
                    case ConfigEntry::GATE_BRIGHTNESS:
                        value8 = &config.gate_brightness;
                        goto handle8;
                    case ConfigEntry::GATE_BRIGHTNESS_MIN:
                        value8 = &config.gate_brightness_min;
                        goto handle8;
                    case ConfigEntry::SYNCHRO_BRIGHTNESS:
                        value8 = &config.synchro_brightness;
                        goto handle8;
                    case ConfigEntry::SYNCHRO_BRIGHTNESS_MIN:
                        value8 = &config.synchro_brightness_min;
                        goto handle8;
                    case ConfigEntry::DISPLAY_BRIGHTNESS:
                        value8 = &config.display_brightness;
                        goto handle8;
                    case ConfigEntry::DISPLAY_BRIGHTNESS_MIN:
                        value8 = &config.display_brightness_min;
                        goto handle8;
                    case ConfigEntry::LDR_DIMMING:
                        value8 = &config.ldr_dimming;
                        goto handle8;
                    case ConfigEntry::DISPLAY_SATURATION:
                        value8 = &config.display_saturation;
                    handle8: {
                        int8_t delta;
                        switch (gpio::event) {
                            case gpio::Event::UP_INIT: delta = 1; break;
                            case gpio::Event::UP_AUTO: delta = 3; break;
                            case gpio::Event::DN_INIT: delta = -1; break;
                            case gpio::Event::DN_AUTO: delta = -3; break;
                            default: delta = 0; break;
                        }
                        int8_t value = (int8_t)*value8 + delta;
                        if (value < 0) {
                            value = 0;
                        } else if (value > 100) {
                            value = 100;
                        }
                        *value8 = (uint8_t)value;
                        break;
                    }

                    case ConfigEntry::DISPLAY_HUE:
                        value16 = &config.display_hue;
                        max = 359;
                        goto handle16;
                    case ConfigEntry::LOCATION_CODE:
                        value16 = &config.location_code;
                        max = tz::num_locations();
                        goto handle16;
                    handle16: {
                        int8_t delta;
                        switch (gpio::event) {
                            case gpio::Event::UP_INIT: delta = 1; break;
                            case gpio::Event::UP_AUTO: delta = 5; break;
                            case gpio::Event::DN_INIT: delta = -1; break;
                            case gpio::Event::DN_AUTO: delta = -5; break;
                            default: delta = 0; break;
                        }
                        int16_t value = (int16_t)*value16 + delta;
                        if (value < 0) {
                            value = max;
                        } else if (value > max) {
                            value = 0;
                        }
                        *value16 = (uint16_t)value;
                        break;
                    }

                    default:
                        screen = Screen::MENU;
                        break;
                }
                break;

        }

        // Reset blink timer.
        blink_timer = 0;

        // Handle logic reset.
        if (gpio::event == gpio::Event::RESET) {
            clk::valid = false;
        }

        // Clear event flag.
        gpio::event = gpio::Event::NONE;

    }

    // Reset display override configuration to defaults.
    char text[7];
    text[0] = 0;
    uint8_t blink_from = 6;
    uint32_t status_color;
    if (config.location_code && !gps::valid) {
        status_color = 0xFF0000;
    } else {
        status_color = 0;
    }
    int32_t status_synchro = -1;

    // Configure the display overrides.
    switch (screen) {

        case Screen::NORMAL:
            break;

        case Screen::DATE:
            snprintf(text, 7, "%02d%02d%02d", gps::year % 100, gps::month, gps::day);
            if (!status_color) status_color = 0x00FF00;
            break;

        case Screen::MENU:
        case Screen::VALUE:
            switch (config_entry) {
                case ConfigEntry::FF_BRIGHTNESS:
                    snprintf(text, 7, "Fb %3d", (int)config.ff_brightness);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::FF_BRIGHTNESS_MIN:
                    snprintf(text, 7, "F- %3d", (int)config.ff_brightness_min);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::GATE_BRIGHTNESS:
                    snprintf(text, 7, "Gb %3d", (int)config.gate_brightness);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::GATE_BRIGHTNESS_MIN:
                    snprintf(text, 7, "G- %3d", (int)config.gate_brightness_min);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::SYNCHRO_BRIGHTNESS:
                    snprintf(text, 7, "Sb %3d", (int)config.synchro_brightness);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::SYNCHRO_BRIGHTNESS_MIN:
                    snprintf(text, 7, "S- %3d", (int)config.synchro_brightness_min);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::DISPLAY_BRIGHTNESS:
                    if (screen == Screen::VALUE) {
                        snprintf(text, 7, "888888");
                    } else {
                        snprintf(text, 7, "db %3d", (int)config.display_brightness);
                    }
                    break;

                case ConfigEntry::DISPLAY_BRIGHTNESS_MIN:
                    if (screen == Screen::VALUE) {
                        snprintf(text, 7, "888888");
                    } else {
                        snprintf(text, 7, "d- %3d", (int)config.display_brightness_min);
                    }
                    break;

                case ConfigEntry::DISPLAY_SATURATION:
                    snprintf(text, 7, "dS %3d", (int)config.display_saturation);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::DISPLAY_HUE:
                    snprintf(text, 7, "dh %3d", (int)config.display_hue);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::LDR_DIMMING:
                    snprintf(text, 7, "Ldr%3d", (int)config.ldr_dimming);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::SECONDS_SHOWN:
                    snprintf(text, 7, "Sd   %d", (int)config.seconds_shown);
                    break;

                case ConfigEntry::SYCHRO_MODE:
                    switch (config.synchro_mode) {
                        case synchro::Mode::SYNCHRO:
                            snprintf(text, 7, "Syn  1");
                            break;
                        case synchro::Mode::LEAD_LAG:
                            snprintf(text, 7, "Syn LL");
                            break;
                        case synchro::Mode::OFF:
                            snprintf(text, 7, "Syn  0");
                            break;
                        case synchro::Mode::GPS_50:
                            snprintf(text, 7, "Syn 50");
                            break;
                        case synchro::Mode::GPS_60:
                            snprintf(text, 7, "Syn 60");
                            break;
                        default:
                            snprintf(text, 7, "Syn  E");
                            break;
                    }
                    break;

                case ConfigEntry::AUTO_INC_ENABLE:
                    snprintf(text, 7, "AInc %d", (int)config.auto_inc_enable);
                    break;

                case ConfigEntry::LOCATION_CODE:
                    snprintf(text, 7, "LC %3d", (int)config.location_code);
                    if (screen == Screen::VALUE) blink_from = 3;
                    break;

                case ConfigEntry::DST_MODE:
                    switch (config.dst_mode) {
                        case 0:
                            snprintf(text, 7, "dst  0");
                            break;
                        case 1:
                            snprintf(text, 7, "dst  1");
                            break;
                        case 2:
                            snprintf(text, 7, "dst  A");
                            break;
                    }
                    break;

                default:
                    snprintf(text, 7, "uh");
                    break;
            }
            switch (config_entry) {
                case ConfigEntry::FF_BRIGHTNESS:
                case ConfigEntry::FF_BRIGHTNESS_MIN:
                case ConfigEntry::GATE_BRIGHTNESS:
                case ConfigEntry::GATE_BRIGHTNESS_MIN:
                case ConfigEntry::SYNCHRO_BRIGHTNESS:
                case ConfigEntry::SYNCHRO_BRIGHTNESS_MIN:
                case ConfigEntry::DISPLAY_BRIGHTNESS:
                case ConfigEntry::DISPLAY_BRIGHTNESS_MIN:
                case ConfigEntry::DISPLAY_SATURATION:
                case ConfigEntry::DISPLAY_HUE:

                    // Full scale is about 2.5A.
                    status_synchro = pwr::current * 3;
                    if (status_synchro > 29*256) status_synchro = 29*256;
                    break;

                case ConfigEntry::LDR_DIMMING:
                    // map an illuminance of 1-30 lux to the synchroscope.
                    status_synchro = ldr::dimmed_brightness(29 * 256, 1, 64*30);
                    break;

                case ConfigEntry::LOCATION_CODE:
                    status_synchro = gps::signal_strength * 37;
                    if (status_synchro > 29*256) status_synchro = 29*256;
                    break;

                default:
                    break;

            }
            status_color = (screen == Screen::VALUE) ? 0x00FFFF : 0x0040FF;
            break;

    }

    // Handle blinking selected values.
    if (blink_timer & 512) {
        text[blink_from] = 0;
    }

    // If we're overcurrenting (>3A, 75% of power supply max) and we didn't
    // outright reset, reduce brightness values until we're no longer
    // overcurrenting.
    if (pwr::current > 3000) {
        static uint16_t count = 0;
        count += delta;
        while (count >= 100) {
            if (config.ff_brightness) config.ff_brightness--;
            if (config.gate_brightness) config.gate_brightness--;
            if (config.display_brightness) config.display_brightness--;
            if (config.ff_brightness_min) config.ff_brightness_min--;
            if (config.gate_brightness_min) config.gate_brightness_min--;
            if (config.display_brightness_min) config.display_brightness_min--;
            count -= 100;
        }
    }

    // Always update configuration (it includes LDR behavior).
    commit_config(text, status_color, status_synchro);

}

} // namespace ui
