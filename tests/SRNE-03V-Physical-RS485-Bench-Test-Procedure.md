# SRNE-03V — Physical RS485 Bench Test Procedure (ESP32-S3 <-> Windows Simulator)

## 1. Purpose, Safety & Scope Boundary

This procedure validates physical RS485 communication, `9600,N,8,1` Modbus RTU framing, provisional `200ms` turnaround timing, Phase 1 + Phase 2 scheduling, failure isolation, and Home Assistant entity publishing between the deployed **Waveshare ESP32-S3-RS485-CAN-U** bench node (`esphome/srne-bench-test.yaml`) and [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) over a physical USB-RS485 adapter.

- **Synthetic test fixture warning**: All values served during this bench test originate from deterministic synthetic fixtures in [`tests/fixtures/`](fixtures/). Passing `SRNE-03V` validates RS485 bench communication and ESPHome/HA behavior, **not** a physical SRNE SPI-16K-UP inverter.
- **No production inverter connected**: Ensure no live AC mains, battery DC bus, PV array, or physical SRNE inverter is wired to the RS485 bus under test.

---

## 2. Protecting Production Home Assistant Statistics

> **CRITICAL PRE-TEST RULE**: Before connecting the bench ESP32 node to Home Assistant during synthetic runs, isolate or plan cleanup so synthetic kWh, voltage, temperature, and fault spikes do not remain in production dashboards or Long-Term Statistics (LTS).

1. **Energy Dashboard Audit**: Phase 1 daily energy entities (`srne_solar_energy_daily`, `srne_load_energy_daily`, `srne_battery_charge_energy_daily`, `srne_battery_discharge_energy_daily`) use `device_class: energy` with `state_class: ""` (not `total_increasing`), so they are **not** automatically summed as long-term energy dashboard totals, whereas `measurement` sensors (`sensor.*` with `state_class: measurement`) DO record Home Assistant LTS and state history.
2. **Isolation Options (choose one before Step 3)**:
   - **Recommended**: Test against a dedicated bench/staging Home Assistant instance, **OR** disable recording for `sensor.srne_*` / `binary_sensor.srne_*` / `text_sensor.srne_*` in `recorder.yaml` during bench runs if using a shared instance, **OR** ensure **none** of the bench `srne_*` entities are added to production Energy Dashboard / Utility Meters before running `SRNE-03V`.
3. **Post-Bench Cleanup (if connected to production HA)**:
   - Remove the ESPHome bench device integration or purge recorded synthetic states via Developer Tools -> Actions -> `recorder.purge_entities` targeting `srne_*`, and clear any temporary LTS entries via Developer Tools -> Statistics before connecting to a physical inverter.

---

## 3. Pre-Test Setup: COM Port Detection & RS485 Wiring

### Step 1 — Detect the USB-RS485 Adapter COM Port on Windows

> **COM3 SAFETY WARNING**: `COM3` is currently associated with the **Waveshare ESP32-S3 USB interface**. **Never** pass `COM3` to `--port` for the simulator unless Device Manager explicitly proves otherwise. Note that `srne_modbus_simulator.py` never auto-selects any port.

1. Keep the USB-RS485 adapter **unplugged** initially and list existing ports in PowerShell:
   ```powershell
   .\.venv-simulator\Scripts\python.exe -m serial.tools.list_ports -v
   ```
2. Plug in the dedicated **USB-RS485 adapter** and re-run:
   ```powershell
   .\.venv-simulator\Scripts\python.exe -m serial.tools.list_ports -v
   ```
3. Identify the **newly added** COM port (e.g., `COM5` — note adapter chipset such as FTDI / CH340 / CP210x in Device Manager -> **Ports (COM & LPT)**). Let `<ADAPTER_COM>` denote this exact port.
4. Run an offline sanity check (zero serial access) before opening `<ADAPTER_COM>`:
   ```powershell
   .\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --validate-only --interactive --scenario S1_solar_charging
   ```

### Step 2 — Physical RS485 Wiring & Polarity Check

