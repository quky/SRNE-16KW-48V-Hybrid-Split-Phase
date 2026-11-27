# SRNE Modbus RTU Technical Reference

> [!NOTE]
> **Authoritative Source Boundary**: Register layouts and protocol rules below summarize our repository audits of the official **SRNE Modbus Monitoring Protocol V2.04** document (`SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf`) and vendor manuals. Manufacturer PDFs remain gitignored local references (`documentation/official/*.pdf`) and are **not** redistributed in this public repository.

For complete historical audits and raw tables, see:
- [`audits/SRNE-01B-Communication-Specification.md`](../audits/SRNE-01B-Communication-Specification.md)
- [`audits/SRNE-01B-Register-Inventory.csv`](../audits/SRNE-01B-Register-Inventory.csv)
- [`audits/SRNE-01B-Ambiguities.md`](../audits/SRNE-01B-Ambiguities.md)
- [`audits/SRNE-01B-Write-Risk-Matrix.md`](../audits/SRNE-01B-Write-Risk-Matrix.md)
- [`audits/SRNE-04G-R1-Architecture-Correction.md`](../audits/SRNE-04G-R1-Architecture-Correction.md)

---

## 1. Protocol Transport & Framing Summary

| Parameter | Specification | Notes |
| --- | --- | --- |
| **Physical Layer** | Two-wire isolated RS485 (`A+` / `B−`), Modbus RTU | UART on Waveshare `ESP32-S3-RS485-CAN-U` (`TX=GPIO17`, `RX=GPIO18`, DE/RE `GPIO21`) |
| **Serial Parameters** | `9600` baud, `8` data bits, `No` parity, `1` stop bit (`9600,N,8,1`) | Matches SRNE V2.04 p3 |
| **Default Slave Address** | `0x01` (`1`) | Normal range `0x01`–`0xFE`; broadcast `0x00` & universal `0xFF` are disabled/unused by ESPHome |
| **Function Codes Used** | **`FC03` (`0x03`) Read Holding Registers only** | **Zero** write operations (`FC06`, `FC16`) or custom PDUs implemented |
| **Vendor Max Read Size** | **32 words** per operation (V2.04 exception `0x0A`) | Applies to single scalars, strings, and contiguous blocks |
| **Implemented Max Read Size** | **20 words** (`0x0021`..`0x0034` and `0x0035`..`0x0048`) | Keeps every request comfortably below the 32-word limit |
| **Wire Byte Order (Words)** | Big-endian per 16-bit register (high byte first, low byte second) | Standard Modbus RTU register order |
| **CRC Byte Order** | Little-endian CRC-16 Modbus (`0xA001` reflected polynomial, `0xFFFF` init; low byte first) | Distinct from big-endian register words |
| **32-Bit Scalar Order (Protocol Rule)** | Low 16-bit word at lower address, high 16-bit word at next address | Currently unused in Phase 1/2 (all implemented scalars are 16-bit) |
| **String Register Encoding** | **Lower 8 bits per 16-bit word (`word & 0x00FF`) ASCII** | Upper 8 bits per word are invalid/ignored per V2.04 p9 (`0x0021`–`0x0034`, `0x0035`–`0x0048`) |

---

## 2. Implemented Read-Only Request Architecture

### Total Bus Footprint: **40 Groups / 107 Register Words**

- **Phase 1 ([`srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) + [`srne-bench-test.yaml`](../esphome/srne-bench-test.yaml))**: **16** `FC03` readers totaling **32** unique register words (`P1-R01`..`P1-R16`), polled every `10s` via a single `modbus_controller` (`srne_phase1_controller`) with `reuse_previous_range: false` (never spans undocumented register gaps). Exposes **35** public entities (`32` numeric + `2` binary + `1` text) plus **1** local `srne_uptime` entity in `srne-bench-test.yaml` = **36** Phase 1 public entities.
- **Phase 2 ([`srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml))**: **24** independent `FC03` dispatch groups totaling **75** unique register words (**12** dynamic groups `P2-D01`..`D12` = `22` words at `30s` nominal / `90s` freshness; **1** mode config `P2-S08` = `1` word at `300s` nominal / `900s` freshness; **11** static/cumulative groups = `52` words at `3600s` nominal / `10800s` freshness), exposing **37** public entities (`26` numeric + `11` text).
- **Read-Only Access Policy on `RW` Registers**: Modbus **write operations (`FC06`/`FC16`) and writable controls (`number`, `select`, `switch`, `button`) are excluded**. Manufacturer-designated `RW` registers may still be safely monitored through read-only `FC03` (`0x03`) polling; specifically, `0xE003` (rated battery V), `0xE037` (configured operating mode), `0xE201` (parallel mode), and `0xE215` (BMS mode) are polled **exclusively via `FC03`**.

