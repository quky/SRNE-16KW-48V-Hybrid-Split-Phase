# SRNE-04G — Phase 2 Extended Diagnostic Implementation Summary

Completed 2026-11-25 for owner review. Implements all **37 approved Phase 2 read-only diagnostic entities** (35 `SUPPORTED` + 2 `ALTERNATIVE`) across **24 isolated FC03 groups** (**75** register words) using the **SRNE-04G-R1** cooperative `modbus_client.read_holding_registers` architecture under ESPHome **2026.11.1**.

## Validation Status & Boundary

| Check | Status | Notes |
|---|---|---|
| ESPHome `2026.11.1` `esphome config` validation | **PASS** | `esphome config esphome/srne-bench-test.yaml` exited `0` (`Configuration is valid!`) |
| Static ID, address, permission & write-exclusion checks | **PASS** | Automated Python verification against `SRNE-04F` CSV, `SRNE-01B` inventory, and Phase 1 |
| Phase 1 byte-for-byte preservation | **PASS** | Verified unchanged SHA256 on `srne-phase1-monitoring.yaml` |
| Firmware compilation & wireless deployment | **NOT RUN** | Explicitly restricted |
| RS485 simulator testing | **NOT RUN** | Required next step before physical inverter testing; `turnaround_time: 200ms` is provisional |
| Physical SPI-16K-UP RS485 validation | **PENDING** | No live inverter communication performed |

---

## 1. Changed & Created Files (SHA-256 Fingerprints)

| File | Action | SHA-256 |
|---|---|---|
| [srne-bench-test.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/srne-bench-test.yaml) | Modified (2 additions: `srne_phase2_diagnostics` package include + `turnaround_time: 200ms`) | `8d0637b1443e60e0fde9d09963a527ebb4be184f51220b26a8389d8bbcdd2742` |
| [srne-phase2-diagnostics.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/packages/srne-phase2-diagnostics.yaml) | Created (37 entities, 24 FC03 groups, 75 words) | `91ebba7848230ab1b19945d6dca71821f6fa040d1591069b04d2befc2f638b80` |
| [srne-phase1-monitoring.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/packages/srne-phase1-monitoring.yaml) | **Preserved byte-for-byte** | `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80` |
| [SRNE-04G-R1-Architecture-Correction.md](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04G-R1-Architecture-Correction.md) | Created | *(computed post-write; see verification output)* |
| [SRNE-04G-Implementation-Summary.md](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04G-Implementation-Summary.md) | Created | *(this file)* |

All UART (`GPIO17`/`GPIO18`, `9600,N,8,1`), `flow_control_pin: GPIO21`, `send_wait_time: 300ms`, Wi-Fi, API encryption, OTA, logger, and `srne_uptime` configurations were preserved unchanged. No credentials were accessed or exposed.

---

## 2. Public Entity Counts

| Scope | Numeric (`sensor`) | Binary (`binary_sensor`) | Text (`text_sensor`) | Total Public Entities |
|---|---:|---:|---:|---:|
| **Phase 1 (Existing, Unchanged)** | 33 *(incl. `srne_uptime`)* | 2 | 1 | **36** |
| **Phase 2 (New, `entity_category: diagnostic`)** | 26 | 0 | 11 | **37** |
| **Combined Total** | **59** | **2** | **12** | **73** |

- All 37 Phase 2 entities use descriptive SRNE-specific names matching [SRNE-04F-Extended-Diagnostic-Mapping.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04F-Extended-Diagnostic-Mapping.csv).
- Runtime/cumulative counters (`srne_battery_cycle_count`, `srne_inverter_operating_time_today`, `srne_bypass_operating_time_today`, `srne_total_operating_days`, `srne_cumulative_inverter_operating_time`, `srne_cumulative_bypass_operating_time`) and static config values (`srne_device_address`, `srne_model_code`, `srne_battery_rated_voltage`) retain `state_class: ""` until physical reset/persistence validation is completed.
- All 21 held candidates, 7 unsupported candidates, `0xDF00`/`0xDF01` controls, `0x0221` (already in Phase 1), and all gray-invalid registers are excluded.

---

## 3. Exact Phase 2 FC03 Request Groups (24 Groups, 75 Words, Max 20 Words/Req)

