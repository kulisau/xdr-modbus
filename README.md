# xdr-modbus Python library

[![CI](https://github.com/kulisau/xdr-modbus/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/kulisau/xdr-modbus/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/xdr-modbus)](https://pypi.org/project/xdr-modbus/)
[![Python versions](https://img.shields.io/pypi/pyversions/xdr-modbus)](https://pypi.org/project/xdr-modbus/)
[![License](https://img.shields.io/github/license/kulisau/xdr-modbus)](LICENSE)

`xdr-modbus` is an async Python device library for the
[Mean Well XDR series](https://www.meanwell.com) of DIN-rail power supplies
(XDR-240 / XDR-480 / XDR-960 and their 12/24/36/48 V output variants). It
models the device's Modbus registers as typed Python attributes and reads them
in as few requests as possible.

## Purpose and scope

- Full device model built on the backend-neutral
  [`modbus-connection`](https://github.com/home-assistant-libs/modbus-connection)
  modelling framework — swap the Modbus backend without touching device code.
- **The library does not own the transport.** The caller injects a
  `modbus_connection.ModbusUnit` (TCP, UDP, TLS or serial, pymodbus or
  tmodbus backend) and keeps control of the connection lifecycle.
- Live measurements (input/output voltage and current, internal temperature,
  output power), fault and system status flags, output on/off plus voltage
  and current setpoints with per-model range validation, protection
  thresholds, communication settings, run-time counters and the 3-deep
  non-volatile fault event log.
- Neutral datapoint metadata (scaling, unit, min/max, enumeration members)
  attached to every field, so a UI layer can render controls without knowing
  the register layout.
- Reads are pooled into as few block reads as the device allows; writable
  packed-bit settings are written read-modify-write so neighbouring bits are
  never clobbered.

## Supported models

Modbus communication is available on the XDR-240, XDR-480 and XDR-960
families:

| Family | 12 V | 24 V | 36 V | 48 V |
| ------ | ---- | ---- | ---- | ---- |
| XDR-240 | 20 A / 240 W | 10 A / 240 W | 6.66 A / 240 W | 5 A / 240 W |
| XDR-480 | 30 A / 360 W | 20 A / 480 W | 13.3 A / 480 W | 10 A / 480 W |
| XDR-960 | — | 40 A / 960 W | 26.6 A / 957.6 W | 20 A / 960 W |

The device is a Modbus **RTU** device (RS-485, default 115200 8N1, slave
address `0x83`); over a network it is reached through a transparent
TCP↔serial gateway.

## Usage

```python
import asyncio

from modbus_connection import ModbusTcpParams
from modbus_connection.pymodbus import ModbusConnection

from xdr_modbus import XDRPowerSupply


async def main() -> None:
    connection = ModbusConnection(ModbusTcpParams(host="192.168.32.29", framer="rtu"))
    unit = connection.for_unit(131)  # 0x83, the factory-default slave address
    try:
        device = XDRPowerSupply(unit)
        await device.async_update()
        print(device.info.model_name)                    # e.g. "XDR-480-24"
        print(device.measurements.output_voltage)        # e.g. 24.0
        print(device.status.fault_status_1)              # e.g. <FaultStatus1: 0>
        await device.async_set_voltage(26.5)             # range-checked write
    finally:
        await connection.close()


asyncio.run(main())
```

A ready-made diagnostic CLI prints every value of a reachable device:

```bash
pip install xdr-modbus[cli]
python script/query.py tcp 192.168.32.29 --unit 131
python script/query.py serial /dev/ttyUSB0 --baudrate 115200
```

## Testing and validation

The test-suite runs entirely against the in-memory mock backend that ships
with `modbus-connection` — no hardware or Modbus server is needed:

```bash
script/run_checks.sh   # format check, lint, compile, tests, package build
```

## Documentation, development and contribution guidelines

- Every sub-system is a `modbus_connection.model.Component` subclass; field
  factories live in `xdr_modbus.data_model` and attach neutral metadata.
- Register addresses and the readable address ranges are defined in
  `xdr_modbus.addresses` and mirror the manufacturer manual (XDR-75~960-E, §6).
- Development happens on the `develop` branch; PRs to `main` are only
  accepted from `develop`. CI runs formatting (Ruff), lint, `compileall`,
  the test-suite and a package build on every push.

## License

[Apache-2.0](LICENSE)
