# SRNE-04F — Extended Diagnostic Register Audit

Completed 2026-11-25 for owner review. This is a **documentation-only** audit identifying read-only extended diagnostic and device-identification candidates in the official SRNE Modbus Monitoring Protocol V2.04 for the SRNE SPI-16K-UP inverter.

## Baseline & Validation Status

| Check / Milestone | Status | Notes |
|---|---|---|
| Phase 1 ESPHome 2026.11.1 compilation & wireless deployment | **PASS (Owner-Verified)** | Deployed via HA Device Builder (`esphome/srne-bench-test.yaml` + `esphome/packages/srne-phase1-monitoring.yaml`) |
| Disconnected Home Assistant operation | **PASS (Owner-Verified)** | All 36 planned public entities verified in Home Assistant |
| Simulated RS485 / Modbus testing | **NOT RUN** | No simulator traffic exercised |
| Physical RS485 inverter communication | **PENDING** | No live SPI-16K-UP register readback or compatibility proof yet |
| SRNE-04F audit deliverables | **CREATED (Docs Only)** | No YAML, C++, firmware, HA, Anenji, or Git changes performed |

> [!IMPORTANT]
> Protocol documentation (`DOCUMENTED`) establishes series-level register definitions only. Physical register availability, scaling accuracy, sensor presence, and firmware behavior on the installed SPI-16K-UP remain **UNVERIFIED** until live RS485 bench validation succeeds.

## Authoritative Sources & Evidence Rules

| Key | File | Scope / SHA-256 |
|---|---|---|
| P | [SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/documentation/official/SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf) | Primary register authority (15 PDF pages)<br>`0c49c599a1a45c29bca0362241a8b460b308b07ad586561f943b3b25073e2f50` |
| W | [SPI-16K-UP User Manual from srne weg page.pdf](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/documentation/official/SPI-16K-UP%20User%20Manual%20from%20srne%20weg%20page.pdf) | V00, 2025-12-16 (56 PDF pages; ASP datasheet labels)<br>`c688cab158750fd7883ccbe00a793896ee651456b4d35195d072f3932b94813c` |
| S | [SPI-16K-UP User Manual V01 2026-05-08 form seller.pdf](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/documentation/official/SPI-16K-UP%20User%20Manual%20V01%202026-05-08%20form%20seller.pdf) | V01, 2026-05-08 (60 PDF pages; SPI-16K-UP datasheet labels)<br>`8e3fdd95171e0634b07e4751505895d7a0162001d4795171bdbec9a37d52dbf2` |
| 01B-CSV | [SRNE-01B-Register-Inventory.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Register-Inventory.csv) | 1,011 inventory entries<br>`71ed75bdd2d1dd62c3487a57b685586705b1977967aed3b82e1a5d7d11f931aa` |
| 01B-MD | [SRNE-01B-Audit-Summary.md](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Audit-Summary.md), [Communication-Specification](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Communication-Specification.md), [Monitoring-Coverage](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Monitoring-Coverage.md), [Write-Risk-Matrix](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Write-Risk-Matrix.md), [Ambiguities](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Ambiguities.md) | Protocol rules, A01–A25, M01–M10, write risk classifications |
| 04A | [SRNE-04A-Phase1-Entity-Mapping.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04A-Phase1-Entity-Mapping.csv), [SRNE-04A-Phase1-Mapping-Summary.md](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04A-Phase1-Mapping-Summary.md) | Phase 1 45-slot mapping (`5d219924...` / `34a009c1...`) |
| FW | [srne-phase1-monitoring.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/packages/srne-phase1-monitoring.yaml), [srne-bench-test.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/srne-bench-test.yaml) | Read-only baseline inspection (`4fb4a88f...` / `30cb9a0d...`) |

- **Page references** use **1-based PDF page numbers** (`P PDF p9`–`p15`).
- **Evidence definitions**: `DOCUMENTED` = explicitly printed in official sources; `INFERRED` = engineering derivation/applicability from official text; `UNVERIFIED` = missing definition, unresolved conflict, or untested hardware behavior.

---

