# Public Entity Catalog (73 Entities)

This catalog reconciles every public ESPHome entity exposed by [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml), [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml), and [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) against [`audits/SRNE-04A-Phase1-Entity-Mapping.csv`](../audits/SRNE-04A-Phase1-Entity-Mapping.csv) and [`audits/SRNE-04F-Extended-Diagnostic-Mapping.csv`](../audits/SRNE-04F-Extended-Diagnostic-Mapping.csv).

## Definitive YAML-Derived Public Entity Matrix (`C11`)

Counts below are derived directly from [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml), [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml), and [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) (`16` `internal: true` raw Modbus readers in Phase 1 are excluded from public totals):

| Scope / YAML Source | ESPHome `sensor` (Numeric) | ESPHome `binary_sensor` | ESPHome `text_sensor` | Total Public | HA `sensor.*` | HA `binary_sensor.*` |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| **Phase 1 Package** (`srne-phase1-monitoring.yaml`) | **32** *(27 direct Modbus + 5 calculated)* | **2** *(`srne_fault_status`, `srne_modbus_communication_health`)* | **1** *(`srne_operating_mode`)* | **35** | **33** | **2** |
| **Local Uptime in Bench YAML** (`srne-bench-test.yaml`, Phase 1 group) | **1** *(`srne_uptime`, local `platform: uptime`)* | **0** | **0** | **1** | **1** | **0** |
| **Phase 1 Subtotal** | **33** *(32 Modbus + 1 local)* | **2** | **1** | **36** | **34** | **2** |
| **Phase 2 Package** (`srne-phase2-diagnostics.yaml`) | **26** *(all Modbus)* | **0** | **11** *(all Modbus)* | **37** | **37** | **0** |
| **Combined Totals** | **59** *(58 Modbus + 1 local)* | **2** | **12** | **73** | **71** | **2** |

---

## Internal ESPHome IDs vs. Home Assistant Entity Domains & IDs

The catalog tables below use an **`ESPHome Entity Type`** column (`sensor`, `binary_sensor`, or `text_sensor`) matching the YAML platform declarations:

- **`text_sensor` is an ESPHome entity type, NOT a Home Assistant entity domain.** In Home Assistant, both ESPHome `sensor` (`59`) and ESPHome `text_sensor` (`12`) entities appear under the **`sensor.*`** domain (`71` total `sensor.*` entities), while ESPHome `binary_sensor` (`2`) entities appear under **`binary_sensor.*`**.
- Home Assistant generates each live entity ID as `<ha_domain>.<slugified_friendly_name>_<slugified_name>` (plus any entity-registry overrides):
  - In [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml), `friendly_name: SRNE Bench Test` yields entity IDs such as `sensor.srne_bench_test_battery_soc`, `sensor.srne_bench_test_operating_mode`, and `binary_sensor.srne_bench_test_modbus_communication_health`.
  - In Universal Inverter Flow's standalone [`srne-esp32-esphome.yaml`](https://github.com/quky/universal-inverter-flow/blob/main/docs/examples/srne/srne-esp32-esphome.yaml) (`friendly_name: SRNE Inverter`), equivalent IDs become `sensor.srne_inverter_battery_soc`, etc.

Always verify live entity IDs under **Home Assistant → Developer Tools → States**.

---

## Freshness, Invalidation & Failure Behavior

