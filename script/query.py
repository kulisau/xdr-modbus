#!/usr/bin/env python3

"""Query a Mean Well XDR power supply over Modbus and print every value.

Connects over Modbus TCP (a network gateway) or a serial/USB port, reads the
whole device once, and dumps every sub-system's values to the terminal. Handy
for checking a real power supply without any automation platform.

The library only needs the connection protocol; this script selects the
pymodbus backend, so install the ``cli`` extra first.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time

from modbus_connection import (
    ModbusConnection,
    ModbusError,
    ModbusSerialParams,
    ModbusTcpParams,
)
from modbus_connection.cli_helper import CountingUnit, print_component

from xdr_modbus import XDRPowerSupply

# (label, attribute name on XDRPowerSupply) — the order in which sections print.
SECTIONS: list[tuple[str, str]] = [
    ("Device", "info"),
    ("Scaling factors", "scaling"),
    ("Measurements", "measurements"),
    ("Output control", "control"),
    ("Status", "status"),
    ("Configuration", "configuration"),
    ("Statistics", "statistics"),
]


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="transport", required=True)

    # Shared options available on each transport (so --unit can follow the host).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--unit",
        type=int,
        default=131,  # 0x83, the XDR factory-default slave address
        help="Modbus unit/slave address (default: 131 = 0x83)",
    )
    tcp = sub.add_parser(
        "tcp",
        parents=[common],
        help="connect over Modbus TCP (network gateway)",
    )
    tcp.add_argument("host", help="hostname or IP of the gateway/device")
    tcp.add_argument("--port", type=int, default=502, help="TCP port (default: 502)")
    tcp.add_argument(
        "--framer",
        choices=("rtu", "socket"),
        default="rtu",
        help=(
            "wire framing: 'rtu' for RTU-over-TCP (transparent serial gateways, "
            "the XDR default) or 'socket' for native Modbus TCP (default: rtu)"
        ),
    )
    serial = sub.add_parser(
        "serial",
        parents=[common],
        help="connect over a serial/USB port",
    )
    serial.add_argument("device", help="serial device, e.g. /dev/ttyUSB0")
    serial.add_argument("--baudrate", type=int, default=115200, help="default: 115200")
    serial.add_argument("--parity", choices=("N", "E", "O"), default="N")
    serial.add_argument("--stopbits", type=int, choices=(1, 2), default=1)
    serial.add_argument("--bytesize", type=int, choices=(7, 8), default=8)
    return parser.parse_args(argv)


def _connection(args: argparse.Namespace) -> ModbusConnection:
    """Build the connection described by the arguments. Performs no I/O."""
    # Imported here so the module loads (and --help works) without a backend.
    try:  # modbus-connection >= 4.9
        from modbus_connection.pymodbus import ModbusConnection as PymodbusConnection
    except ImportError:  # modbus-connection 4.8.x
        from modbus_connection.pymodbus import PymodbusConnection

    if args.transport == "serial":
        return PymodbusConnection(
            ModbusSerialParams(
                device=args.device,
                baudrate=args.baudrate,
                parity=args.parity,
                stopbits=args.stopbits,
                bytesize=args.bytesize,
            )
        )
    return PymodbusConnection(
        ModbusTcpParams(host=args.host, port=args.port, framer=args.framer)
    )


def _print(device: XDRPowerSupply) -> None:
    for label, attr in SECTIONS:
        print()
        print_component(getattr(device, attr), title=label)


async def _run(args: argparse.Namespace) -> int:
    connection = _connection(args)
    try:
        await connection.connect()
    except ModbusError as err:
        print(f"Could not connect: {err}", file=sys.stderr)
        return 1
    counting = CountingUnit(connection.for_unit(args.unit))
    try:
        probe = await XDRPowerSupply.async_probe(counting)
        device = XDRPowerSupply(counting, model=probe.model_definition)
        start = time.monotonic()
        await device.async_update()
        elapsed = time.monotonic() - start
    except ModbusError as err:
        print(f"Error reading device: {err}", file=sys.stderr)
        return 1
    finally:
        await connection.close()
    model = f" ({probe.model_name})" if probe.model_name else ""
    print(f"XDR power supply{model}")
    _print(device)
    print(f"\nQueried in {elapsed * 1000:.0f} ms ({counting.reads} Modbus reads)")
    return 0


def main() -> int:
    return asyncio.run(_run(_parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