## Summary Totals

| Metric | Count | Details |
|---|---:|---|
| Total audited candidates | **67** | 18 requested Anenji-equivalent (`A01`–`A18`) + 49 SRNE-specific (`S01`–`S49`) |
| `SUPPORTED` | **35** | Documented at protocol level; read-only FC03 candidates |
| `ALTERNATIVE` | **2** | Related SRNE measurement (`0x0016` Control Board HW, `0x0220` Heatsink A DC-DC) |
| `AMBIGUOUS` (Held) | **21** | Held pending physical readback or semantic clarification (A02–A25, M05–M06) |
| `UNSUPPORTED` | **7** | No documented equivalent in SRNE V2.04 |
| `ALREADY_IMPLEMENTED` | **1** | `0x0221` Inverter Temperature (Heatsink B) in Phase 1 `R09` |
| `DEFERRED_WRITE` (Prohibited) | **1** | `0xDF01` Reset Control (write-only; implementation prohibited) |
| **Recommended Phase 2 entities** | **37** | **35 `SUPPORTED` + 2 `ALTERNATIVE`** (22 dynamic + 15 static/slow) |
| **Proposed Phase 2 FC03 groups** | **24** | 12 dynamic (`D01`–`D12`, `30s`) + 12 static/slow (`S01`–`S12`, `300s–3600s`) |
| **Total Phase 2 register words** | **75** | 22 dynamic + 53 static/slow; **0 overlap** with Phase 1's 32 words |
| Max words per Phase 2 request | **20** | Static strings `S05` / `S06` (20 words each); dynamic max **4** words (`D05`); protocol limit `<= 32` |

---

## 1. Requested Anenji-Equivalent Candidates (18 Items)

Every requested entity from the separate Anenji project was evaluated strictly against SRNE V2.04 without importing Anenji register addresses, scales, or enumerations. Full per-column specifications are in [SRNE-04F-Extended-Diagnostic-Mapping.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04F-Extended-Diagnostic-Mapping.csv).

