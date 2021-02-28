library ieee;
use ieee.std_logic_1164.all;

entity ffled is
  port (
    a         : in  std_logic;
    if_state  : out std_logic
  );
end entity;

architecture behavior of ffled is
begin
  if_state <= a;
end architecture;
