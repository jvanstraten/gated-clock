library ieee;
use ieee.std_logic_1164.all;

entity config_sw is
  port (
    run  : out std_logic;
    inc  : out std_logic
  );
end entity;

architecture behavior of config_sw is
begin
  run <= '1';
  inc <= '0';
end architecture;
