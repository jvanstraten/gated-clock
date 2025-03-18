import numpy as np
import matplotlib.pyplot as plt



SAMPLE_COUNT = 0x1000
PULLUP_RESISTANCE = 220e3
MIN_RESISTANCE = 10e3
AVG_RESISTANCE = 15e3
MAX_RESISTANCE = 20e3
FULL_MOON = 0.1
INDOORS = 150.0


def calc_ldr_resistance(illuminance, gamma=0.7, dark_resistance=1e6, res_at_10lux=10e3):
    # (E / 10) ** gamma = (R_10lux / R)
    # so
    # R = R_10lux * (E / 10) ** -gamma
    base_resistance = res_at_10lux * (illuminance / 10) ** -gamma
    return 1/(1/base_resistance + 1/dark_resistance)

def wanted_brightness(illuminance, max_illuminance=100.0, max_val=1023, min_val=1):
    # our target brigness curve. max brightness above a certain illuminance, then linearly down with
    # illuninance until min brightness is reached
    illuminance = np.minimum(illuminance, max_illuminance)
    return np.minimum(illuminance / max_illuminance, 1.0) * (max_val - min_val) + min_val

def samples_to_illuminance_perfect(samples, gamma=0.7, res_at_10lux=15e3):
    resistance = PULLUP_RESISTANCE * samples / (SAMPLE_COUNT - samples)
    return 10 * (res_at_10lux / resistance) ** (1/gamma)

def clampfixedpoint(value, lowerbits, upperbits):
    value = int(round(value * (2 ** lowerbits)))
    if value >= 2 ** (lowerbits + upperbits):
        value = (2 ** (lowerbits + upperbits)) - 1

    return value


class SamplesToIlluminanceApproximation:
    # The actual formula we're trying to solve works like
    # I = I_0 * (R_0  / R_pullup) ** (1 / gamma) * ((SAMPLE_COUNT - samples) / samples) ** (1 / gamma)
    def __init__(self, gamma=0.7, res_at_10lux=15e3):
        # we store a lookup table of 
        # ((SAMPLE_COUNT - samples) / samples) in 12.4 unsigned fixed point (full accuracy at low sample counts)
        # to illuminance in 10.6 unsigned fixed point
        self.table = []

        for sample in reversed((2, 4, 8, 0x10, 0x20, 0x40, 0x80, 0x100, 0x200, 0x400, 0x600, 0x800, 0xC00, 0xFFF)):

            self.table.append((
                ((SAMPLE_COUNT - sample) * (2 ** 4)) // sample,
                clampfixedpoint(samples_to_illuminance_perfect(sample, gamma, res_at_10lux), 6, 10)
            ))

        self.table.append((0xFFFF, 0xFFFF))

        for i, j in self.table:
            print(i, j)

    def table_lookup(self, value):
        # expects a 12.4 fixed point value in table lookup

        for i in range(len(self.table) - 1):
            if value <= self.table[i+1][0]:
                break

        minx, miny = self.table[i]
        maxx, maxy = self.table[i + 1]

        xdist = (maxx - minx)
        # perform interpolation in 32-bit 
        interpolated = (maxy * (value - minx) + miny * (maxx - value)) // (maxx - minx)
        # interpolated ought to be a 6.10 unsigned fixed point value now

        # interpolated &= 0xFFFF
        return interpolated

    def samples_to_illuminance(self, samples):
        rv = []
        for sample in samples:
            # pretend that we're working with integers
            sample = np.round(sample)
            assert 0 <= sample <= SAMPLE_COUNT

            if sample == 0:
                rv.append(0xFFFF)
                continue

            # calculate this in 12.4 fixed point
            sample = ((SAMPLE_COUNT - sample) * (2 ** 4)) // sample
            #sample &= 0xFFFF

            # do the lookup
            illuminance = self.table_lookup(sample)

            # convert to floating point for rendering
            rv.append(illuminance)

        return np.array(rv)

def fp_brightness(illuminance, max_illuminance=int(100 * 2**6), max_brightness=1023, min_brightness=1):
    illuminance = np.minimum(illuminance, max_illuminance)
    brightness = ((max_brightness - min_brightness) * illuminance) // max_illuminance + min_brightness
    return brightness


