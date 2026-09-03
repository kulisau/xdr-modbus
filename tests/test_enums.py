"""Tests for the enumeration and flag types."""

from xdr_modbus import (
    BaudRate,
    EepConfig,
    EventCode,
    FaultStatus1,
    FaultStatus2,
    FrameFormat,
    OlpType,
    OperationInit,
    ProtectConfig,
    SystemConfig,
    SystemStatus,
)


def test_event_codes_are_sequential() -> None:
    """The event log codes follow the manual's table (8/10 reserved)."""
    assert EventCode.OUTPUT_OLP == 1
    assert EventCode.OUTPUT_OVP == 2
    assert EventCode.OTP == 3
    assert EventCode.COMM_ERROR == 4
    assert EventCode.INPUT_AC_FAIL == 5
    assert EventCode.OL_ALARM == 6
    assert EventCode.EEPROM_ERROR == 7
    assert EventCode.EMFP == 9


def test_baud_rate_enumeration() -> None:
    """Baud rates map to the documented register values."""
    assert BaudRate.BPS_4800 == 0
    assert BaudRate.BPS_115200 == 5


def test_frame_format_enumeration() -> None:
    """Frame formats map to the documented register values."""
    assert FrameFormat.NO_PARITY_2_STOP == 0
    assert FrameFormat.NO_PARITY_1_STOP == 1
    assert FrameFormat.ODD_PARITY_1_STOP == 2
    assert FrameFormat.EVEN_PARITY_1_STOP == 3


def test_configuration_bit_masks() -> None:
    """The packed-bit masks match the manual's bit layout."""
    assert SystemConfig.MOD_CTRL == 0x0001
    assert SystemConfig.PEAK_EN == 0x0008
    assert SystemConfig.EEP_OFF == 0x0400
    assert ProtectConfig.EMFP_EN == 0x0100
    assert OperationInit.ON == 0b01
    assert OlpType.CONSTANT_CURRENT == 0b01
    assert EepConfig.DELAY_10_MIN == 0b10


def test_fault_status_bit_masks() -> None:
    """The alarm bits sit on the documented positions."""
    assert FaultStatus1.OTP == 0x0002
    assert FaultStatus1.OP_OFF == 0x0040
    assert FaultStatus1.HI_TEMP == 0x0080
    assert FaultStatus2.EMFP == 0x0001
    assert FaultStatus2.OL_ALM == 0x0100
    assert SystemStatus.DC_OK == 0x0002
    assert SystemStatus.EEPROM_ERROR == 0x0040
    assert SystemStatus.REMOTE_CONTROL == 0x0100
