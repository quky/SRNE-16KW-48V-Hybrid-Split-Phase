# SRNE-04E-H — Final Offline Simulator Validation Audit

## 1. Executive Summary & Readiness Verdict

- **Overall Offline Readiness Status**: **PASS — READY FOR PHYSICAL RS485 BENCH TESTING (`SRNE-03V`)**
- **Scope**: Independent, read-only audit of [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py), [`tests/test_srne_modbus_simulator.py`](../tests/test_srne_modbus_simulator.py), [`tests/README.md`](../tests/README.md), [`tests/fixtures/`](../tests/fixtures/), and compatibility with the deployed ESPHome configuration ([`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml), [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml), [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml)).
- **Hardware Validation Boundary**: Zero physical serial ports were opened during this audit. Physical USB-RS485 adapter framing, `200ms` turnaround timing, and live **SRNE SPI-16K-UP** hardware testing remain pending [`SRNE-03V`](../tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md).

---

## 2. Independent Verification Matrix (Required Checks 1–10)

| # | Required Check | Verdict | Observed Evidence |
| --- | --- | --- | --- |
| 1 | Register addresses & response lengths vs. ESPHome packages | **PASS** | Phase 1 YAML parsed: `16` `modbus_controller` FC03 readers / `32` words (`response_size == 2 * register_count`); Phase 2 YAML parsed: `24` dispatch groups / `75` words. Exact 1:1 match with [`srne-register-groups.json`](../tests/fixtures/srne-register-groups.json) (`40` groups, `107` words). |
| 2 | Fixture coverage for all 5 operating scenarios | **PASS** | `S1_solar_charging`, `S2_battery_discharging`, `S3_utility_zero_solar`, `S4_standby`, and `S5_active_fault` each define exact `107` `uint16` register entries (`0..65535`) and matching `group_payloads` for all `40` groups. |
| 3 | Expected entity values, scaling, signed conversions, strings & calculated values | **PASS** | Independent recalculation of all `71 × 5 = 355` deterministic entity values from raw `uint16` words matched [`srne-expected-entities.json`](../tests/fixtures/srne-expected-entities.json) (`355/355`), plus `2` runtime-dependent entities (`srne_uptime`, `srne_modbus_communication_health`) = `73` total public entities. |
| 4 | Failure targeting, counters & restartless recovery | **PASS** | `FailureInjectionController` supports all `6` modes (`NORMAL`, `SILENT_TIMEOUT`, `SELECTIVE_TIMEOUT`, `SELECTIVE_EXCEPTION`, `INVALID_CRC`, `TRUNCATED_FRAME`), approved group aliases (`bms`, `phase1`, `phase2`, `phase2_dynamic`, `phase2_static`, `all`), `FailureCounters` (`total_injected`, per-mode counts, `recoveries`), and live recovery (`n` / `f normal`) without restart. |
| 5 | Read-only enforcement including broadcast requests | **PASS** | 3-layer FC03-only enforcement (`handle_request` guard before fault injection, `callback_data` unregistered-FC guard, `async_setValues` `0x01` + `MappingProxyType`). In-memory probe of broadcast (`dev_id=0x00`) and universal (`dev_id=0xFF`) FC03/FC06/FC09 frames produced `0` response bytes and `0` mutation (`0xE003` remained `48`). |
| 6 | Windows interactive console & serial startup readiness | **PASS (with notes)** | Daemon console reader uses `msvcrt.kbhit()`/`getwch()` on Windows TTY (`os.name == "nt"`), `stream.readline()` on pipes/tests, handles `Ctrl+C`, `Ctrl+Z`/EOF, `q`, invalid commands, and never auto-selects `COM3`. Uses `ModbusSerialServer` (`9600,N,8,1`, dev `1`) with explicit `--port`. See Discrepancy D2/D6. |
| 7 | Complete automated test suite execution | **PASS** | `.venv-simulator\Scripts\python.exe -W default -m unittest discover -s tests -p "test_*.py"` ran **24 tests in 4.312s**: **OK** (`0` failures, `0` errors, `0` skipped, `0` deprecation warnings). |
| 8 | Dependency versions & `pip check` | **PASS** | Python `3.14.3`, `pip==25.3`, `pymodbus==3.16.2`, `pyserial==3.5`; `pip check` reported `No broken requirements found.` (exit `0`). |
| 9 | Offline CLI help, scenario listing & validation | **PASS** | Zero serial access: `--help` (exit `0`), `--list-scenarios` (exit `0`, 5 scenarios), `--validate-only` (exit `0`), `--validate-only --scenario S5_active_fault` (exit `0`), `--validate-only --interactive --scenario S4_standby` (exit `0`), missing `--port` (exit `2`). |
| 10 | Remaining discrepancies identified (unmodified) | **RECORDED** | Six non-blocking documentation, protocol-exception-choice, test-coverage, and cosmetic/lifecycle observations documented verbatim in Section 5 without code/file changes. |

---

## 3. Firmware & Architecture Compatibility Assessment

- **Serial framing & turnaround compatibility**: [`srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) configures `uart_rs485` at `9600,N,8,1` (`GPIO17` TX / `GPIO18` RX), RS485 DE/RE on `GPIO21`, `send_wait_time: 300ms`, and provisional `turnaround_time: 200ms`. The simulator listens via `ModbusSerialServer(..., framer=FramerType.RTU, baudrate=9600, bytesize=8, parity="N", stopbits=1, timeout=3.0)` on an explicitly supplied `--port`.
- **Zero-based wire addressing**: PyModbus `ReadHoldingRegistersRequest` decodes the big-endian 16-bit request address directly as zero-based wire address into `SRNEReadOnlyContext.async_getValues`, matching ESPHome's `address: 0x....` configuration (`0x000B` through `0xF04E`).
- **Response size compatibility**: Maximum ESPHome group read is `20` words (`P2-S05` at `0x0021` and `P2-S06` at `0x0035`), within the `32`-word simulator and protocol limit.
- **Polling sweep atomicity**: Live scenario transitions (`1`–`5`) atomically swap `ActiveSnapshot` per Modbus FC03 request; a switch occurring mid-sweep will produce mixed scenario states between groups until the next 10s (Phase 1) and 30s/300s/3600s (Phase 2) polls complete.

---

## 4. Environment, Test & Checksum Evidence

### Software Environment (`pip list --format=freeze` & `pip check`)

- Executable: `f:\temp\SRNE-16KW-48V-Hybrid-Split-Phase\.venv-simulator\Scripts\python.exe`
- `Python 3.14.3`
- `pip==25.3`, `pymodbus==3.16.2`, `pyserial==3.5`
- `python -m pip check`: `No broken requirements found.` (`exit=0`)

### Preserved Project Artifact Checksums

All prior artifacts remained untouched during `SRNE-04E-H`:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) | 978 | `ff19087f95e83d77e9ee7a65244622037bcf963f60c67ba768cdbe7c9f686a25` |
| [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) | 33,475 | `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80` |
| [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) | 34,982 | `91ebba7848230ab1b19945d6dca71821f6fa040d1591069b4245910e4726c630` |
| [`tests/fixtures/srne-register-groups.json`](../tests/fixtures/srne-register-groups.json) | 57,250 | `ad37d8602f48af7307ecd1c767d6e85f2d84079c8ac8ff7db7656c36c78279c4` |
| [`tests/fixtures/srne-synthetic-scenarios.json`](../tests/fixtures/srne-synthetic-scenarios.json) | 79,575 | `b4424f9533baeee525ef67190240eb99190ccca510fa2171e03caf10e921b944` |
| [`tests/fixtures/srne-expected-entities.json`](../tests/fixtures/srne-expected-entities.json) | 41,926 | `a5d4f94d8f84a1ba5f43fe34ee381385050343bb691c30a0074777becec48e71` |
| [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) | 70,589 | `21fca8b461b3d6d5c8f9295cd18d1010e6a65350a1a6151503af00ada6af4bc2` |
| [`tests/test_srne_modbus_simulator.py`](../tests/test_srne_modbus_simulator.py) | 51,442 | `b9d702e8173a5c04fd4120788a767d1902c3bd7ea36c14601ecb5486b8878c82` |
| [`tests/README.md`](../tests/README.md) | 8,805 | `be03ab0aead5bf3a74b80124f45bcca2f380abf9aea94a0e3a5e9b7894d6ecd7` |
| [`audits/SRNE-04E-E-Simulator-Implementation-Summary.md`](SRNE-04E-E-Simulator-Implementation-Summary.md) | 9,253 | `33faa12c85c1b65f137547c4e7a54dde96b750a41d647d4b29162f7e7a1608dc` |
| [`audits/SRNE-04E-F-Runtime-Scenario-Controls-Summary.md`](SRNE-04E-F-Runtime-Scenario-Controls-Summary.md) | 8,020 | `6fcac9b80e456312c5253201f8c66fd243a7754ad0c5f98d172e09195c3e22fd` |
| [`audits/SRNE-04E-G-Failure-Injection-Recovery-Summary.md`](SRNE-04E-G-Failure-Injection-Recovery-Summary.md) | 8,313 | `a3baae48fe4603c408c798afc5a25d168c2e35b1825beb74523d2f0b69ac06db` |

