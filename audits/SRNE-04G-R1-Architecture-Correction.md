# SRNE-04G-R1 — Shared Modbus Architecture Correction

Completed 2026-11-25 for owner review. Documents the two architectural blockers identified in ESPHome **2026.11.1** prior to Phase 2 implementation, the owner-authorized **Option A** resolution (`turnaround_time: 200ms` provisional + cooperative `modbus_client.read_holding_registers`), and worst-case scheduling/utilization analysis across six operational scenarios.

> [!IMPORTANT]
> `turnaround_time: 200ms` is a **provisional software-development setting**. No simulator run or physical SPI-16K-UP test has been performed. Simulator validation must precede physical inverter testing, and simulator success does not establish physical SPI-16K-UP compatibility.

---

## 1. Blockers Identified in ESPHome 2026.11.1 Source Inspection

Inspection of installed ESPHome `2026.11.1` (`esphome/components/modbus/` and `esphome/components/modbus_controller/`) established two hard blockers against naive `modbus_controller` Phase 2 expansion on shared bus `modbus1`:

| Blocker | ESPHome 2026.11.1 Source Mechanism | Consequence for Phase 1 |
|---|---|---|
| **B1 — Default `600ms` Turnaround Saturation** | `modbus/__init__.py:314` defaults `turnaround_time` to `600ms` when omitted. `ModbusClientHub::tx_delay_remaining()` (`modbus.cpp:140-146`) enforces `frame_delay_us_ + turnaround_delay_us_` (`3.65 ms + 600 ms = 603.65 ms`) after every transaction. `select_next_ready_()` (`modbus.cpp:955-971`) schedules all `READ` frames strictly **FIFO** with `max_pending() == 2`. | Phase 1 alone (`16` requests / `10s`) already consumes `9.94 s–11.54 s` (**99.4%–115.4%**) per `10s` at `T_resp = 0–100 ms`. Adding 12 Phase 2 dynamic requests / `30s` pushes demand to **124.3%–144.3%**, causing queue saturation and breaching Phase 1's `30s` freshness bound (`fresh_ms = 3UL * 10s`). |
| **B2 — Cross-Controller Teardown on Timeout** | `skip_updates` is deprecated and a no-op (`modbus_controller/__init__.py:125-135`). Adding a second `ModbusController` on `address: 0x01` triggers `ModbusController::set_online(false, ...)` (`modbus_controller.cpp:270-274`) upon timeout, calling `this->hub_->clear_tx_queue_for_address(0x01)` (`modbus.cpp:1194-1202`). | Any offline/timeout event on an optional Phase 2 / BMS `modbus_controller` clears **all queued frames for `0x01`** on `modbus1`—including Phase 1's in-queue `R01`–`R16` polls—invalidating all 36 Phase 1 entities. |

---

## 2. Authorized Option A Resolution

1. **Bench Bus Timing (`esphome/srne-bench-test.yaml`)**: Explicitly set `turnaround_time: 200ms` on `modbus1`, keeping `uart_rs485` (`9600,N,8,1`), `flow_control_pin: GPIO21`, and `send_wait_time: 300ms` unchanged.
2. **Byte-Identical Phase 1 Preservation (`esphome/packages/srne-phase1-monitoring.yaml`)**: Zero edits; retains `10s` polling, `1000ms` completion guard, `30s` freshness window, and `srne_phase1_mask` unchanged (`SHA256: 4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80`).
3. **Independent `modbus_client.read_holding_registers` (`esphome/packages/srne-phase2-diagnostics.yaml`)**:
   - **Zero** additional `modbus_controller` instances (`clear_tx_queue_for_address` is never called by Phase 2).
   - **Single in-flight request**: `srne_p2_in_flight` guarantees at most 1 Phase 2 frame in the hub queue at any moment (preventing unbounded queues and overlapping sweeps).
   - **Cooperative Phase 1 Priority**: Because `ModbusClientHub::select_next_ready_()` uses FIFO within `READ` priority (`modbus.cpp:955-971`), Phase 2 does **not** assume hub-level priority. Instead, the `250ms` scheduler yields whenever `!id(modbus1).tx_buffer_empty() || id(modbus1).tx_blocked()`, `srne_phase1_scan_active`, `srne_phase1_awaiting`, or within `700ms` of Phase 1's next `10s` sweep start (`(now - last_scan) % p1_int >= p1_int - 700ms`).
   - **Bounded Retries & Backoff**: `on_no_response` sets `retry: !lambda 'return false;'` so the hub never auto-retries. Timeout/malformed failures get **1 bounded retry** (`3s` dynamic / `5s` static) followed by exponential backoff (`60s -> 120s -> 300s` dynamic/mode; `300s -> 900s -> 3600s` static). Modbus exceptions (e.g., `02H` unsupported optional register) skip immediate retry and jump directly to `60s -> 120s -> 300s` (or `3600s` static).
   - **Static Staggering**: Boot due times are staggered (`15.5s` to `70.5s` at `5s` steps), and runtime static dispatches enforce `srne_phase2_static_min_spacing_ms: 2000ms`.

