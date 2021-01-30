library ieee;
use ieee.std_logic_1164.all;

entity feed is
  port (
    a : in  std_logic;
    b : in  std_logic
  );
end entity;

architecture behavior of feed is
begin
  -- Do nothing. a and b should be connected to the same physical net in the
  -- parent circuit.
end architecture;
