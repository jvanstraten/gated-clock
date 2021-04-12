#include "timer.hpp"

#include <WProgram.h>
#include "clk.hpp"

/**
 * FTM2 input capture and repetitive tick interrupt logic.
 */
namespace timer {

/**
 * Modulo value for the timer; 48000 for 1kHz overflow interrupt rate with a
 * peripheral base clock of 48MHz.
 */
static const uint32_t MODULO = 48000;

/**
 * 32-bit offset for the 16-bit counter, incremented by MODULO whenever the
 * timer overflows.
 */
static uint32_t offset;

/**
 * Previously captured time for the grid frequency input.
 */
static uint32_t grid_prev;

/**
 * Previously captured time for the GPS 1PPS input.
 */
static uint32_t gps_prev;

/**
 * Whether the previous grid edge time is valid. Set to 40 when an edge is
 * captured and is then decremented every 1kHz tick back down to 0; nonzero
 * means valid.
 */
static uint16_t grid_prev_valid;

/**
 * Whether the previous GPS 1PPS edge time is valid. Set to 1200 when an edge
 * is captured and is then decremented every 1kHz tick back down to 0; nonzero
 * means valid.
 */
static uint16_t gps_prev_valid;

/**
 * Detected grid cycle period in 48MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
volatile uint32_t grid_period;

/**
 * Detected GPS 1PPs period in 48MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
volatile uint32_t gps_period;

/**
 * Clock signal override state.
 */
static volatile bool clk_override;

/**
 * Configures the timer logic.
 */
void setup() {
    clk_override = false;

    // Configure pin modes.
    pinMode(PIN_GRID_F, INPUT);     // = FTM2 channel 0
    pinMode(PIN_GPS_PPS, INPUT);    // = FTM2 channel 1

    // Configure TPM2.
    TPM2_SC     = (0ul << 8)    // disable DMA
                | (1ul << 7)    // clear timer overflow
                | (0ul << 6)    // disable timer overflow interrupt for now
                | (0ul << 5)    // no PWM stuff
                | (0ul << 3)    // disable counting for now
                | (0ul << 0);   // prescaler divide by 1
    TPM2_CNT    = 0;            // clear counter value
    TPM2_MOD    = MODULO - 1;   // configure modulo value
    TPM2_C0SC   = 0;            // disable channel; must be done before reconfiguring
    TPM2_C1SC   = 0;            // disable channel; must be done before reconfiguring
    delayMicroseconds(10);      // give the TPM plenty of time to acknowledge the above
    TPM2_C0SC   = (1ul << 7)    // clear channel interrupt flag
                | (1ul << 6)    // enable channel interrupt
                | (1ul << 2)    // input capture on rising edge
                | (0ul << 0);   // disable DMA
    TPM2_C1SC   = (1ul << 7)    // clear channel interrupt flag
                | (1ul << 6)    // enable channel interrupt
                | (1ul << 2)    // input capture on rising edge
                | (0ul << 0);   // disable DMA
    TPM2_CONF   = (0ul << 24)   // no trigger stuff
                | (0ul << 18)   // no counter reload on trigger
                | (0ul << 17)   // no counter stop on overflow
                | (0ul << 16)   // no counter start on trigger
                | (0ul << 9)    // disable global timebase, whatever that is
                | (0ul << 6)    // debug mode is don't care, who needs debugging?
                | (0ul << 5);   // doze mode is also not used
    TPM2_SC     = (0ul << 8)    // disable DMA
                | (1ul << 7)    // clear timer overflow
                | (1ul << 6)    // enable timer overflow interrupt
                | (0ul << 5)    // no PWM stuff
                | (1ul << 3)    // increment on clock
                | (0ul << 0);   // prescaler divide by 1

    // Connect the input pins to the timer.
    CORE_PIN3_CONFIG = PORT_PCR_MUX(3) | PORT_PCR_SRE;
    CORE_PIN4_CONFIG = PORT_PCR_MUX(3) | PORT_PCR_SRE;

    // Set max priority for the timer interrupt.
    NVIC_SET_PRIORITY(IRQ_FTM2, 0);
    NVIC_ENABLE_IRQ(IRQ_FTM2);

}

/**
 * Overrides the clock's clk signal to the given state.
 */
void override_clk(bool state) {
    clk_override = true;
    grid_prev_valid = 0;
    digitalWrite(PIN_GRID_F, state);
    pinMode(PIN_GRID_F, OUTPUT);
}

/**
 * Releases the clock's clk signal, giving control to the power grid.
 */
void release_clk() {
    pinMode(PIN_GRID_F, INPUT);
    CORE_PIN3_CONFIG = PORT_PCR_MUX(3) | PORT_PCR_SRE;
    clk_override = false;
}

/**
 * Returns the detected grid frequency (either 50 or 60Hz).
 */
uint8_t grid_frequency() {
    if (grid_period < 48000000/55) {
        return 50;
    } else {
        return 60;
    }
}

/**
 * Returns true if b comes after a, modulo 32bit.
 */
static inline bool ordered(uint32_t a, uint32_t b) {
    return (b - a) < 0x80000000;
}

/**
 * Handles a grid edge capture event.
 */
static void grid_edge(uint32_t grid_cap) {
    if (clk_override) {
        return;
    }
    if (grid_prev_valid) {
        grid_period = grid_cap - grid_prev;
    }
    grid_prev = grid_cap;
    grid_prev_valid = 40;
}

/**
 * Handles a GPS 1PPS edge capture event.
 */
static void gps_edge(uint32_t gps_cap) {
    if (gps_prev_valid) {
        gps_period = gps_cap - gps_prev;
    }
    gps_prev = gps_cap;
    gps_prev_valid = 1200;
}

} // namespace timer

