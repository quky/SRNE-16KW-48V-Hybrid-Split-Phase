# SRNE-04E-G — Communication Failure Injection and Recovery Summary

## 1. Scope & Verified Baseline

Extended [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) with controlled communication failure injection and live recovery capabilities (`SRNE-04E-G`), independent of runtime operating scenarios (`S1_solar_charging`..`S5_active_fault`), without opening physical serial ports or modifying firmware, fixtures, or prior audit documents.

### Pre-Edit & Post-Edit Unchanged Baseline Checksums

All 11 pre-edit baseline SHA-256 checksums matched verbatim prior to edits, and all 8 preserved files remain byte-identical:

| Preserved File | Bytes | SHA-256 |
| --- | ---: | --- |
| [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) | 978 | `ff19087f95e83d77e9ee7a65244622037bcf963f60c67ba768cdbe7c9f686a25` |
| [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) | 33,475 | `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80` |
| [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) | 34,982 | `91ebba7848230ab1b19945d6dca71821f6fa040d1591069b4245910e4726c630` |
| [`tests/fixtures/srne-register-groups.json`](../tests/fixtures/srne-register-groups.json) | 57,250 | `ad37d8602f48af7307ecd1c767d6e85f2d84079c8ac8ff7db7656c36c78279c4` |
| [`tests/fixtures/srne-synthetic-scenarios.json`](../tests/fixtures/srne-synthetic-scenarios.json) | 79,575 | `b4424f9533baeee525ef67190240eb99190ccca510fa2171e03caf10e921b944` |
| [`tests/fixtures/srne-expected-entities.json`](../tests/fixtures/srne-expected-entities.json) | 41,926 | `a5d4f94d8f84a1ba5f43fe34ee381385050343bb691c30a0074777becec48e71` |
| [`audits/SRNE-04E-E-Simulator-Implementation-Summary.md`](SRNE-04E-E-Simulator-Implementation-Summary.md) | 9,253 | `33faa12c85c1b65f137547c4e7a54dde96b750a41d647d4b29162f7e7a1608dc` |
| [`audits/SRNE-04E-F-Runtime-Scenario-Controls-Summary.md`](SRNE-04E-F-Runtime-Scenario-Controls-Summary.md) | 8,020 | `6fcac9b80e456312c5253201f8c66fd243a7754ad0c5f98d172e09195c3e22fd` |

### Modified & Created Files

| Artifact | Action | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) | Modified | 70,589 | `21fca8b461b3d6d5c8f9295cd18d1010e6a65350a1a6151503af00ada6af4bc2` |
| [`tests/test_srne_modbus_simulator.py`](../tests/test_srne_modbus_simulator.py) | Modified | 51,442 | `b9d702e8173a5c04fd4120788a767d1902c3bd7ea36c14601ecb5486b8878c82` |
| [`tests/README.md`](../tests/README.md) | Modified | 8,805 | `be03ab0aead5bf3a74b80124f45bcca2f74b80124f45bcca2f380abf9aea94a0e3a5e9b7894d6ecd7` |
| [`audits/SRNE-04E-G-Failure-Injection-Recovery-Summary.md`](SRNE-04E-G-Failure-Injection-Recovery-Summary.md) | Created | — | *(verified post-write)* |

---

## 2. Implementation Architecture

- **Independent `FailureInjectionController`**: Decoupled from `SRNEReadOnlyContext` (`scenario` snapshots) so operating scenario transitions (`1`–`5`) never reset failure modes, and failure modes/recoveries never alter synthetic register payloads or switch counts.
- **Explicit activation, normal default**: Initializes to `FailureMode.NORMAL` with `FailureInjectionConfig()` and zeroed `FailureCounters` (`total_injected`, `silent_timeouts`, `selective_timeouts`, `selective_exceptions`, `invalid_crc_frames`, `truncated_frames`, `recoveries`).
- **Validated group & alias resolution**: Restricts selective targets strictly to the **40** approved FC03 register groups and curated aliases (`bms` -> `P2-D04`, `P2-D05`; `phase1`; `phase2`; `phase2_dynamic`; `phase2_static`; `all`). Unknown groups or out-of-range exception codes are rejected cleanly without inventing registers or changing state.
- **Wire-level RTU fault injection in `SRNERequestHandler`**:
  - **Strict FC03-only guard executes first**: Non-FC03 requests (`FC05/06/15/16/21/22/23`, unsupported FCs) are always rejected with `0x01` (`ILLEGAL_FUNCTION`) *before* failure evaluation across every failure mode. Unapproved FC03 gaps/lengths still return normal `0x02`/`0x03`.
  - **`INVALID_CRC` and `TRUNCATED_FRAME` mutate actual RTU wire bytes**: `SRNERequestHandler` encodes the authentic `ReadHoldingRegistersResponse` via PyModbus `self.framer.buildFrame(self.trace_pdu(True, response))` (`dev_id + 03 + byte_count + words + swapped_crc16`), then either XORs the final 2 CRC bytes with `0xFF` (`_send_corrupted_crc`) or slices off the trailing 3 wire bytes (`_send_truncated_frame`), transmitting the exact malformed wire frame via `self.low_level_send(...)`.
  - **Live recovery without restart**: `n` / `f normal` atomically restores `FailureMode.NORMAL` and increments `recoveries` on the active `SRNEModbusSerialServer` without dropping or reopening transport/serial handles.

