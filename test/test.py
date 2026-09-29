# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

# Timing based on baud_rate_generator.v (M=54, oversampled 16 times)
# 54 * 16 = 864 clock cycles per UART bit
CYCLES_PER_BIT = 864  

async def send_uart_byte(dut, byte_data):
    """Simulates a PC sending a byte to the FPGA via UART (LSB first)"""
    
    # Send Start bit (Drive line Low)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, CYCLES_PER_BIT)

    # Send 8 Data bits (LSB First)
    for i in range(8):
        bit = (byte_data >> i) & 1
        dut.ui_in.value = bit
        await ClockCycles(dut.clk, CYCLES_PER_BIT)

    # Send Stop bit (Drive line High)
    dut.ui_in.value = 1
    await ClockCycles(dut.clk, CYCLES_PER_BIT)

async def receive_uart_byte(dut):
    """Simulates a PC receiving a byte from the FPGA via UART (LSB first)"""
    
    # Wait for the Start bit (falling edge on TX, which is uo_out[0])
    while (dut.uo_out.value.integer & 1) == 1:
        await ClockCycles(dut.clk, 1)
        
    # Move to the middle of the Start bit to ensure stable sampling
    await ClockCycles(dut.clk, CYCLES_PER_BIT // 2)
    
    # Read the 8 Data bits
    byte_data = 0
    for i in range(8):
        # Move to the middle of the next data bit
        await ClockCycles(dut.clk, CYCLES_PER_BIT)
        bit = dut.uo_out.value.integer & 1
        byte_data |= (bit << i)
        
    # Wait for the Stop bit to finish
    await ClockCycles(dut.clk, CYCLES_PER_BIT)
    
    return byte_data

@cocotb.test()
async def test_uart_loopback(dut):
    dut._log.info("Starting UART Loopback Test")

    # Set the system clock period to 10 ns (100 MHz)
    clock = Clock(dut.clk, 10, unit="ns")
    cocotb.start_soon(clock.start())

    # Initialize inputs to their default states
    dut.ena.value = 1
    dut.ui_in.value = 1     # UART RX line idles HIGH
    dut.uio_in.value = 0
    
    # Apply Reset (Active Low for Tiny Tapeout)
    dut._log.info("Resetting design")
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 50) # Give the FIFOs and FSMs time to stabilize

    dut._log.info("Testing UART Loopback with value 0xA5")

    # The byte we want to send and expect to receive back
    test_byte = 0xA5 

    # Start a parallel background task to listen to the TX pin for the echo
    rx_task = cocotb.start_soon(receive_uart_byte(dut))

    # Send the byte into the RX pin
    dut._log.info(f"PC Sending byte: {hex(test_byte)}")
    await send_uart_byte(dut, test_byte)

    # Wait for the background task to capture the outgoing byte from the TX pin
    received_byte = await rx_task
    dut._log.info(f"PC Received byte: {hex(received_byte)}")

    # Assert that the loopback worked correctly
    assert received_byte == test_byte, f"Loopback failed! Expected {hex(test_byte)}, got {hex(received_byte)}"
    
    dut._log.info("UART Loopback test passed successfully!")