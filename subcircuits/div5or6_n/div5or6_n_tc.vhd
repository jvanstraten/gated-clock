library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity div5or6_n_tc is
end entity;

architecture test_case of div5or6_n_tc is

  signal Arn    : std_logic;
  signal ClkIn_n: std_logic;
  signal ClkIn  : std_logic;
  signal ClkOut : std_logic;
  signal mode     : natural := 0;

  signal counter  : natural := 0;

begin

  clk_src: entity work.nand1
    port map (
      A => ClkIn_n,
      Y => ClkIn
    );

  uut: entity work.div5or6_n
    port map (
      Arn    => Arn,
      ClkIn  => ClkIn,
      ClkOut => ClkOut,
      if_c_s1_state => mode,
      if_s1_state => mode,
      if_s2_state => mode
    );

  count_proc: process (ClkOut, Arn) is
  begin
    if Arn = '0' then
      counter <= 0;
    elsif ClkOut'event and ClkOut = '1' then
      counter <= counter + 1;
    end if;
  end process;

  stim_proc: process is

    procedure clock(val : in natural) is
    begin
      ClkIn_n <= '0';
      wait for 5 us;
      assert counter = val
        report integer'image(counter) & " rising clock edges have occured, "
          & "but expected " & integer'image(val)
        severity failure;
      ClkIn_n <= '1';
      wait for 5 us;
      assert counter = val
        report integer'image(counter) & " rising clock edges have occured, "
          & "but expected " & integer'image(val)
        severity failure;
    end procedure;

  begin
    mode <= 0; -- 50Hz
    Arn <= '0';
    ClkIn_n <= '1';
    wait for 2 us;
    Arn <= '1';
    wait for 2 us;
    assert ClkOut = '1' report "clock out is not high after reset" severity failure;
    clock(0);
    clock(0);
    clock(0);
    clock(0);
    clock(1);
    clock(1);
    clock(1);
    clock(1);
    clock(1);
    clock(2);

    wait for 2 us;

    mode <= 1; -- 60Hz
    Arn <= '0';
    ClkIn_n <= '1';
    wait for 2 us;
    Arn <= '1';
    wait for 2 us;
    assert ClkOut = '1' report "clock out is not high after reset" severity failure;
    clock(0);
    clock(0);
    clock(0);
    clock(0);
    clock(0);
    clock(1);
    clock(1);
    clock(1);
    clock(1);
    clock(1);
    clock(1);
    clock(2);
    wait;
  end process;

end architecture;
