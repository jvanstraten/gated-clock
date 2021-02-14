library ieee;
use ieee.std_logic_1164.all;

entity config_uc is
  port (
    ien  : out std_logic;
    isw  : in  std_logic;
    inc  : out std_logic;
    ren  : out std_logic
  );
end entity;

architecture behavior of config_uc is
begin
  ien <= '1';
  inc <= '1';
  ren <= '1';
end architecture;
