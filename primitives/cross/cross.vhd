library ieee;
use ieee.std_logic_1164.all;

entity cross is
  port (
    a : in  std_logic;
    b : in  std_logic;
    x : in  std_logic;
    y : in  std_logic
  );
end entity;

architecture behavior of cross is
begin
  -- Do nothing. a and b should be connected to the same physical net in the
  -- parent circuit. Same for x and y.
end architecture;
