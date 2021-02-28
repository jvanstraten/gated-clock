library ieee;
use ieee.std_logic_1164.all;

entity config_uc is
  port (
    ien     : out std_logic;
    isw     : in  std_logic;
    inc     : out std_logic;
    ren     : out std_logic;

    if_ien  : in  std_logic := '1';
    if_isw  : out std_logic;
    if_inc  : in  std_logic := '1';
    if_ren  : in  std_logic := '1'
  );
end entity;

architecture behavior of config_uc is
begin
  ien <= if_ien;
  if_isw <= isw;
  inc <= if_inc;
  ren <= if_ren;
end architecture;
