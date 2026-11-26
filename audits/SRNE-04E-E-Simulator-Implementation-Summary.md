# SRNE-04E-E — Read-Only Modbus RTU Simulator Implementation Summary

## 1. Scope & Status

Implemented the standalone Windows-compatible **read-only Modbus RTU simulator** for the **SRNE SPI-16K-UP** synthetic fixtures (`SRNE-04E-D`), independent of `esphome/` firmware and strictly offline during this task (**zero physical serial ports opened**).

### Created Deliverables

| Artifact | Role | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) | Standalone read-only Modbus RTU server, fixture validator, immutable datastore, CLI, and logger | 31,993 | `0893bd3b9422d8bf00b00fe35e475afe0b6784024438bf9df15face3c8aaa8cd` |
| [`tests/test_srne_modbus_simulator.py`](../tests/test_srne_modbus_simulator.py) | 13-test `unittest` suite (application-level + in-memory protocol-level RTU wire tests) | 21,464 | `4493b1167bf479f1744ac6aa7ae3d3e33eebfd62e4d0835ccf5b8bd826d42b49` |
| [`tests/README.md`](../tests/README.md) | Simulator CLI usage, scenarios, dependencies, test layers, and limitations | 5,060 | `364b6631c639b2bdb6a57fff2e2822c3fa6d12bc1a624d46c81293157a9150f0` |
| [`audits/SRNE-04E-E-Simulator-Implementation-Summary.md`](SRNE-04E-E-Simulator-Implementation-Summary.md) | Architecture, PyModbus 3.16.2 API analysis, test results, and checksum verification | — | *(verified post-write)* |

---

## 2. PyModbus 3.16.2 APIs Used & Verification Findings

Verified directly against installed `pymodbus==3.16.2` (`.venv-simulator`) and `pyserial==3.5` under Python `3.14.3`:

- **APIs used**:
  - `pymodbus.server.ModbusSerialServer` & `pymodbus.server.requesthandler.ServerRequestHandler` (async RTU server transport & framing lifecycle).
  - `pymodbus.framer.FramerType`, `pymodbus.framer.FramerRTU` (`compute_CRC`, `check_CRC`, RTU framing/deframing).
  - `pymodbus.pdu.ModbusPDU`, `pymodbus.pdu.ExceptionResponse` (validated PyModbus 3.16.2 constructor parameters: `device_id=`, `transaction=`).
  - `pymodbus.constants.ExcCodes` (`ILLEGAL_FUNCTION` `0x01`, `ILLEGAL_ADDRESS` `0x02`, `ILLEGAL_VALUE` `0x03`, `DEVICE_FAILURE` `0x04`) and `pymodbus.exceptions.NoSuchIdException`.
  - `pymodbus.simulator.SimDevice`, `SimData`, `DataType` (read-only placeholder purely to avoid deprecated `ModbusDeviceContext`/`ModbusServerContext` warnings during `ModbusBaseServer.__init__` before assigning `self.context = SRNEReadOnlyContext`).
- **Why custom `SRNEReadOnlyContext` + `SRNERequestHandler` were required instead of `ModbusServerContext` / `SimRuntime`**:
  - `ModbusDeviceContext` / `ModbusServerContext` are deprecated in PyModbus 3.16.2 and auto-wrap into `SimDevice`/`SimCore`.
  - Default `SimRuntime` returns `0x02` (`ILLEGAL_ADDRESS`) instead of `0x01` on writes to read-only blocks, does not enforce the 32-word SRNE max count (`0x03`), and allows non-datastore PDUs (`FC07, FC08, FC11, FC12, FC17, FC24, FC43`) to bypass datastore checks entirely.
  - Default `FramerRTU.decode` silently drops unregistered function codes (`FC09`) when `DecodePDU.calculateRtuFrameSize` returns `0`.

---

## 3. Register Addressing & FC03-Only Enforcement

- **Zero-based wire addressing**: `ReadHoldingRegistersRequest.x_decode` unpacks the exact 16-bit big-endian wire address (`struct.unpack(">HH", data[:4])`) directly into `SRNEReadOnlyContext.async_getValues(device_id, 3, address, count)` with zero offset translation. Wire tests confirm exact boundary reads for first word `0x000B` (`[4]`) and last word `0xF04E` (`[21]`).
- **No gap filling**: Only the **107** exact register words from the **40** approved groups are populated inside immutable `types.MappingProxyType[int, int]`. Any FC03 request touching any unapproved address or spanning an undocumented gap returns `0x83 0x02` (`ILLEGAL_ADDRESS`).
- **Length enforcement**: FC03 quantities outside `1..32` (`0`, `33`, `125`, `126`) return `0x83 0x03` (`ILLEGAL_VALUE`).
- **FC03-only & read-only enforcement (three layers)**:
  1. `SRNERequestHandler.handle_request` rejects **all** decoded non-FC03 requests (`fc != 3`, including writes `FC05/06/15/16/21/22/23` and other FCs `FC01/02/04/07/08/11/12/17/24/43`) *before* calling `datastore_update`, returning `ExceptionResponse(fc, ExcCodes.ILLEGAL_FUNCTION)` (`0x80 | fc`, exception `0x01`).
  2. `SRNERequestHandler.callback_data` catches CRC-valid frames addressed to `device_id == 1` whose function code is not registered in `DecodePDU.pdu_table` (e.g., `FC09`) and returns `(0x80 | fc)` with `0x01`.
  3. `SRNEReadOnlyContext.async_setValues` unconditionally returns `ExcCodes.ILLEGAL_FUNCTION` (`0x01`), and backing storage is immutable (`MappingProxyType`).

