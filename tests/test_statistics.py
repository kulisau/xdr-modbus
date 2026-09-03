"""Tests for statistics decoding (runtimes, counters, event log)."""

from xdr_modbus import EventCode, XDRPowerSupply


async def test_runtimes(device: XDRPowerSupply) -> None:
    """The 32-bit run-time counters combine both words big-endian."""
    await device.async_update()
    assert device.statistics.total_runtime == 70000
    assert device.statistics.session_runtime == 3600


async def test_protection_counters(device: XDRPowerSupply) -> None:
    """Each protection counter reads its own register."""
    await device.async_update()
    assert device.statistics.overvoltage_protection_count == 3
    assert device.statistics.overload_protection_count == 5
    assert device.statistics.overheat_protection_count == 0
    assert device.statistics.ac_undervoltage_protection_count == 1
    assert device.statistics.ac_overvoltage_protection_count == 2


async def test_event_log(device: XDRPowerSupply) -> None:
    """The event log decodes newest-to-oldest into event codes."""
    await device.async_update()
    assert device.statistics.latest_event is EventCode.OUTPUT_OLP
    assert device.statistics.previous_event is EventCode.OUTPUT_OVP
    assert device.statistics.oldest_event is EventCode.INPUT_AC_FAIL
