# SRNE Read-Only Modbus RTU Simulator — Test & Usage Guide

## Purpose & Validation Boundary

`scripts/srne_modbus_simulator.py` is a standalone Windows-compatible **read-only Modbus RTU simulator** for the **SRNE SPI-16K-UP** ESPHome integration. It serves deterministic **synthetic** register snapshots from [`tests/fixtures/`](fixtures/) (`SRNE-04E-D`) covering only the **40 implemented `FC03` groups / 107 register words** (**73** public entities: **59** ESPHome `sensor` [`58` Modbus + `1` local `srne_uptime`], **2** `binary_sensor`, **12** `text_sensor`; mapped in Home Assistant as `71` `sensor.*` + `2` `binary_sensor.*`) over Modbus RTU (`9600,N,8,1`, slave address `1`, **FC03 only**).

- **Synthetic subset only**: It validates only the **implemented register mappings** against synthetic fixtures — **not** the complete manufacturer register inventory and **not** physical SRNE `SPI-16K-UP` inverter compatibility or live RS485 electrical bus timing.
- **No firmware dependency**: Completely independent of `esphome/` YAML configs; does not read `esphome/secrets.yaml` or Home Assistant state.

### Related Documentation

- [`README.md`](../README.md) — Project overview, validation status, and repository index
- [`docs/INSTALLATION.md`](../docs/INSTALLATION.md) — Hardware wiring, termination, ESPHome setup, and Recorder protection
- [`docs/ENTITIES.md`](../docs/ENTITIES.md) — Complete 73-entity catalog and YAML-derived matrix
- [`docs/MODBUS-REFERENCE.md`](../docs/MODBUS-REFERENCE.md) — Read-only FC03 register groups, scheduling, and boundaries
- [`SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](SRNE-03V-Physical-RS485-Bench-Test-Procedure.md) — Step-by-step physical RS485 bench test procedure

> **Home Assistant Entity Naming & Pre-Traffic Rule**: `esphome/srne-bench-test.yaml` sets `name: srne-bench-test` and `friendly_name: SRNE Bench Test`, so Home Assistant entity IDs may use a `srne_bench_test_*` (or other registry-assigned) prefix rather than `srne_*`. Additionally, `text_sensor` is an ESPHome entity type (not a Home Assistant domain): ESPHome `text_sensor` entities appear under **`sensor.*`** in Home Assistant. Verify actual entity IDs in **Developer Tools → States** and confirm staging HA or `recorder` exclusions **before** starting serial simulator traffic (`SRNE-03V` Section 2).

---

## Tested Environment & Reproducible Setup (`Python 3.14.3`)

- **Tested environment**: **Python `3.14.3`** (`pymodbus==3.16.2`, `pyserial==3.5`, pinned in [`tests/requirements-simulator.txt`](requirements-simulator.txt)).

To create the isolated Windows virtual environment from the repository root:

```powershell
py -3.14 -m venv .venv-simulator
.\.venv-simulator\Scripts\python.exe -m pip install -r tests/requirements-simulator.txt
```

Invoke the virtual environment Python executable directly (as shown in all commands below).

---

## Command-Line Interface

> **USB-RS485 Port Identification Rule**: `srne_modbus_simulator.py` **never** auto-selects a COM port. Always positively identify your dedicated USB-RS485 adapter port first (compare `.\.venv-simulator\Scripts\python.exe -m serial.tools.list_ports -v` before and after plugging in the adapter, and verify in Windows Device Manager → **Ports (COM & LPT)**). Avoid guessing ports belonging to USB-UART/JTAG flashing cables.

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

### Starting the Modbus RTU Serial Simulator *(Bench RS485)*

Ensure Home Assistant entity IDs and Recorder protection are verified before starting live serial traffic (`SRNE-03V` Section 2), substituting your positively identified `<ADAPTER_COM>` (e.g., `COM5`):

```powershell
# Serve default scenario S1_solar_charging on a positively identified USB-RS485 COM port
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port COM5

# Serve a specific scenario with DEBUG logging (prints returned raw register words)
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port COM5 --scenario S4_standby --log-level DEBUG

# Enable interactive scenario & failure-injection controls without restarting or reopening the port
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port COM5 --scenario S1_solar_charging --interactive
```

Press `Ctrl+C` for graceful shutdown (or type `q` in `--interactive` mode).

### CLI Options

| Flag | Default | Description |
| --- | --- | --- |
| `--help` | — | Show help text and exit |
| `--port` | *(required in server mode)* | Explicit positively identified COM port (never auto-selected) |
| `--scenario` | `S1_solar_charging` | Initial synthetic scenario ID to serve |
| `--list-scenarios` | `False` | Print available scenarios and exit (no serial access) |
| `--validate-only` | `False` | Validate fixtures + scenario and exit (no serial access) |
| `--interactive` | `False` | Enable non-blocking interactive console controls (`1`-`5`, `f ...`, `n`, `s`, `h`, `q`) |
| `--log-level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |
| `--fixtures-dir` | `tests/fixtures` | Optional custom fixture directory path |

### Interactive Console Commands (`--interactive`)

When `--interactive` is enabled, the simulator accepts operator commands without interrupting active Modbus RTU serving or reopening the serial port. Operating scenario selection and communication failure injection remain independent:

| Command | Action |
| --- | --- |
| `1` | Switch active snapshot to `S1_solar_charging` |
| `2` | Switch active snapshot to `S2_battery_discharging` |
| `3` | Switch active snapshot to `S3_utility_zero_solar` |
| `4` | Switch active snapshot to `S4_standby` |
| `5` | Switch active snapshot to `S5_active_fault` |
| `s` | Display active scenario, description, device address, serial config, coverage, switch count, elapsed runtime, and failure injection counters |
| `n` | Restore normal communication (clear active failure injection; alias for `f normal`) |
| `f` / `f status` | Display active failure injection mode, target groups, and counters |
| `f list` | List approved group aliases (`bms`, `phase1`, `phase2`, `phase2_dynamic`, `phase2_static`, `all`) and all 40 `FC03` group IDs |
| `f normal` | Restore normal communication without restarting or reopening the serial port |
| `f timeout` | Inject complete response timeout (silent simulator) for all `FC03` requests |
| `f gtimeout <groups>` | Inject timeout only on selected approved groups (e.g., `f gtimeout bms`, `f gtimeout P2-D04,P2-D05`) |
| `f exc <groups> [code]` | Inject Modbus exception frame (`0x01`–`0x0B`, default `0x02`) on selected groups |
| `f crc [groups]` | Corrupt the final 2 CRC-16 bytes on encoded RTU responses globally or for `[groups]` |
| `f trunc [groups]` | Truncate the final 3 bytes of encoded RTU response frames globally or for `[groups]` |
| `f groups <groups>` | Update target groups for active selective/wire-level failure modes |
| `h` | Display interactive command help |
| `q` | Gracefully shut down the simulator |

> **Failure Injection & Read-Only Safety**: Normal communication is always the default (`FailureMode.NORMAL`). CRC corruption (`f crc`) and frame truncation (`f trunc`) mutate the **encoded Modbus RTU wire bytes** produced by PyModbus `FramerRTU.buildFrame` while leaving the underlying synthetic register snapshots untouched. Strict FC03-only read-only enforcement executes *before* failure injection, so write requests (`FC05/06/15/16/22/23`) and unsupported function codes are rejected with `0x01` (`ILLEGAL_FUNCTION`) across every failure mode.

> **Single-Response Snapshot vs. Multi-Request Polling Sweep (`C26`)**:
> - Switching scenarios updates the active in-memory `ActiveSnapshot` reference, so **each individual Modbus `FC03` response** reads from one consistent scenario snapshot.
> - A scenario switch occurring mid-sweep does **not** isolate an entire multi-request ESPHome polling sweep — Home Assistant may temporarily reflect mixed scenario measurements across groups until the relevant complete polling cycles finish.
> - Likewise, multi-entity Home Assistant updates from Phase 1's complete-sweep-gated publication (`srne_phase1_mask == 0xFFFF`) are not guaranteed to constitute one atomic database transaction; always verify settled entity values after the corresponding `outcome=OK` polling cycles finish.

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

## Running Offline Automated Tests *(Historical `SRNE-04E-H` Evidence)*

```powershell
.\.venv-simulator\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

- **Historical validation evidence (`SRNE-04E-H`)**: In [`audits/SRNE-04E-H-Final-Offline-Validation.md`](../audits/SRNE-04E-H-Final-Offline-Validation.md), the **24/24** offline unit tests below and `pip check` passed under Python `3.14.3` with PyModbus `3.16.2` and PySerial `3.5`. *(Recorded as historical validation evidence; not re-executed during documentation-only updates.)*

### Test Layers

- **Application-level tests** (`TestFixtureLoadingAndValidation`, `TestReadOnlyContextApplicationLevel`, `TestRuntimeScenarioControlsApplicationLevel`, `TestFailureInjectionApplicationLevel`, `TestCLIAndNoSerialAccess`): validate JSON fixture loading, error handling, direct `SRNEReadOnlyContext` gap/quantity/immutability rules, snapshot switching, group/alias resolution, failure & console command handling, and CLI flags with PySerial/serial-transport patched to fail if called.
- **Protocol-level RTU wire tests** (`TestProtocolLevelRTUWireFrames`, `TestProtocolLevelRuntimeSwitchingRTU`, `TestProtocolLevelFailureInjectionRTU`): exercise PyModbus `FramerRTU`, `DecodePDU`, `SRNEModbusSerialServer`, and `SRNERequestHandler` over an in-memory `asyncio.Transport` double with full Modbus RTU CRC-16 encoding/decoding, verifying all `40` groups × `5` scenarios (`200` static + `200` live post-switch round-trips), exceptions (`0x01`, `0x02`, `0x03`), write rejections (`FC05/06/15/16/22/23`), unsupported FCs, complete silence, selective BMS timeout isolation, selective Modbus exceptions, wire-level CRC corruption and truncation, runtime recovery without restart, read-only enforcement across all 6 modes, and graceful shutdown.

---

## Known Limitations & Hardware Boundary (`C28`)

- Failure injection modes are controlled manually via `--interactive` rather than automated probabilistic/scheduled fault scripts.
- **Oversized-read exception code (`count > 32`)**: SRNE Modbus Monitoring Protocol V2.04 specifies vendor exception `0x0A` (`Invalid Length`) for requests exceeding `32` registers, whereas `scripts/srne_modbus_simulator.py` intentionally returns standard Modbus `0x03` (`ILLEGAL_VALUE`) per `SRNE-04E-E` (documented as non-blocking Discrepancy `D3` in [`audits/SRNE-04E-H-Final-Offline-Validation.md`](../audits/SRNE-04E-H-Final-Offline-Validation.md); ESPHome requests at most `20` words).
- **Available bench hardware vs. unarchived `SRNE-03V` report vs. pending inverter validation**: USB-to-RS485 bench hardware is available for executing [`SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](SRNE-03V-Physical-RS485-Bench-Test-Procedure.md), **however no executed `SRNE-03V` bench report is archived in this repository yet**, and **live physical SRNE `SPI-16K-UP` inverter validation remains completely pending**.
