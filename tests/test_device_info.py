"""Tests for device identity and scaling-factor decoding."""

import pytest

from xdr_modbus import XDRPowerSupply
from xdr_modbus.device_info import FACTOR_NIBBLES


async def test_device_info(device: XDRPowerSupply) -> None:
    """The identity block decodes into manufacturer, model and serial."""
    await device.async_update()
    info = device.info
    assert info.manufacturer == "MEANWELL"
    assert info.model_name == "XDR-480-24"
    assert info.firmware_version == "R25.4, R10.5"
    assert info.serial_number == "251201000001"


async def test_model_definition_detected(device: XDRPowerSupply) -> None:
    """The model string parses into rated values and setpoint ranges."""
    await device.async_update()
    definition = device.model_definition
    assert definition is not None
    assert definition.name == "XDR-480-24"
    assert definition.rated_current == 20.0
    assert definition.rated_power == 480.0
    assert definition.vout_set_range == (24.0, 29.0)
    assert definition.iout_set_range == (4.0, 25.0)
    assert definition.has_modbus is True


async def test_probe_reads_identity_only(
    device: XDRPowerSupply, mock_modbus_unit
) -> None:
    """Probing a reachable unit returns identity without touching setpoints."""
    probe = await XDRPowerSupply.async_probe(mock_modbus_unit)
    assert probe.model_name == "XDR-480-24"
    assert probe.serial_number == "251201000001"
    assert probe.firmware_version == "R25.4, R10.5"
    assert probe.model_definition is not None
    assert probe.model_definition.name == "XDR-480-24"
    # Only the identity block (one pooled read) was touched.
    assert len(mock_modbus_unit.read_events) == 1


async def test_scaling_factors(device: XDRPowerSupply) -> None:
    """The live scaling-factor nibbles decode to the factory defaults."""
    await device.async_update()
    assert device.scaling.output_voltage_factor == 0.01
    assert device.scaling.output_current_factor == 0.01
    assert device.scaling.input_voltage_factor == 0.1
    assert device.scaling.temperature_factor == 0.1


@pytest.mark.parametrize(
    ("nibble", "factor"),
    [
        (0x4, 0.001),
        (0x5, 0.01),
        (0x6, 0.1),
        (0x7, 1.0),
        (0x8, 10.0),
        (0x9, 100.0),
    ],
)
def test_factor_nibbles(nibble: int, factor: float) -> None:
    """Every documented factor nibble maps to its multiplier."""
    assert FACTOR_NIBBLES[nibble] == factor