---

## 3. Supported Failure Modes & Interactive Commands

| Mode / Command | Behavior |
| --- | --- |
| Default / `n` / `f normal` | Normal communication (`FailureMode.NORMAL`); increments `recoveries` when clearing an active fault |
| `f` / `f status` | Displays active failure mode, targeted groups, exception/truncation parameters, and all failure counters |
| `f list` | Lists approved group aliases (`bms`, `phase1`, `phase2`, `phase2_dynamic`, `phase2_static`, `all`) and all 40 FC03 groups |
| `f timeout` | `SILENT_TIMEOUT` — complete silence (zero reply bytes sent) for all approved FC03 requests |
| `f gtimeout <groups>` | `SELECTIVE_TIMEOUT` — silence only for FC03 requests overlapping `<groups>`; unaffected groups reply normally |
| `f exc <groups> [code]` | `SELECTIVE_EXCEPTION` — returns CRC-valid `ExceptionResponse(0x03, code)` (`0x01`–`0x0B`, default `0x02`) for `<groups>` |
| `f crc [groups]` | `INVALID_CRC` — flips both CRC-16 bytes of the encoded RTU response globally or selectively for `[groups]` |
| `f trunc [groups]` | `TRUNCATED_FRAME` — truncates final 3 bytes of the encoded RTU response globally or selectively for `[groups]` |
| `f groups <groups>` | Updates target group filter on active selective or wire-level failure mode |

Existing commands `1`–`5`, `s`, `h`, and `q` remain preserved; `s` now also appends active failure configuration and counters.

---

## 4. Verification, Regression & Read-Only Results

Executed under `.venv-simulator`:

```powershell
.\.venv-simulator\Scripts\python.exe -W default -m unittest discover -s tests -p "test_*.py" -v
```

- **Test suite result**: **24 tests passed in 4.399s** (`OK`, 0 failures, 0 errors, 0 skipped, 0 deprecation warnings):
  - **Regression suite**: All **18** existing tests from `SRNE-04E-E` and `SRNE-04E-F` passed unchanged.
  - **New SRNE-04E-G tests (6 tests)**:
    - Application-level (`TestFailureInjectionApplicationLevel`, 2 tests): Normal default state, alias resolution (`bms`, `phase1`, `phase2`, `all`, comma lists), rejection of invalid failure commands without changing state, independent scenario switching, and counter/status formatting.
    - Protocol-level RTU wire tests (`TestProtocolLevelFailureInjectionRTU`, 4 async tests): Complete silence + restartless recovery; selective `bms` (`P2-D04`/`P2-D05`) timeout with unaffected `P1-R01`/`P2-D01`/`P2-S06` normal replies + recovery; selective Modbus exceptions (`0x02`, `0x04`); encoded RTU wire CRC corruption & 3-byte frame truncation verified rejected (`pdu is None`) by client `FramerRTU(DecodePDU(is_server=False))` while unaffected groups succeed; independent scenario switch `S1 -> S4` during active `f gtimeout bms`; **strict read-only FC06/FC16/FC22/FC23 -> `0x01` enforcement verified across ALL 6 modes with zero register mutation**; concurrent async console lifecycle + counters + `q` quit.
- **Offline CLI checks (zero serial access)**: `--help`, `--list-scenarios`, `--validate-only`, and `--validate-only --interactive --scenario S4_standby` exited `0`; `--interactive` without `--port` exited `2`.

---

## 5. Known Limitations & Blockers

- Failure modes are manually controlled via interactive console rather than probabilistic or timed fault schedules.
- Physical USB-RS485 adapter hardware connection and live RS485 inverter validation remain pending (no physical COM ports opened; no physical inverter compatibility claimed).
- **No blockers identified**.
