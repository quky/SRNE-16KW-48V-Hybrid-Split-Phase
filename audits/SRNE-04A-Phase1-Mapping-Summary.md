# SRNE-04A - Phase 1 Essential Monitoring Mapping

Prepared 2026-11-25 for owner review. Exactly 45 approved slots: Solar 7, Battery 8, Grid 10, Load 9, Energy 6, Diagnostics 5. This is documentation only. Physical RS485 validation awaits the USB-to-RS485 adapter. Every proposed inverter read is function 03; no writes or controls are included.

## Exact counts

These are mutually exclusive **primary classifications**. The CSV's separate `value_origin` field preserves whether an ambiguous slot would be direct or calculated. DIRECT means a documented candidate, not hardware-proven support.

| Classification | Count | Selected mapping |
|---|---:|---|
| DIRECT | 28 | Source-register candidates with usable proposed meanings, pending physical validation |
| CALCULATED | 5 | Total PV power; battery net, charge and discharge power; total output power |
| DIAGNOSTIC | 3 | Fault presence, Modbus communication health, existing ESP32 uptime |
| AMBIGUOUS | 8 | Battery SOH; two phase grid powers; grid total/import/export power; overall load percentage; daily grid export |
| UNSUPPORTED | 1 | No unambiguous direct daily whole-grid import counter; conditional HA alternative documented |
| **Total** | **45** | No additional public entities |

Five ambiguous slots have direct-register origins (SOH, two phase grid powers, load percentage, daily export); three have calculated origins (grid total/import/export). Fault presence is classified DIAGNOSTIC although it reduces four raw words. Daily import remains UNSUPPORTED directly; its HA alternative is not counted as an implemented calculation. A second grouping by origin is therefore 33 direct-register slots, 8 calculated slots, 3 diagnostics and 1 unsupported slot, covering the same 45.

DOCUMENTED = printed source fields. INFERRED = arithmetic, IDs, accounting choices, software metadata or diagnostic policy. UNVERIFIED = firmware applicability, physical sensor behavior, resets or unresolved meanings. Semantic HOLD rows must not publish final HA values until resolved. All daily-energy statistics are withheld until reset/monotonicity validation, including counters with unambiguous names.

## Sources and conventions

Required sources read: `audits/SRNE-01B-Register-Inventory.csv`, `audits/SRNE-01B-Monitoring-Coverage.md`, `audits/SRNE-01B-Communication-Specification.md`, `audits/SRNE-01B-Ambiguities.md`, and `documentation/official/SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf` (P). P is primary: communication pp3-4, numeric encoding p8, DC/fault words p9, AC/state/temperature p10, overall load p11, energy counters p14. References are **1-based PDF pages**, original named areas and source row addresses. Source fields were checked against the current PDF, not only copied from prior conclusions. Earlier audits' comments about absent desired lists/projects are historical; the current owner's approved list governs this task. No Anenji compatibility assumption was used.

