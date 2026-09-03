"""Tests for output control writes (OPERATION, VOUT_SET, IOUT_SET)."""

import pytest

from xdr_modbus import XDRPowerSupply, XdrValueValidationError


async def test_operation_write(device: XDRPowerSupply, unit) -> None:
    """Switching the output writes 0/1 to OPERATION (0x00)."""
    await device.async_update()
    await device.async_set_output(False)
    assert unit.holding[0] == 0
    await device.async_set_output(True)
    assert unit.holding[0] == 1


async def test_voltage_setpoint_write(device: XDRPowerSupply, unit) -> None:
    """A setpoint inside the model range encodes with the 0.01 factor."""
    await device.async_update()
    await device.async_set_voltage(26.5)
    assert unit.holding[32] == 2650


async def test_current_setpoint_write(device: XDRPowerSupply, unit) -> None:
    """The current limit encodes with the 0.01 factor."""
    await device.async_update()
    await device.async_set_current(12.5)
    assert unit.holding[48] == 1250


async def test_voltage_setpoint_range_checked(device: XDRPowerSupply, unit) -> None:
    """XDR-480-24 only accepts 24.0-29.0 V; out-of-range writes are rejected."""
    await device.async_update()
    with pytest.raises(XdrValueValidationError):
        await device.async_set_voltage(45.0)
    with pytest.raises(XdrValueValidationError):
        await device.async_set_voltage(23.5)
    # A boundary value is accepted.
    await device.async_set_voltage(29.0)
    assert unit.holding[32] == 2900


async def test_current_setpoint_range_checked(device: XDRPowerSupply, unit) -> None:
    """IOUT_SET is validated against 20-125 % of the rated current (4-25 A)."""
    await device.async_update()
    with pytest.raises(XdrValueValidationError):
        await device.async_set_current(30.0)
    with pytest.raises(XdrValueValidationError):
        await device.async_set_current(2.0)
    await device.async_set_current(25.0)
    assert unit.holding[48] == 2500


async def test_unknown_model_skips_validation(
    mock_modbus_unit,
) -> None:
    """Without a detected model, setpoint writes pass through unvalidated."""
    # Blank the model registers so parsing fails.
    for address in range(134, 140):
        mock_modbus_unit.holding[address] = 0x2020
    device = XDRPowerSupply(mock_modbus_unit)
    await device.async_update()
    assert device.model_definition is None
    await device.async_set_voltage(45.0)  # no model, no range check
    assert mock_modbus_unit.holding[32] == 4500


async def test_model_override_from_constructor(mock_modbus_unit) -> None:
    """A caller-supplied model enables validation before identity is read."""
    device = XDRPowerSupply(mock_modbus_unit, model="XDR-240-24")
    assert device.model_definition is not None
    assert device.model_definition.rated_current == 10.0
    await device.async_update()
    with pytest.raises(XdrValueValidationError):
        await device.async_set_current(20.0)
