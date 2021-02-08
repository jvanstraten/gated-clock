library ieee;
use ieee.std_logic_1164.all;

entity nand2s is
  port (
    a : in  std_logic;
    b : in  std_logic;
    y : out std_logic
  );
end entity;

architecture behavior of nand2s is
begin
  nand3s_inst: entity work.nand3s
    port map (
      a => a,
      b => b,
      c => '1',
      y => y
    );
end architecture;
