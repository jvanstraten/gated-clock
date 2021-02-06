library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity div2_tc is
end entity;

architecture test_case of div2_tc is

  signal Arn    : std_logic;
  signal ClkIn  : std_logic;
  signal ClkOut : std_logic;
  signal d2p    : std_logic;
  signal d2n    : std_logic;

begin

  uut: entity work.div2
    port map (
      Arn    => Arn,
      ClkIn  => ClkIn,
      ClkOut => ClkOut,
      d2p    => d2p,
      d2n    => d2n
    );

  stim_proc: process is

    procedure check(val : in integer) is
      variable expected : std_logic_vector(0 downto 0);
      variable actual : std_logic_vector(0 downto 0);
    begin
      expected := std_logic_vector(to_unsigned(val, 1));
      assert d2p = not d2n report "inverted output incorrect" severity failure;
      actual(0) := d2p;
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
    wait for 1 us;
    Arn <= '1';
    wait for 1 us;
    check(0);
    clock(1);
    clock(0);
    wait;
  end process;

end architecture;
