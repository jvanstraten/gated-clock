library ieee;
use ieee.std_logic_1164.all;

entity jumper is
  port (
    a         : in  std_logic;
    b         : in  std_logic;
    y         : out std_logic;

    if_state  : in  natural := 0
  );
end entity;

architecture behavior of jumper is
begin
  y <= a when if_state = 0 else b when if_state = 1 else '0';
end architecture;