1. **Power off** the ESP32-S3 before touching terminal screws.
2. Connect the USB-RS485 adapter to the Waveshare ESP32-S3-RS485-CAN-U RS485 transceiver port:
   - USB-RS485 **`A+` / `D+`** <-> Waveshare **`RS485 A` (`485_A`)**
   - USB-RS485 **`B-` / `D-`** <-> Waveshare **`RS485 B` (`485_B`)**
   - USB-RS485 **`GND`** <-> Waveshare **`GND`** (common reference prevents common-mode drift on bench USB buses)
3. Keep bench cable short (< 2 m). If adapter + board both have fixed 120 Ω termination, leave short bench wiring as-is unless signal reflections occur; never short `A` to `B` or tie `5V/VCC` pins.
4. Power the Waveshare ESP32-S3 board cleanly (ESP32 boots into disconnected polling attempting FC03 every `10s`).

---

## 4. Sequential Bench Execution Procedure

### Step 3 — Start the Simulator in Interactive Mode

Run in a dedicated PowerShell terminal (adjust `<ADAPTER_COM>` e.g. `COM5`):

```powershell
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port <ADAPTER_COM> --scenario S1_solar_charging --interactive --log-level INFO
```

**Verify immediately**:
- Startup banner displays `SYNTHETIC SRNE SIMULATOR — NOT A PHYSICAL INVERTER`.
- Serial config reads `port=<ADAPTER_COM>  9600,N,8,1  (Modbus RTU)`, Device Address `1 (0x01)`, `40 approved FC03 groups / 107 unique words`, `Failure Injection: OFF by default`.

### Step 4 — Verify Initial Normal Communication & Polarity

1. Observe the simulator console for incoming `Modbus request OK dev=1 fc=0x03 (3) ... outcome=OK` lines within 10–15 seconds.
   - **If zero requests appear** after 20 seconds: verify `<ADAPTER_COM>` is not opened by another app, quit simulator (`q`), power down ESP32, **swap `A` and `B` leads once**, restore power, and restart Step 3.
2. Confirm in Home Assistant (and optional ESPHome logs) that:
   - `binary_sensor.srne_modbus_communication_health` transitions from `OFF` to **`ON`**.
   - Within 60–90 seconds, initial Phase 2 dynamic (`D01`–`D12`) and initial staggered static identification (`S01`–`S12`) polls also register `outcome=OK` on the simulator log.

### Step 5 — Validate Phase 1 (36) & Phase 2 (37) Entities Under `S1_solar_charging`

Verify all **73 public entities** in Home Assistant are non-unavailable and match [`tests/fixtures/srne-expected-entities.json`](fixtures/srne-expected-entities.json) (`S1_solar_charging`):

| Entity ID | Phase | Expected Value (`S1_solar_charging`) | Verification Focus |
| --- | --- | --- | --- |
| `srne_modbus_communication_health` | P1 | `ON` (`true`) | Fresh Phase 1 sweep |
| `srne_uptime` | P1 | Increasing (`s`) | Runtime ESPHome uptime |
| `srne_operating_mode` | P1 | `Inverter operation` | Enum `0x0210 = 3` |
| `srne_fault_status` | P1 | `OFF` (`false`) | `0x0204..0x0207 = 0` |
| `srne_battery_soc` | P1 | `74 %` | `0x0100 = 74` |
| `srne_battery_voltage` | P1 | `53.6 V` | Scale `0.1` (`0x0101 = 536`) |
| `srne_battery_current` | P1 | `-85.0 A` | **Signed16 negative** (`0xFCAE`) |
| `srne_battery_net_power` | P1 Calc | `-4556.0 W` | Negative = charging |
| `srne_battery_charging_power` | P1 Calc | `4556.0 W` | Derived charging power |
| `srne_battery_discharging_power` | P1 Calc | `0.0 W` | Clamped at `0` |
| `srne_pv_total_power` | P1 Calc | `8428 W` | `4312 + 4116` (`PV1 + PV2`) |
| `srne_output_total_power` | P1 Calc | `3450 W` | `1750 + 1700` (`L1 + L2`) |
| `srne_inverter_temperature` | P1 | `42.5 °C` | Heatsink B (`0x0221`) |
| `srne_bms_voltage` | P2 Dyn | `53.5 V` | `D04` (`0x0112`) |
| `srne_ambient_temperature` | P2 Dyn | `28.4 °C` | `D10` (`0x0223`) |
| `srne_battery_charging_status` | P2 Dyn | `Quick charge` | Enum `0x010B = 1` |
| `srne_product_type` | P2 Stat | `Controller-Inverter Integrated Unit` | `S01` (`0x000B = 4`) |
| `srne_protocol_version` | P2 Stat | `raw 204 (0x00CC)` | Ambiguity preserved verbatim |
| `srne_software_build_time` | P2 Stat | `2025-11-15 10:30:00` | Lower-8-bits/word masking |
| `srne_product_serial_number` | P2 Stat | `SYNTH-SPI16K-0001` | Lower-8-bits/word masking + NUL trim |