- **Local Uptime Excluded from Modbus Invalidation (`1` entity)**: `srne_uptime` (defined locally in `esphome/srne-bench-test.yaml`, `platform: uptime`, `10s`) has no Modbus dependency, is **not** touched by `srne_phase1_invalidate`, and remains available and monotonically increasing even when RS485 communication is offline.
- **Modbus-Derived Numeric Sensors (`58` total: `32` Phase 1 + `26` Phase 2)**: Invalidated by publishing `NAN` (rendered as `unavailable` in Home Assistant). Never fabricated or defaulted to `0`.
- **`binary_sensor` (`2` total, Phase 1)**: `srne_fault_status` calls `.invalidate_state()` (rendered as `unavailable` in Home Assistant); `srne_modbus_communication_health` publishes `false` (`OFF`) on boot, sweep failure, or freshness expiry.
- **Text Sensors (`text_sensor`, `12` total: `1` Phase 1 + `11` Phase 2)**: ESPHome's `text_sensor` platform lacks `.invalidate_state()`, so firmware explicitly publishes the literal text string `"Unavailable"` (state present as HA `sensor.*` with value `"Unavailable"`) on boot or invalidation.
- **Phase 1 Complete-Sweep-Gated Publication Policy**: Phase 1 polls `16` `FC03` groups every `10s`. All **34** Modbus-derived Phase 1 entities (`32` numeric + `srne_fault_status` + `srne_operating_mode`) publish **only after all `16` required groups in the same scan pass** (`srne_phase1_mask == 0xFFFF`), setting `srne_modbus_communication_health = true`. Failure of **any** required group (`> 1000ms` completion guard, `on_offline`, bad payload length, or `> 30s` [`3 × 10s`] freshness expiry) executes `srne_phase1_invalidate`, invalidating all **34** Modbus-derived Phase 1 entities and setting `srne_modbus_communication_health = false` (**35** entities handled total; `srne_uptime` remains unaffected). Note that Home Assistant state updates across the published entities are not guaranteed to constitute one atomic database transaction.
- **Phase 2 Nominal Polling vs. Freshness Thresholds & Isolation (`37` entities across `24` groups)**:
  - **Dynamic diagnostics (`P2-D01`–`P2-D12`)**: `30s` nominal poll target / **`90s`** per-group freshness expiration threshold (`3 × 30s`).
  - **Slow configured operating mode (`P2-S08`, `0xE037`)**: `300s` nominal poll target / **`900s`** freshness expiration threshold (`3 × 300s`).
  - **Static identification, ratings & cumulative counters (`P2-S01`–`P2-S07`, `P2-S09`–`P2-S12`)**: `3600s` nominal poll target / **`10800s`** freshness expiration threshold (`3 × 3600s`).
  - **Nominal interval vs. freshness distinction**: Configured `30s` / `300s` / `3600s` values are scheduler due-time cadences, **not guaranteed polling intervals** — actual dispatch depends on bus availability (`tx_buffer_empty()`, `!tx_blocked()`), Phase 1 priority yielding, single-in-flight serialization, `2000ms` static spacing, and stepped bounded backoff (`3s/60s/120s/300s` or `5s/300s/900s/3600s` timeouts; `60s/120s/300s` or `3600s` exceptions). When a Phase 2 group fails (`on_no_response`, `on_error`, `on_custom_response`, `on_not_sent`, `> 2000ms` watchdog, or exceeds its `3×` freshness threshold), **only that group's entities** invalidate.

---

## Phase 1 Core Monitoring & Diagnostics (36 Public Entities)

