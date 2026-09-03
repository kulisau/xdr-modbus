"""Fixtures for the XDR tests.

The ``mock_modbus_connection`` fixture comes from the ``modbus_connection``
library's pytest plugin (registered as a ``pytest11`` entry point). Seeding
the unit's stores drives the real ``xdr_modbus`` library exactly as a device
would; every entry is commented with the decoded view.
"""

import pytest
from modbus_connection.mock import MockModbusConnection, MockModbusUnit

from xdr_modbus import XDRPowerSupply

UNIT_ID = 131  # 0x83, the factory-default slave address


def _ascii_words(text: str, start: int) -> dict[int, int]:
    """Pack ASCII into big-endian register words, two characters each."""
    padded = text.ljust(6)[:6]
    return {
        start + offset: (ord(padded[2 * offset]) << 8) | ord(padded[2 * offset + 1])
        for offset in range(3)
    }


# Input registers (FC 0x04).
INPUT: dict[int, int] = {
    80: 2301,  # measurements.input_voltage -> 230.1 V
    96: 2400,  # measurements.output_voltage -> 24.00 V
    97: 500,  # measurements.output_current -> 5.00 A
    98: 355,  # measurements.internal_temperature -> 35.5 °C
    99: 120,  # measurements.output_power -> 120 W
}

# Holding registers (FC 0x03 / 0x06).
HOLDING: dict[int, int] = {
    0: 1,  # control.operation -> True
    32: 2400,  # control.voltage_setpoint -> 24.00 V
    48: 2000,  # control.current_setpoint -> 20.00 A
    64: 0x0006,  # status.fault_status_1 -> OTP | OVP
    65: 0x0101,  # status.fault_status_2 -> EMFP | OL_ALM
    195: 0x0122,  # status.system_status -> DC_OK | INITIALIZED | REMOTE_CONTROL
    196: 0x000A,  # configuration: OPERATION_INIT=ON, PEAK_EN=1 (factory default)
    197: 0x0101,  # configuration: OLP_TYPE=constant current, EMFP_EN=1
    198: 0,
    224: 740,  # configuration.ac_fail_threshold -> 74.0 V
    226: 790,  # configuration.ac_recover_threshold -> 79.0 V
    240: 8000,  # configuration.dc_ok_threshold -> 80 %
    241: 60000,  # configuration.peak_current_limit -> 600 %
    243: 9000,  # configuration.overload_alarm_level -> 90 %
    2304: 131,  # configuration.modbus_id -> 0x83
    2305: 5,  # configuration.baud_rate -> BaudRate.BPS_115200
    2306: 1,  # configuration.frame_format -> NO_PARITY_1_STOP
    2320: 0,
    2323: 1,  # statistics.total_runtime (uint32 high word)
    2324: 4464,  # -> 70000
    2325: 0,  # statistics.session_runtime (uint32 high word)
    2326: 3600,  # -> 3600
    2329: 3,  # statistics.overvoltage_protection_count
    2330: 5,  # statistics.overload_protection_count
    2331: 0,  # statistics.overheat_protection_count
    2332: 1,  # statistics.ac_undervoltage_protection_count
    2333: 2,  # statistics.ac_overvoltage_protection_count
    2337: 1,  # statistics.latest_event -> OUTPUT_OLP
    2338: 2,  # statistics.previous_event -> OUTPUT_OVP
    2339: 5,  # statistics.oldest_event -> INPUT_AC_FAIL
}
HOLDING.update(
    {
        **_ascii_words("MEANWE", 128),  # info.manufacturer (first half)
        **_ascii_words("LL", 131),  # info.manufacturer (second half)
        **_ascii_words("XDR-48", 134),  # info.model_name (first half)
        **_ascii_words("0-24", 137),  # info.model_name (second half)
        140: 0xFE69,  # info.firmware_version MCU 1-2 -> R25.4, R10.5
        141: 0xFFFF,  # no MCU 3-4
        142: 0xFFFF,  # no MCU 5-6
        **_ascii_words("251201", 148),  # info.serial_number (first half)
        **_ascii_words("000001", 151),  # info.serial_number (second half)
        192: 0x55,  # scaling: VOUT 0.01, IOUT 0.01
        193: 0x06,  # scaling: VIN 0.1
        194: 0x06,  # scaling: temperature 0.1
    }
)


@pytest.fixture
def mock_modbus_unit(
    mock_modbus_connection: MockModbusConnection,
) -> MockModbusUnit:
    """A seeded XDR-480-24 on unit ``UNIT_ID``.

    Overrides the library plugin's ``mock_modbus_unit`` to pick the XDR unit
    and preload a full device register image.
    """
    unit = mock_modbus_connection.for_unit(UNIT_ID)
    unit.input.update(INPUT)
    unit.holding.update(HOLDING)
    return unit


@pytest.fixture
def device(mock_modbus_unit: MockModbusUnit) -> XDRPowerSupply:
    """An XDRPowerSupply over the mock unit."""
    return XDRPowerSupply(mock_modbus_unit)


@pytest.fixture
def unit(mock_modbus_unit: MockModbusUnit) -> MockModbusUnit:
    """The mock unit the ``device`` fixture reads and writes through."""
    return mock_modbus_unit
