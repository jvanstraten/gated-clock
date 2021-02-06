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

  -- Minimum propagation delay is 1 ns (74LVC1G10 datasheet). With series
  -- resistance and minimal loading, it should be more like 3 ns.
  y_min <= not (a and b and c) after 3 ns;

  -- Maximum propagation delay is guesstimated. Chip maximum is 3.6 ns, traces
  -- are about 5.6 ns/m, and the better-safe-than-sorry series resistor will
  -- add some delay as well. It's all peanuts according to LTspice, maybe
  -- 6-10ns. So let's add some safety margin and call it 15.
  y_max <= not (a and b and c) after 8 ns;

  y <= 'U' when y_min /= y_max else y_min;
end architecture;
