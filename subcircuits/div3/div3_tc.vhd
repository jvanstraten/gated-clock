library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity div3_tc is
end entity;

architecture test_case of div3_tc is

  signal Arn    : std_logic;
  signal ClkIn  : std_logic;
  signal ClkOut : std_logic;
  signal d3ap   : std_logic;
  signal d3an   : std_logic;
  signal d3bp   : std_logic;
  signal d3bn   : std_logic;

begin

  uut: entity work.div3
    port map (
      Arn    => Arn,
      ClkIn  => ClkIn,
      ClkOut => ClkOut,
      d3ap   => d3ap,
      d3an   => d3an,
      d3bp   => d3bp,
      d3bn   => d3bn
    );

  stim_proc: process is

    procedure check(val : in integer) is
      variable expected : std_logic_vector(1 downto 0);
      variable actual : std_logic_vector(1 downto 0);
    begin
      expected := std_logic_vector(to_unsigned(val, 2));
      assert d3ap = not d3an report "inverted output incorrect" severity failure;
      assert d3bp = not d3bn report "inverted output incorrect" severity failure;
      actual(0) := d3ap;
      actual(1) := d3bp;
      assert not is_x(actual) report "output is undefined" severity failure;
      assert actual = expected
        report "expected " & integer'image(to_integer(unsigned(expected)))
             & ", got " & integer'image(to_integer(unsigned(actual)))
        severity failure;
    end procedure;

    procedure clock(val : in integer) is
    begin
      ClkIn <= '1';
      wait for 1 us;
      check(val);
      ClkIn <= '0';
      wait for 1 us;
      check(val);
    end procedure;

  begin
    Arn <= '0';
    ClkIn <= '0';
    wait for 2 us;
    Arn <= '1';
    wait for 2 us;
    check(0);
    clock(1);
    clock(2);
    clock(0);
    wait;
  end process;

end architecture;