### Cooperative Single-In-Flight Scheduling & Failure Isolation

Inspecting ESPHome `2026.11.1` identified two shared-bus hazards (`SRNE-04G-R1`) resolved by the current architecture:

1. **No second `modbus_controller` for Phase 2**: A second `modbus_controller` on `address: 0x01` calls `clear_tx_queue_for_address(0x01)` whenever an optional register times out, wiping queued Phase 1 frames. Instead, Phase 2 executes via independent **`modbus_client.read_holding_registers`** calls.
2. **Single-in-flight guard (`srne_p2_in_flight`)**: Prevents overlapping Phase 2 sweeps or queue buildup (`max 1` Phase 2 frame in transit; `2000ms` application watchdog).
3. **Cooperative Phase 1 Priority**: Because ESPHome's `ModbusClientHub` schedules reads FIFO, Phase 2's `250ms` scheduler checks queue and Phase 1 state before dispatching — yielding whenever `!modbus1.tx_buffer_empty()`, `modbus1.tx_blocked()`, `srne_phase1_scan_active`, `srne_phase1_awaiting`, or within `700ms` of Phase 1's next `10s` sweep.
4. **Selective Failure Isolation & Stepped, Bounded Backoff**:
   - **Timeouts / malformed responses (`is_exception=false`, `is_not_sent=false`)**: One bounded retry (`3s` fast groups / `5s` static), then stepped backoff `60s -> 120s -> 300s` (fast groups `D01`–`D12`, `S08`) or `300s -> 900s -> 3600s` (static groups).
   - **Modbus exceptions (`is_exception=true`, e.g. `0x02` missing optional BMS register)**: Skips immediate retry and enters stepped backoff (`60s -> 120s -> 300s` fast; `3600s` static).
   - **Not sent (`is_not_sent=true`)**: Stepped backoff `5s -> 30s -> 60s -> 300s`.
   - **Phase 1 recovery edge**: When `srne_modbus_communication_health` recovers (`false -> true`), Phase 2 re-staggers non-exception backed-off groups cleanly; groups marked `exc_fail` stay on their exception backoff schedule.

---

## 3. Hub Timing Configuration & Calculated Transaction Scheduling Occupancy

