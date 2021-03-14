library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

--pragma simulation timeout 100000 ms

entity mainboard_tc is
end entity;

architecture test_case of mainboard_tc is

  signal Arn        : std_logic;
  signal f50hz      : std_logic;

  signal su_An      : std_logic;
  signal su_Bn      : std_logic;
  signal su_Cn      : std_logic;
  signal su_Dn      : std_logic;
  signal su_En      : std_logic;
  signal su_Fn      : std_logic;
  signal su_Gn      : std_logic;
  signal su         : integer;

  signal st_ADn     : std_logic;
  signal st_Bn      : std_logic;
  signal st_Cn      : std_logic;
  signal st_En      : std_logic;
  signal st_Fn      : std_logic;
  signal st_Gn      : std_logic;
  signal st         : integer;

  signal mu_An      : std_logic;
  signal mu_Bn      : std_logic;
  signal mu_Cn      : std_logic;
  signal mu_Dn      : std_logic;
  signal mu_En      : std_logic;
  signal mu_Fn      : std_logic;
  signal mu_Gn      : std_logic;
  signal mu         : integer;

  signal mt_ADn     : std_logic;
  signal mt_Bn      : std_logic;
  signal mt_Cn      : std_logic;
  signal mt_En      : std_logic;
  signal mt_Fn      : std_logic;
  signal mt_Gn      : std_logic;
  signal mt         : integer;

  signal hu_An      : std_logic;
  signal hu_Bn      : std_logic;
  signal hu_Cn      : std_logic;
  signal hu_Dn      : std_logic;
  signal hu_En      : std_logic;
  signal hu_Fn      : std_logic;
  signal hu_Gn      : std_logic;
  signal hu         : integer;

  signal ht_ADEGn   : std_logic;
  signal ht_Bn      : std_logic;
  signal ht_Cn      : std_logic;
  signal ht         : integer;

  signal fsel       : natural := 0;
  signal mcfg_sw    : natural := 0;
  signal hcfg_sw    : natural := 0;

  signal mcfw_ien   : std_logic := '1';
  signal mcfw_inc   : std_logic := '1';
  signal mcfw_ren   : std_logic := '1';
  signal hcfw_ien   : std_logic := '1';
  signal hcfw_inc   : std_logic := '1';
  signal hcfw_ren   : std_logic := '1';

