# SRNE-04C - Phase 1 Read-Only Implementation

Completed 2026-11-25 for owner review. Implemented the 36 approved SRNE-04A candidates. Configuration validation passed with installed ESPHome 2026.7.0. No compilation, deployment, hardware communication or simulator validation was performed. Physical RS485 testing remains pending arrival of the USB-to-RS485 adapter.

## Changed files

- `esphome/packages/srne-phase1-monitoring.yaml`: new modular monitoring package; controller, internal FC03 readers, validated-sweep staging, approved entity reporting and failure/freshness handling.
- `esphome/srne-bench-test.yaml`: one package include and `id: srne_uptime` added to the SAME existing uptime sensor. Its name Uptime and existing 10-second update interval are retained. No duplicate uptime sensor.
- `audits/SRNE-04C-Implementation-Summary.md`: this report.

The existing top-level UART and Modbus sections were preserved byte-for-byte, along with the rest of bench content except the two intended insertions. Board/framework, logging, WiFi, encrypted API and OTA configuration were not changed. Existing credential references remain unchanged; resolved credentials and expanded configuration were not displayed. No Home Assistant, Samba, Anenji or Git changes were made.

## Entity counts and identities

| Mapping class | Implemented public candidates |
|---|---:|
| DIRECT | 28 |
| CALCULATED | 5 |
| DIAGNOSTIC | 3, including existing uptime |
| **Total** | **36** |
| AMBIGUOUS / UNSUPPORTED | **0 / 0 implemented**; all nine excluded |

By approved area: Solar 7, Battery 7, Grid 5, Load 8, Energy 4, Diagnostics 5. The merged configuration contains 33 public numeric sensors (including existing uptime), two binary diagnostics and one public operating-state text sensor. The package therefore adds 35 public candidates while reusing the 36th, uptime. All stable IDs match the approved allowlist.

Sixteen internal Modbus text readers are transport/decoding plumbing, marked internal and not exposed as additional HA entities. Their purpose is to validate complete response lengths BEFORE indexing and stage each generation for coherent calculated values. Direct numeric readings are published through event-driven template sensors after that check. This is a backend refinement from 04A's proposed individual numeric Modbus sensors: the direct source addresses, signedness, multipliers and meaning remain unchanged. A template-backed publication does not make a directly measured register a calculated entity.

Temperature unit normalization: two 04A `engineering_unit` cells contain ASCII `C`, while their `source_unit_verbatim`, the 01B inventory and official P pp9-10 state degrees Celsius. The package uses the correct HA unit `°C` for battery temperature and heatsink B. The prior mapping/audit files were not edited.

## Communication and register grouping

Controller: `srne_phase1_controller`, slave `0x01`, existing `modbus1` hub. All readers use holding registers, which selects FC03 in ESPHome 2026.7.0. No raw/custom PDU, write action, output, switch, number, button or selector is added. Initial polling is configurable via `srne_phase1_poll_interval`, default **10s**. This is an owner-approved initial policy, not a manufacturer-guaranteed cadence.

Existing baseline retained: UART `uart_rs485`, TX GPIO17, RX GPIO18, 9600 baud, no parity, one stop bit, rx_buffer_size512; Modbus flow control GPIO21 and send_wait_time300ms. No UART/Modbus timing or pin settings were changed. Controller retry/throttle options remain at installed defaults; no claim is made that a sweep will complete in exactly 10 seconds under retries.

Every reader explicitly sets register_count, response_size and force_new_range=true. All have the same HOLDING type and forced-range flag, so the installed range-builder sorts them by address and cannot reuse/extend them across gaps. This follows static inspection of ESPHome's create_register_ranges_ and SensorItemsComparator, not observed wire traffic. Actual requests still require future bench verification.

| Reader | Start | Inclusive end | Words | Expected data bytes |
|---|---|---|---:|---:|
| srne_phase1_reader_01 | 0x0100 | 0x0103 | 4 | 8 |
| srne_phase1_reader_02 | 0x0107 | 0x0109 | 3 | 6 |
| srne_phase1_reader_03 | 0x010F | 0x0111 | 3 | 6 |
| srne_phase1_reader_04 | 0x0204 | 0x0207 | 4 | 8 |
| srne_phase1_reader_05 | 0x0210 | 0x0210 | 1 | 2 |
| srne_phase1_reader_06 | 0x0213 | 0x0216 | 4 | 8 |
| srne_phase1_reader_07 | 0x0218 | 0x0219 | 2 | 4 |
| srne_phase1_reader_08 | 0x021B | 0x021B | 1 | 2 |
| srne_phase1_reader_09 | 0x0221 | 0x0221 | 1 | 2 |
| srne_phase1_reader_10 | 0x022A | 0x022A | 1 | 2 |
| srne_phase1_reader_11 | 0x022C | 0x022C | 1 | 2 |
| srne_phase1_reader_12 | 0x0230 | 0x0230 | 1 | 2 |
| srne_phase1_reader_13 | 0x0232 | 0x0232 | 1 | 2 |
| srne_phase1_reader_14 | 0x0238 | 0x0238 | 1 | 2 |
| srne_phase1_reader_15 | 0xF02F | 0xF030 | 2 | 4 |
| srne_phase1_reader_16 | 0xF04D | 0xF04E | 2 | 4 |

