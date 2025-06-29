library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity spi_flash_controller is
    Port (
        clk         : in  std_logic;
        reset       : in  std_logic;
        start       : in  std_logic;
        data_in     : in  std_logic_vector(7 downto 0);
        data_out    : out std_logic_vector(7 downto 0);
        done_flag   : out std_logic;

        -- SPI signals
        spi_clk     : out std_logic;
        spi_mosi    : out std_logic;
        spi_miso    : in  std_logic;
        spi_cs      : out std_logic;

        -- Debug signal (internal shift register)
        shift_debug : out std_logic_vector(7 downto 0)
    );
end spi_flash_controller;

architecture Behavioral of spi_flash_controller is

    type state_type is (IDLE, ASSERT_CS, TRANSFER, STATE_DONE);
    signal state        : state_type := IDLE;

    signal clk_div_cnt  : integer := 0;
    constant CLK_DIV    : integer := 4;
    signal spi_clk_int  : std_logic := '0';

    signal bit_cnt      : integer range 0 to 7 := 0;
    signal shift_reg_tx : std_logic_vector(7 downto 0);
    signal shift_reg_rx : std_logic_vector(7 downto 0);

begin

    shift_debug <= shift_reg_rx;  -- assign debug output

    process(clk, reset)
    begin
        if reset = '1' then
            state <= IDLE;
            spi_cs <= '1';
            spi_clk_int <= '0';
            done_flag <= '0';
            spi_mosi <= '0';
        elsif rising_edge(clk) then

            -- Clock divider
            if clk_div_cnt = CLK_DIV then
                clk_div_cnt <= 0;
                spi_clk_int <= not spi_clk_int;
            else
                clk_div_cnt <= clk_div_cnt + 1;
            end if;

            case state is
                when IDLE =>
                    done_flag <= '0';
                    spi_cs <= '1';
                    if start = '1' then
                        shift_reg_tx <= data_in;
                        bit_cnt <= 7;
                        state <= ASSERT_CS;
                    end if;

                when ASSERT_CS =>
                    spi_cs <= '0';
                    state <= TRANSFER;

                when TRANSFER =>
                    if spi_clk_int = '0' then
                        spi_mosi <= shift_reg_tx(bit_cnt);  -- Drive data on falling edge
                    elsif spi_clk_int = '1' then
                        shift_reg_rx(bit_cnt) <= spi_miso;  -- Sample MISO on rising edge
                        if bit_cnt = 0 then
                            state <= STATE_DONE;
                        else
                            bit_cnt <= bit_cnt - 1;
                        end if;
                    end if;

                when STATE_DONE =>
                    data_out <= shift_reg_rx;
                    done_flag <= '1';
                    spi_cs <= '1';
                    state <= IDLE;
            end case;
        end if;
    end process;

    spi_clk <= spi_clk_int;

end Behavioral;