| # | Requested Concept | Classification | Proposed SRNE Entity / ID | Register (Hex / Dec) | Len | Perm / FC | Scale / Unit | PDF Ref | Phase 2 Decision |
|---|---|---|---|---|---:|---|---|---|---|
| 1 | Negative DC Bus Voltage | `SUPPORTED` | Negative DC Bus Voltage (`srne_negative_dc_bus_voltage`) | `0x0229` (`553`) | 1 | `R` / `0x03` | `0.1` V (uint16) | P p10 | `RECOMMENDED` (`D11`) |
| 2 | Positive DC Bus Voltage | `SUPPORTED` | Positive DC Bus Voltage (`srne_positive_dc_bus_voltage`) | `0x0228` (`552`) | 1 | `R` / `0x03` | `0.1` V (uint16) | P p10 | `RECOMMENDED` (`D11`) |
| 3 | Charging Status | `SUPPORTED` | Battery Charging Status (`srne_battery_charging_status`) | `0x010B` (`267`) | 1 | `R` / `0x03` | Enum (uint16) | P p9 | `RECOMMENDED` (`D02`) |
| 4 | Ambient Temperature | `SUPPORTED` | Ambient Temperature (`srne_ambient_temperature`) | `0x0223` (`547`) | 1 | `R` / `0x03` | `0.1` °C (int16) | P p10 | `RECOMMENDED` (`D10`) |
| 5 | Fault Record Count | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P pp14–15 (absent) | `EXCLUDED` |
| 6 | Fault Record Pointer | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P pp14–15 (absent) | `EXCLUDED` |
| 7 | Hardware Version M1 | `ALTERNATIVE` | Hardware Version (Control Board) (`srne_hardware_version_control_board`) | `0x0016` (`22`) | 1 | `R` / `0x03` | `1` / `V1.00` (uint16) | P p9 | `RECOMMENDED` (`S03`) |
| 8 | Hardware Version M2 | `AMBIGUOUS` | Hardware Version (Power Board) (`srne_hardware_version_power_board`) | `0x0017` (`23`) | 1 | `R` / `0x03` | `1` / `V1.00` (uint16) | P p9 | `HOLD` (marked `reserved`) |
| 9 | Hardware Version S1 | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P p9 (absent) | `EXCLUDED` |
| 10 | Internal Fan Duty | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P pp9–15 (absent) | `EXCLUDED` |
| 11 | Inverter Restart | `DEFERRED_WRITE` | Reset Control (`NONE`) | `0xDF01` (`57089`) | 1 | `W` / **Prohibited** | `1: Reset` (uint16) | P p11 | **PROHIBITED** |
| 12 | Inverter Temperature | `ALREADY_IMPLEMENTED` | Inverter Temperature (Heatsink B) (`srne_inverter_temperature`) | `0x0221` (`545`) | 1 | `R` / `0x03` | `0.1` °C (int16) | P p10 | `EXCLUDED` (Phase 1 `R09`) |
| 13 | Library Version | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P p9 (absent) | `EXCLUDED` |
| 14 | Manufacturer Name | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P p9 (absent) | `EXCLUDED` |
| 15 | Product Serial Number | `SUPPORTED` | Product Serial Number (`srne_product_serial_number`) | `0x0035–0x0048` (`53–72`) | 20 | `R` / `0x03` | Lower 8 bits/word string | P p9 | `RECOMMENDED` (`S06`) |
| 16 | PV Temperature | `ALTERNATIVE` | Heatsink A Temperature (DC-DC) (`srne_heatsink_a_temperature`) | `0x0220` (`544`) | 1 | `R` / `0x03` | `0.1` °C (int16) | P p10 | `RECOMMENDED` (`D09`) |
| 17 | Rated Active Power | `UNSUPPORTED` | `NONE` | `NONE` | 0 | `NONE` | `N/A` | P pp9–15 (absent) | `EXCLUDED` |
| 18 | Transformer Temperature | `SUPPORTED` | Heatsink C Temperature (Transformer) (`srne_heatsink_c_temperature`) | `0x0222` (`546`) | 1 | `R` / `0x03` | `0.1` °C (int16) | P p10 | `RECOMMENDED` (`D10`) |

### Key Rationale for Non-Exact Matches
- **DC Bus Rails (`0x0228`, `0x0229`)**: P p10 explicitly remarks both as *"Used by split-phase integrated units and European-standard 10 kW units."* Both are unsigned `0.1 V` values; physical testing must confirm whether `0x0229` is reported as positive magnitude and how `0x0228 + 0x0229` compares to `0x0212` Total DC Bus Voltage.
- **Charging Status (`0x010B`)**: Non-gray P01 register with explicit bit/state table (`0x0000` Charge off, `0x0001` Quick charge, `0x0002` Const voltage charge, `0x0004` Float charge, `0x0005` Reserved, `0x0006` Lithium battery activation, `0x0008` Full). Gray-invalid customized register `0x0227` (`Charging Status (RV)`) is excluded per P p9 note 1.
- **Hardware Versions (`0x0016`, `0x0017`)**: SRNE does not use `M1/M2/S1`. `0x0016` (Control board version) is recommended as an `ALTERNATIVE`; `0x0017` is remarked *"Power board version; ... reserved"* and held as `AMBIGUOUS` pending bench readback; no third/slave hardware version register exists (`UNSUPPORTED`).
- **Temperatures (`0x0220`, `0x0221`, `0x0222`, `0x0223`)**: `0x0221` (Heatsink B, DC-AC) is already in Phase 1 (`srne_inverter_temperature`). `0x0220` (Heatsink A, DC-DC) is an `ALTERNATIVE` for PV temperature because user manuals display *PV-side*, *INV*, and *BAT* heatsink temperatures (W p28 / S p27) whereas V2.04 labels *DC-DC / DC-AC / Transformer* (ambiguity **M09**). `0x0222` (Heatsink C, Transformer) and `0x0223` (Ambient Temperature) are `SUPPORTED`.
- **Inverter Restart (`0xDF01`)**: Write-only (`W`), CRITICAL risk (`1: Reset; Other values: No action`). Distinct from `0xDF00` Power ON/OFF Control (`W`, `0: OFF / 1: ON`). **Identified only; implementation is strictly prohibited.**
- **Unsupported Items (`A05`, `A06`, `A09`, `A10`, `A13`, `A14`, `A17`)**: V2.04 contains no fault record count, fault ring-buffer pointer, slave hardware version, fan duty/PWM/RPM telemetry (only manual fault code `21` `FanFail` exists), library version, manufacturer name (`0x0020` Manufacturing Location Code is gray-invalid), or rated active power register.