---

## 3. Recalculated Bus Utilization (`turnaround_time = 200ms`, `9600,N,8,1`)

Wire primitives at `9600,N,8,1` (`1.0417 ms/byte`, `frame_delay_us_ = 3.647 ms`):
- FC03 Request (`8 bytes`): `8.33 ms`
- FC03 Normal Response (`5 + 2*W bytes`): `7.29 ms` (1 word), `13.54 ms` (4 words), `46.88 ms` (20 words)
- Transaction Cycle (`T_tx_req + T_resp + T_rx_resp + 3.65 ms + 200 ms`):
  - 1-word OK at `T_resp = 50ms`: **`269.27 ms`** | 4-word OK: **`275.52 ms`** | 20-word OK: **`308.86 ms`**
  - Exception reply (`5 bytes`) at `T_resp = 50ms`: **`267.19 ms`**
  - Single timeout attempt (`8.33 ms + max(300 ms, 203.65 ms)`): **`308.33 ms`**
  - Phase 1 full offline timeout (`1 + 4 retries` = 5 attempts): **`1.54 s`** (`1541.67 ms`)

### Steady-State & Burst Utilization Table

| Inverter `T_resp` | Phase 1 (`16` reqs / `10s`) | Phase 1 Quiet Window / `10s` | Phase 2 Dyn (`12` reqs) | Phase 1 + P2 Dyn (`60` reqs / `30s`) | Phase 2 Static+Slow (`12` reqs) | 1-Hour Avg (incl. `S08`@`300s` + 11@`3600s`) |
|---:|---:|---:|---:|---:|---:|---:|
| `0 ms` | `3.54 s` (**35.4%**) | `6.46 s` | `2.65 s` | `13.28 s` (**44.3%**) | `2.72 s` | **44.4%** |
| `30 ms` | `4.02 s` (**40.2%**) | `5.98 s` | `3.01 s` | `15.08 s` (**50.3%**) | `3.08 s` | **50.4%** |
| `50 ms` | `4.34 s` (**43.4%**) | `5.66 s` | `3.25 s` | `16.28 s` (**54.3%**) | `3.32 s` | **54.4%** |
| `100 ms` | `5.14 s` (**51.4%**) | `4.86 s` | `3.85 s` | `19.28 s` (**64.3%**) | `3.92 s` | **64.5%** |
| `250 ms` | `7.54 s` (**75.4%**) | `2.46 s` | `5.65 s` | `28.28 s` (**94.3%**) | `5.72 s` | **94.6%** |

---

## 4. Evaluation of Six Worst-Case Scheduling Scenarios

