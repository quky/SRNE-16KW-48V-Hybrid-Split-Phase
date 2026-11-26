# SRNE Read-Only Modbus RTU Simulator — Test & Usage Guide

## Purpose & Validation Boundary

`scripts/srne_modbus_simulator.py` is a standalone Windows-compatible **read-only Modbus RTU simulator** for the **SRNE SPI-16K-UP** ESPHome integration. It serves deterministic **synthetic** register snapshots from [`tests/fixtures/`](fixtures/) (`SRNE-04E-D`) over Modbus RTU (`9600,N,8,1`, slave address `1`, **FC03 only**).

- **Synthetic data only**: It is **not** a physical inverter and does not establish physical inverter compatibility or live RS485 bus timing.
- **No firmware dependency**: Completely independent of `esphome/` YAML configs; does not read `esphome/secrets.yaml` or Home Assistant state.

---

## Verified Environment & Dependencies

Use the isolated virtual environment Python executable directly:

- **Python**: `3.14.3` (`.venv-simulator\Scripts\python.exe`)
- **Packages** (pinned in [`tests/requirements-simulator.txt`](requirements-simulator.txt)):
  - `pymodbus==3.16.2`
  - `pyserial==3.5`

---

## Command-Line Interface

> **Serial Port Safety Notice**: Never guess or pass `COM3` unless you intentionally target that interface — `COM3` is associated with the Waveshare ESP32-S3 USB interface. Always verify Device Manager / USB-RS485 COM port assignment first, and note that **no port is ever auto-selected**.

### Offline Inspection & Validation (Zero Serial Port Access)

```powershell
# Display CLI help
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --help

# List approved synthetic scenarios
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --list-scenarios

# Validate fixtures and selected scenario without opening any serial port
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --validate-only
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --validate-only --scenario S5_active_fault
```

### Starting the Modbus RTU Serial Simulator

```powershell
# Serve default scenario S1_solar_charging on an explicit USB-RS485 COM port (e.g. COM5)
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port COM5

# Serve a specific scenario with DEBUG logging (prints returned raw register words)
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port COM5 --scenario S4_standby --log-level DEBUG

# Enable optional interactive console scenario switching without restarting or reopening the port
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port COM5 --scenario S1_solar_charging --interactive
```

Press `Ctrl+C` for graceful shutdown (or type `q` in `--interactive` mode).

### CLI Options

| Flag | Default | Description |
| --- | --- | --- |
| `--help` | — | Show help text and exit |
| `--port` | *(required in server mode)* | Explicit COM port (never auto-selected) |
| `--scenario` | `S1_solar_charging` | Initial synthetic scenario ID to serve |
| `--list-scenarios` | `False` | Print available scenarios and exit (no serial access) |
| `--validate-only` | `False` | Validate fixtures + scenario and exit (no serial access) |
| `--interactive` | `False` | Enable non-blocking interactive console controls (`1`-`5`, `s`, `h`, `q`) |
| `--log-level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `--fixtures-dir` | `tests/fixtures` | Optional custom fixture directory path |

### Interactive Console Commands (`--interactive`)

When `--interactive` is enabled, the simulator accepts operator commands without interrupting active Modbus RTU serving or reopening the serial port:

| Command | Action |
| --- | --- |
| `1` | Switch active snapshot to `S1_solar_charging` |
| `2` | Switch active snapshot to `S2_battery_discharging` |
| `3` | Switch active snapshot to `S3_utility_zero_solar` |
| `4` | Switch active snapshot to `S4_standby` |
| `5` | Switch active snapshot to `S5_active_fault` |
| `s` | Display active scenario, description, device address, serial config, coverage, switch count, and elapsed runtime |
| `h` | Display interactive command help |
| `q` | Gracefully shut down the simulator |

> **Atomicity Note (Single-Response vs. Polling Sweep)**: Switching scenarios atomically replaces the immutable active register snapshot reference (`ActiveSnapshot`) in memory. Each individual Modbus FC03 response is guaranteed to read from a single consistent scenario snapshot. However, atomicity does **not** span an entire multi-request ESPHome polling sweep — if a scenario switch occurs mid-sweep, Home Assistant may temporarily display mixed values across register groups until subsequent polls complete.

---

## Supported Synthetic Scenarios (`SRNE-04E-D`)

| Scenario ID | Operating Mode (`0x0210`) | Description |
| --- | --- | --- |
| `S1_solar_charging` *(default)* | `3` (`Inverter operation`) | Daytime solar (`8,428 W` PV), battery charging (`-85.0 A` = `0xFCAE`), load `3,450 W` |
| `S2_battery_discharging` | `3` (`Inverter operation`) | Evening discharge (`+75.0 A`), zero solar, load `3,470 W` |
| `S3_utility_zero_solar` | `2` (`Utility operation`) | Grid bypass (`2,420 W`), utility charging (`30.0 A`), zero solar |
| `S4_standby` | `1` (`Standby`) | Idle standby (`0 W`), `100%` SOC (`Full`), negative ambient temp `-2.5 °C` (`0xFFE7`) |
| `S5_active_fault` | `1` (`Standby`) | Active fault registers (`0x0204=1`, `0x0205=20`), elevated heatsinks (`82.1 °C`) |

---

## Running Offline Automated Tests

```powershell
.\.venv-simulator\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

### Test Layers

- **Application-level tests** (`TestFixtureLoadingAndValidation`, `TestReadOnlyContextApplicationLevel`, `TestRuntimeScenarioControlsApplicationLevel`, `TestCLIAndNoSerialAccess`): validate JSON fixture loading, error handling, direct `SRNEReadOnlyContext` gap/quantity/immutability rules, atomic snapshot switching, console command handling (`1`-`5`, `s`, `h`, `q`, invalid commands, repeated selection), and CLI flags (`--interactive` included) with PySerial/serial-transport patched to fail if called.
- **Protocol-level RTU wire tests** (`TestProtocolLevelRTUWireFrames`, `TestProtocolLevelRuntimeSwitchingRTU`): exercise PyModbus `FramerRTU`, `DecodePDU`, `SRNEModbusSerialServer`, and `SRNERequestHandler` over an in-memory `asyncio.Transport` double with full Modbus RTU CRC-16 encoding/decoding, verifying all `40` groups × `5` scenarios (`200` static round-trips + `200` live post-switch round-trips), exceptions (`0x01`, `0x02`, `0x03`), write rejections (`FC05/06/15/16/22/23`), unsupported FCs (`FC01/02/04/07/09/17`), concurrent non-blocking async console switching, and EOF graceful shutdown.

---

## Known Limitations (Scope of SRNE-04E-F)

- Does not yet support timeout injection, malformed RTU frame injection, or dynamic fault injection (planned for later tasks).
- Physical COM-port RS485 wire verification remains pending USB-RS485 hardware setup.