---

## 5. Identified Discrepancies & Known Limitations (Reported Without Correction)

| ID | Category | Finding Description | Impact on Bench Testing (`SRNE-03V`) |
| --- | --- | --- | --- |
| **D1** | Documentation Checksum Typo | In [`audits/SRNE-04E-G-Failure-Injection-Recovery-Summary.md`](SRNE-04E-G-Failure-Injection-Recovery-Summary.md) line 28, the SHA-256 recorded for `tests/README.md` (`be03ab0aead5bf3a74b80124f45bcca2f74b80124f45bcca2f380abf9aea94a0e3a5e9b7894d6ecd7`, 81 hex chars) contains a duplicated 17-char substring (`74b80124f45bcca2f`). Actual `tests/README.md` SHA-256 is `be03ab0aead5bf3a74b80124f45bcca2f380abf9aea94a0e3a5e9b7894d6ecd7` (64 hex chars). | Zero runtime impact; documentation discrepancy noted here without altering the prior audit file. |
| **D2** | Test Stream Cleanup Timing | `InteractiveConsoleController.run()` calls `thread.join(timeout=0.5)` in `finally:` when `input_stream is not None`, triggering an asyncio slow-callback diagnostic (`0.508s`) in `unittest` with blocking queue streams. On real Windows interactive TTY runs (`input_stream is None`), this branch is skipped and `msvcrt` exits within `50 ms`. | Zero runtime impact on Windows interactive console operation. |
| **D3** | Exception Code `0x03` vs. Vendor `0x0A` | SRNE V2.04 documents exception `0x0A` (`Invalid Length`) for requests exceeding `32` registers, whereas the simulator intentionally returns standard Modbus `0x03` (`ILLEGAL_VALUE`). | Non-blocking; ESPHome requests at most `20` words (`P2-S05`, `P2-S06`). |
| **D4** | `SILENT_TIMEOUT` Request Ordering | Invalid FC03 gaps/counts (`0x02`/`0x03`) and non-FC03 writes/FCs (`0x01`) execute before `SILENT_TIMEOUT`, so malformed/unapproved probes still receive exception replies even during `f timeout`, while all valid FC03 groups are completely silenced. | Non-blocking; ESPHome sends only approved FC03 group requests, so `f timeout` achieves total ESPHome silence. |
| **D5** | Broadcast Unit Test Gap | Runtime code ignores `dev_id=0x00` (`broadcast_enable=False`) and `dev_id=0xFF`, confirmed by our independent read-only probe (`0` responses, `0` mutation), though `tests/test_srne_modbus_simulator.py` explicitly tests `dev_id=2` rather than `dev_id=0`. | Low risk; ESPHome uses `slave_address: 1` (`0x01`). |
| **D6** | Console Output Interleaving & Dongle Unplug | In `--interactive --log-level INFO`, live Modbus request logs write to `sys.stdout` alongside echoed keystrokes (mitigable via `--log-level WARNING` during manual entry). PyModbus `ModbusSerialServer` uses `reconnect_delay=2` if a USB-RS485 dongle disconnects while running. | Cosmetic/operational only during manual bench operation. |

---

## 6. Final Readiness Statement

All offline simulator software checks, protocol-level RTU wire tests (`24/24` PASS), dependency checks (`pip check` exit `0`), and ESPHome register/entity reconciliations (`40` groups / `107` words / `73` entities / `355` deterministic checks) pass. The project is **READY FOR PHYSICAL RS485 BENCH TESTING (`SRNE-03V`)** using [`tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](../tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md). No physical hardware claims are made prior to bench execution.
