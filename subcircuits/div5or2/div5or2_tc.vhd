library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity div5or2_tc is
end entity;

architecture test_case of div5or2_tc is

  signal Arn    : std_logic;
  signal ClkIn  : std_logic;
  signal ClkOut : std_logic;
  signal d5ap   : std_logic;
  signal d5an   : std_logic;
  signal d5bp   : std_logic;
  signal d5bn   : std_logic;
  signal d5cp   : std_logic;
  signal d5cn   : std_logic;
  signal div5   : std_logic;
  signal div2   : std_logic;

begin

  uut: entity work.div5or2
    port map (
      Arn    => Arn,
      ClkIn  => ClkIn,
      ClkOut => ClkOut,
      d5ap   => d5ap,
      d5an   => d5an,
      d5bp   => d5bp,
      d5bn   => d5bn,
      d5cp   => d5cp,
      d5cn   => d5cn,
      div5   => div5,
      div2   => div2
    );

  stim_proc: process is

    procedure check(val : in integer) is
      variable expected : std_logic_vector(2 downto 0);
      variable actual : std_logic_vector(2 downto 0);
    begin
      expected := std_logic_vector(to_unsigned(val, 3));
      assert d5ap = not d5an report "inverted output incorrect" severity failure;
      assert d5bp = not d5bn report "inverted output incorrect" severity failure;
      assert d5cp = not d5cn report "inverted output incorrect" severity failure;
      actual(0) := d5ap;
      actual(1) := d5bp;
      actual(2) := d5cp;
      assert not is_x(actual) report "output is undefined" severity failure;
      assert actual = expected
        report "expected " & integer'image(to_integer(unsigned(expected)))
             & ", got " & integer'image(to_integer(unsigned(actual)))
        severity failure;
    end procedure;

    procedure clock(val : in integer) is
    begin
      ClkIn <= '1';
      wait for 2 us;
      check(val);
      ClkIn <= '0';
      wait for 2 us;
      check(val);
    end procedure;

  begin
    Arn <= '0';
    ClkIn <= '0';
    div5 <= '1';
    div2 <= '0';
    wait for 2 us;
    Arn <= '1';
    wait for 2 us;
    check(0);
    clock(1);
    clock(3);
    clock(6);
    clock(4);
    clock(0);
    div5 <= '0';
    div2 <= '1';
    clock(1);
    clock(0);
    wait;
  end process;

end architecture;
