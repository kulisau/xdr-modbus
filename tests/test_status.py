"""Tests for fault/system status flag decoding."""

from xdr_modbus import FaultStatus1, FaultStatus2, SystemStatus, XDRPowerSupply


async def test_fault_status(device: XDRPowerSupply) -> None:
    """The fault registers decode into named alarm bits."""
    await device.async_update()
    assert device.status.fault_status_1 == FaultStatus1.OTP | FaultStatus1.OVP
    assert device.status.fault_status_2 == FaultStatus2.EMFP | FaultStatus2.OL_ALM


async def test_system_status(device: XDRPowerSupply) -> None:
    """The system status decodes into named state bits."""
    await device.async_update()
    assert device.status.system_status == (
        SystemStatus.DC_OK | SystemStatus.INITIALIZED | SystemStatus.REMOTE_CONTROL
    )
