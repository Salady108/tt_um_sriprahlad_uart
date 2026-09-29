`default_nettype none

module tt_um_sriprahlad_uart (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);

    // 1. Assign bidirectional pins as inputs (since we aren't using them)
    assign uio_oe  = 8'b00000000;
    assign uio_out = 8'b00000000;
    
    // 2. Map standard pins to UART Interface
    wire reset = ~rst_n;        // UART interface expects active-high reset
    wire rx_pin = ui_in[0];     // Use dedicated input 0 for RX
    wire tx_pin;                
    assign uo_out[0] = tx_pin;  // Use dedicated output 0 for TX
    
    // HFT Core / Streaming Interface connections
    wire [7:0] rx_data_stream;
    wire rx_valid_stream;
    wire [7:0] tx_data_stream;
    wire tx_valid_stream;
    
    // 3. Loopback testing setup
    // Connect the RX stream directly back into the TX stream for echo testing
    assign tx_data_stream = rx_data_stream;
    assign tx_valid_stream = rx_valid_stream;

    // Ground unused dedicated outputs to prevent floating states
    assign uo_out[7:1] = 7'b0000000;

    // 4. Instantiate the UART Interface
    uart_interface UART_WRAPPER (
        .clk(clk),
        .reset(reset),
        .rx(rx_pin),
        .tx(tx_pin),
        .rx_data(rx_data_stream),
        .rx_valid(rx_valid_stream),
        .tx_data(tx_data_stream),
        .tx_valid(tx_valid_stream)
    );

endmodule