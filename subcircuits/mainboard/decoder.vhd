library ieee;
use ieee.std_logic_1164.all;

entity decoder is
  port (
    An    : in  std_logic := '1';
    Bn    : in  std_logic := '1';
    Cn    : in  std_logic := '1';
    Dn    : in  std_logic := '1';
    En    : in  std_logic := '1';
    Fn    : in  std_logic := '1';
    Gn    : in  std_logic := '1';

    -- 0-9 for regular digits, -1 for space, -2 for unknown
    digit : out integer
  );
end entity;

architecture behavioral of decoder is
  signal c : std_logic_vector(6 downto 0);
begin

  c <= (not An) & (not Bn) & (not Cn) & (not Dn) & (not En) & (not Fn) & (not Gn);

  digit <= 0  when c = "1111110"
      else 1  when c = "0110000"
      else 2  when c = "1101101"
      else 3  when c = "1111001"
      else 4  when c = "0110011"
      else 5  when c = "1011011"
      else 6  when c = "1011111"
      else 7  when c = "1110000"
      else 8  when c = "1111111"
      else 9  when c = "1111011"
      else -1 when c = "0000000"
      else -2;

end architecture;
