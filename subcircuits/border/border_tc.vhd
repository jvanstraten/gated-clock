library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity border_tc is
end entity;

architecture test_case of border_tc is

  signal Arn    : std_logic;
  signal ClkIn  : std_logic;
  signal ClkOut : std_logic;
  signal div2   : std_logic;
  signal div5   : std_logic;

begin

  uut: entity work.border
    port map (
      Arn    => Arn,
      f50hz  => ClkIn,
      f24h_n => ClkOut,
      h5p    => div2,
      h5n    => div5,
      div2   => div2,
      div5   => div5
    );

  stim_proc: process is
  begin
    Arn <= '0';
    ClkIn <= '0';
    wait for 20 us;
    Arn <= '1';
    wait for 20 us;
    loop
      ClkIn <= '1';
      wait for 10 us;
      ClkIn <= '0';
      wait for 10 us;
    end loop;
    wait;
  end process;

end architecture;
