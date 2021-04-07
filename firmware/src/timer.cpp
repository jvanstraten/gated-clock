#include "timer.hpp"
#include <WProgram.h>

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
 * Detected grid cycle period in 24MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
volatile uint32_t grid_period;

/**
 * Detected GPS 1PPs period in 24MHz ticks. Set by an ISR when two
 * consecutive edges are detected, cleared when processed by the main loop.
 */
volatile uint32_t gps_period;

/**
 * Configures the timer logic.
 */
void setup() {

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

    // Tick is handled in a low-priority software interrupt. We're not using
    // FTM1, so we abuse its interrupt vector.
    NVIC_SET_PRIORITY(IRQ_FTM1, 192);
    NVIC_ENABLE_IRQ(IRQ_FTM1);

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
    // multiple at once, we can't trivially tell what the order is. That has
    // to be done by comparing the captured values with the current timer
    // value. The current value is captured after the capture values and the
    // flags, so it always represents a later time. Thus, if current is
    // actually less than capture, we know the overflow happened after the
    // capture, and thus that we have to adjust the capture value too.
    if (!ordered(cap_grid, current)) {
        cap_grid += MODULO;
    }
    if (!ordered(cap_gps, current)) {
        cap_gps += MODULO;
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
    if (grid_prev_valid) grid_prev_valid--;
    if (gps_prev_valid) gps_prev_valid--;

    // Call tick() on overflow via a low-priority software interrupt.
    if (flags & (1ul << 8)) {
        NVIC_SET_PENDING(IRQ_FTM1);
    }

}

/**
 * Low-priority tick interrupt.
 */
void ftm1_isr(void) {
    tick();
}

} // extern "C"