### Dynamic Diagnostics (`30s` Default Poll, `90s` Freshness, `5.5s`–`13.75s` Boot Stagger)

| Index | Group | Start | Inclusive End | Words | Data Bytes | Entities (IDs) |
|---:|---|---|---|---:|---:|---|
| 0 | `D01` | `0x0105` | `0x0106` | 2 | 4 | `srne_battery_rated_capacity`, `srne_battery_remaining_capacity` |
| 1 | `D02` | `0x010B` | `0x010C` | 2 | 4 | `srne_battery_charging_status`, `srne_battery_cycle_count` |
| 2 | `D03` | `0x010E` | `0x010E` | 1 | 2 | `srne_total_charging_power` |
| 3 | `D04` | `0x0112` | `0x0112` | 1 | 2 | `srne_bms_voltage` |
| 4 | `D05` | `0x0114` | `0x0117` | 4 | 8 | `srne_bms_temperature`, `srne_bms_charge_voltage_limit`, `srne_bms_charge_current_limit`, `srne_bms_discharge_current_limit` |
| 5 | `D06` | `0x020F` | `0x020F` | 1 | 2 | `srne_grid_connection_countdown` |
| 6 | `D07` | `0x0211` | `0x0212` | 2 | 4 | `srne_password_protection_status`, `srne_total_dc_bus_voltage` |
| 7 | `D08` | `0x021E` | `0x021E` | 1 | 2 | `srne_utility_charging_current` |
| 8 | `D09` | `0x0220` | `0x0220` | 1 | 2 | `srne_heatsink_a_temperature` |
| 9 | `D10` | `0x0222` | `0x0224` | 3 | 6 | `srne_heatsink_c_temperature`, `srne_ambient_temperature`, `srne_pv_charging_current` |
| 10 | `D11` | `0x0228` | `0x0229` | 2 | 4 | `srne_positive_dc_bus_voltage`, `srne_negative_dc_bus_voltage` |
| 11 | `D12` | `0xF03E` | `0xF03F` | 2 | 4 | `srne_inverter_operating_time_today`, `srne_bypass_operating_time_today` |

### Static Identification & Slow Config/Runtime (`300s`–`3600s`, `>= 2000ms` Spacing, `15.5s`–`70.5s` Boot Stagger)

| Index | Group | Start | Inclusive End | Words | Data Bytes | Poll / Freshness | Entities (IDs) |
|---:|---|---|---|---:|---:|---|---|
| 12 | `S01` | `0x000B` | `0x000B` | 1 | 2 | `3600s` / `10800s` | `srne_product_type` |
| 13 | `S02` | `0x0014` | `0x0014` | 1 | 2 | `3600s` / `10800s` | `srne_software_version_app` |
| 14 | `S03` | `0x0016` | `0x0016` | 1 | 2 | `3600s` / `10800s` | `srne_hardware_version_control_board` |
| 15 | `S04` | `0x001A` | `0x001C` | 3 | 6 | `3600s` / `10800s` | `srne_device_address`, `srne_model_code`, `srne_protocol_version` |
| 16 | `S05` | `0x0021` | `0x0034` | 20 | 40 | `3600s` / `10800s` | `srne_software_build_time` |
| 17 | `S06` | `0x0035` | `0x0048` | 20 | 40 | `3600s` / `10800s` | `srne_product_serial_number` |
| 18 | `S07` | `0xE003` | `0xE003` | 1 | 2 | `3600s` / `10800s` | `srne_battery_rated_voltage` *(FC03 read-only; A03 prohibits writes)* |
| 19 | `S08` | `0xE037` | `0xE037` | 1 | 2 | `300s` / `900s` | `srne_configured_operating_mode` *(FC03 read-only)* |
| 20 | `S09` | `0xE201` | `0xE201` | 1 | 2 | `3600s` / `10800s` | `srne_parallel_operation_mode` *(FC03 read-only)* |
| 21 | `S10` | `0xE215` | `0xE215` | 1 | 2 | `3600s` / `10800s` | `srne_bms_enable_mode` *(FC03 read-only)* |
| 22 | `S11` | `0xF031` | `0xF031` | 1 | 2 | `3600s` / `10800s` | `srne_total_operating_days` |
| 23 | `S12` | `0xF04A` | `0xF04B` | 2 | 4 | `3600s` / `10800s` | `srne_cumulative_inverter_operating_time`, `srne_cumulative_bypass_operating_time` |

