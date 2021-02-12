library ieee;
use ieee.std_logic_1164.all;

entity jumper is
  port (
    a : in  std_logic;
    b : in  std_logic;
    y : out std_logic
  );
end entity;

architecture behavior of jumper is
begin
  y <= a;
end architecture;