### Step 6 — Switch Across All Five Operating Scenarios (`1`–`5`)

> Remember atomicity applies per individual Modbus response; allow at least **35 seconds** after each key press (`1`–`5`) so a full Phase 1 (10s) and Phase 2 dynamic (30s) cycle settles cleanly before reading HA values.

Switch sequentially (`2`, `3`, `4`, `5`, then back to `1`) and verify key reference values from [`srne-expected-entities.json`](fixtures/srne-expected-entities.json):

| Key | Scenario | Wait | Key Expected HA Values |
| --- | --- | --- | --- |
| `2` | `S2_battery_discharging` | >= 35 s | Mode=`Inverter operation`, SOC=`52 %`, Bat Current=`+75.0 A`, Net Power=`+3840.0 W`, Discharging=`3840.0 W`, Charging=`0.0 W`, PV Total=`0 W`, Output Total=`3470 W`, Charging Status=`Charge off` |
| `3` | `S3_utility_zero_solar` | >= 35 s | Mode=`Utility operation`, SOC=`35 %`, Bat Current=`-30.0 A`, Charging Power=`1572.0 W`, PV Total=`0 W`, Output Total=`2420 W`, Utility Charging I=`30.0 A`, Charging Status=`Const voltage charge`, Password=`User password entered` |
| `4` | `S4_standby` | >= 35 s | Mode=`Standby`, SOC=`100 %`, Bat Current=`0.0 A`, Output Total=`0 W`, Charging Status=`Full`, Grid Countdown=`60 s`, **Ambient Temp=`-2.5 °C`** (negative `s16` check!) |
| `5` | `S5_active_fault` | >= 35 s | Mode=`Standby`, **`srne_fault_status = ON`**, SOC=`18 %`, Bat V=`47.2 V`, Inverter Temp=`82.1 °C`, Ambient=`41.0 °C`, Password=`Manufacturer password entered` |
| `1` | `S1_solar_charging` | >= 35 s | Returns smoothly to Step 5 baseline values |

Run `s` in simulator console and confirm `Scenario Switch Count: 5`.

### Step 7 — Selective Diagnostic Failures (`P2-D04`, `P2-D05` / `bms`)

1. Type `f gtimeout bms` in the simulator console (silences `P2-D04` and `P2-D05` only).
2. Observe for **60–90 seconds**:
   - Simulator logs `INJECTED ... mode=SELECTIVE_TIMEOUT groups=P2-D04` / `P2-D05`, while `P1-R01`..`P1-R16` and unaffected `P2` groups continue logging `outcome=OK`.
   - `srne_modbus_communication_health` **MUST remain `ON`**.
   - Switch scenario `1 -> 2` mid-fault and confirm unaffected Phase 1 & `P2-D10` update to `S2` values while `srne_bms_voltage` (`D04`) and `srne_bms_temperature`..`srne_bms_discharge_current_limit` (`D05`) become `unavailable` (do **not** fall back to `0`).
3. Type `n` to restore normal communication; verify BMS entities recover cleanly without restarting ESP32 or simulator.
4. Type `f exc P2-D05 0x02` for 45 seconds, confirm `D05` rejects gracefully without disturbing Phase 1 (`srne_modbus_communication_health = ON`), then type `n` and confirm recovery.

### Step 8 — Complete Communication Loss (`f timeout`)

1. Type `f timeout` in the simulator console.
2. Observe for **45 seconds**:
   - All FC03 requests log `mode=SILENT_TIMEOUT (no reply sent)`.
   - Within ~30 seconds (Phase 1 30-second freshness window), `srne_modbus_communication_health` transitions to **`OFF`** and Phase 1 + Phase 2 entities transition to `unavailable` (zero stale false positives).