- **Zero Phase 1 overlap**: All 75 words are disjoint from Phase 1's 32 words.
- **Adjacent string separation**: `S05` (`0x0021–0x0034`, 20 words) and `S06` (`0x0035–0x0048`, 20 words) are dispatched as separate `modbus_client.read_holding_registers` calls (never merged to 40 words).

---

## 4. Scheduling, Bus Utilization & Failure Isolation

- **No additional `modbus_controller`**: Uses one parameterized `srne_p2_dispatch` script invoking `modbus_client.read_holding_registers` on `modbus1` (`address: 0x01`). Phase 2 can never invoke `clear_tx_queue_for_address(0x01)`.
- **Cooperative single-in-flight scheduler (`250ms` interval)**: Dispatches at most 1 Phase 2 group only when `srne_p2_in_flight == false`, `modbus1.tx_buffer_empty()`, `!modbus1.tx_blocked()`, `!srne_phase1_scan_active`, `!srne_phase1_awaiting`, and not within `700ms` of Phase 1's next `10s` sweep start. Static/slow groups (`g >= 12`) also enforce `srne_phase2_static_min_spacing_ms: 2000ms`.
- **Recalculated bus utilization (`turnaround_time = 200ms`, `9600,N,8,1`)**:
  - At `T_resp = 50ms`: Phase 1 (`16` reqs/`10s`) = `4.34 s` (**43.4%**, `5.66 s` quiet window); combined Phase 1 + Phase 2 Dynamic (`60` reqs/`30s`) = `16.28 s` (**54.3%**); 1-hour average = **54.4%**.
  - Missing 3 optional BMS groups (`D01`, `D04`, `D05`): initial timeout window `57.7%`, dropping to `51.8%` steady-state under `300s` exception/timeout backoff.
  - Detailed breakdown across all 6 worst-case scenarios is in [SRNE-04G-R1-Architecture-Correction.md](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04G-R1-Architecture-Correction.md).
- **Per-group failure & freshness isolation**:
  - `on_response` verifies `values.size() == srne_p2_expected_count`; `on_custom_response`, `on_error`, `on_no_response` (`retry: false`), `on_not_sent`, and the `2000ms` in-flight watchdog route to `srne_p2_handle_failure`.
  - Only the affected group is invalidated (`NAN` for numeric sensors, `"Unavailable"` for text sensors), guarded by `srne_p2_invalid_pub[g]` to avoid repeated identical invalid publications.
  - Per-group freshness expires at `3x` the group's configured poll interval (`90s` dynamic, `900s` `S08`, `10800s` static/slow). Valid responses clear `fail_count[g]` and restore valid states.

---

## 5. String, Version & Enumeration Decoding

- **Lower-8-bit string decoder (`S05`, `S06`)**: Per V2.04 P p9, masks each word with `w & 0x00FF`, stops at `0x00` or `0xFF` terminator, rejects non-printable control/high bytes (`< 0x20` or `>= 0x7F`) before the terminator, trims leading/trailing ASCII spaces, and rejects empty strings (invalidating the group rather than fabricating text).
- **Version formatting (`S02`, `S03`, `S04`)**: `0x0014` (`S02`) and `0x0016` (`S03`) format as `V<major>.<minor> (raw <n>)` per P p9's `100 -> V1.00` example. `0x001C` (`S04` RS485 Protocol Version) formats as `raw <n> (0x<HEX>)` to preserve both decimal and P p9's `%x` display convention without guessing.
- **Enumerations (`D02`, `D07`, `S01`, `S08`, `S09`, `S10`)**: All documented enum values map verbatim; any undocumented code publishes `"Unknown (<raw decimal>)"`.

---

## 6. Confirmation of Zero Writable Inverter Controls

- Protocol function code used exclusively: **FC03** (`modbus_client.read_holding_registers`).
- Static inspection confirms **zero** `write_single_register`, `write_multiple_registers`, `write_single_coil`, `write_multiple_coils`, `read_write_multiple_registers`, `custom_pdu` writes, `switch`, `number`, `select`, `button`, or `output` entities in [srne-phase2-diagnostics.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/packages/srne-phase2-diagnostics.yaml).

Stop for owner review after SRNE-04G / SRNE-04G-R1.