---

## 2. Additional SRNE-Specific Diagnostic Candidates (`S01`–`S49`)

All 49 SRNE-specific candidates are itemized in [SRNE-04F-Extended-Diagnostic-Mapping.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04F-Extended-Diagnostic-Mapping.csv) across the requested diagnostic domains:

1. **Model Identification (3 `SUPPORTED`, 1 `AMBIGUOUS` held)**:
   - `RECOMMENDED`: `0x000B` Product Type (`S01`), `0x001A` Device RS485 Address (`S05`), `0x001B` Model Code (`S06`, raw integer; no lookup table in V2.04).
   - `HOLD`: `0x024D` Parallel Unit Count Display (`S36`, **A02**: erroneous `W` unit, V2.04 red-text addition).
2. **Firmware & Hardware Versions (3 `SUPPORTED`, 2 `AMBIGUOUS` held)**:
   - `RECOMMENDED`: `0x0014` Software Version APP (`S02`, word 0 of `0x0014–0x0015`), `0x001C` RS485 Protocol Version (`S07`, word 0 of `0x001C–0x001D`; `%x` display format vs `100 -> V1.00` remark), `0x0021–0x0034` Software Build Time (`S08`, 20-word lower-8-bit string).
   - `HOLD`: `0x000A` Minor Version (`S04`, remarked `Reserved`), `0x0015` Software Version Bootloader (`S03`, remarked `reserved`). Note: manuals W p28 / S p27 display a *Slave chip software version* on the LCD, but V2.04 defines no slave-chip software register.
3. **Additional Internal Temperatures (1 `SUPPORTED`)**:
   - `RECOMMENDED`: `0x0114` Battery BMS Temperature (`S15`, signed `0.1 °C`, V1.99 addition; distinct from Phase 1 `0x0103` Battery Temperature).
4. **Fan Speed & Status (0 registers)**:
   - No fan speed (RPM), fan duty (%), or fan run-status register exists in V2.04. Only user-manual fault code `21` (`FanFail`) indicates fan blockage/failure.
5. **Fault & Warning Information (0 newly recommended; 5 `AMBIGUOUS` held)**:
   - `HOLD`: `0x0118–0x0119` BMS Alarm Flags (`S19`, **A21**), `0x011A–0x011B` BMS Protection Flags (`S20`, **A21**), `0x0200–0x0203` Current Fault Bits (`S21`, **A21**, internal debug), `0x0204–0x0207` Active Fault Codes (`S22`, **A25** radix ambiguity; already polled in Phase 1 `R04` with 0 extra wire words), `0xF800–0xF9FF` Fault History Records 0–31 (`S23`, **A21**/**A25**).
6. **Charging, Operating States, BMS Limits & Runtime Diagnostics (17 `SUPPORTED`, 6 `AMBIGUOUS` held)**:
   - `RECOMMENDED` Dynamic: `0x0105` Battery Rated Capacity (`S09`), `0x0106` Remaining Battery Capacity (`S10`), `0x010C` Battery Cycle Count (`S11`), `0x010E` Total Charging Power (`S12`), `0x0112` Battery BMS Voltage (`S13`), `0x0115–0x0117` BMS Charge/Discharge Voltage & Current Limits (`S16`–`S18`), `0x020F` Grid-Connection Countdown (`S26`), `0x0211` Password Protection Status (`S27`), `0x0212` Total DC Bus Voltage (`S28`), `0x021E` Utility Charging Current (`S29`), `0x0224` PV Charging Current (`S30`), `0xF03E` Inverter Operating Time Today (`S32`), `0xF03F` Bypass Operating Time Today (`S33`).
   - `RECOMMENDED` Slow/Config Readback (FC03 only): `0xE037` Configured Operating Mode (`S39`, distinct from Phase 1 `0x0210` Current Operating Status), `0xF031` Total Operating Days (`S31`), `0xF04A` Cumulative Inverter Operating Time (`S34`), `0xF04B` Cumulative Bypass Operating Time (`S35`).
   - `HOLD`: `0x0113` Battery BMS Current (`S14`, **A04**), `0x020B` Power Flow Diagram Flag (`S24`, **A21**), `0x020C–0x020E` Inverter RTC Clock (`S25`, century/BCD/TZ unspecified), `0xE039` PV Output Priority (`S40`, **M05**), `0xE204` Output Priority (`S42`, **A09**/**M05**), `0xE20F` Charging Priority (`S44`, **M06**).
