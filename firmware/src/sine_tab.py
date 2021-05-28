import math

with open('sine_tab.hpp', 'w') as f:
    f.write("""#include <inttypes.h>

#pragma once

namespace sine {

static const int16_t SINE[256] = {
""")
    for i in range(256):
        f.write('    0x%04X,\n' % int(round(math.sin((i + 0.5) / 512 * math.pi) * 32767)))
    f.write("""};

} // namespace sine
""")