| ESPHome Internal ID | Display Name | ESPHome Entity Type | Unit | Register / Source | Scaling & Signedness | Nominal Poll | Freshness & Invalidation | Limitations / Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `srne_uptime` | Uptime | `sensor` | `s` | Local ESPHome (`sensor.uptime`, bench YAML) | Runtime seconds (`u32`) | `10s` | **Excluded from Modbus invalidation**; stays available & incrementing when RS485 is offline | Runtime-dependent (no Modbus register) |
| `srne_pv1_voltage` | PV1 Voltage | `sensor` | `V` | `0x0107` (`P1-R02`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Disconnected/simulator verified only |
| `srne_pv1_current` | PV1 Current | `sensor` | `A` | `0x0108` (`P1-R02`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Disconnected/simulator verified only |
| `srne_pv1_power` | PV1 Power | `sensor` | `W` | `0x0109` (`P1-R02`) | `uint16 × 1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Disconnected/simulator verified only |
| `srne_pv2_voltage` | PV2 Voltage | `sensor` | `V` | `0x010F` (`P1-R03`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Disconnected/simulator verified only |
| `srne_pv2_current` | PV2 Current | `sensor` | `A` | `0x0110` (`P1-R03`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Disconnected/simulator verified only |
| `srne_pv2_power` | PV2 Power | `sensor` | `W` | `0x0111` (`P1-R03`) | `uint16 × 1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Disconnected/simulator verified only |
| `srne_pv_total_power` | Total PV Power | `sensor` | `W` | Calculated (`P1-R02` + `P1-R03` powers) | Sum of `0x0109` + `0x0111` | `10s` | `NAN` on any incomplete Phase 1 sweep or `> 30s` stale (complete-sweep-gated publication) | Derived sum; failure of any required Phase 1 group invalidates full Modbus set |
| `srne_battery_voltage` | Battery Voltage | `sensor` | `V` | `0x0101` (`P1-R01`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Pack terminal voltage (separate from BMS `0x0112`) |
| `srne_battery_current` | Battery Current | `sensor` | `A` | `0x0102` (`P1-R01`) | **`int16 × 0.1`** (`+` dischg / `−` chg) | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | V2.04 sign convention (`+` discharge, `−` charge) |
| `srne_battery_soc` | Battery SOC | `sensor` | `%` | `0x0100` (`P1-R01`) | `uint16 × 1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | — |
| `srne_battery_temperature` | Battery Temperature | `sensor` | `°C` | `0x0103` (`P1-R01`) | **`int16 × 0.1`** | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Ambiguity `A10`: BMS/sensor placement unit-dependent |
| `srne_battery_net_power` | Battery Net Power | `sensor` | `W` | Calculated (`0x0101`, `0x0102`) | `(V × 0.1) × (s16(I) × 0.1)` (`+` dischg) | `10s` | `NAN` on any incomplete Phase 1 sweep or `> 30s` stale (complete-sweep-gated publication) | Derived (`+` discharge / `−` charge); failure of any required Phase 1 group invalidates full Modbus set |
| `srne_battery_charging_power` | Battery Charging Power | `sensor` | `W` | Calculated (`0x0101`, `0x0102`) | `max(-net_power, 0.0)` | `10s` | `NAN` on any incomplete Phase 1 sweep or `> 30s` stale (complete-sweep-gated publication) | Non-negative charging magnitude |
| `srne_battery_discharging_power` | Battery Discharging Power | `sensor` | `W` | Calculated (`0x0101`, `0x0102`) | `max(net_power, 0.0)` | `10s` | `NAN` on any incomplete Phase 1 sweep or `> 30s` stale (complete-sweep-gated publication) | Non-negative discharging magnitude |
| `srne_grid_l1_voltage` | Grid L1 Voltage | `sensor` | `V` | `0x0213` (`P1-R06`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Ambiguity `A14`: L1-N vs L-L depends on inverter wiring |
| `srne_grid_l1_current` | Grid L1 Current | `sensor` | `A` | `0x0214` (`P1-R06`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Unsigned grid input current only (not signed power) |
| `srne_grid_l2_voltage` | Grid L2 Voltage | `sensor` | `V` | `0x022A` (`P1-R10`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Split-phase L2 leg |
| `srne_grid_l2_current` | Grid L2 Current | `sensor` | `A` | `0x0238` (`P1-R14`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Split-phase L2 leg |
| `srne_grid_frequency` | Grid Frequency | `sensor` | `Hz` | `0x0215` (`P1-R06`) | `uint16 × 0.01` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | — |
| `srne_output_l1_voltage` | Output L1 Voltage | `sensor` | `V` | `0x0216` (`P1-R06`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | — |
| `srne_output_l1_current` | Output L1 Current | `sensor` | `A` | `0x0219` (`P1-R07`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | — |
| `srne_output_l1_power` | Output L1 Power | `sensor` | `W` | `0x021B` (`P1-R08`) | **`int16 × 1`** | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Always inverter L1 LOAD/UPS output (not whole-home CT) |
| `srne_output_l2_voltage` | Output L2 Voltage | `sensor` | `V` | `0x022C` (`P1-R11`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Split-phase L2 output |
| `srne_output_l2_current` | Output L2 Current | `sensor` | `A` | `0x0230` (`P1-R12`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Split-phase L2 output |
| `srne_output_l2_power` | Output L2 Power | `sensor` | `W` | `0x0232` (`P1-R13`) | **`int16 × 1`** | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Always inverter L2 LOAD/UPS output (not whole-home CT) |
| `srne_output_total_power` | Total Output Power | `sensor` | `W` | Calculated (`0x021B`, `0x0232`) | `s16(0x021B) + s16(0x0232)` | `10s` | `NAN` on any incomplete Phase 1 sweep or `> 30s` stale (complete-sweep-gated publication) | Always inverter LOAD/UPS output sum; map external whole-home CTs separately |
| `srne_output_frequency` | Output Frequency | `sensor` | `Hz` | `0x0218` (`P1-R07`) | `uint16 × 0.01` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | — |
| `srne_solar_energy_daily` | Daily Solar Production | `sensor` | `kWh` | `0xF02F` (`P1-R15`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | `state_class: ""` (reset behavior pending live check) |
| `srne_load_energy_daily` | Daily Load Consumption | `sensor` | `kWh` | `0xF030` (`P1-R15`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | `state_class: ""` (reset behavior pending live check) |
| `srne_battery_charge_energy_daily` | Daily Battery Charge Energy | `sensor` | `kWh` | `0xF04D` (`P1-R16`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | `state_class: ""` (reset behavior pending live check) |
| `srne_battery_discharge_energy_daily` | Daily Battery Discharge Energy | `sensor` | `kWh` | `0xF04E` (`P1-R16`) | `uint16 × 0.1` | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | `state_class: ""` (reset behavior pending live check) |
| `srne_inverter_temperature` | Inverter Temperature (Heatsink B) | `sensor` | `°C` | `0x0221` (`P1-R09`) | **`int16 × 0.1`** | `10s` | `NAN` on incomplete Phase 1 sweep or `> 30s` stale | Explicitly named Heatsink B; Transformer/DC-DC are in Phase 2 |
| `srne_fault_status` | Fault Status | `binary_sensor` | — | `0x0204`–`0x0207` (`P1-R04`) | Boolean (`any word != 0`) | `10s` | `.invalidate_state()` on incomplete sweep / stale | Ambiguity `A25`: fault numeric codes are not mapped to text |
| `srne_modbus_communication_health` | Modbus Communication Health | `binary_sensor` | — | Runtime freshness (`P1-R01`..`P1-R16`) | Boolean (`true` within `30s`) | `10s` | Publishes `false` on timeout, bad reply, or `> 30s` stale | Runtime-dependent sweep health indicator (no register) |
| `srne_operating_mode` | Operating Mode (Current Operating State) | `text_sensor` | — | `0x0210` (`P1-R05`) | `uint16` split-phase enum (`0`–`3`) | `10s` | Publishes `"Unavailable"` on sweep failure / stale | Exposed in HA as `sensor.*`; maps `0–3` or `"Unknown (<raw>)"` |

---

## Phase 2 Extended Diagnostics & Identification (37 Public Entities)

All Phase 2 entities carry `entity_category: diagnostic` and update independently per `FC03` group (`P2-D01`..`D12`, `P2-S01`..`S12`). When a group fails or exceeds its `3×` freshness threshold (`> 90s` for `30s` groups, `> 900s` for `300s` `P2-S08`, `> 10800s` for `3600s` static groups), **only that group's entities** invalidate and enter stepped bounded backoff while Phase 1 and remaining Phase 2 groups continue.

| ESPHome Internal ID | Display Name | ESPHome Entity Type | Unit | Register (`Group`) | Scaling / Encoding | Nominal Poll | Freshness & Invalidation | Limitations / Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `srne_battery_rated_capacity` | Battery Rated Capacity | `sensor` | `Ah` | `0x0105` (`P2-D01`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | May return `0x02` if optional BMS params unavailable |
| `srne_battery_remaining_capacity` | Remaining Battery Capacity | `sensor` | `Ah` | `0x0106` (`P2-D01`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | May return `0x02` if optional BMS params unavailable |
| `srne_battery_charging_status` | Battery Charging Status | `text_sensor` | — | `0x010B` (`P2-D02`) | `uint16` enum (`0,1,2,4,5,6,8`) | `30s` | `"Unavailable"` on failure / `> 90s` stale | HA `sensor.*`; preserves `"Unknown (<raw>)"` |
| `srne_battery_cycle_count` | Battery Cycle Count | `sensor` | `cycles` | `0x010C` (`P2-D02`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | No `state_class`; persistence pending hardware check |
| `srne_total_charging_power` | Total Charging Power | `sensor` | `W` | `0x010E` (`P2-D03`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | Combined PV + utility charging power reported by inverter |
| `srne_bms_voltage` | Battery BMS Voltage | `sensor` | `V` | `0x0112` (`P2-D04`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | Optional BMS register; isolated stepped backoff on `0x02` |
| `srne_bms_temperature` | Battery BMS Temperature | `sensor` | `°C` | `0x0114` (`P2-D05`) | **`int16 × 0.1`** | `30s` | `NAN` on group failure / `> 90s` stale | Optional BMS register group |
| `srne_bms_charge_voltage_limit` | BMS Charge Voltage Limit | `sensor` | `V` | `0x0115` (`P2-D05`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | Optional BMS register group |
| `srne_bms_charge_current_limit` | BMS Charge Current Limit | `sensor` | `A` | `0x0116` (`P2-D05`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | Optional BMS register group |
| `srne_bms_discharge_current_limit` | BMS Discharge Current Limit | `sensor` | `A` | `0x0117` (`P2-D05`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | Optional BMS register group |
| `srne_grid_connection_countdown` | Grid-Connection Countdown | `sensor` | `s` | `0x020F` (`P2-D06`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | — |
| `srne_password_protection_status` | Password Protection Status | `text_sensor` | — | `0x0211` (`P2-D07`) | `uint16` enum (`0, 1, 4`) | `30s` | `"Unavailable"` on failure / `> 90s` stale | HA `sensor.*`; preserves `"Unknown (<raw>)"` |
| `srne_total_dc_bus_voltage` | Total DC Bus Voltage | `sensor` | `V` | `0x0212` (`P2-D07`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | — |
| `srne_utility_charging_current` | Utility Charging Current | `sensor` | `A` | `0x021E` (`P2-D08`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | — |
| `srne_heatsink_a_temperature` | Heatsink A Temperature (DC-DC) | `sensor` | `°C` | `0x0220` (`P2-D09`) | **`int16 × 0.1`** | `30s` | `NAN` on group failure / `> 90s` stale | Distinct from Heatsink B (`0x0221`) and C (`0x0222`) |
| `srne_heatsink_c_temperature` | Heatsink C Temperature (Transformer) | `sensor` | `°C` | `0x0222` (`P2-D10`) | **`int16 × 0.1`** | `30s` | `NAN` on group failure / `> 90s` stale | Physical sensor location pending live verification |
| `srne_ambient_temperature` | Ambient Temperature | `sensor` | `°C` | `0x0223` (`P2-D10`) | **`int16 × 0.1`** | `30s` | `NAN` on group failure / `> 90s` stale | Signed16 verified `-2.5 °C` (`0xFFE7`) in simulator |
| `srne_pv_charging_current` | PV Charging Current | `sensor` | `A` | `0x0224` (`P2-D10`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | — |
| `srne_positive_dc_bus_voltage` | Positive DC Bus Voltage | `sensor` | `V` | `0x0228` (`P2-D11`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | — |
| `srne_negative_dc_bus_voltage` | Negative DC Bus Voltage | `sensor` | `V` | `0x0229` (`P2-D11`) | `uint16 × 0.1` | `30s` | `NAN` on group failure / `> 90s` stale | Unsigned magnitude in V2.04 inventory |
| `srne_inverter_operating_time_today` | Inverter Operating Time Today | `sensor` | `min` | `0xF03E` (`P2-D12`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | Conservative no `state_class` until reset verified |
| `srne_bypass_operating_time_today` | Bypass Operating Time Today | `sensor` | `min` | `0xF03F` (`P2-D12`) | `uint16 × 1` | `30s` | `NAN` on group failure / `> 90s` stale | Conservative no `state_class` until reset verified |
| `srne_product_type` | Product Type | `text_sensor` | — | `0x000B` (`P2-S01`) | `uint16` enum (`0,1,3,4,5`) | `3600s` | `"Unavailable"` on group failure / `> 10800s` stale | HA `sensor.*`; stepped backoff (`5s`/`300s`/`900s`/`3600s`) |
| `srne_software_version_app` | Software Version (APP) | `text_sensor` | — | `0x0014` (`P2-S02`) | `"V%u.%02u (raw %u)"` | `3600s` | `"Unavailable"` on group failure / `> 10800s` stale | HA `sensor.*`; ambiguity `A13` preserves both formats |
| `srne_hardware_version_control_board` | Hardware Version (Control Board) | `text_sensor` | — | `0x0016` (`P2-S03`) | `"V%u.%02u (raw %u)"` | `3600s` | `"Unavailable"` on group failure / `> 10800s` stale | HA `sensor.*`; ambiguity `A13` preserves both formats |
| `srne_device_address` | Device RS485 Address | `sensor` | — | `0x001A` (`P2-S04`) | `uint16 × 1` | `3600s` | `NAN` on group failure / `> 10800s` stale | Read-only mirror of inverter slave address |
| `srne_model_code` | Model Code | `sensor` | — | `0x001B` (`P2-S04`) | `uint16 × 1` | `3600s` | `NAN` on group failure / `> 10800s` stale | Numeric model identifier (no unit) |
| `srne_protocol_version` | RS485 Protocol Version | `text_sensor` | — | `0x001C` (`P2-S04`) | `"raw %u (0x%04X)"` | `3600s` | `"Unavailable"` on failure / `> 10800s` stale | HA `sensor.*`; ambiguity `A13`/`A22` raw preserved |
| `srne_software_build_time` | Software Build Time | `text_sensor` | — | `0x0021`–`0x0034` (`P2-S05`, 20w) | Lower-8-bits/word ASCII | `3600s` | `"Unavailable"` on failure, non-ASCII, or `> 10800s` stale | HA `sensor.*`; stops on `0x00`/`0xFF`, trims spaces |
| `srne_product_serial_number` | Product Serial Number | `text_sensor` | — | `0x0035`–`0x0048` (`P2-S06`, 20w) | Lower-8-bits/word ASCII | `3600s` | `"Unavailable"` on failure, non-ASCII, or `> 10800s` stale | HA `sensor.*`; live encoding unverified |
| `srne_battery_rated_voltage` | Battery Rated Voltage | `sensor` | `V` | `0xE003` (`P2-S07`) | `uint16 × 1` | `3600s` | `NAN` on group failure / `> 10800s` stale | `RW` in V2.04; **monitored strictly via `FC03` only** |
| `srne_configured_operating_mode` | Configured Operating Mode | `text_sensor` | — | `0xE037` (`P2-S08`) | `uint16` enum (`0`–`3`) | `300s` | `"Unavailable"` on group failure / `> 900s` stale | HA `sensor.*`; `RW` in V2.04, **monitored strictly via `FC03` only** |
| `srne_parallel_operation_mode` | Parallel Operation Mode | `text_sensor` | — | `0xE201` (`P2-S09`) | `uint16` enum (`0`–`7`) | `3600s` | `"Unavailable"` on group failure / `> 10800s` stale | HA `sensor.*`; `RW` in V2.04, **monitored strictly via `FC03` only** |
| `srne_bms_enable_mode` | BMS Communication Mode | `text_sensor` | — | `0xE215` (`P2-S10`) | `uint16` enum (`0`–`2`) | `3600s` | `"Unavailable"` on group failure / `> 10800s` stale | HA `sensor.*`; `RW` in V2.04, **monitored strictly via `FC03` only** |
| `srne_total_operating_days` | Total Operating Days | `sensor` | `d` | `0xF031` (`P2-S11`) | `uint16 × 1` | `3600s` | `NAN` on group failure / `> 10800s` stale | Conservative no `state_class` until persistence verified |
| `srne_cumulative_inverter_operating_time` | Cumulative Inverter Operating Time | `sensor` | `h` | `0xF04A` (`P2-S12`) | `uint16 × 1` | `3600s` | `NAN` on group failure / `> 10800s` stale | Conservative no `state_class` until reset verified |
| `srne_cumulative_bypass_operating_time` | Cumulative Bypass Operating Time | `sensor` | `h` | `0xF04B` (`P2-S12`) | `uint16 × 1` | `3600s` | `NAN` on group failure / `> 10800s` stale | Conservative no `state_class` until reset verified |

---

## Implemented Enumeration Mappings

Unknown values never silently map to `0` or an unrelated label; every enum sensor preserves `"Unknown (<raw>)"`:

- **`srne_operating_mode` (`0x0210`)**: `0=Initialization`, `1=Standby`, `2=Utility operation`, `3=Inverter operation`.
- **`srne_battery_charging_status` (`0x010B`)**: `0=Charge off`, `1=Quick charge`, `2=Const voltage charge`, `4=Float charge`, `5=Reserved`, `6=Lithium battery activation`, `8=Full`.
- **`srne_password_protection_status` (`0x0211`)**: `0=User password not entered`, `1=User password entered`, `4=Manufacturer password entered`.
- **`srne_product_type` (`0x000B`)**: `0=Controller, Residential`, `1=Controller, Street Lighting`, `3=Grid-Tied Inverter`, `4=Controller-Inverter Integrated Unit`, `5=Low-Frequency Off-Grid`.
- **`srne_configured_operating_mode` (`0xE037`)**: `0=Off-grid mode (disabled)`, `1=Grid-connected mode`, `2=AC OUT anti-backflow`, `3=AC IN anti-backflow`.
- **`srne_parallel_operation_mode` (`0xE201`)**: `0=Single unit`, `1=Single-phase parallel`, `2=Split-phase A`, `3=Split-phase B`, `4=Split-phase C`, `5=Three-phase A`, `6=Three-phase B`, `7=Three-phase C`.
- **`srne_bms_enable_mode` (`0xE215`)**: `0=Disable`, `1=Enable 485-BMS`, `2=Enable CAN-BMS`.