7. **Device Ratings & Capabilities / Read-Only Config Readbacks (3 `SUPPORTED`, 6 `AMBIGUOUS` held)**:
   - `RECOMMENDED` (FC03 read-only): `0xE003` Battery Rated Voltage (`S37`, **A03** RW conflict prohibits writes), `0xE201` Parallel Operation Mode (`S41`), `0xE215` BMS Communication Mode (`S45`).
   - `HOLD`: `0xE004` Battery Type (`S38`, **A16**), `0xE20A` Maximum Charging Current (`S43`, **A07**/**A10**), `0xE218` Inverter Power Derating (`S46`, **A10**), `0xE21B` BMS Protocol (`S47`, undocumented enum), `0xE21E` Split-Phase AC Wiring Type (`S48`, **A13**), `0xE403` Grid Standard Setting (`S49`, Signed/default 100 mismatch).

### Explicitly Excluded Gray-Invalid Registers (P p9 Note 1)
All gray-text rows in V2.04 are invalid for energy storage inverters and excluded: `0x000C–0x0013` (Reserved), `0x0018–0x0019` (Reserved), `0x001E–0x001F` (Manufacturing Date), `0x0020` (Manufacturing Location Code), `0x0049` (Reserved), `0x021A` (Load PF), `0x021D` (DC Component), `0x0226` (Inverter Fault Status RV), `0x0227` (Charging Status RV), `0xE002` (Battery Nominal Capacity), and `0xE014–0xE01A` (Temperature compensation/limits).

---

## 3. Recommended Phase 2 Polling Tiers & FC03 Request Groups

Phase 2 separates **dynamic operational diagnostics** (`30s`) from **static device identification and slow configuration/cumulative runtime readbacks** (`300s–3600s`), minimizing RS485 bus airtime at `9600,N,8,1`.

### Tier A — Dynamic Diagnostics (`30s` Poll Interval: 12 Groups, 22 Entities, 22 Words)

| Group | Start | Inclusive End | Words | Data Bytes | Entities Included (CSV IDs) |
|---|---|---|---:|---:|---|
| `D01` | `0x0105` | `0x0106` | 2 | 4 | `S09` Battery Rated Capacity, `S10` Remaining Battery Capacity |
| `D02` | `0x010B` | `0x010C` | 2 | 4 | `A03` Battery Charging Status, `S11` Battery Cycle Count |
| `D03` | `0x010E` | `0x010E` | 1 | 2 | `S12` Total Charging Power |
| `D04` | `0x0112` | `0x0112` | 1 | 2 | `S13` Battery BMS Voltage |
| `D05` | `0x0114` | `0x0117` | 4 | 8 | `S15` BMS Temp, `S16` Charge V Limit, `S17` Charge I Limit, `S18` Discharge I Limit |
| `D06` | `0x020F` | `0x020F` | 1 | 2 | `S26` Grid-Connection Countdown |
| `D07` | `0x0211` | `0x0212` | 2 | 4 | `S27` Password Protection Status, `S28` Total DC Bus Voltage |
| `D08` | `0x021E` | `0x021E` | 1 | 2 | `S29` Utility Charging Current |
| `D09` | `0x0220` | `0x0220` | 1 | 2 | `A16` Heatsink A Temperature (DC-DC) |
| `D10` | `0x0222` | `0x0224` | 3 | 6 | `A18` Heatsink C Temp (Transformer), `A04` Ambient Temp, `S30` PV Charging Current |
| `D11` | `0x0228` | `0x0229` | 2 | 4 | `A02` Positive DC Bus Voltage, `A01` Negative DC Bus Voltage |
| `D12` | `0xF03E` | `0xF03F` | 2 | 4 | `S32` Inverter Operating Time Today, `S33` Bypass Operating Time Today |

### Tier B1 — Static Device Identification (`3600s` Poll Interval: 6 Groups, 8 Entities, 46 Words)

| Group | Start | Inclusive End | Words | Data Bytes | Entities Included (CSV IDs) |
|---|---|---|---:|---:|---|
| `S01` | `0x000B` | `0x000B` | 1 | 2 | `S01` Product Type |
| `S02` | `0x0014` | `0x0014` | 1 | 2 | `S02` Software Version (APP) |
| `S03` | `0x0016` | `0x0016` | 1 | 2 | `A07` Hardware Version (Control Board) |
| `S04` | `0x001A` | `0x001C` | 3 | 6 | `S05` Device RS485 Address, `S06` Model Code, `S07` RS485 Protocol Version |
| `S05` | `0x0021` | `0x0034` | 20 | 40 | `S08` Software Build Time (lower 8 bits/word) |
| `S06` | `0x0035` | `0x0048` | 20 | 40 | `A15` Product Serial Number (lower 8 bits/word) |

### Tier B2 — Slow Ratings, Config Readbacks & Cumulative Runtime (`300s–3600s`: 6 Groups, 7 Entities, 7 Words)

| Group | Start | Inclusive End | Words | Data Bytes | Cadence | Entities Included (CSV IDs) |
|---|---|---|---|---:|---|---|
| `S07` | `0xE003` | `0xE003` | 1 | 2 | `3600s` | `S37` Battery Rated Voltage (FC03 read-only; A03 prohibits writes) |
| `S08` | `0xE037` | `0xE037` | 1 | 2 | `300s–3600s` | `S39` Configured Operating Mode (FC03 read-only) |
| `S09` | `0xE201` | `0xE201` | 1 | 2 | `3600s` | `S41` Parallel Operation Mode (FC03 read-only) |
| `S10` | `0xE215` | `0xE215` | 1 | 2 | `3600s` | `S45` BMS Communication Mode (FC03 read-only) |
| `S11` | `0xF031` | `0xF031` | 1 | 2 | `3600s` | `S31` Total Operating Days |
| `S12` | `0xF04A` | `0xF04B` | 2 | 4 | `3600s` | `S34` Cumulative Inverter Operating Time, `S35` Cumulative Bypass Operating Time |

### Critical ESPHome 2026.11.1 & Architecture Constraints for Future Phase 2 Design
1. **Strict Range Isolation (`reuse_previous_range: false`)**: Every Phase 2 reader MUST set `reuse_previous_range: false`. In particular, `S05` (`0x0021–0x0034`, 20 words) and `S06` (`0x0035–0x0048`, 20 words) are directly adjacent; allowing ESPHome to merge them would create a **40-word** FC03 request, violating P p3's 32-word limit and triggering Exception `0AH`.
2. **Decouple from Phase 1's All-or-Nothing Sweep Gate**: Phase 1 (`srne_phase1_mask`) invalidates all 36 entities if any single group fails. Phase 2 includes optional/BMS-dependent registers (`D01`, `D04`, `D05`) and newly tested metadata blocks (`P00`, `P05`, `P07`) that may return Exception `02H` or sentinel values when BMS is absent. Phase 2 MUST NOT share `srne_phase1_mask` or poison Phase 1 health/sensors.
3. **Read-Only Access to `RW` Registers (`S07`–`S10`)**: `0xE003`, `0xE037`, `0xE201`, and `0xE215` carry `RW` permission in V2.04. Phase 2 must poll them strictly via read-only FC03 `sensor` / `text_sensor` readers—never `number`, `select`, or `switch` controls.
4. **Zero-Wire-Cost Future Promotion**: `S22` (`0x0204–0x0207` Active Fault Codes) is already read on the wire by Phase 1 `R04`. If **A25** is resolved on physical hardware, exposing active fault-code text adds **0** additional Modbus requests or words.

---

## 4. Held Candidates & Physical Validation Requirements

The **21 held (`AMBIGUOUS`) candidates** cluster into five unresolved areas from [SRNE-01B-Ambiguities.md](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Ambiguities.md):
- **Reserved / Unpopulated Words**: `0x000A` (`S04`), `0x0015` (`S03`), `0x0017` (`A08`) — probe via read-only bench tests to see if SPI-16K-UP populates them.
- **Undocumented Bitmaps & Fault Radix (A21 / A25)**: `0x0118–0x011B` (`S19`–`S20`), `0x0200–0x0203` (`S21`), `0x0204–0x0207` (`S22`), `0x020B` (`S24`), `0xF800–0xF9FF` (`S23`) — require manufacturer bit maps and radix confirmation (`14` decimal vs `0x14` hex).
- **Unsigned BMS Current (A04)**: `0x0113` (`S14`) — observe raw values during natural charging and discharging.
- **Unverified Packed / Unit Conflicts (A02)**: `0x020C–0x020E` (`S25` RTC binary vs BCD and century base), `0x024D` (`S36` erroneous `W` unit).
- **Config Enum & Limit Conflicts (A07, A09, A10, A13, A16, M05, M06)**: `0xE004` (`S38`), `0xE039` (`S40`), `0xE204` (`S42`), `0xE20A` (`S43`), `0xE20F` (`S44`), `0xE218` (`S46`), `0xE21B` (`S47`), `0xE21E` (`S48`), `0xE403` (`S49`) — compare raw FC03 readbacks against the inverter LCD settings menu.

### Prioritized Physical Validation Sequence (Once RS485 Is Connected)
1. **Verify Phase 1 baseline first** (`R01`–`R16`, 32 words, `srne_modbus_communication_health`).
2. **Verify Static Identification (`S01`–`S06`)**: record `0x000B`, `0x0014`, `0x0016`, `0x001A–0x001C`, `0x0021–0x0034`, `0x0035–0x0048`; check lower-8-bit ASCII decoding and upper-byte masking against nameplate SN and LCD pages 5–6.
3. **Verify Dynamic Diagnostics (`D01`–`D12`)**: compare `0x0220` / `0x0221` / `0x0222` / `0x0223` against LCD pages 5 & 7 (**M09**), `0x0212` vs `0x0228 + 0x0229`, `0x010B` across charging phases, and BMS registers (`D01`/`D04`/`D05`) with actual BMS state.
4. **Verify Runtime Counter Boundaries (`D12`, `S11`–`S12`)**: confirm midnight reset on `0xF03E` / `0xF03F` and persistence on `0xF031` / `0xF04A` / `0xF04B` before enabling `total_increasing`.

---

## 5. Verification & Stop

- Verified all 67 rows in [SRNE-04F-Extended-Diagnostic-Mapping.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04F-Extended-Diagnostic-Mapping.csv) against [SRNE-01B-Register-Inventory.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-01B-Register-Inventory.csv), [SRNE-04A-Phase1-Entity-Mapping.csv](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/audits/SRNE-04A-Phase1-Entity-Mapping.csv), and [srne-phase1-monitoring.yaml](file:///f:/temp/SRNE-16KW-48V-Hybrid-Split-Phase/esphome/packages/srne-phase1-monitoring.yaml).
- Confirmed zero gray-invalid rows in recommended entities, zero address overlap with Phase 1's 32 words, zero ESPHome ID collisions, contiguous FC03 groups `<= 32` words, and byte-identical preservation of all existing files.
- **Stop after SRNE-04F for owner review.** No YAML, C++, firmware, HA, Anenji, or Git changes were performed.
