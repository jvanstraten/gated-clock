library ieee;
use ieee.std_logic_1164.all;

entity nand1s is
  port (
    a : in  std_logic;
    y : out std_logic
  );
end entity;

architecture behavior of nand1s is
begin
  nand3s_inst: entity work.nand3s
    port map (
      a => a,
      b => '1',
      c => '1',
      y => y
    );
end architecture;
