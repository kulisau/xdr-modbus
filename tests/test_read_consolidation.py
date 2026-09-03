"""Tests for pooled-read planning against the readable address ranges."""

from xdr_modbus import XDRPowerSupply
from xdr_modbus.addresses import HOLDING_RANGES, INPUT_RANGES


def _in_range(ranges: tuple[tuple[int, int], ...], address: int, count: int) -> bool:
    """True if the whole block lies inside a single declared range."""
    return any(low <= address and address + count - 1 <= high for low, high in ranges)


async def test_full_update_consolidates_reads(
    device: XDRPowerSupply, mock_modbus_unit
) -> None:
    """A full update pools fields into blocks that stay inside the ranges."""
    await device.async_update()
    events = mock_modbus_unit.read_events
    assert len(events) == 17
    for event in events:
        assert event.count <= 125
        if event.register_type == "input":
            assert _in_range(INPUT_RANGES, event.address, event.count)
        else:
            assert _in_range(HOLDING_RANGES, event.address, event.count)


async def test_full_update_never_reads_across_an_undocumented_gap(
    device: XDRPowerSupply, mock_modbus_unit
) -> None:
    """No read block spans an address the manual does not define."""
    await device.async_update()
    for event in mock_modbus_unit.read_events:
        assert _in_range(
            INPUT_RANGES if event.register_type == "input" else HOLDING_RANGES,
            event.address,
            event.count,
        )


async def test_measurements_read_in_one_block(
    device: XDRPowerSupply, mock_modbus_unit
) -> None:
    """The five measurement words pool into two input-space reads."""
    await device.async_update_measurements()
    blocks = {(event.address, event.count) for event in mock_modbus_unit.read_events}
    assert blocks == {(80, 1), (96, 4)}
