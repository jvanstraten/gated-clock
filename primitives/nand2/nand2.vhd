library ieee;
use ieee.std_logic_1164.all;

entity nand2 is
  port (
    a         : in  std_logic;
    b         : in  std_logic;
    y         : out std_logic;
    if_state  : out std_logic
  );
end entity;

architecture behavior of nand2 is
begin
  nand3_inst: entity work.nand3
    port map (
      a => a,
      b => b,
      c => '1',
      y => y
    );
  if_state <= y;
end architecture;
