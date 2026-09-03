"""Tests for measurement decoding (input registers)."""

import pytest

from xdr_modbus import XDRPowerSupply


async def test_measurements(device: XDRPowerSupply) -> None:
    """Raw register words scale into physical units."""
    await device.async_update()
    measurements = device.measurements
    assert measurements.input_voltage == pytest.approx(230.1)
    assert measurements.output_voltage == pytest.approx(24.0)
    assert measurements.output_current == pytest.approx(5.0)
    assert measurements.internal_temperature == pytest.approx(35.5)
    assert measurements.output_power == 120


async def test_measurements_update_alone(
    device: XDRPowerSupply, mock_modbus_unit
) -> None:
    """The measurement-only refresh reads the input space only."""
    await device.async_update_measurements()
    assert device.measurements.output_voltage == pytest.approx(24.0)
    assert mock_modbus_unit.read_events
    assert all(event.register_type == "input" for event in mock_modbus_unit.read_events)