using namespace timer;

extern "C" {

/**
 * FTM2 overflow or input capture interrupt.
 */
void ftm2_isr(void) {

    // Do all the important stuff at the start.
    uint32_t flags = TPM2_STATUS;
    uint32_t cap_grid = TPM2_C0V;
    uint32_t cap_gps = TPM2_C1V;
    uint32_t current = TPM2_CNT;
    TPM2_STATUS = flags;

    // Handle overflow.
    uint32_t offs = offset;
    if (flags & (1ul << 8)) {
        offs += MODULO;
        offset = offs;
    }

    // Adjust based on the 32-bit offset value that we update on overflow.
    cap_grid += offs;
    cap_gps += offs;
    current += offs;

    // We have flags for the capture and overflow events, but if we receive
    // multiple at once, we can't trivially tell what the order is. Possible
    // cases are:
    //
    //  -------------
    //    ^   ^   ^         A: no overflow
    //   CAP ISR CUR
    //
    //  -----------------
    //    ^   ^   ^   ^     B: overflow before capture in same ISR
    //   OVF CAP ISR CUR
    //
    //  -----------------
    //    ^   ^   ^   ^     C: capture before overflow in same ISR
    //   CAP OVF ISR CUR
    //
    //  -----------------
    //    ^   ^   ^   ^     D: overflow between flags and current value readout
    //   CAP ISR OVF CUR
    //
    // In the code above, we assume that either A or B happened; overflow is
    // applied to offset, and the new offset is applied to the capture values
    // and current values. If this is indeed what happened, cap < cur.
    // Otherwise, we need to adjust.
    //
    // In case C and D, cap will appear to have happened later than cur,
    // which is logically impossible. If we rule out interrupts not being
    // processed within one timer cycle, this uniquely tells us that C or
    // D did in fact happen. If this is combined with an overflow flag readout,
    // case C is what happened, which means we've "overestimated" the capture
    // event time by MODULO by already having applied the overflow offset to
    // it, which is easily remedied by subtracting MODULO. In case D, the
    // logical impossibility is also there, but only because cur was not
    // adjusted for the overflow yet, which will happen in the next interrupt,
    // so we don't need to adjust the capture value.
    if (flags & (1ul << 8)) {
        if (!ordered(cap_grid, current)) {
            cap_grid -= MODULO;
        }
        if (!ordered(cap_gps, current)) {
            cap_gps -= MODULO;
        }
    }

    // Call the grid_edge() and gps_edge() functions in the right order.
    if (ordered(cap_grid, cap_gps)) {
        if (flags & (1ul << 0)) {
            grid_edge(cap_grid);
        }
        if (flags & (1ul << 1)) {
            gps_edge(cap_gps);
        }
    } else {
        if (flags & (1ul << 1)) {
            gps_edge(cap_gps);
        }
        if (flags & (1ul << 0)) {
            grid_edge(cap_grid);
        }
    }

    // Decrement edge validity counters.
    static uint16_t invalidate_cooldown = 500;
    if (grid_prev_valid) {
        grid_prev_valid--;
        invalidate_cooldown = 500;
    } else {
        if (invalidate_cooldown) {
            invalidate_cooldown--;
        } else {
            clk::valid = false;
            invalidate_cooldown = 500;
        }
    }
    if (gps_prev_valid) gps_prev_valid--;

}

} // extern "C"