IDs and HA metadata are proposed software choices, not attributes defined by SRNE. [Official ESPHome Modbus sensor documentation](https://esphome.io/components/sensor/modbus_controller/) defines holding as FC03, U_WORD/S_WORD as unsigned/signed 16-bit and U_DWORD_R as unsigned 32-bit low-word-first. A register's read-only permission does not imply input/FC04. Numeric scaling is separate from value_type. The installed CLI was confirmed as ESPHome 2026.7.0; no compilation occurred.

[HA sensor metadata documentation](https://contributors.home-assistant.io/core/entities/sensor/) supports measurement for instantaneous numeric readings and energy totals with appropriate total classes. Here voltage/current/power/frequency/temperature use their matching device classes; SOC uses battery. SOH has no battery device class because that class describes charge left, not health. Load percentage has no device class. Text states and binary diagnostics have no state class. These are design choices; no HA entity was edited.

Every slot reserves a stable `srne_...` explicit ESPHome ID. These are not guaranteed HA entity IDs and do not claim existing configuration. The existing `sensor.uptime` at `esphome/srne-bench-test.yaml:16` is named Uptime, updates every 10 seconds and has **no explicit ID**. `srne_uptime` is reserved for that SAME sensor in future authorized work, preserving its HA identity; do not duplicate it. Its defaults were checked in installed 2026.7.0 `components/uptime/sensor/__init__.py`: seconds, duration, total_increasing, diagnostic. If daily import is implemented entirely by HA helpers, its logical reserved ID does not imply an ESPHome entity exists.

All selected source words have permission R. Normal numeric reads are one word with high byte first and no word swap; signed decode precedes scaling. No FP32 or swapped-byte decoder is proposed. A calculated value has no register of its own (`NONE`, length 0); exact dependency addresses and their individual encodings/scales appear in separate columns. Fault block 0204-0207 is four independent uint16 codes, not uint64. An optional lifetime-export source F032/F033 instead uses uint32, low register word first, high byte first within each word.

## Key decisions and semantic holds

1. **Total solar:** select 0109 + 0111, both explicitly W, as the existing total-solar slot. Do not silently assign W to 010A, whose source unit is `-`. 010A is an optional alternative only and is excluded from planned reads. Summation uses already-scaled values and coherent fresh samples.
2. **Battery:** 0101 is full-pack measured voltage at 0.1 V, with no 12 V normalization for settings. Signed 0102 is positive discharge / negative charging. Net DC power = V*I; charging=max(-P,0), discharging=max(P,0). Neither unsigned BMS current 0113 nor 010E total charging power is a substitute. SOH 0104 is ambiguous because its remark repeats remaining-capacity/SOC wording and unit is blank. Confirm SOH/percent before exposure; do not clamp implausible data into a believable percentage. Temperature 0103 is a direct candidate but source/sensor presence and missing-data representation require validation.
3. **Grid active power (A01):** 023A/023B are signed multiplier1 with documented positive export/negative import; unit A conflicts with active-power names and W displays. Hold both and the three dependent entities. Once resolved, Pnet=P_L1+P_L2, import=max(-Pnet,0), export=max(Pnet,0). Cross-leg netting is intentional: +500 W and -500 W produces zero net import/export. Summing per-leg imports would produce a different result.
4. **Grid accounting:** decoded AC input-port power is not automatically service-point/whole-home grid exchange. Validate CT placement/ratio/orientation, phase correspondence and route accounting against a reference meter. The same caveat gates daily grid energy. Do not substitute parallel total 0252.
5. **Output load:** select voltages 0216/022C, LOAD-side currents 0219/0230 and signed active powers 021B/0232. Exclude inductor currents 0217/022E. Total output is the signed per-leg real-power sum, not V*I and not whole-home consumption. External Home Load/secondary circuits may be outside this boundary. Negative circulation is possible in parallel operation. Verify LOAD/UPS and bypass terminal correspondence. No Home Load or secondary-load entities were added.
6. **Load percentage (A02):** 024C is named overall percentage but unit W. Hold pending percent unit, denominator/rating and SPI firmware support. Do not silently average phase percentages, use their maximum or divide watts by 16000 as an equivalent measurement.
7. **Operating mode:** deliberately define the slot as CURRENT OPERATING STATE 0210, not configured UTI/SUB/SBU/SOL priority. Split-phase map: 0 Initialization, 1 Standby, 2 Utility operation, 3 Inverter operation. Other values remain Unknown(raw decimal); do not fall back automatically to the incompatible generic 0-10 map. Compare naturally observed states; no mode changes or writable selectors.
8. **Inverter temperature:** use 0221, explicitly DC-AC heatsink B. Keep that qualifier; it is not ambient or the maximum of multiple sensors. Audit M09 requires LCD/sensor correspondence validation.
9. **Fault status:** one binary problem diagnostic = any nonzero word in a valid fresh 0204-0207 block. All four zero means no current fault code. This avoids undocumented 0200 fault bit assignments and A25 label/radix assumptions; it does not claim all faults stop output or decode severity. Do not provoke/clear faults. Communication failure must never publish fault-free.
10. **Communication health:** one local connectivity diagnostic based on validated measurements, not WiFi/API connection or uptime. False at startup/failure/exception/staleness; true after a valid complete pass of all enabled Phase1 groups and while they remain fresh. Exclude held/unsupported groups from normal active polling. Proposed freshness expiry is three configured poll periods per group (INFERRED; finalize after adapter tests). Node/API offline means HA unavailable. An ESPHome online callback alone is insufficient proof that all requested measurements succeeded; version-specific behavior requires validation.

## Daily energy and alternatives

Daily solar F02F, daily load F030, daily battery charge F04D and discharge F04E are unsigned one-word TODAY counters at 0.1 kWh (P p14). They are not lifetime F038/F03A/F050/F052 counters and not Ah capacity counters. Daily load retains the inverter's load-accounting boundary, not certified whole-home consumption.

For all six daily energy slots, proposed device class is energy and unit kWh. **Current state class is NONE (withheld); target total_increasing only after validation.** Verify nonnegative within-day accumulation, actual midnight reset, missing/stale samples, normal reboot behavior when observed, persistence and rollover. P does not specify inverter timezone, DST or reset/wrap policy. The numeric range of a 0.1 kWh uint16 is 6553.5 kWh; this does not establish actual firmware rollover behavior.

**Daily grid import is unsupported directly.** F03D describes utility-to-load, F04C utility charging with disputed scale and F048 a disputed cumulative utility/battery contribution; none establishes whole-site import, nor is their sum documented to do so. Conditional alternative: [HA Integral](https://www.home-assistant.io/integrations/integration/) of validated nonnegative Grid Import Power -> persistent accumulated kWh -> daily [Utility Meter](https://www.home-assistant.io/integrations/utility_meter/). For seconds, kWh=integral(W dt)/3,600,000. This depends on A01 and physical accounting resolution. No helper was created.

**Daily grid export is ambiguous.** F02C names Today's Grid-Connected Energy, not explicitly exported energy. Confirm its direction and counter boundary before release. An alternative is a daily Utility Meter from explicitly cumulative exported F032-F033: FC03 holding, length2, uint32, low word F032/high F033, U_DWORD_R, multiplier0.1 kWh, P pp8/14. That source is lifetime energy; it cannot be renamed Daily Export without daily conversion. Another conditional alternative integrates validated Grid Export Power, then uses a daily meter.

Alternatives are plumbing for the same approved daily slots, not additional public Phase1 entities. Optional lifetime source polling is excluded from current read-group counts. If an alternative is selected later, update the slot's classification in a reviewed mapping; current counts do not assume it implemented. Compare the inverter day boundary with the owner's HA time zone (client context America/Chicago); do not assume they match. Do not put a second daily meter on a daily-reset register without a deliberate reset-aware design.

Any future integration must choose and validate a numerical method for sampled power, persistent accumulation, constant-power updates, restart behavior and explicit outage handling. Do not extrapolate stale power across outages or backfill invented history. Missing samples make derived daily totals incomplete. Daily helpers start accumulating when created and cannot recover earlier unmeasured consumption. Persistence does not recover missing power history. All such work remains proposed, not configured.

## Hardware baseline and read plan

Retained owner baseline: Waveshare ESP32-S3-RS485-CAN-U Rev2.2; TX GPIO17, RX GPIO18, direction GPIO21; 9600 baud 8N1; slave1; send_wait_time300ms; CLI2026.7.0; HA Device Builder2026.11.1. Encrypted API, OTA and HA reporting are owner-verified, not proof of RS485. Installed 2026.7.0 Modbus code uses send_wait_time in response-start waiting behavior; it is not the scan cadence or a guaranteed 300ms inter-request delay. No new timing setting was made.

P p3 allows at most 32 words per operation. Use normal slave1 unicast FC03, high-byte-first register bytes and low-byte-first CRC (P pp3-4); validate actual address, function, byte count and CRC. Preserve vendor exceptions, including 02 illegal address, 06 frame/CRC, 09 password lock and 0A length. A lock/error does not authorize writing or unlocking. No FC04/06/10, broadcast or universal addressing is proposed. Serial parameters come from P p3; the 300ms value is the owner baseline, not an official SRNE polling requirement.

Below is a **candidate narrow-group plan**, including semantic-HOLD words for future raw validation, not a deployed schedule. Each group is contiguous, contains selected dependencies only and is at most5 words. In a future implementation, inspect generated request ranges and prevent automatic merging across gaps or beyond32 words. Templates reuse existing reads; no duplicates required. Keep one master and serialize requests. Select polling cadence from measured response times and bus duty after the adapter arrives; the official protocol specifies no rate/timeout guarantee. Coherent dependency samples and same completed scan generation are required; stale or partial dependencies invalidate a computed value rather than being replaced with zero.

| Group | Start | Words | Inclusive end | Release status |
|---|---|---:|---|---|
| G01 | 0x0100 | 5 | 0x0104 | Contains semantic HOLD; raw validation only |
| G02 | 0x0107 | 3 | 0x0109 | Physical validation pending |
| G03 | 0x010F | 3 | 0x0111 | Physical validation pending |
| G04 | 0x0204 | 4 | 0x0207 | Physical validation pending |
| G05 | 0x0210 | 1 | 0x0210 | Physical validation pending |
| G06 | 0x0213 | 4 | 0x0216 | Physical validation pending |
| G07 | 0x0218 | 2 | 0x0219 | Physical validation pending |
| G08 | 0x021B | 1 | 0x021B | Physical validation pending |
| G09 | 0x0221 | 1 | 0x0221 | Physical validation pending |
| G10 | 0x022A | 1 | 0x022A | Physical validation pending |
| G11 | 0x022C | 1 | 0x022C | Physical validation pending |
| G12 | 0x0230 | 1 | 0x0230 | Physical validation pending |
| G13 | 0x0232 | 1 | 0x0232 | Physical validation pending |
| G14 | 0x0238 | 1 | 0x0238 | Physical validation pending |
| G15 | 0x023A | 2 | 0x023B | Contains semantic HOLD; raw validation only |
| G16 | 0x024C | 1 | 0x024C | Contains semantic HOLD; raw validation only |
| G17 | 0xF02C | 1 | 0xF02C | Contains semantic HOLD; raw validation only |
| G18 | 0xF02F | 2 | 0xF030 | Physical validation pending |
| G19 | 0xF04D | 2 | 0xF04E | Physical validation pending |

The 19 groups cover 37 unique words, including held candidates; none is a hole or control register. Split held words from otherwise validated neighbors as needed. Optional F032-F033 fallback is a separate two-word read only if selected and is excluded from these counts. No request was issued.

## Complete owner review index

The CSV contains every slot's exact encoding, length, order, scale, units, software types/classes, sources, ambiguities, physical validation, equations/signs and alternatives. Zero register length means a local calculated/unsupported slot has no own wire register, not a zero-length Modbus request.

| # | Category | Entity | Stable proposed ID | Primary class | Register / dependencies |
|---|---|---|---|---|---|
| 1 | Solar | PV1 Voltage | `srne_pv1_voltage` | DIRECT | 0x0107 |
| 2 | Solar | PV1 Current | `srne_pv1_current` | DIRECT | 0x0108 |
| 3 | Solar | PV1 Power | `srne_pv1_power` | DIRECT | 0x0109 |
| 4 | Solar | PV2 Voltage | `srne_pv2_voltage` | DIRECT | 0x010F |
| 5 | Solar | PV2 Current | `srne_pv2_current` | DIRECT | 0x0110 |
| 6 | Solar | PV2 Power | `srne_pv2_power` | DIRECT | 0x0111 |
| 7 | Solar | Total PV Power | `srne_pv_total_power` | CALCULATED | 0x0109;0x0111 |
| 8 | Battery | Battery Voltage | `srne_battery_voltage` | DIRECT | 0x0101 |
| 9 | Battery | Battery Current | `srne_battery_current` | DIRECT | 0x0102 |
| 10 | Battery | Battery SOC | `srne_battery_soc` | DIRECT | 0x0100 |
| 11 | Battery | Battery SOH | `srne_battery_soh` | AMBIGUOUS | 0x0104 |
| 12 | Battery | Battery Temperature | `srne_battery_temperature` | DIRECT | 0x0103 |
| 13 | Battery | Battery Net Power | `srne_battery_net_power` | CALCULATED | 0x0101;0x0102 |
| 14 | Battery | Battery Charging Power | `srne_battery_charging_power` | CALCULATED | 0x0101;0x0102 |
| 15 | Battery | Battery Discharging Power | `srne_battery_discharging_power` | CALCULATED | 0x0101;0x0102 |
| 16 | Grid | Grid L1 Voltage | `srne_grid_l1_voltage` | DIRECT | 0x0213 |
| 17 | Grid | Grid L1 Current | `srne_grid_l1_current` | DIRECT | 0x0214 |
| 18 | Grid | Grid L1 Active Power | `srne_grid_l1_power` | AMBIGUOUS | 0x023A |
| 19 | Grid | Grid L2 Voltage | `srne_grid_l2_voltage` | DIRECT | 0x022A |
| 20 | Grid | Grid L2 Current | `srne_grid_l2_current` | DIRECT | 0x0238 |
| 21 | Grid | Grid L2 Active Power | `srne_grid_l2_power` | AMBIGUOUS | 0x023B |
| 22 | Grid | Grid Frequency | `srne_grid_frequency` | DIRECT | 0x0215 |
| 23 | Grid | Total Grid Power | `srne_grid_total_power` | AMBIGUOUS | 0x023A;0x023B |
| 24 | Grid | Grid Import Power | `srne_grid_import_power` | AMBIGUOUS | 0x023A;0x023B |
| 25 | Grid | Grid Export Power | `srne_grid_export_power` | AMBIGUOUS | 0x023A;0x023B |
| 26 | Load | Output L1 Voltage | `srne_output_l1_voltage` | DIRECT | 0x0216 |
| 27 | Load | Output L1 Current | `srne_output_l1_current` | DIRECT | 0x0219 |
| 28 | Load | Output L1 Power | `srne_output_l1_power` | DIRECT | 0x021B |
| 29 | Load | Output L2 Voltage | `srne_output_l2_voltage` | DIRECT | 0x022C |
| 30 | Load | Output L2 Current | `srne_output_l2_current` | DIRECT | 0x0230 |
| 31 | Load | Output L2 Power | `srne_output_l2_power` | DIRECT | 0x0232 |
| 32 | Load | Total Output Power | `srne_output_total_power` | CALCULATED | 0x021B;0x0232 |
| 33 | Load | Load Percentage | `srne_load_percentage` | AMBIGUOUS | 0x024C |
| 34 | Load | Output Frequency | `srne_output_frequency` | DIRECT | 0x0218 |
| 35 | Energy | Daily Solar Production | `srne_solar_energy_daily` | DIRECT | 0xF02F |
| 36 | Energy | Daily Load Consumption | `srne_load_energy_daily` | DIRECT | 0xF030 |
| 37 | Energy | Daily Grid Import | `srne_grid_import_energy_daily` | UNSUPPORTED | NONE |
| 38 | Energy | Daily Grid Export | `srne_grid_export_energy_daily` | AMBIGUOUS | 0xF02C |
| 39 | Energy | Daily Battery Charge Energy | `srne_battery_charge_energy_daily` | DIRECT | 0xF04D |
| 40 | Energy | Daily Battery Discharge Energy | `srne_battery_discharge_energy_daily` | DIRECT | 0xF04E |
| 41 | Diagnostics | Inverter Temperature (Heatsink B) | `srne_inverter_temperature` | DIRECT | 0x0221 |
| 42 | Diagnostics | Operating Mode (Current Operating State) | `srne_operating_mode` | DIRECT | 0x0210 |
| 43 | Diagnostics | Fault Status | `srne_fault_status` | DIAGNOSTIC | 0x0204 |
| 44 | Diagnostics | Modbus Communication Health | `srne_modbus_communication_health` | DIAGNOSTIC | NONE |
| 45 | Diagnostics | Existing Uptime | `srne_uptime` | DIAGNOSTIC | NONE |

## Verification and stop

Verified45 rows/unique IDs and category totals; each planned dependency exists in the inventory with R permission, correct signedness/scaling and original PDF locator. All candidate requests use03 and meet the32-word limit. Source engineering conflicts remain visible. Primary classifications reconcile to45. Physical validation and semantic holds remain pending. No supported mapping is claimed for an invented register.

Only `audits/SRNE-04A-Phase1-Entity-Mapping.csv` and `audits/SRNE-04A-Phase1-Mapping-Summary.md` were created. Existing audit sources and official PDF were retained. No YAML modification, firmware compilation/deployment, HA change, Modbus write, credential use/disclosure, Anenji modification or Git operation occurred. Stop for owner review after SRNE-04A.

No moon landing, just a reliable inverter integration!

### Required-source SHA-256 fingerprints

- `audits/SRNE-01B-Register-Inventory.csv`: `71ed75bdd2d1dd62c3487a57b685586705b1977967aed3b82e1a5d7d11f931aa`
- `audits/SRNE-01B-Monitoring-Coverage.md`: `f2f1c78ee08f1105ececfd87824b6a180daad5a8b120c70bf696ebbbb87d5be4`
- `audits/SRNE-01B-Communication-Specification.md`: `24f6ce7e14617934be77e1a7bf9befa9f179d52a45b41c2c78bdc149ae159a03`
- `audits/SRNE-01B-Ambiguities.md`: `c7010a44d706a112689b36faf63240e1666b71005129400bc84b01fbc64707b9`
- `documentation/official/SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf`: `0c49c599a1a45c29bca0362241a8b460b308b07ad586561f943b3b25073e2f50`
