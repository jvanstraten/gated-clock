/*

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
 - short mode confirms new value (value -> eeprom);
 - long mode or cancel rejects new value (eeprom -> value);
 - inactivity confirms new value (value -> eeprom) and leaves menu.

Pressing the reset button at any time causes resynchronization with GPS, if
automatic synchronization is enabled. Otherwise it just makes the time blink
until manual configuration.

Menu items and values:

Second      select to modify seconds value                          | synchroscope
            (display shows time when selected)                      | is disabled

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

SYn  1      enable synchroscope                                     |
SYn  0      disable synchroscope                                    |
SYn LL      lead-lag synchroscope mode                              |
SYn 50      disable grid time, use XTAL/GPS for 50Hz square wave    |
SYn 60      disable grid time, use XTAL/GPS for 60Hz square wave    |
                                                                    | synchroscope
Sd   1      enable seconds display                                  | is disabled
Sd   0      disable seconds display                                 |
                                                                    |
AInc 1      enable auto-increment                                   |
AInc 0      disable auto-increment                                  |

LC ###      location code for GPS synchronization (0..num_codes)    | synchroscope shows
            (0 to disable synchronization)                          | GPS signal strength

DSt A0      auto DST (auto DST not in effect)                       | synchroscope is
DSt A1      auto DST (auto DST in effect)                           | disabled; menu entry
DSt  1      DST on                                                  | is not shown when GPS
DSt  0      DST off                                                 | sync is disabled

*/

#include "ui.hpp"

#include <WProgram.h>
#include "clk.hpp"

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
    SECONDS_CONFIG,
    FF_BRIGHTNESS,
    GATE_BRIGHTNESS,
    SYNCHRO_BRIGHTNESS,
    DISPLAY_BRIGHTNESS,
    DISPLAY_SATURATION,
    DISPLAY_HUE,
    LDR_DIMMING,
    SYCHRO_MODE,
    SECONDS_SHOWN,
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
    uint8_t size;
    uint8_t ff_brightness;
    uint8_t gate_brightness;
    uint8_t synchro_brightness;
    uint8_t display_brightness;
    uint8_t display_saturation;
    uint16_t display_hue;
    bool ldr_dimming;
    synchro::Mode synchro_mode;
    bool seconds_shown;
    bool auto_inc_enable;
    uint16_t location_code;
    uint8_t dst_mode;
};

/**
 * Initializes the UI system. Also loads configuration from EEPROM.
 */
void setup() {
}

/**
 * Updates the UI system.
 */
void update() {
}

} // namespace ui
