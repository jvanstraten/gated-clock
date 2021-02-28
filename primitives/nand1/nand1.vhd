library ieee;
use ieee.std_logic_1164.all;

entity nand1 is
  port (
    a         : in  std_logic;
    y         : out std_logic;
    if_state  : out std_logic
  );
end entity;

architecture behavior of nand1 is
begin
  nand3_inst: entity work.nand3
    port map (
      a => a,
      b => '1',
      c => '1',
      y => y
    );
  if_state <= y;
end architecture;
