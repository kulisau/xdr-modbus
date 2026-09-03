"""Tests for configuration writes (packed bits, thresholds, commands)."""

import pytest

from xdr_modbus import BaudRate, FrameFormat, XDRPowerSupply, XdrValueValidationError


async def test_thresholds(device: XDRPowerSupply) -> None:
    """The threshold registers decode with their documented factors."""
    await device.async_update()
    configuration = device.configuration
    assert configuration.ac_fail_threshold == 74.0
    assert configuration.ac_recover_threshold == 79.0
    assert configuration.dc_ok_threshold == 80.0
    assert configuration.peak_current_limit == 600.0
    assert configuration.overload_alarm_level == 90.0
    assert configuration.modbus_id == 131
    assert configuration.baud_rate is BaudRate.BPS_115200
    assert configuration.frame_format is FrameFormat.NO_PARITY_1_STOP


async def test_threshold_write_validated(device: XDRPowerSupply, unit) -> None:
    """Out-of-range threshold writes are rejected before reaching the wire."""
    await device.async_update()
    with pytest.raises(XdrValueValidationError):
        await device.configuration.write("dc_ok_threshold", 50.0)
    await device.configuration.write("dc_ok_threshold", 85.0)
    assert unit.holding[240] == 8500


async def test_packed_bit_write_preserves_neighbours(
    device: XDRPowerSupply, unit
) -> None:
    """Writing one config bit leaves the other bits of the register intact."""
    await device.async_update()
    # Seed value is the factory default 0x000A (OPERATION_INIT=ON, PEAK_EN=1).
    await device.configuration.write("modbus_control", True)
    assert unit.holding[196] == 0x000B
    await device.configuration.write("peak_enable", False)
    assert unit.holding[196] == 0x0003


async def test_packed_bits_write(device: XDRPowerSupply, unit) -> None:
    """Multi-bit fields merge into the register without clobbering bits."""
    await device.async_update()
    await device.configuration.write("power_on_behavior", 2)  # previous value
    assert unit.holding[196] & 0x06 == 0x04


async def test_protect_config_bits(device: XDRPowerSupply, unit) -> None:
    """PROTECT_CONFIG bits write read-modify-write."""
    await device.async_update()
    await device.configuration.write("overload_protection", 2)  # latch-off
    assert unit.holding[197] == 0x0102
    await device.configuration.write("back_emf_protection", False)
    assert unit.holding[197] == 0x0002


async def test_modbus_id_range_checked(device: XDRPowerSupply, unit) -> None:
    """The slave address is limited to 0x80-0xBF."""
    await device.async_update()
    with pytest.raises(XdrValueValidationError):
        await device.configuration.write("modbus_id", 5)
    await device.configuration.write("modbus_id", 0x84)
    assert unit.holding[2304] == 0x84


async def test_command_fields_require_aa(device: XDRPowerSupply, unit) -> None:
    """Command registers only accept the 0xAA command key."""
    await device.async_update()
    with pytest.raises(XdrValueValidationError):
        await device.configuration.write("reset_defaults", 1)
    await device.configuration.write("reset_defaults", 0xAA)
    assert unit.holding[198] == 0xAA
    await device.configuration.write("clear_event_log", 0xAA)
    assert unit.holding[2320] == 0xAA
