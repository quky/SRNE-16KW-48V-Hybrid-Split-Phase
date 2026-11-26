# SRNE-04E-F — Runtime Operating Scenario Controls Summary

## 1. Scope & Verified Baseline

Extended the standalone Windows-compatible read-only Modbus RTU simulator ([`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py)) with optional non-blocking interactive console controls (`--interactive`) allowing live transitions across all five preloaded synthetic scenarios without restarting the server, reopening the serial port, mutating individual register values, or weakening FC03-only enforcement.

### Pre-Edit & Post-Edit Unchanged Baseline Checksums

All 10 pre-edit baseline SHA-256 checksums matched verbatim before modification, and the 7 preserved artifacts remain byte-identical after completion:

| Preserved File | Bytes | SHA-256 |
| --- | ---: | --- |
| [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) | 978 | `ff19087f95e83d77e9ee7a65244622037bcf963f60c67ba768cdbe7c9f686a25` |
| [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) | 33,475 | `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80` |
| [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) | 34,982 | `91ebba7848230ab1b19945d6dca71821f6fa040d1591069b4245910e4726c630` |
| [`tests/fixtures/srne-register-groups.json`](../tests/fixtures/srne-register-groups.json) | 57,250 | `ad37d8602f48af7307ecd1c767d6e85f2d84079c8ac8ff7db7656c36c78279c4` |
| [`tests/fixtures/srne-synthetic-scenarios.json`](../tests/fixtures/srne-synthetic-scenarios.json) | 79,575 | `b4424f9533baeee525ef67190240eb99190ccca510fa2171e03caf10e921b944` |
| [`tests/fixtures/srne-expected-entities.json`](../tests/fixtures/srne-expected-entities.json) | 41,926 | `a5d4f94d8f84a1ba5f43fe34ee381385050343bb691c30a0074777becec48e71` |
| [`audits/SRNE-04E-E-Simulator-Implementation-Summary.md`](SRNE-04E-E-Simulator-Implementation-Summary.md) | 9,253 | `33faa12c85c1b65f137547c4e7a54dde96b750a41d647d4b29162f7e7a1608dc` |

### Modified & Created Deliverables

| Artifact | Action | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) | Modified | 45,768 | `85ac723f00989f47e277d8e310a5ec54b6cafa543deb8266c094122cdfa3719a` |
| [`tests/test_srne_modbus_simulator.py`](../tests/test_srne_modbus_simulator.py) | Modified | 33,754 | `055dc8f8ea893f5ce25a0994be284eb2aca8492488b51f6be6e7c44eb7e1b373` |
| [`tests/README.md`](../tests/README.md) | Modified | 6,935 | `aef3bac6182e7b46c3bdb97dc42f75c1d7ad44e389ef94a405cf5b4f116bdad2` |
| [`audits/SRNE-04E-F-Runtime-Scenario-Controls-Summary.md`](SRNE-04E-F-Runtime-Scenario-Controls-Summary.md) | Created | — | *(verified post-write)* |

---

## 2. Scenario Switching Architecture

- **Preloaded immutable snapshots**: `load_and_validate_fixtures()` loads and validates all 5 scenarios (`S1_solar_charging`..`S5_active_fault`), storing every scenario's 107 raw `uint16` words in its own immutable `types.MappingProxyType[int, int]`. All 5 `ScenarioData` objects are supplied to `SRNEReadOnlyContext(..., scenarios=fixtures.scenarios)` at server startup.
- **Atomic snapshot replacement**: `SRNEReadOnlyContext` maintains `self._active_snapshot = ActiveSnapshot(scenario=..., switch_count=...)` (a frozen dataclass). Calling `switch_scenario(scenario_id)` atomically rebinds `self._active_snapshot` to a new `ActiveSnapshot` referencing the target preloaded immutable map and increments `switch_count` only when the active scenario actually changes.
- **Single-response consistency guarantee**: Inside `SRNEReadOnlyContext.async_getValues`, one local reference `registers = self._active_snapshot.scenario.registers` is captured once at the start of address validation and used for the entire register slice read. Individual registers are never mutated (`async_setValues` continues returning `0x01`, and write/unsupported FCs remain blocked at `SRNERequestHandler`).
- **Sweep-level limitation documented**: Atomicity applies strictly per individual Modbus FC03 response, not across an entire multi-request ESPHome polling sweep. If a runtime switch occurs mid-sweep, Home Assistant can temporarily display mixed scenario values across register groups until subsequent polls complete.

---

## 3. Windows Console Input & Shutdown Mechanism

- **Opt-in `--interactive` flag**: When `--interactive` is omitted, `run_server_async` runs only `server.serve_forever()`, preserving identical SRNE-04E-E behavior. `--scenario` continues setting the initial active scenario in both modes.
- **Non-blocking `InteractiveConsoleController`**:
  - Spawns a daemon reader thread (`srne-console-reader`) coordinated via `threading.Event` and pushes received lines (or `None` on EOF) onto an `asyncio.Queue` using `loop.call_soon_threadsafe(...)`, so the asyncio Modbus RTU event loop is never blocked.
  - On Windows interactive TTY consoles (`os.name == "nt"` and `sys.stdin.isatty()`), uses `msvcrt.kbhit()` (50 ms poll checking `stop_event`) and `msvcrt.getwch()`, supporting backspace editing, extended-key prefix consumption, `Ctrl+C` (`\x03` -> graceful quit), and `Ctrl+Z` (`\x1a` -> EOF shutdown).
  - On piped/redirected/test streams, uses `stream.readline()` cleanly without touching `msvcrt`.
- **Supported commands**: `1`–`5` (switch to `S1_solar_charging`..`S5_active_fault`), `s` (display active scenario, description, device address, serial config, 40-group/107-word coverage, switch count, and elapsed runtime), `h` (command list), and `q` (graceful shutdown). Unknown commands log a `WARNING` and keep the current scenario and server running.
- **Coordinated shutdown**: `run_server_async` awaits `asyncio.wait({server_task, console_task}, return_when=FIRST_COMPLETED)` and cleanly cancels/joins tasks while calling `await server.shutdown()` without raising spurious serial errors.

---

## 4. Offline & In-Memory RTU Verification Results

Executed under `.venv-simulator`:

```powershell
.\.venv-simulator\Scripts\python.exe -W default -m unittest discover -s tests -p "test_*.py" -v
```

Result: **18 tests passed in 3.181s** (`OK`, 0 failures, 0 errors, 0 skipped, 0 warnings):

- **Original baseline tests preserved**: All **13** tests from SRNE-04E-E passed unmodified.
- **New SRNE-04E-F tests added**: **5** new tests (**13 + 5 = 18 total**):
  - **Application-level (`TestRuntimeScenarioControlsApplicationLevel`, 2 tests)**: Verified `switch_scenario` across all 5 scenarios (`switch_count` 0..4), immutable old snapshot preservation, repeated same-scenario selection (`changed=False`, unchanged `switch_count`), unknown-ID `KeyError`, `h`/`s`/`q` commands, invalid commands (`""`, `"9"`, `"invalid_cmd"`), and `INFO`/`WARNING` logging.
  - **Protocol-level in-memory RTU wire tests (`TestProtocolLevelRuntimeSwitchingRTU`, 3 tests)**:
    - Exercised **200 live RTU wire round-trips** (`5` scenario transitions via `"1".."5"` × all `40` FC03 groups per transition) on a single `SRNEModbusSerialServer` + `SRNERequestHandler` + `_InMemoryRTUTransport` instance without restarting the server, plus post-switch `FC06 -> 0x01` and gap `0x0104 -> 0x02` enforcement checks.
    - Verified concurrent non-blocking `InteractiveConsoleController.run` switching (`"2"`, `"bogus"`, `"4"`, `"q"`) interleaved with live in-memory RTU FC03 wire queries, plus separate EOF (`""`) graceful shutdown.
    - Verified CLI compatibility (`--help`, `--validate-only --interactive --scenario S4_standby` -> exit `0`, `--interactive` missing `--port` -> exit `2`) with PySerial and `create_serial_connection` patched to fail if called.

---

## 5. Limitations & Blockers

- **Deferred features**: Runtime timeout injection, malformed RTU frame injection, and physical COM port hardware validation remain out of scope for `SRNE-04E-F` and pending future tasks.
- **Physical inverter status**: Zero physical serial ports were opened; synthetic values make no physical inverter compatibility claim.
- **No blockers identified**.
