#include <inttypes.h>

#pragma once

/**
 * User interface logic.
 */
namespace ui {

/**
 * Initializes the UI system. Also loads configuration from EEPROM.
 */
void setup();

/**
 * Updates the UI system.
 */
void update();

} // namespace ui
