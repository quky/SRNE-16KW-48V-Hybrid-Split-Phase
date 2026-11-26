# SRNE-04E-D — Synthetic Modbus Register Fixture Summary

## 1. Scope & Baseline Status

This report summarizes the deterministic synthetic Modbus register fixtures created under **SRNE-04E-D** for offline verification and future RS485 RTU simulator testing of the **SRNE SPI-16K-UP** ESPHome integration.

- **Status**: `SYNTHETIC_OFFLINE_FIXTURE_NOT_PHYSICAL_INVERTER_DATA`
- **No physical inverter telemetry**: Zero values in these fixtures originate from a physical SRNE inverter. Physical USB-RS485 adapter delivery and live physical RS485 inverter validation remain pending.
- **No RTU server / firmware edits**: No Modbus RTU server code was implemented, and all existing ESPHome YAML configurations, audit reports, and Anenji project files remain untouched.

### Created Deliverables

| Artifact | Purpose | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [`tests/fixtures/srne-register-groups.json`](../tests/fixtures/srne-register-groups.json) | 40 FC03 register groups and 107 unique registers with hex/decimal addresses and protocol metadata | 57,250 | `ad37d8602f48af7307ecd1c767d6e85f2d84079c8ac8ff7db7656c36c78279c4` |
| [`tests/fixtures/srne-synthetic-scenarios.json`](../tests/fixtures/srne-synthetic-scenarios.json) | 5 deterministic scenarios (`S1_solar_charging`..`S5_active_fault`), 107 raw uint16 words each | 79,575 | `b4424f9533baeee525ef67190240eb99190ccca510fa2171e03caf10e921b944` |
| [`tests/fixtures/srne-expected-entities.json`](../tests/fixtures/srne-expected-entities.json) | Independent expected values for all 73 public entities (71 deterministic + 2 runtime-dependent) | 41,926 | `a5d4f94d8f84a1ba5f43fe34ee381385050343bb691c30a0074777becec48e71` |
| [`audits/SRNE-04E-D-Synthetic-Fixture-Summary.md`](SRNE-04E-D-Synthetic-Fixture-Summary.md) | Fixture design, protocol reconciliation, and validation boundary summary | — | *(pending final check)* |

### Unchanged Firmware Baseline Checksums

| File | SHA-256 |
| --- | --- |
| [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) | `ff19087f95e83d77e9ee7a65244622037bcf963f60c67ba768cdbe7c9f686a25` |
| [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) | `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80` |
| [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) | `91ebba7848230ab1b19945d6dca71821f6fa040d1591069b4245910e4726c630` |

---

## 2. Register & Group Reconciliation

The fixture set matches the currently implemented firmware register map 1:1 per `SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf`:

- **Protocol transport**: Slave address `1` (`0x01`), `9600,N,8,1`, **FC03 (`0x03`) Read Holding Registers only**, max 32 words per request (maximum implemented group is 20 words in `P2-S05` and `P2-S06`).
- **Word and byte ordering**: 16-bit big-endian payload words (`uint16` `0..65535`); CRC-16 Modbus low byte first.
- **Total coverage**: **40 groups**, **107 unique 16-bit register words**.
  - **Phase 1 (`10s` polling)**: **16 groups** (`P1-R01`..`P1-R16`), **32 unique words**.
  - **Phase 2 Dynamic (`30s` cooperative polling)**: **12 groups** (`P2-D01`..`P2-D12`), **22 unique words**.
  - **Phase 2 Static / Slow (`300s` / `3600s` cooperative polling)**: **12 groups** (`P2-S01`..`P2-S12`), **53 unique words**.
- **Read-only enforcement of RW config registers**: `0xE003` (`57347`), `0xE037` (`57399`), `0xE201` (`57857`), and `0xE215` (`57877`) are included strictly under FC03 read-only policy; zero FC06/FC10 write operations are present.
- **Explicit exclusions**: Gray-text invalid registers, deferred/ambiguous Phase 1 & Phase 2 slots, unsupported Anenji equivalents, and prohibited restart/control registers are excluded.