### Step 9 — CRC Corruption & Truncated Frames (`f crc`, `f trunc`)

1. Restore normal first (`n`, wait 15s for health `ON`), then type `f crc` (or `f crc P1-R01`).
2. Observe for 35 seconds: ESPHome rejects corrupted CRC frames cleanly without publishing arbitrary or zeroed measurements (after 30s without valid `P1` replies, `srne_modbus_communication_health` goes `OFF` / entities invalidate).
3. Type `n`, wait 15s for health `ON`, then type `f trunc` (or `f trunc P2-D05`).
4. Observe for 35 seconds: ESPHome rejects truncated frames cleanly without crash, hang, or bogus values.

### Step 10 — Automatic ESPHome Recovery

1. Type `n` in the simulator console (without touching ESP32 or restarting simulator).
2. Observe within **30–45 seconds**:
   - `srne_modbus_communication_health` automatically returns **`ON`**.
   - All 73 public entities repopulate accurately matching the active scenario (`s` shows `Active Failure Mode: normal`).

### Step 11 — Polling Performance & Phase 2 Scheduling Check

Run normal communication (`S1_solar_charging`, `--log-level INFO`) cleanly for **3 full minutes** (`180 s`):
- Inspect timestamps in simulator output:
  - Phase 1 groups (`P1-R01`..`P1-R16`) complete cleanly on a **~10 s** cadence without colliding with `send_wait_time: 300ms` or `turnaround_time: 200ms`.
  - Phase 2 dynamic groups (`P2-D01`..`P2-D12`) cycle cleanly on a **~30 s** cooperative cadence, leaving > 80% bus headroom.
  - Zero watchdog resets, zero heap crashes, zero UART frame corruption errors under normal mode (`s` -> `Invalid CRC Frames: 0` during clean window).
- Type `q` in simulator console to verify clean graceful shutdown (serial port released cleanly).

---

## 5. Evidence Collection & Formal PASS / FAIL Acceptance Criteria

Record and archive under a dedicated bench evidence report (`SRNE-03V`):
1. Adapter identity + COM port proof (`serial.tools.list_ports -v`, confirming `<ADAPTER_COM> != COM3`).
2. Simulator console capture showing startup banner, normal `P1`/`P2` cycles, all 5 transitions (`s` status output), fault injections (`f status`), recovery (`n`), 3-minute steady-state cadence, and `q` shutdown.
3. ESPHome UART/Modbus logs covering normal polling, selective timeout/exception backoff, full timeout invalidation, CRC/truncation rejection, and automatic recovery.
4. Home Assistant entity state snapshots / screenshots across `S1`–`S5` (verifying negative currents, `-2.5 °C` ambient temp, lower-8-bit strings, fault sensor `ON`/`OFF`) plus post-test cleanup confirmation if a production HA instance was used.

### Go / No-Go Acceptance Gate

| Criterion | PASS Requirement | FAIL Trigger |
| --- | --- | --- |
| Physical RTU Link | Stable `9600,N,8,1` FC03 traffic at `turnaround_time: 200ms` with `0` framing errors in normal mode | Persistent timeouts, CRC errors in normal mode, or garbled frames |
| Entity Accuracy (`S1`–`S5`) | Spot & calculated values match `srne-expected-entities.json` (signed `s16`, strings, raw/bool states) | Off-by-one address shift, sign inversion, broken string mask, missing entities |
| Fault Isolation | `f gtimeout bms` / `f exc` keeps `srne_modbus_communication_health = ON` and Phase 1 unaffected | Selective Phase 2 fault drops Phase 1 freshness or stalls polling |
| Total Loss, CRC & Truncation | `f timeout`, `f crc`, `f trunc` invalidate affected entities cleanly without zeroing or crashes | Entities show `0` instead of `unavailable`, or ESP32 reboots/hangs |
| Automatic Recovery | `n` restores all `73` entities automatically without ESP32 or simulator reboot | Requires manual ESP32 reset or port reopen to resume |
| Bus Scheduling | 3-minute normal run maintains ~10s Phase 1 + cooperative Phase 2 polling cleanly | Bus collisions, overflowing queues, or stale Phase 1 sweeps (> 30s) |

Only after **all 6 criteria PASS** should physical RS485 connection planning for the real **SRNE SPI-16K-UP** inverter begin.