---

## 4. Verification Summary

### Offline Automated Test Suite (`unittest`)

Command executed under `.venv-simulator`:

```powershell
.\.venv-simulator\Scripts\python.exe -W default -m unittest discover -s tests -p "test_*.py" -v
```

Result: **13 tests passed in 1.349s** (`OK`, 0 failures, 0 errors, 0 skipped, 0 deprecation warnings):

1. **Application-level tests (8 tests)** across `TestFixtureLoadingAndValidation`, `TestReadOnlyContextApplicationLevel`, and `TestCLIAndNoSerialAccess`:
   - 5 scenarios (`S1_solar_charging`..`S5_active_fault`), 40 groups, 107 registers, 73 entity summary validated; safe `FixtureValidationError` on missing directory, corrupt JSON, `bool` disguised as `uint16`, and out-of-range `> 65535`.
   - `200` context group reads (`40` groups × `5` scenarios), negative `int16` wire values (`0xFCAE`, `0xFFE7`), string upper-byte preservation (`0x0021..0x0034`), gap/quantity/write/unknown-ID rejections, and immutable `MappingProxyType` protection.
   - CLI `--help`, `--list-scenarios`, `--validate-only`, missing `--port` (`exit 2`), and unknown `--scenario` (`exit 2`) verified with `serial.Serial`, `serial.serial_for_url`, and `pymodbus.transport.serialtransport.create_serial_connection` patched to fail if called.
2. **Protocol-level in-memory RTU wire tests (5 async tests)** in `TestProtocolLevelRTUWireFrames`:
   - Instantiates `SRNEModbusSerialServer` + `SRNERequestHandler` wired to an `_InMemoryRTUTransport` (`asyncio.Transport`), encoding requests with `FramerRTU.compute_CRC` and verifying CRC-16, slave byte, FC/exception byte, byte count, and big-endian wire payload on every reply:
     - **200** RTU wire round-trips covering all **40** approved groups across all **5** scenarios.
     - Exact wire boundary verification (`0x000B`, `0xF04E`), `int16` (`0x0102` -> `0xfc ae`, `0x0223` -> `0xff e7`), and string upper bytes (`0x0035` count `20`).
     - RTU exception `01 83 02` on gaps/bounds (`0x0000`, `0x0103+2`, `0x0104`, `0xF04F`) and `01 83 03` on invalid quantities (`0`, `33`, `125`, `126`).
     - Explicit RTU exception `01 <0x80|fc> 01` on **FC01, FC02, FC04, FC05, FC06, FC07, FC09, FC15, FC16, FC17, FC22, FC23**, followed by FC03 verification confirming zero register mutation.
     - Non-matching slave (`dev=2`) silence, corrupted CRC silence, and INFO/DEBUG/WARNING timestamped logging checks.

### CLI Validation Results (Zero Serial Port Access)

- `--help`: exit `0`
- `--list-scenarios`: exit `0`, printed `SYNTHETIC SRNE SIMULATOR — NOT A PHYSICAL INVERTER` and all 5 scenarios (`S1_solar_charging [default]`..`S5_active_fault`)
- `--validate-only` (default) and `--validate-only --scenario S5_active_fault`: exit `0`, confirmed `groups=40, registers=107, entities=73, policy=FC03-only`
- Default invocation without `--port`: exit `2`, printed clear error requiring explicit `--port` (never auto-selects `COM3`)

---

## 5. Unchanged Baseline Checksums & Known Limitations

### Unchanged Firmware & Fixture SHA-256 Checksums

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) | 978 | `ff19087f95e83d77e9ee7a65244622037bcf963f60c67ba768cdbe7c9f686a25` |
| [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) | 33,475 | `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80` |
| [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) | 34,982 | `91ebba7848230ab1b19945d6dca71821f6fa040d1591069b4245910e4726c630` |
| [`tests/fixtures/srne-register-groups.json`](../tests/fixtures/srne-register-groups.json) | 57,250 | `ad37d8602f48af7307ecd1c767d6e85f2d84079c8ac8ff7db7656c36c78279c4` |
| [`tests/fixtures/srne-synthetic-scenarios.json`](../tests/fixtures/srne-synthetic-scenarios.json) | 79,575 | `b4424f9533baeee525ef67190240eb99190ccca510fa2171e03caf10e921b944` |
| [`tests/fixtures/srne-expected-entities.json`](../tests/fixtures/srne-expected-entities.json) | 41,926 | `a5d4f94d8f84a1ba5f43fe34ee381385050343bb691c30a0074777becec48e71` |

### Limitations & Blockers

- **Known limitations**: No runtime scenario switching, timeout injection, malformed frame injection, or physical COM port execution in `SRNE-04E-E` (deferred by task scope).
- **Physical validation status**: No physical RS485 serial port was opened; hardware RS485 turnaround timing and live **SRNE SPI-16K-UP** register validation remain pending.
- **No blockers**: PyModbus 3.16.2 enforces strict FC03-only operation cleanly via `SRNERequestHandler` + `SRNEReadOnlyContext`.