[`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) explicitly configures two distinct ESPHome `2026.11.1` Modbus client hub timers on `modbus1` (documented directly in `modbus/__init__.py` and `modbus.cpp`) alongside separate application-level YAML watchdogs:

- **`send_wait_time: 300ms`** (replaces ESPHome's `2000ms` default): **Hub-level response-wait timeout** (`send_wait_time_us_`) starting after a request is transmitted before the hub expires waiting for a reply (`expire_waiting_()`).
- **`turnaround_time: 200ms`** (replaces ESPHome's `600ms` default, which yielded `99.4%–115.4%` calculated scheduling occupancy for Phase 1 alone): **Provisional hub-level inter-transaction quiet turnaround delay** (`turnaround_delay_us_`) enforced inside `ModbusClientHub::tx_delay_remaining()` on top of the `3.65 ms` Modbus RTU 3.5-character inter-frame silence (`frame_delay_us_`) after the last transmitted or received byte before dispatching the next transaction. Unverified on physical `SPI-16K-UP` hardware.
- **Application-level completion/in-flight watchdogs (distinct from the hub timers above)**: Phase 1's `srne_phase1_response_deadline_ms: 1000` (`100ms` interval check) and `30s` freshness window; Phase 2's `srne_phase2_inflight_watchdog_ms: 2000` (`250ms` interval check) and per-group `3×` freshness windows (`90s` / `900s` / `10800s`).

The table below from [`audits/SRNE-04G-R1-Architecture-Correction.md`](../audits/SRNE-04G-R1-Architecture-Correction.md) presents **calculated transaction scheduling occupancy** and **available scheduling headroom** at `9600,N,8,1`. Because these sums include assumed slave response latency (`T_resp`) and configured hub turnaround delays (`200ms + 3.65 ms`), they measure **scheduler slot occupancy** — **not** direct electrical RS485 wire activity:

| Assumed Inverter Latency (`T_resp`) | Phase 1 (`16` reqs / `10s`) Occupancy | Phase 1 + Phase 2 Dynamic (`60` reqs / `30s`) Occupancy | 1-Hour Avg Occupancy (incl. `300s` + `3600s`) | Available Scheduling Headroom (`30s` avg) |
| ---: | ---: | ---: | ---: | ---: |
| `0 ms` | `3.54 s` (`35.4%`) | `13.28 s` (`44.3%`) | `44.4%` | `55.7%` |
| `30 ms` | `4.02 s` (`40.2%`) | `15.08 s` (`50.3%`) | `50.4%` | `49.7%` |
| `50 ms` | `4.34 s` (`43.4%`) | `16.28 s` (`54.3%`) | `54.4%` | `45.7%` |
| `100 ms` | `5.14 s` (`51.4%`) | `19.28 s` (`64.3%`) | `64.5%` | `35.7%` |
| `250 ms` *(illustrative high-latency condition)* | `7.54 s` (`75.4%`) | `28.28 s` (`94.3%`) | `94.6%` | `5.7%` |

Under an **illustrative high-latency condition** such as `T_resp = 250ms` (or higher latencies approaching `300ms` `send_wait_time`), available scheduling headroom tightens to `5.7%`; `250ms` is **not** a programmed Phase 2 starvation threshold. Actual Phase 2 dispatch continues dynamically whenever queue availability (`tx_buffer_empty()`, `!tx_blocked()`), Phase 1 activity (`!srne_phase1_scan_active`, `!srne_phase1_awaiting`), and the `700ms` pre-sweep scheduling guard allow, prioritizing Phase 1 if headroom narrows and indicating that `turnaround_time`, `send_wait_time`, or polling intervals would need tuning after live inverter measurement.

---

## 4. Sign Conventions & Measurement Boundaries

### Battery Current & Power Sign Convention

- Register `0x0102` (`srne_battery_current`) is documented in SRNE V2.04 p9 as **signed 16-bit** (`int16 × 0.1 A`):
  - **Positive (`> 0`)**: **Discharging** from battery.
  - **Negative (`< 0`)**: **Charging** into battery.
- Calculated `srne_battery_net_power` (`(0x0101 × 0.1) × (s16(0x0102) × 0.1)`) preserves the exact same polarity (`+` discharge, `−` charge), corresponding to Universal Inverter Flow's `battery.power_mode: signed_positive_discharge`.
- Note: Per `SRNE-01B-Communication-Specification.md`, register `0x0113` (BMS current, currently **excluded**) uses unsigned representation in V2.04 without a documented direction convention and is intentionally omitted.

### Grid & Inverter Output Measurement Boundaries

- **Inverter Output Power (`0x021B`, `0x0232`, `srne_output_total_power`)**: **Always measures inverter LOAD / UPS output power** on split-phase L1 and L2 (`signed int16 W`). External whole-home CT sensors measuring non-backed-up main panel loads upstream of the inverter or behind an external ATS must be mapped as **separate** Home Assistant sensors and do not change the inverter register measurement boundary.
- **Grid Leg Voltage & Current (`0x0213`, `0x0214`, `0x022A`, `0x0238`)**: Expose per-leg grid voltages (`L1`/`L2`) and **unsigned** grid currents (`L1`/`L2`). Signed grid import/export power registers were deferred due to unresolved V2.04 documentation ambiguities (`A14`/`A16`).

---

## 5. Preserved Unresolved Protocol Ambiguities

Several protocol items from [`audits/SRNE-01B-Ambiguities.md`](../audits/SRNE-01B-Ambiguities.md) remain unresolved without live inverter telemetry and are handled conservatively:

- **`A13` / `A22` (`0x001C` Protocol Version)**: V2.04 conflicts on hex vs decimal version interpretation; firmware formats verbatim as `"raw %u (0x%04X)"` (e.g., `raw 204 (0x00CC)`).
- **`A25` (`0x0204`–`0x0207` Fault Codes)**: Official manual/protocol fault tables diverge and bit/index layout is unverified on hardware; Phase 1 exposes boolean `srne_fault_status` (`any != 0`) without guessing fault names.
- **`0x0210` Operating Mode Split-Phase Enum**: Uses the split-phase table (`0`–`3`) cleanly and formats unexpected values as `"Unknown (<raw>)"`.
- **Daily & Cumulative Energy / Runtime Counters (`0xF02F`, `0xF030`, `0xF04D`, `0xF04E`, `0xF03E`, `0xF03F`, `0xF031`, `0xF04A`, `0xF04B`)**: Reset and persistence behavior is unverified on hardware; daily kWh entities keep `state_class: ""` and runtime counters omit `state_class` to protect Home Assistant statistics.
- **Deferred Registers & Excluded Writes**: `21` ambiguous Phase 2 candidates (including BMS current `0x0113`, fan speed/duty, fault history records, inverter hardware M1/M2/S1 slots) remain deferred pending live verification. Write commands (`FC06`/`FC16`) and writable controls are excluded, while the four safe-to-poll `RW`-designated registers (`0xE003`, `0xE037`, `0xE201`, `0xE215`) are read strictly via `FC03`.
