library IEEE;
use IEEE.STD_LOGIC_1164.ALL;
use IEEE.NUMERIC_STD.ALL;

entity tb_spi_flash_controller is
end tb_spi_flash_controller;

architecture sim of tb_spi_flash_controller is

    component spi_flash_controller
        Port (
            clk         : in  std_logic;
            reset       : in  std_logic;
            start       : in  std_logic;
            data_in     : in  std_logic_vector(7 downto 0);
            data_out    : out std_logic_vector(7 downto 0);
            done_flag   : out std_logic;
            spi_clk     : out std_logic;
            spi_mosi    : out std_logic;
            spi_miso    : in  std_logic;
            spi_cs      : out std_logic;
            shift_debug : out std_logic_vector(7 downto 0)
        );
    end component;

    -- Testbench signals
    signal clk         : std_logic := '0';
    signal reset       : std_logic := '1';
    signal start       : std_logic := '0';
    signal data_in     : std_logic_vector(7 downto 0) := x"A5";
    signal data_out    : std_logic_vector(7 downto 0);
    signal done_flag   : std_logic;
    signal spi_clk     : std_logic;
    signal spi_mosi    : std_logic;
    signal spi_miso    : std_logic := '1';  -- simulate '1's from slave
    signal spi_cs      : std_logic;
    signal shift_debug : std_logic_vector(7 downto 0);

    constant clk_period : time := 10 ns;

begin

    -- DUT instance
    uut: spi_flash_controller
        port map (
            clk         => clk,
            reset       => reset,
            start       => start,
            data_in     => data_in,
            data_out    => data_out,
            done_flag   => done_flag,
            spi_clk     => spi_clk,
            spi_mosi    => spi_mosi,
            spi_miso    => spi_miso,
            spi_cs      => spi_cs,
            shift_debug => shift_debug
        );

    -- Clock generation
    clk_process : process
    begin
        while true loop
            clk <= '0';
            wait for clk_period / 2;
            clk <= '1';
            wait for clk_period / 2;
        end loop;
    end process;

    -- Stimulus process
    stim_proc: process
    begin
        wait for 20 ns;
        reset <= '0';

        wait for 30 ns;
        start <= '1';
        wait for clk_period;
        start <= '0';

        wait until done_flag = '1';

        wait for 100 ns;
        assert false report "Simulation finished." severity failure;
    end process;

end sim;

