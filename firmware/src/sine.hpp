#include <inttypes.h>

#pragma once

namespace sine {

/**
 * Returns the sine of 2pi pos / 65536 in 1.15 signed fixed point.
 */
int16_t sine(uint16_t pos);

} // namespace sine
