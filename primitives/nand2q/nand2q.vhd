library ieee;
use ieee.std_logic_1164.all;

entity nand2q is
  port (
    a         : in  std_logic;
    b         : in  std_logic;
    y         : out std_logic;
    if_state  : out std_logic
  );
end entity;

architecture behavior of nand2q is
begin
  -- Note that in nand2q pin A is delayed, in nand3qn pin B is delayed, so we
  -- need to swap pins A and B to make use of the nand3qn model.
  nand3_inst: entity work.nand3qn
    port map (
      a => b,
      b => a,
      c => '1',
      y => y
    );
  if_state <= y;
end architecture;