**16 isolated requests, 32 unique register words in total per complete sweep; maximum FOUR words in any request**, below P p3's maximum of32 per operation. A total of32 words across a sweep must not be confused with one32-word request. No undocumented gaps are read.

Excluded wire addresses include SOH0104, grid active power023A/023B, overall load percentage024C and ambiguous daily grid-connected energyF02C. All eight ambiguous entity IDs and unsupported daily import are absent. No lifetime-export fallback F032/F033, total-PV alternative010A, inductor-current substitute0217/022E, Home Load, secondary-load, phase-C, fault bitmap or settings register is polled.

## Encoding and calculations

Primary sources: official `SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf` (P) pp3-4 communication, p8 encoding, p9 DC/fault words, p10 AC/state/temperature, p14 TODAY counters; 04A CSV/summary and 01B inventory. Register bytes are high byte first. All selected numeric values are16-bit; no scalar FP32, byte swap, uint32 word swap or normalization to12V is used.

The shared decoder implements approved U_WORD as unsigned16 and S_WORD as signed16, converting high-bit raw values by subtracting65536 before multiplying. Power/register multipliers and source pages are included beside each direct decoder. Battery0102 remains positive discharge and negative charging. Measured battery0101 is full-pack0.1V directly. Source current channels are unsigned magnitudes unless explicitly signed; no grid direction is inferred from them.

The five calculations use decoded values from the SAME complete, fresh sweep:

- Total PV W = PV1 W + PV2 W (0109 + 0111); no silent unit assignment to010A.
- Battery net DC W = scaled voltage0101 * signed scaled current0102.
- Battery charging W = max(-net,0); discharging W = max(net,0).
- Total output W = signed output L1 W + signed output L2 W (021B + 0232).

Calculation inputs/results must be finite. No old public `.state` values from a partial scan are used. Age and complete-generation checks reject stale/missing dependencies before calculating; NaN propagates on invalidation instead of substituting zero. The valid directional split can legitimately produce zero for the inactive direction, and real zero-power readings remain zero; these are not unavailable-value fallbacks. Negative output circulation is preserved.

Output current uses LOAD-side0219/0230, not inductor currents. Output power and daily load energy are inverter LOAD/UPS measurements, **not whole-home consumption**. Grid values implemented here are only phase voltages, unsigned current magnitudes and frequency; no grid active-power/import/export entity or grid daily energy is implemented.

Operating mode uses0210 as CURRENT OPERATING STATE, not a configured priority or writable mode: split-phase0 Initialization,1 Standby,2 Utility operation,3 Inverter operation. Other codes publish Unknown(raw decimal), without a generic0-10 fallback. Inverter temperature remains explicitly DC-AC heatsink B0221, not ambient, maximum or an invented sensor correspondence.

Four daily energy candidates use0.1kWh unsigned TODAY registers F02F/F030/F04D/F04E. Each explicitly has an empty state_class, so no total_increasing or total metadata is emitted for these counters. Device class energy and unit kWh are retained. They are not lifetime/Ah counters, and reset behavior is not claimed validated. Existing local uptime retains its own normal total_increasing default; the daily-energy restriction does not change uptime.

## Validity, freshness and fault semantics

The Modbus hub checks CRC and expected slave/function. A normal-response handler must additionally match the tracked request start address and exact byte length before staging any word. Each of16 groups sets one bit; a sweep can publish only with all16 bits present and within the freshness window. A new first-address0100 transmission starts a generation. Any failed group poisons that generation; remaining groups cannot complete it. Recovery requires a subsequent complete valid sweep.

Only the validated full-sweep publication sets communication health true. It is false at startup, on detected request failures, malformed data, controller offline or stale generations. Neither API/WiFi connectivity, a controller online callback, nor elapsed uptime can set it true. SOC outside0-100 rejects the entire sweep rather than being clamped to a plausible percentage; undocumented general sensor sentinel values are not invented.

There is no per-request exception YAML hook in installed2026.7.0. The package instead leaves a request pending until its correctly sized normal response is accepted. A still-pending request at the next command transmission/retry invalidates the sweep. An application watchdog also checks every100ms and invalidates an uncompleted request after configurable `srne_phase1_response_deadline_ms` (initial1000ms). Thus a last-group exception that does not produce another immediate command is still detected. This is a conservative data-validity guard, not a modification to Modbus send_wait_time300ms. Detection is bounded by that policy and loop scheduling, not instantaneous exception/CRC instrumentation. It does not expose error counters or extra features.

Freshness is three configured polling periods: initially30seconds. Scan assembly and published-value expiry are measured from the OLDEST request of the generation, not its final response; changing the polling substitution changes this bound automatically. The100ms watchdog invalidates an expired published generation even if polling stops. Uptime is intentionally independent and continues to reflect the ESP32, not the inverter.