def main():
    illuminance = np.logspace(-4, 4, 500)

    min_resistance = calc_ldr_resistance(illuminance, res_at_10lux=MIN_RESISTANCE)
    avg_resistance = calc_ldr_resistance(illuminance, res_at_10lux=AVG_RESISTANCE)
    max_resistance = calc_ldr_resistance(illuminance, res_at_10lux=MAX_RESISTANCE)

    samples_min = SAMPLE_COUNT * min_resistance / (min_resistance + PULLUP_RESISTANCE)
    samples_avg = SAMPLE_COUNT * avg_resistance / (avg_resistance + PULLUP_RESISTANCE)
    samples_max = SAMPLE_COUNT * max_resistance / (max_resistance + PULLUP_RESISTANCE)

    estimator = SamplesToIlluminanceApproximation()
    illuminance_min = estimator.samples_to_illuminance(samples_min)
    illuminance_avg = estimator.samples_to_illuminance(samples_avg)
    illuminance_max = estimator.samples_to_illuminance(samples_max)

    brightness_target = wanted_brightness(illuminance)
    brightness_min = wanted_brightness(samples_to_illuminance_perfect(samples_min))
    brightness_avg = wanted_brightness(samples_to_illuminance_perfect(samples_avg))
    brightness_max = wanted_brightness(samples_to_illuminance_perfect(samples_max))

    brightness_actual_min = fp_brightness(illuminance_min)
    brightness_actual_avg = fp_brightness(illuminance_avg)
    brightness_actual_max = fp_brightness(illuminance_max)

    plt.figure()

    subplot = plt.subplot(3, 2, 1)
    plt.xscale("log")
    plt.yscale("log")
    plt.plot(illuminance, min_resistance, label="min resistance")
    plt.plot(illuminance, avg_resistance, label="avg resistance")
    plt.plot(illuminance, max_resistance, label="max resistance")
    plt.axvline(FULL_MOON, color="k", linewidth=0.5, label="full moon")
    plt.axvline(INDOORS, color="k", linewidth=0.5, label="indoors during day")
    plt.legend()
    plt.xlabel("illuminance [lux]")
    plt.ylabel("resistance [Ohm]")

    subplot = plt.subplot(3, 2, 2)
    plt.xscale("log")
    plt.plot(illuminance, samples_min, label="min sample count")
    plt.plot(illuminance, samples_avg, label="avg sample count")
    plt.plot(illuminance, samples_max, label="max sample count")
    plt.axvline(FULL_MOON, color="k", linewidth=0.5, label="full moon")
    plt.axvline(INDOORS, color="k", linewidth=0.5, label="indoors during day")
    plt.legend()
    plt.xlabel("illuminance [lux]")
    plt.ylabel("ldr samples [-]")

    subplot = plt.subplot(3, 2, 3)
    plt.xscale("log")
    plt.yscale("log")
    plt.plot(illuminance, brightness_target, label="target brightness count")
    plt.plot(illuminance, brightness_min, label="min brightness count theoretical")
    plt.plot(illuminance, brightness_avg, label="avg brightness count theoretical")
    plt.plot(illuminance, brightness_max, label="max brightness count theoretical")
    plt.plot(illuminance, brightness_actual_min, label="min brightness count estimated")
    plt.plot(illuminance, brightness_actual_avg, label="avg brightness count estimated")
    plt.plot(illuminance, brightness_actual_max, label="max brightness count estimated")
    plt.axvline(FULL_MOON, color="k", linewidth=0.5, label="full moon")
    plt.axvline(INDOORS, color="k", linewidth=0.5, label="indoors during day")
    plt.legend()
    plt.xlabel("illuminance [lux]")
    plt.ylabel("brightness [-]")

    subplot = plt.subplot(3, 2, 4)
    plt.plot((SAMPLE_COUNT - samples_min)/samples_min, illuminance, label="illuminance v samples_min")
    plt.plot((SAMPLE_COUNT - samples_avg)/samples_avg, illuminance, label="illuminance v samples_avg")
    plt.plot((SAMPLE_COUNT - samples_max)/samples_max, illuminance, label="illuminance v samples_max")
    plt.legend()
    plt.xlabel("1/ldr samples [-]")
    plt.ylabel("brightness [-]")

    subplot = plt.subplot(3, 2, 5)
    plt.xscale("log")
    plt.yscale("log")
    plt.plot(illuminance, illuminance_min / (2 ** 6), label="min estimated illuminance count")
    plt.plot(illuminance, illuminance_avg / (2 ** 6), label="avg estimated illuminance count")
    plt.plot(illuminance, illuminance_max / (2 ** 6), label="max estimated illuminance count")
    plt.axvline(FULL_MOON, color="k", linewidth=0.5, label="full moon")
    plt.axvline(INDOORS, color="k", linewidth=0.5, label="indoors during day")
    plt.legend()
    plt.xlabel("illuminance [lux]")
    plt.ylabel("illuminance [lux]")

    plt.show()

if __name__ == '__main__':
    main()