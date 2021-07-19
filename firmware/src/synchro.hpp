#include <inttypes.h>

#pragma once

/**
 * Synchroscope and time synchronization logic namespace.
 */
namespace synchro {

/**
 * Synchroscope/synchronization modes.
 */
enum class Mode {

    /**
     * Synchroscope mode. The LED bar behaves as if it's the needle of a
     * mechanical synchroscope (though rolling over every 84 degrees).
     */
    SYNCHRO,

    /**
     * Lead-lag mode. The LED position indicates by how many seconds the
     * grid time is leading or lagging behind GPS time, judging only by the
     * current second. When it's in the middle, the phase is aligned. The
     * rollover point is +/-30 seconds.
     */
    LEAD_LAG,

    /**
     * The synchroscope LEDs are off, but the grid is used as frequency
     * reference.
     */
    OFF,

    /**
     * Grid frequency usage is disabled entirely. The GPS/crystal frequency
     * is instead used to generate a much more stable 50Hz, so the time should
     * always be accurate. The synchroscope LEDs are disabled, because the grid
     * frequency cannot be detected simultaneously.
     */
    GPS_50,

    /**
     * Same as GPS_50, but generating 60Hz rather than 50Hz.
     */
    GPS_60,

    /**
     * This unit does not update the synchroscope position, giving the UI full
     * control.
     */
    EXT

};

/**
 * Current synchroscope mode.
 */
extern Mode mode;

/**
 * Updates the synchroscope logic.
 */
void update();

} // namespace synchro
