library ieee;
use ieee.std_logic_1164.all;

entity nand3qn is
  port (
    a : in  std_logic;
    b : in  std_logic;
    c : in  std_logic;
    y : out std_logic
  );
end entity;

architecture behavior of nand3qn is
  signal b_dly        : std_logic;
  signal y_min, y_max : std_logic;
begin

  -- RC filter in path for B adds at least 699 ns and at most ~2943 ns to the
  -- datapath latency (1k +/- 1%, 2.2nF +/- 10%, to 30%/70% Vcc). Since this
  -- only exists to fix the hold path, we're only interested in this minimum
  -- latency; the maximum latency just affects the maximum clock frequency,
  -- which is multiple orders of magnitude higher than it needs to be anyway.
  -- In fact, in order to make the entire circuit work in simulation, we need
  -- to be a bit more optimistic about the switching uncertainty of the FF
  -- output than we would be if we'd just pass all undefineds unchanged; it's
  -- impossible to distinguish between uncertain timing for an edge (for which
  -- we only care about the minimum latency, as noted) and slow edge timing
  -- (which is only determined by this flipflop anyway), so without hacks here
  -- the uncertainty would compound from divider to divider until everything
  -- is undefined. Fortunately, VHDL's inertial delay model gets the job done
  -- here.
  b_dly <= b after 699 ns;

  -- Minimum time:
  --  - 1ns from the gate
  --  - ~17R equivalent gate output resistance (for pulling low)
  --  - 100R-1% for minimum series resistor
  --  - 330pF-10% for load capacitor
  --  - no additional load
  --  - switch at 30%
  -- -> 13 ns
  y_min <= not (a and b_dly and c) after 13 ns;

  -- Minimum time:
  --  - 1ns from the gate
  --  - ~37R equivalent gate output resistance (for pulling low)
  --  - 100R+1% for minimum series resistor
  --  - 330pF+10% for load capacitor
  --  - ~300mm of trace (= 450pF)
  --  - fanout of 10 (= 30pF)
  --  - switch at 70%
  -- -> 80 ns
  y_max <= not (a and b_dly and c) after 80 ns;

  -- As above but switch at 45% and 55%:
--   y_min <= not (a and b and c) after 26 ns;
--   y_max <= not (a and b and c) after 48 ns;

  -- As above but switch at 40% and 60%:
--   y_min <= not (a and b and c) after 21 ns;
--   y_max <= not (a and b and c) after 52 ns;

  y <= 'U' when y_min /= y_max else y_min;
end architecture;
