"""Tests for the datapoint metadata attached to fields."""

from xdr_modbus import XDRPowerSupply, metadata_for, require_metadata_for
from xdr_modbus.components.control import Control
from xdr_modbus.components.measurements import Measurements


def test_number_metadata() -> None:
    """A scaled field reports unit, digits and the raw register range."""
    field = Control.declared_fields["voltage_setpoint"]
    metadata = require_metadata_for(field)
    assert metadata.command == "VOUT_SET"
    assert metadata.writable is True
    assert metadata.number is not None
    assert metadata.number.unit == "V"
    assert metadata.number.digits == 2


def test_readonly_field_not_writable() -> None:
    """Measurement fields are read-only metadata."""
    metadata = require_metadata_for(Measurements.declared_fields["input_voltage"])
    assert metadata.writable is False
    assert metadata.number is not None
    assert metadata.number.unit == "V"


def test_metadata_for_missing_returns_none() -> None:
    """Fields without metadata report None instead of raising."""
    assert metadata_for(object()) is None


async def test_component_declared_fields(device: XDRPowerSupply) -> None:
    """Every declared field on every live component carries metadata."""
    for component in device.components:
        for name, field in component.declared_fields.items():
            assert metadata_for(field) is not None, f"{type(component).__name__}.{name}"