On invalidation: all32 public numeric monitoring sensors publish NaN; communication health publishes false; fault status calls invalidate_state(), sending a missing/unknown binary state through the installed API, never false/fault-free. Operating-state text publishes the explicit marker Unavailable. The installed text-sensor class has no invalidate_state API; this marker is an explicit limitation rather than a claim of per-text HA availability. A node/API disconnection uses normal HA integration availability.

Fault presence is any nonzero unsigned code in0204-0207; OFF requires all four zero within a complete valid sweep. No fault-name/radix, severity, undocumented bitmap or fault-clear behavior is inferred. Failure cannot make an inverter appear fault-free. Frontend entity messages remain separate API messages; generation-coherent inputs do not promise an atomic multi-entity HA transaction.

## Validation performed

Command: `esphome config esphome/srne-bench-test.yaml`

Result: **exit0**, `INFO ESPHome 2026.7.0`, `INFO Configuration is valid!` on the final package. Expanded configuration and resolved credentials were suppressed. The merged configuration was inspected without displaying secret fields: exact36 public IDs, one existing uptime, polling10s, slave1 and four daily energy state classes all empty.

Additional STATIC inspection (not simulation): exact public-ID allowlist and excluded IDs; every read word compared with inventory permissionR and approved dependencies; cache offsets and signed decoders/multipliers;16 forced FC03 ranges/max4 words/no overlaps or gaps; correct temperature units; no write/control/custom-PDU configuration; and byte-preservation of UART/Modbus and untouched bench sections. Installed component sources were read to verify script parameters, range construction, request callbacks, binary invalidation and get_update_interval APIs.

No ESPHome compile/run/upload command, generated firmware, C++ compiler, simulator, serial access or hardware test was run. Passing configuration validation checks schemas, IDs and YAML/lambda structure; it does not compile or execute inline C++ lambdas or prove runtime compatibility/behavior. Firmware build validation is intentionally outstanding, not reported as passed.

## Outstanding limitations for owner review

1. All SPI firmware register support, physical values, CT/leg accounting, actual frame grouping and response timing remain unverified on hardware.
2. The conservative complete-sweep gate means ONE unsupported/unresponsive approved register or out-of-range SOC suppresses the whole monitoring generation. This favors integrity over partial availability; per-group degraded operation is not added in this scope.
3. The1000ms completion guard and30s freshness bound are initial policies. Slow responses, a busy queue or retries can invalidate a sweep; tune only after measured bench behavior. Transport retry/queue behavior may extend the nominal polling period.
4. No Modbus RTU transaction ID exists. Ordinary serialization and response-size checks cannot absolutely distinguish every extremely late response from a subsequent same-size request. No simulator or physical delayed-frame testing was performed.
5. Battery/temperature sources and undocumented sentinel values, output-versus-Home Load boundaries, split-phase enum support and daily energy midnight/reset/persistence behavior remain as04A physical validation requirements. No semantic-HOLD item was silently promoted.
6. Fault/health missing-state and NaN reporting are based on installed API source inspection; actual end-to-end HA recovery behavior has not been exercised. Operating-state text has the explicit Unavailable marker limitation described above.
7. C++ compilation and deployment are not performed under this task. No claim of electrical communication or simulator validation is made.

Stop after SRNE-04C for owner review. No moon landing, just a reliable inverter integration!

### Implemented stable IDs

- DIRECT: `srne_pv1_voltage`, `srne_pv1_current`, `srne_pv1_power`, `srne_pv2_voltage`, `srne_pv2_current`, `srne_pv2_power`, `srne_battery_voltage`, `srne_battery_current`, `srne_battery_soc`, `srne_battery_temperature`, `srne_grid_l1_voltage`, `srne_grid_l1_current`, `srne_grid_l2_voltage`, `srne_grid_l2_current`, `srne_grid_frequency`, `srne_output_l1_voltage`, `srne_output_l1_current`, `srne_output_l1_power`, `srne_output_l2_voltage`, `srne_output_l2_current`, `srne_output_l2_power`, `srne_output_frequency`, `srne_solar_energy_daily`, `srne_load_energy_daily`, `srne_battery_charge_energy_daily`, `srne_battery_discharge_energy_daily`, `srne_inverter_temperature`, `srne_operating_mode`.
- CALCULATED: `srne_pv_total_power`, `srne_battery_net_power`, `srne_battery_charging_power`, `srne_battery_discharging_power`, `srne_output_total_power`.
- DIAGNOSTIC: `srne_fault_status`, `srne_modbus_communication_health`, `srne_uptime`.

### Required-source fingerprints

- `audits/SRNE-04A-Phase1-Entity-Mapping.csv`: `5d2199245e5286ca19d16512a1838b316dfb767a8cd8fc604c4c5ec23fee002e`
- `audits/SRNE-04A-Phase1-Mapping-Summary.md`: `34a009c17b44d775165ca244f6e9e0c9a5c7ede3de2ed5bf08763016e8f36d36`
- `audits/SRNE-01B-Register-Inventory.csv`: `71ed75bdd2d1dd62c3487a57b685586705b1977967aed3b82e1a5d7d11f931aa`
- `documentation/official/SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf`: `0c49c599a1a45c29bca0362241a8b460b308b07ad586561f943b3b25073e2f50`
