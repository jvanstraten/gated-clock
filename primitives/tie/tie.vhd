library ieee;
use ieee.std_logic_1164.all;

entity tie is
  port (
    a : in  std_logic;
    y : out std_logic
  );
end entity;

architecture behavior of tie is
begin
  y <= a;
end architecture;
