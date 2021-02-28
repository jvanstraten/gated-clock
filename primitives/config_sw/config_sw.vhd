library ieee;
use ieee.std_logic_1164.all;

entity config_sw is
  port (
    run       : out std_logic;
    inc       : out std_logic;
    if_state  : in  natural := 0
  );
end entity;

architecture behavior of config_sw is
begin
  run <= '1' when if_state = 0 else '0';
  inc <= '1' when if_state = 2 else '0';
end architecture;
