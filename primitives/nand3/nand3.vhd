library ieee;
use ieee.std_logic_1164.all;

entity nand3 is
  port (
    a : in  std_logic;
    b : in  std_logic;
    c : in  std_logic;
    y : out std_logic
  );
end entity;

architecture behavior of nand3 is
  signal y_min, y_max : std_logic;
begin

  -- Minimum time:
  --  - 1ns from the gate
  --  - ~17R equivalent gate output resistance (for pulling low)
  --  - 100R-1% for minimum series resistor
  --  - 330pF-10% for load capacitor
  --  - no additional load
  --  - switch at 30%
  -- -> 13 ns
  y_min <= not (a and b and c) after 13 ns;

  -- Minimum time:
  --  - 1ns from the gate
  --  - ~37R equivalent gate output resistance (for pulling low)
  --  - 100R+1% for minimum series resistor
  --  - 330pF+10% for load capacitor
  --  - ~300mm of trace (= 450pF)
  --  - fanout of 10 (= 30pF)
  --  - switch at 70%
  -- -> 80 ns
  y_max <= not (a and b and c) after 80 ns;

  -- As above but switch at 45% and 55%:
--   y_min <= not (a and b and c) after 26 ns;
--   y_max <= not (a and b and c) after 48 ns;

  -- As above but switch at 40% and 60%:
--   y_min <= not (a and b and c) after 21 ns;
--   y_max <= not (a and b and c) after 52 ns;

  y <= 'U' when y_min /= y_max else y_min;
end architecture;