---

## 3. Synthetic Scenarios

All five requested deterministic operating regimes are modeled using coherent synthetic measurements and synthetic identification constants (`model_code = 16000`, `software_version_app = V1.25 (raw 125)`, `hardware_version_control_board = V1.10 (raw 110)`, `protocol_version = raw 204 (0x00CC)`, `build_time = 2025-11-15 10:30:00`, `serial_number = SYNTH-SPI16K-0001`):

| Scenario ID | Operating State (`0x0210`) | Key Conditions & Edge Cases Exercised |
| --- | --- | --- |
| `S1_solar_charging` | `3` (`Inverter operation`) | PV total `8,428 W`; split-phase load `3,450 W`; negative battery current `-85.0 A` (`0xFCAE`) -> net `-4,556.0 W`, charging power `4,556.0 W`; `Quick charge` (`1`). |
| `S2_battery_discharging` | `3` (`Inverter operation`) | Zero PV (`0 W`); positive battery current `+75.0 A` (`0x02EE`) -> net `+3,840.0 W`, discharging power `3,840.0 W`; split-phase output `3,470 W`; `Charge off` (`0`). |
| `S3_utility_zero_solar` | `2` (`Utility operation`) | Zero solar (`0 W`); bypass load `2,420 W` (`Grid L1/L2 20.5 A / 18.0 A`); utility charging `30.0 A` (`-30.0 A` battery `0xFED4` -> `-1,572.0 W`); `Const voltage charge` (`2`); grid countdown `15 s`; user password `1`. |
| `S4_standby` | `1` (`Standby`) | Idle output `0 W`; SOC `100%` (`Full` `8`); grid countdown `60 s`; **negative signed16 ambient temperature `-2.5 °C` (`0xFFE7`)** verifying signedness handling. |
| `S5_active_fault` | `1` (`Standby`) | Active fault registers `[1, 20, 0, 0]` (`srne_fault_status = true`); zero AC output; elevated heatsinks (`82.1 °C` inverter); manufacturer password status `4`. |

---

## 4. Public Entity Coverage & Preserved Ambiguities

- **Total public entities covered**: **73** (**36 Phase 1 + 37 Phase 2**).
  - **71 deterministic entities**: Independently calculated from raw `uint16` register payloads across all 5 scenarios (`355` expected values total).
  - **2 runtime-dependent entities**: `srne_uptime` (`esphome sensor.uptime`, monotonically increasing seconds) and `srne_modbus_communication_health` (`true` while Phase 1 `R01..R16` remain fresh within `30 s`), explicitly classified as `runtime_dependent`.
- **String masking verification**: Synthetic words for `0x0021..0x0034` (`srne_software_build_time`) and `0x0035..0x0048` (`srne_product_serial_number`) intentionally embed non-zero upper bytes (`0xA5`, `0x3C`, `0x7E`, `0xFF`) in character words to verify `(word & 0x00FF)` lower-8-bit extraction and `0x00`/`0xFF` null termination per protocol page 9.
- **Preserved ambiguities**:
  - `0x001C` (`srne_protocol_version`): Uses firmware verbatim format `"raw %u (0x%04X)"` (`raw 204 (0x00CC)`) rather than guessing decimal vs hex encoding (A13/A22).
  - `0x0204..0x0207` (`srne_fault_status`): Kept boolean-only without decoding fault numeric IDs into text (A25).
  - `0x0210` (`srne_operating_mode`): Uses split-phase `0..3` table exclusively rather than generic off-grid `0..10` enum.

---

## 5. Validation Boundary

All JSON syntax, register coverage, `uint16` bounds, group alignment, independent calculation verification, firmware cross-referencing, and checksum checks apply strictly to **offline static software verification of synthetic fixtures**. They do **not** validate physical RS485 timing (`200ms` turnaround), UART framing on hardware, or undocumented/firmware-specific register behavior on a real **SRNE SPI-16K-UP** inverter.