begin

  uut: entity work.mainboard
    port map (
      Arn                   => Arn,
      f50hz                 => f50hz,
      su_An                 => su_An,
      su_Bn                 => su_Bn,
      su_Cn                 => su_Cn,
      su_Dn                 => su_Dn,
      su_En                 => su_En,
      su_Fn                 => su_Fn,
      su_Gn                 => su_Gn,
      st_ADn                => st_ADn,
      st_Bn                 => st_Bn,
      st_Cn                 => st_Cn,
      st_En                 => st_En,
      st_Fn                 => st_Fn,
      st_Gn                 => st_Gn,
      mu_An                 => mu_An,
      mu_Bn                 => mu_Bn,
      mu_Cn                 => mu_Cn,
      mu_Dn                 => mu_Dn,
      mu_En                 => mu_En,
      mu_Fn                 => mu_Fn,
      mu_Gn                 => mu_Gn,
      mt_ADn                => mt_ADn,
      mt_Bn                 => mt_Bn,
      mt_Cn                 => mt_Cn,
      mt_En                 => mt_En,
      mt_Fn                 => mt_Fn,
      mt_Gn                 => mt_Gn,
      hu_An                 => hu_An,
      hu_Bn                 => hu_Bn,
      hu_Cn                 => hu_Cn,
      hu_Dn                 => hu_Dn,
      hu_En                 => hu_En,
      hu_Fn                 => hu_Fn,
      hu_Gn                 => hu_Gn,
      ht_ADEGn              => ht_ADEGn,
      ht_Bn                 => ht_Bn,
      ht_Cn                 => ht_Cn,
      if_ff_fd2_C_s1_state  => fsel,
      if_ff_fd2_s1_state    => fsel,
      if_ff_fd2_s2_state    => fsel,
      if_ff_mcfg_S_state    => mcfg_sw,
      if_ff_mcfg_uc_ien     => mcfw_ien,
      if_ff_mcfg_uc_inc     => mcfw_inc,
      if_ff_mcfg_uc_ren     => mcfw_ren,
      if_ff_hcfg_S_state    => hcfg_sw,
      if_ff_hcfg_uc_ien     => hcfw_ien,
      if_ff_hcfg_uc_inc     => mcfw_inc,
      if_ff_hcfg_uc_ren     => mcfw_ren
    );

  su_dec: entity work.decoder
    port map (
      An    => su_An,
      Bn    => su_Bn,
      Cn    => su_Cn,
      Dn    => su_Dn,
      En    => su_En,
      Fn    => su_Fn,
      Gn    => su_Gn,
      digit => su
    );

  st_dec: entity work.decoder
    port map (
      An    => st_ADn,
      Bn    => st_Bn,
      Cn    => st_Cn,
      Dn    => st_ADn,
      En    => st_En,
      Fn    => st_Fn,
      Gn    => st_Gn,
      digit => st
    );

  mu_dec: entity work.decoder
    port map (
      An    => mu_An,
      Bn    => mu_Bn,
      Cn    => mu_Cn,
      Dn    => mu_Dn,
      En    => mu_En,
      Fn    => mu_Fn,
      Gn    => mu_Gn,
      digit => mu
    );

  mt_dec: entity work.decoder
    port map (
      An    => mt_ADn,
      Bn    => mt_Bn,
      Cn    => mt_Cn,
      Dn    => mt_ADn,
      En    => mt_En,
      Fn    => mt_Fn,
      Gn    => mt_Gn,
      digit => mt
    );

  hu_dec: entity work.decoder
    port map (
      An    => hu_An,
      Bn    => hu_Bn,
      Cn    => hu_Cn,
      Dn    => hu_Dn,
      En    => hu_En,
      Fn    => hu_Fn,
      Gn    => hu_Gn,
      digit => hu
    );

  ht_dec: entity work.decoder
    port map (
      An    => ht_ADEGn,
      Bn    => ht_Bn,
      Cn    => ht_Cn,
      Dn    => ht_ADEGn,
      En    => ht_ADEGn,
      Fn    => '1',
      Gn    => ht_ADEGn,
      digit => ht
    );

  stim_proc: process is

    procedure check(h: natural; m: natural; s: natural) is
      variable h_actual, m_actual, s_actual : natural;
    begin
      assert su >= 0 report "seconds unit digit is undefined" severity failure;
      assert st >= 0 and st < 6 report "seconds tens digit is undefined" severity failure;
      s_actual := st * 10 + su;

      assert mu >= 0 report "minutes unit digit is undefined" severity failure;
      assert mt >= 0 and mt < 6 report "minutes tens digit is undefined" severity failure;
      m_actual := mt * 10 + mu;

      assert hu >= 0 report "hours unit digit is undefined" severity failure;
      assert ht >= -1 and ht < 3 report "hours tens digit is undefined" severity failure;
      if ht = -1 then
        h_actual := hu;
      else
        h_actual := ht * 10 + hu;
      end if;

      assert h = h_actual and m = m_actual and s = s_actual
        report "display reads " & integer'image(h_actual) & ":" & integer'image(m_actual) & ":" & integer'image(s_actual)
             & " but should read " & integer'image(h) & ":" & integer'image(m) & ":" & integer'image(s)
        severity failure;
    end procedure;

  begin

    fsel       <= 0;
    mcfg_sw    <= 0;
    hcfg_sw    <= 0;

    mcfw_ien   <= '1';
    mcfw_inc   <= '1';
    mcfw_ren   <= '1';
    hcfw_ien   <= '1';
    mcfw_inc   <= '1';
    mcfw_ren   <= '1';

    Arn <= '0';
    f50hz <= '0';
    wait for 10 us;
    Arn <= '1';
    wait for 10 us;

    for h in 0 to 23 loop
      for m in 0 to 59 loop
        report "the time is now " & integer'image(h) & ":" & integer'image(m) severity note;
        for s in 0 to 59 loop
          for f in 0 to 49 loop
            check(h, m, s);

            -- 1000x speed
            f50hz <= '1';
            wait for 10 us;
            f50hz <= '0';
            wait for 10 us;

          end loop;
        end loop;
      end loop;
    end loop;
    check(0, 0, 0);
    wait;

  end process;

end architecture;