| Scenario | Worst-Case Bus & Timing Behavior | Phase 1 Freshness (`30s`) & Isolation Outcome |
|---|---|---|
| **1. Normal responses (`T_resp <= 100ms`)** | Phase 1 finishes in `3.54–5.14 s`, leaving `4.86–6.46 s` quiet per `10s` cycle. Phase 2 dispatches 1 request per `>= 250ms` only inside Phase 1's quiet window (`44.3%–64.5%` avg load). | **PASS**: Phase 1 sweeps complete well inside `10s`; zero queue collisions. |
| **2. Missing optional BMS registers (`D01`, `D04`, `D05`)** | *Exception `02H`*: 3 failures × `267 ms = 0.80 s`, then immediate backoff to `60s -> 120s -> 300s` (no tight retry). *Silent timeout*: initial cycle takes `3 × 2 × 308 ms = 1.85 s` (`57.7%` 30s load at `T_resp=50ms`), then backs off to `300s` (`51.8%` steady load). | **PASS**: Only `D01`/`D04`/`D05` invalidate (`NAN`); all other Phase 2 groups and all 36 Phase 1 entities remain unaffected. |
| **3. Delayed responses (`T_resp = 250–280ms`)** | At `T_resp = 250ms`, Phase 1 alone takes `7.54 s` (`2.46 s` quiet), and combined 30s utilization reaches **94.3%**. At `T_resp = 280ms` (just below `300ms` `send_wait_time`), combined 30s demand reaches **100.3%** (`30.08 s`). Because Phase 2 stops dispatching once `srne_phase1_scan_active` or the `700ms` pre-sweep guard triggers, Phase 1 retains priority while Phase 2 dynamic groups defer and may age out at `90s`. *(If `T_resp > 300ms`, `send_wait_time` expires and Phase 1 itself invalidates.)* | **PASS (Phase 1 prioritized)** up to `T_resp ~250ms`; at `T_resp > 250ms` Phase 2 gracefully starves to protect Phase 1, indicating `turnaround_time` / `send_wait_time` would need tuning after simulator/bench measurement. |
| **4. Complete communication loss** | Phase 1 detects offline after `5` attempts (`1.54 s`), calls `clear_tx_queue_for_address(0x01)` and `srne_phase1_invalidate`, and enters `offline_skip_updates = 0` probing (`~1.54 s` every `10s`). Any in-flight Phase 2 request retires via `on_not_sent` (`srne_p2_handle_failure`) or `on_no_response`, invalidates only that group, and backs off (`3s -> 60s -> 120s -> 300s`), yielding whenever Phase 1 is active. | **PASS**: Phase 2 cannot worsen Phase 1 offline recovery and enters exponential backoff without queueing bursts. |
| **5. Communication recovery** | When Phase 1 regains `srne_modbus_communication_health == true`, Phase 2 observes the `false -> true` edge (read-only) and reschedules **only non-exception** backed-off groups staggered at `now + 2000ms + 750ms/2500ms` steps (`D` then `S`), keeping `exc_fail` groups backed off. | **PASS**: Smooth staggered restoration with 1 in-flight request at a time; zero burst congestion. |
| **6. Simultaneous static due times** | At boot (`15.5s + 5s*idx`) and after `3600s`, even if all 12 static/slow groups become due simultaneously, `srne_p2_in_flight` + `srne_phase2_static_min_spacing_ms: 2000ms` caps static dispatches to **at most 1 static request every `2.0 s`** inside Phase 1 quiet windows (spreading 12 requests over `>= 24 s`, ~`3–4` Phase 1 cycles). | **PASS**: Zero burst impact on Phase 1 `10s` sweep or `30s` freshness. |

---

## 5. Remaining Risks & Validation Boundary

1. **Provisional `200ms` Turnaround**: Official SRNE V2.04 specifies no turnaround or response latency. If the physical SPI-16K-UP requires `> 200ms` silence between frames or exhibits `T_resp > 200ms`, `turnaround_time` and/or `send_wait_time` must be adjusted after simulator and physical bench testing.
2. **250ms Cooperative Yield Window**: A Phase 2 request dispatched `~255ms` before Phase 1's `10s` timer can overlap Phase 1's first `0x0100` queue entry by `~50–100ms` (with `T_resp <= 100ms`), delaying Phase 1 sweep start by `< 0.15 s` — negligible relative to Phase 1's `1000ms` per-request guard and `30s` sweep freshness.
3. **Physical Compatibility Unverified**: Software config validation under ESPHome `2026.11.1` does not prove wire-level inverter support, string formatting, or sensor availability.
