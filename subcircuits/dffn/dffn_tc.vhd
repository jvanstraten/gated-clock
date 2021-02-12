library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

--pragma simulation timeout 1000 ms

entity dffn_tc is
end entity;

architecture test_case of dffn_tc is

  signal Clk_n  : std_logic;
  signal Clk    : std_logic;
  signal Arn    : std_logic;
  signal Dn     : std_logic;
  signal Q      : std_logic;
  signal Qn     : std_logic;

  signal prime          : std_logic;
  signal t_out_invalid  : time;
  signal t_out_valid    : time;

  signal cur_phase      : integer;
  signal cur_result     : std_logic;

begin

  clk_src: entity work.nand1
    port map (
      A => Clk_n,
      Y => Clk
    );

  uut: entity work.dffn
    port map (
      Clk   => Clk,
      ArnA  => Arn,
      ArnB  => Arn,
      Dn    => Dn,
      Q     => Q,
      Qn    => Qn
    );

  timer_proc: process (Clk_n, Q, Qn) is
    variable cur_state    : std_logic := 'U';
    variable prev_state   : std_logic := 'U';
    variable start        : time := 0 ns;
    variable primed       : boolean := false;
  begin
    if not is_x(Q) and not is_x(Qn) and to_x01(Qn) = not to_x01(Q) then
      cur_state := Q;
    else
      cur_state := 'U';
    end if;
    if falling_edge(Clk_n) then
      if primed then
        primed := false;
      end if;
      if cur_state /= 'U' and prime = '1' then
        start := now;
        prev_state := cur_state;
        t_out_invalid <= 0 ns;
        t_out_valid <= 0 ns;
        primed := true;
      end if;
    elsif primed and prev_state /= cur_state then
      if t_out_invalid = 0 ns then
        t_out_invalid <= now - start;
      elsif cur_state = 'U' then
        t_out_valid <= 0 ns;
      else
        t_out_valid <= now - start;
      end if;
      prev_state := cur_state;
    end if;
  end process;

  stim_proc: process is

    variable t_setup      : time := 0 ns;
    variable t_hold       : time := 0 ns;
    variable t_invalid    : time := 0 ns;
    variable t_valid      : time := 0 ns;

    procedure test(phase: integer) is
    begin
      prime <= '1';
      Clk_n <= '0' after 1000 ns;
      Dn <= not Dn after (phase + 1000) * 1 ns;
      wait for 10 us;
      prime <= '0';
      Clk_n <= '1';
      wait for 10 us;
      Clk_n <= '0';
      wait for 10 us;
      Clk_n <= '1';
      wait for 9 us;
      cur_phase <= phase;
      if t_out_invalid = 0 ns then
--         report "Clock to data " & integer'image(phase) & ": flipflop didn't flip";
        cur_result <= '0';
      elsif t_out_valid = 0 ns then
--         report "Clock to data " & integer'image(phase) & ": flipflop didn't stabilize";
        cur_result <= 'U';
      else
        if t_invalid = 0 ns or t_out_invalid < t_invalid then
          t_invalid := t_out_invalid;
        end if;
        if t_valid = 0 ns or t_out_valid > t_valid then
          t_valid := t_out_valid;
        end if;
--         report "Clock to data " & integer'image(phase) & ": "
--           & "flipflop went undefined " & time'image(t_out_invalid) & " after clk, "
--           & "and stable " & time'image(t_out_valid) & " after clk";
        cur_result <= '1';
      end if;
      wait for 1 us;
    end procedure;

    variable new_result   : std_logic;
    variable prev_result  : std_logic;

  begin
    Dn <= '1';
    Arn <= '0';
    Clk_n <= '1';
    wait for 10 us;
    Arn <= '1';
    wait for 10 us;
    assert Q = '0' report "Reset failed" severity failure;
    assert Qn = '1' report "Reset failed" severity failure;
    prev_result := '1';
    for i in -1000 to 3000 loop
      test(i);
      new_result := cur_result;
      test(i);
      if cur_result /= new_result then
        new_result := 'U';
      end if;
      if new_result /= prev_result then
        if new_result = 'U' and prev_result = '1' then
          t_setup := i * 1 ns;
        elsif new_result = '0' and prev_result = 'U' then
          t_hold := i * 1 ns;
        else
          report "failed to determine flipflop timing" severity failure;
        end if;
      end if;
      prev_result := new_result;
    end loop;
    assert prev_result = '0' report "flipflop doesn't actually work" severity failure;
    report "setup: " & time'image(t_setup);
    report "hold: " & time'image(t_hold);
    report "invalid: " & time'image(t_invalid);
    report "valid: " & time'image(t_valid);
    report "min datapath delay: " & time'image(t_hold - t_invalid);
    report "max datapath delay: t_clk - " & time'image(t_valid - t_setup);
    assert t_hold - t_invalid < 0 ns report "min datapath delay greater than zero; back-to-back FFs won't work!" severity failure;
    wait;
  end process;

end architecture;
