#include "sine.hpp"
#include "sine_tab.hpp"

namespace sine {

/**
 * Handles the lookup table symmetry, returning the (virtual) table entry for
 * 2pi pos / 1024.
 */
static int16_t lookup(uint16_t pos)  {
    switch ((pos >> 8) & 3) {
        case 0: return SINE[pos & 0xFF];
        case 1: return SINE[255 - (pos & 0xFF)];
        case 2: return -SINE[pos & 0xFF];
        default: return -SINE[255 - (pos & 0xFF)];
    }
}

/**
 * Returns the sine of 2pi pos / 65536 in 1.15 signed fixed point.
 */
int16_t sine(uint16_t pos) {
    pos -= 32;
    uint16_t idx = pos >> 6;
    uint16_t lin = pos & 0x3F;
    int32_t x = lookup(idx);
    int32_t y = lookup(idx + 1);
    int32_t z = x * (64 - lin) + y * lin;
    return (z + 32) >> 6;
}

} // namespace sine
