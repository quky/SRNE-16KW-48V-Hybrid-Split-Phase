# SRNE-03V — Physical RS485 Bench Test Procedure (ESP32-S3 <-> Windows Simulator)

## 1. Purpose, Safety & Scope Boundary

This procedure validates physical RS485 communication, `9600,N,8,1` Modbus RTU framing, provisional `200ms` turnaround timing, Phase 1 + Phase 2 scheduling, failure isolation, and Home Assistant entity publishing between the deployed **Waveshare ESP32-S3-RS485-CAN-U (`SKU 34781`)** bench node ([`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml)) and [`scripts/srne_modbus_simulator.py`](../scripts/srne_modbus_simulator.py) over a physical USB-RS485 adapter.

Related references: [`docs/INSTALLATION.md`](../docs/INSTALLATION.md) (wiring, termination, and deployment), [`docs/ENTITIES.md`](../docs/ENTITIES.md) (73-entity catalog and YAML-derived matrix), [`docs/MODBUS-REFERENCE.md`](../docs/MODBUS-REFERENCE.md) (FC03 register groups and scheduling), and [`tests/README.md`](README.md) (simulator CLI and offline test guide).

- **Synthetic test fixture warning**: All values served during this bench test originate from deterministic synthetic fixtures in [`tests/fixtures/`](fixtures/) covering only the **40 implemented `FC03` groups / 107 register words**. Passing `SRNE-03V` validates RS485 bench communication and ESPHome/HA behavior, **not** a physical SRNE SPI-16K-UP inverter or the full manufacturer register inventory.
- **No production inverter connected**: Ensure no live AC mains, battery DC bus, PV array, or physical SRNE inverter is wired to the RS485 bus under test.

---

## 2. Protecting Production Home Assistant Statistics

> **CRITICAL PRE-TEST RULE**: Keep synthetic simulator traffic **disabled** (do not run Step 3 until all checks below pass) so synthetic kWh, voltage, temperature, and fault values are never recorded into production Home Assistant history or Long-Term Statistics (LTS).

1. **Home Assistant Entity ID Prefix & Domain Behavior (`C11` Reconciled)**:
   - The repository exposes **73 public entities** (**59** ESPHome `sensor` [`58` Modbus + `1` local `srne_uptime`] + **2** `binary_sensor` + **12** `text_sensor`), which appear in Home Assistant as **`71` `sensor.*`** and **`2` `binary_sensor.*`** entities.
   - [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) sets `name: srne-bench-test` and `friendly_name: SRNE Bench Test`, so Home Assistant entity IDs may use a **`srne_bench_test_*`** prefix (or another registry-assigned prefix) rather than `srne_*`.
   - **`text_sensor` is an ESPHome platform, NOT a Home Assistant entity domain**: In Home Assistant, ESPHome `text_sensor` entities appear under **`sensor.*`** alongside numeric sensors, while ESPHome `binary_sensor` entities appear under **`binary_sensor.*`**.
   - **Mandatory check (while simulator traffic is OFF)**: Open **Developer Tools -> States** in Home Assistant and record the **actual** `sensor.*` and `binary_sensor.*` entity IDs assigned to the bench node before writing `recorder` exclusions or starting simulator traffic.
2. **Energy Dashboard vs. Recorder & LTS Behavior**:
   - Phase 1 daily energy entities (`srne_solar_energy_daily`, `srne_load_energy_daily`, `srne_battery_charge_energy_daily`, `srne_battery_discharge_energy_daily`) use `device_class: energy` with `state_class: ""` (not `total_increasing`), so they are not automatically accumulated as long-term energy totals, whereas sensors with `state_class: measurement` DO record Home Assistant Long-Term Statistics (LTS) and state history.
   - **Important**: Excluding bench entities from the Home Assistant **Energy Dashboard** alone does **not** prevent Recorder state history or Long-Term Statistics (LTS) from being written for `state_class: measurement` sensors.
3. **Isolation Options (verify BEFORE starting Step 3 simulator traffic)**:
   - **Recommended**: Test against a dedicated bench or staging Home Assistant instance so production Recorder and LTS databases are never touched.
   - **Shared-instance alternative**: Configure explicit `recorder` exclusions in `configuration.yaml` / `recorder.yaml` matching the **actual** verified entity IDs (`sensor.*` and `binary_sensor.*` only — never `text_sensor.*`), reload/restart Home Assistant, and confirm exclusions are active **before** running Step 3.
4. **Optional & Conditional Post-Bench Cleanup (Irreversible Data Deletion)**:
   - Cleanup is **optional and conditional**: required **only if** synthetic data was actually recorded into a shared or production Home Assistant database (skipped completely when using an isolated staging instance or verified `recorder` exclusions).
   - **WARNING — IRREVERSIBLE ACTION**: Running `recorder.purge_entities` or deleting entries in **Developer Tools -> Statistics** **permanently destroys** historical state graphs and/or Long-Term Statistics for every matched entity. An unverified or overly broad pattern/glob can unintentionally wipe production sensor history. Back up your Home Assistant database/configuration first, confirm every target entity ID explicitly in **Developer Tools -> States** and **Developer Tools -> Statistics**, and target only verified bench entities.

---

## 3. Pre-Test Setup: COM Port Detection & RS485 Wiring

### Step 1 — Positively Identify the USB-RS485 Adapter COM Port on Windows

> **PORT IDENTIFICATION RULE**: `srne_modbus_simulator.py` never auto-selects any port. Positively identify the dedicated USB-RS485 adapter COM port via unplug/replug comparison and Windows Device Manager before passing `--port`. Any positively identified USB-RS485 adapter COM port is acceptable; avoid guessing ports shared by USB-UART/JTAG flashing cables.

1. Keep the USB-RS485 adapter **unplugged** initially and list existing ports in PowerShell:
   ```powershell
   .\.venv-simulator\Scripts\python.exe -m serial.tools.list_ports -v
   ```
2. Plug in the dedicated **USB-RS485 adapter** and re-run:
   ```powershell
   .\.venv-simulator\Scripts\python.exe -m serial.tools.list_ports -v
   ```
3. Positively identify the **newly appeared** USB-RS485 COM port in both the `list_ports -v` diff and Device Manager -> **Ports (COM & LPT)** (confirming the adapter chipset such as FTDI / CH340 / CP210x). Let `<ADAPTER_COM>` denote this verified port.
4. Run an offline sanity check (zero serial access) before opening `<ADAPTER_COM>`:
   ```powershell
   .\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --validate-only --interactive --scenario S1_solar_charging
   ```

### Step 2 — Physical RS485 Wiring, Isolation & Termination Check

1. **De-energize and disconnect all power sources** (unplug Waveshare USB-C power and keep the USB-RS485 adapter disconnected) before touching terminal screws or changing any RS485 wiring.
2. **Two-wire isolated RS485 connection (`A+` / `B-` only)**:
   - On the **Waveshare ESP32-S3-RS485-CAN-U (`SKU 34781`)**, the isolated communication terminal strip exposes ONLY `A+`, `B-`, `CAN-H`, and `CAN-L` — it has **no isolated RS485 `GND` terminal**.
   - Wire ONLY the differential pair between the USB-RS485 adapter and the Waveshare RS485 terminals:
     - USB-RS485 **`A+` / `D+`** <-> Waveshare **`A+`** (`RS485 A+`)
     - USB-RS485 **`B-` / `D-`** <-> Waveshare **`B-`** (`RS485 B-`)
   - **Galvanic isolation warning**: Never connect the USB-RS485 adapter's `GND` to the Waveshare **`7–36V DC (-)`** power input terminal. Doing so bypasses the onboard galvanic isolation barrier and risks ground loops or hardware damage.
   - Never short `A+` to `B-`, and never tie `5V`/`VCC` pins between the USB-RS485 adapter and the Waveshare board.
3. **Vendor `A/B` vs. `D+/D-` polarity warning**: Not all USB-RS485 adapter vendors label `A`/`B` and `D+`/`D-` with the same differential polarity convention. Check your adapter's datasheet and verify continuity while disconnected before powering on. If zero Modbus requests arrive in Step 4, completely de-energize and disconnect power before swapping `A+` and `B-` once.
4. **Termination & signal integrity (`Component No. 16`)**:
   - On the Waveshare `ESP32-S3-RS485-CAN-U`, **Component No. 16** is the selectable internal RS485 termination jumper (`NC` = onboard termination disconnected; `120R` = onboard `120 Ω` termination enabled). Leave **Component No. 17** (CAN-only termination) untouched.
   - The physical factory jumper position on an uninspected board is **unverified until physically inspected** with all equipment completely unpowered. Inspect **Component No. 16** and your USB-RS485 adapter datasheet before powering on.
   - **Explicit prohibition**: Do **not** add an external discrete `120 Ω` termination resistor across the Waveshare `A+`/`B-` terminals when onboard `120R` termination is enabled.
   - Distinguish **RS485 impedance-mismatch signal reflections** (addressed by proper `120 Ω` end-of-bus termination) from **electromagnetic interference (EMI)** (addressed by twisted-pair wiring and physical separation from switching supplies and AC mains).
5. **Strict separation from future physical inverter wiring**: Keep this USB-RS485 synthetic bench harness completely separate from any future physical **SRNE SPI-16K-UP** inverter connection (which uses the inverter's dedicated **`WiFi Port 1`** interface). See [`docs/INSTALLATION.md`](../docs/INSTALLATION.md) and the Universal Inverter Flow SRNE guide (`https://github.com/quky/universal-inverter-flow/blob/main/docs/inverters/srne-spi-16k-up.md`).
6. **Independent regulated `5V` USB-C power**: Power the Waveshare ESP32-S3 cleanly through its regulated **`5V` USB-C** port (board boots into disconnected polling attempting `FC03` every `10s`).

---

## 4. Sequential Bench Execution Procedure

### Step 3 — Start the Simulator in Interactive Mode

Confirm Section 2 (Home Assistant entity IDs verified and Recorder/staging protection active) **before** launching this command in a dedicated PowerShell terminal (substituting your verified `<ADAPTER_COM>`):

```powershell
.\.venv-simulator\Scripts\python.exe scripts\srne_modbus_simulator.py --port <ADAPTER_COM> --scenario S1_solar_charging --interactive --log-level INFO
```

**Verify immediately**:
- Startup banner displays `SYNTHETIC SRNE SIMULATOR — NOT A PHYSICAL INVERTER`.
- Serial config reads `port=<ADAPTER_COM>  9600,N,8,1  (Modbus RTU)`, Device Address `1 (0x01)`, `40 approved FC03 groups / 107 unique words`, `Failure Injection: OFF by default`.

### Step 4 — Verify Initial Normal Communication & Polarity

1. Observe the simulator console for incoming `Modbus request OK dev=1 fc=0x03 (3) ... outcome=OK` lines (preliminary startup observation estimate: typically within ~10–15 seconds on a healthy link; not a guaranteed deadline).
   - **If zero requests appear** after ~20–30 seconds: verify `<ADAPTER_COM>` is the positively identified USB-RS485 adapter and not opened by another app, quit simulator (`q`), **de-energize and disconnect ESP32 USB-C power and the USB-RS485 adapter**, swap the `A+` and `B-` leads once, restore power, and restart Step 3.
2. **Wait for actual successful polling and Home Assistant state publication before advancing to Step 5**:
   - Confirm Phase 1 sweeps complete cleanly on the simulator console (`P1-R01`..`P1-R16` logging `outcome=OK`) and verified HA entity `srne_modbus_communication_health` (`binary_sensor.*`) transitions from `off` to **`on`**.
   - Preliminary observation estimates: Phase 2 dynamic groups (`D01`–`D12`, boot stagger `5.5s–13.75s`) normally begin logging `outcome=OK` within ~15–20 seconds after boot/health recovery, and staggered static identification groups (`S01`–`S12`, boot stagger `15.5s–70.5s`, `>= 2000ms` spacing) normally register `outcome=OK` within ~75–90 seconds. **Confirm actual `outcome=OK` logs and populated HA states for all 73 entities before proceeding.**

### Step 5 — Validate Phase 1 (36) & Phase 2 (37) Public Entities Under `S1_solar_charging`

Verify all **73 public entities** in Home Assistant (under their verified `sensor.*` [`71`] and `binary_sensor.*` [`2`] entity IDs) are populated and match [`tests/fixtures/srne-expected-entities.json`](fixtures/srne-expected-entities.json) (`S1_solar_charging`). Note: **`73` total** = `35` in `srne-phase1-monitoring.yaml` + `1` local `srne_uptime` in `srne-bench-test.yaml` (`36` Phase 1) + `37` in `srne-phase2-diagnostics.yaml`.

| Internal ESPHome ID | Phase & YAML File | ESPHome Entity Type (-> HA Domain) | Expected Value (`S1_solar_charging`) | Verification Focus |
| --- | --- | --- | --- | --- |
| `srne_modbus_communication_health` | P1 (`phase1`) | `binary_sensor` (`binary_sensor.*`) | `ON` (`true`) | Complete-sweep-gated health |
| `srne_uptime` | P1 (`bench YAML`) | `sensor` (`sensor.*`, local) | Increasing (`s`) | Stays online during Modbus loss |
| `srne_operating_mode` | P1 (`phase1`) | `text_sensor` (`sensor.*`) | `Inverter operation` | Enum `0x0210 = 3` |
| `srne_fault_status` | P1 (`phase1`) | `binary_sensor` (`binary_sensor.*`) | `OFF` (`false`) | `0x0204..0x0207 = 0` |
| `srne_battery_soc` | P1 (`phase1`) | `sensor` (`sensor.*`) | `74 %` | `0x0100 = 74` |
| `srne_battery_voltage` | P1 (`phase1`) | `sensor` (`sensor.*`) | `53.6 V` | Scale `0.1` (`0x0101 = 536`) |
| `srne_battery_current` | P1 (`phase1`) | `sensor` (`sensor.*`) | `-85.0 A` | **Signed16 negative** (`0xFCAE`) |
| `srne_battery_net_power` | P1 Calc (`phase1`) | `sensor` (`sensor.*`) | `-4556.0 W` | Negative = charging |
| `srne_battery_charging_power` | P1 Calc (`phase1`) | `sensor` (`sensor.*`) | `4556.0 W` | Derived charging power |
| `srne_battery_discharging_power` | P1 Calc (`phase1`) | `sensor` (`sensor.*`) | `0.0 W` | Clamped at `0` |
| `srne_pv_total_power` | P1 Calc (`phase1`) | `sensor` (`sensor.*`) | `8428 W` | `4312 + 4116` (`PV1 + PV2`) |
| `srne_output_total_power` | P1 Calc (`phase1`) | `sensor` (`sensor.*`) | `3450 W` | Inverter LOAD/UPS `1750 + 1700` (`L1 + L2`) |
| `srne_inverter_temperature` | P1 (`phase1`) | `sensor` (`sensor.*`) | `42.5 °C` | Heatsink B (`0x0221`) |
| `srne_bms_voltage` | P2 Dyn (`phase2`) | `sensor` (`sensor.*`) | `53.5 V` | `D04` (`0x0112`) |
| `srne_ambient_temperature` | P2 Dyn (`phase2`) | `sensor` (`sensor.*`) | `28.4 °C` | `D10` (`0x0223`) |
| `srne_battery_charging_status` | P2 Dyn (`phase2`) | `text_sensor` (`sensor.*`) | `Quick charge` | Enum `0x010B = 1` |
| `srne_product_type` | P2 Stat (`phase2`) | `text_sensor` (`sensor.*`) | `Controller-Inverter Integrated Unit` | `S01` (`0x000B = 4`) |
| `srne_protocol_version` | P2 Stat (`phase2`) | `text_sensor` (`sensor.*`) | `raw 204 (0x00CC)` | Ambiguity preserved verbatim |
| `srne_software_build_time` | P2 Stat (`phase2`) | `text_sensor` (`sensor.*`) | `2025-11-15 10:30:00` | Lower-8-bits/word masking |
| `srne_product_serial_number` | P2 Stat (`phase2`) | `text_sensor` (`sensor.*`) | `SYNTH-SPI16K-0001` | Lower-8-bits/word masking + NUL trim |

### Step 6 — Switch Across All Five Operating Scenarios (`1`–`5`)

> **Snapshot & Sweep Boundaries (`C26`)**:
> - Each individual simulator `FC03` response is served from one consistent scenario snapshot.
> - Switching scenarios mid-sweep can temporarily mix old and new scenario values across register groups until subsequent full sweeps complete.
> - Phase 1 uses **complete-sweep-gated publication** (`srne_phase1_mask == 0xFFFF`), **not** guaranteed cross-entity atomic Home Assistant database commits; Home Assistant entity state updates across multiple entities are not guaranteed to form one atomic transaction.
> - **Advancement rule**: Preliminary observation estimate after switching scenarios is `>= 35 s` (`10s` Phase 1 + `30s` nominal Phase 2 dynamic), **not** a guaranteed deadline — wait until you observe successful simulator `outcome=OK` cycles for `P1` and `D01`–`D12` **and** settled entity values in Home Assistant before advancing.

Switch sequentially (`2`, `3`, `4`, `5`, then back to `1`) and verify settled reference values from [`srne-expected-entities.json`](fixtures/srne-expected-entities.json):

| Key | Scenario | Observation Gate *(Estimate + Verified Settlement)* | Key Settled HA Values |
| --- | --- | --- | --- |
| `2` | `S2_battery_discharging` | `~35+ s` **and** verified settled P1 + P2 dynamic polls | Mode=`Inverter operation`, SOC=`52 %`, Bat Current=`+75.0 A`, Net Power=`+3840.0 W`, Discharging=`3840.0 W`, Charging=`0.0 W`, PV Total=`0 W`, Output Total=`3470 W`, Charging Status=`Charge off` |
| `3` | `S3_utility_zero_solar` | `~35+ s` **and** verified settled P1 + P2 dynamic polls | Mode=`Utility operation`, SOC=`35 %`, Bat Current=`-30.0 A`, Charging Power=`1572.0 W`, PV Total=`0 W`, Output Total=`2420 W`, Utility Charging I=`30.0 A`, Charging Status=`Const voltage charge`, Password=`User password entered` |
| `4` | `S4_standby` | `~35+ s` **and** verified settled P1 + P2 dynamic polls | Mode=`Standby`, SOC=`100 %`, Bat Current=`0.0 A`, Output Total=`0 W`, Charging Status=`Full`, Grid Countdown=`60 s`, **Ambient Temp=`-2.5 °C`** (negative `s16` check!) |
| `5` | `S5_active_fault` | `~35+ s` **and** verified settled P1 + P2 dynamic polls | Mode=`Standby`, **`srne_fault_status = ON`**, SOC=`18 %`, Bat V=`47.2 V`, Inverter Temp=`82.1 °C`, Ambient=`41.0 °C`, Password=`Manufacturer password entered` |
| `1` | `S1_solar_charging` | `~35+ s` **and** verified settled P1 + P2 dynamic polls | Returns smoothly to Step 5 baseline values |

Run `s` in simulator console and confirm `Scenario Switch Count: 5`.

### YAML-Verified Publication, Invalidation & Backoff Reference (Steps 7–10)

The deployed firmware in [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml), [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml), and [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) implements these exact entity counts and behaviors (`C22`):

- **Phase 1 (`36` public entities: `35` in Phase 1 package + `1` local uptime in bench YAML)**:
  - Hub/app timing: `10s` poll interval, `send_wait_time: 300ms` (hub response timeout), `turnaround_time: 200ms` (provisional inter-transaction delay), `srne_phase1_response_deadline_ms: 1000` (`100ms` application guard), `on_offline` invalidation, and `3 × 10s = 30s` freshness threshold.
  - **Complete-sweep-gated publication (`srne_phase1_mask == 0xFFFF`)**: Publishes all **34** Modbus-derived Phase 1 entities (`32` numeric `sensor` [`27` direct + `5` calculated] + `1` `srne_fault_status` + `1` `srne_operating_mode`) plus `srne_modbus_communication_health = ON` only after all 16 groups succeed in the same sweep.
  - **`srne_phase1_invalidate` (`35` entities affected; `1` local entity excluded)**:
    - `srne_modbus_communication_health` -> **`OFF` (`false`)** (`1` entity)
    - `srne_fault_status` -> **`unavailable`** via `.invalidate_state()` (`1` entity)
    - `srne_operating_mode` -> literal text string **`"Unavailable"`** under HA `sensor.*` (`1` entity)
    - **`32` Phase 1 Modbus numeric sensors** (including all `5` calculated sensors) -> **`unavailable`** via `NAN` (`32` entities)
    - **`srne_uptime`** (`1` local `platform: uptime` entity in `srne-bench-test.yaml`) -> **excluded from Modbus invalidation**; remains available and incrementing continuously.
- **Phase 2 (`37` public entities across `24` groups: `26` numeric `sensor` + `11` `text_sensor`)**:
  - Nominal poll / `3×` freshness thresholds (nominal schedules, not guaranteed intervals): dynamic `D01`–`D12` = `30s` / `90s`; slow config `S08` (`0xE037`) = `300s` / `900s`; static `S01`–`S07`, `S09`–`S12` = `3600s` / `10800s`; application watchdog = `2000ms`; static spacing = `2000ms`.
  - **`srne_p2_invalidate_group` (per-group across `26` numeric + `11` text)**: Numeric sensors publish `NAN` (HA `unavailable`); `text_sensor` entities publish literal `"Unavailable"` (HA `sensor.*`).
  - **Stepped, bounded backoff (`srne_p2_handle_failure`)**:
    - Timeout (`on_no_response`, `retry: false`) / malformed (`on_custom_response`) / `2000ms` watchdog: fast groups (`D01`–`D12`, `S08`) `3s -> 60s -> 120s -> 300s`; static groups `5s -> 300s -> 900s -> 3600s`.
    - Modbus exception (`on_error`, skips immediate retry, sets `srne_p2_exc_fail[g]`): fast groups `60s -> 120s -> 300s`; static groups `3600s`.
    - `on_not_sent`: `5s -> 30s -> 60s -> 300s`.
  - **Phase 2 recovery edge**: Fast rescheduling (`now + 2000ms` base + `+750ms` dynamic / `+2500ms` static stagger) fires **ONLY** when `srne_modbus_communication_health` transitions **`OFF -> ON`**, and **ONLY** for non-exception failed groups (`!srne_p2_exc_fail[g]`).

### Step 7 — Selective Diagnostic Failures (`P2-D04`, `P2-D05` / `bms`)

> **BACKOFF & SETTLEMENT WARNING (`C23`)**: Because Phase 1 stays `ON` during selective Phase 2 faults, typing `n` does **not** trigger the `OFF -> ON` recovery edge or immediately reset Phase 2 backoff. Total recovery time after typing `n` equals **remaining scheduled backoff delay + cooperative scheduler wait (`250ms`/yields) + successful `FC03` transaction + HA entity publication time** (preliminary estimate: `3s` after fail 1, `~60–120s+` after fails 2–3 or exceptions `1–2`, up to `~300s+` after 4+ timeouts / 3+ exceptions on dynamic/`S08`, or `~3600s+` if a static group hit an exception).

1. Type `f gtimeout bms` in the simulator console (silences `P2-D04` and `P2-D05` only).
2. Observe (preliminary estimate `~60–90 s`, **and** confirm `INJECTED ... mode=SELECTIVE_TIMEOUT groups=P2-D04` / `P2-D05` in simulator logs before judging HA state):
   - `P1-R01`..`P1-R16` and unaffected `P2` groups continue logging `outcome=OK`.
   - `srne_modbus_communication_health` **MUST remain `ON`**.
   - Switch scenario `1 -> 2` mid-fault and wait for settled Phase 1 + unaffected `P2-D10` updates in HA while verifying `srne_bms_voltage` (`D04`) and `srne_bms_temperature`..`srne_bms_discharge_current_limit` (`D05`) report `unavailable` (never `0`).
3. Type `n` to restore normal communication, then wait through the **remaining backoff window + scheduler/transaction/HA publication time** until you observe actual `outcome=OK` polls for `P2-D04`/`P2-D05` and settled BMS values in Home Assistant before advancing.
4. Type `f exc P2-D05 0x02` and observe until you confirm injected `0x02` responses and `D05` invalidation in HA (preliminary estimate `~45–60 s`) while Phase 1 remains `ON`. Note `on_error` enters `60s` immediate exception backoff on fail 1. Type `n` and wait for **remaining exception backoff (`60s`/`120s`/`300s`) + scheduling + successful `D05` poll/HA publication** before advancing to Step 8.

### Step 8 — Complete Communication Loss (`f timeout`)

1. Type `f timeout` in the simulator console.
2. Observe until all invalidation conditions settle (preliminary observation estimate `~45–60 s`, not a guaranteed deadline):
   - All `FC03` requests log `mode=SILENT_TIMEOUT (no reply sent)`.
   - Phase 1 invalidates on failure (within `~1–2 s` after next poll hits `1000ms` guard / hub `on_offline`, and by the `30s` freshness bound): **`35` entities affected** (`srne_modbus_communication_health = OFF`, `srne_fault_status = unavailable`, `srne_operating_mode` literal `"Unavailable"`, and **`32` Modbus numeric sensors = `unavailable`**).
   - **`1` local entity (`srne_uptime`) MUST remain available and keep incrementing**.
   - Phase 2 groups invalidate **individually** as each due poll fails or crosses its `3×` freshness threshold (`90s` dynamic / `900s` `S08` / `10800s` static) — not simultaneously with Phase 1.

### Step 9 — CRC Corruption & Truncated Frames (`f crc`, `f trunc`)

1. Restore normal first (`n`) and **confirm `srne_modbus_communication_health = ON` and settled dynamic recovery** before proceeding, then type `f crc` (global) or `f crc P1-R01`.
2. Observe (`~35+ s` preliminary estimate until invalidation confirms): ESPHome rejects corrupted CRC frames cleanly without publishing bogus/zeroed measurements; global/`P1-R01` invalidates the `35` Phase 1 Modbus/health entities (`srne_uptime` remains online).
3. Type `n`, **confirm `srne_modbus_communication_health = ON` and settled recovery**, then type `f trunc` (global) or `f trunc P2-D05`.
4. Observe (`~35–45+ s` preliminary estimate until settled): ESPHome rejects truncated frames cleanly without crash or hang. Under `f trunc P2-D05`, Phase 1 remains `ON`, only `P2-D05` invalidates, and post-`n` recovery requires remaining backoff + scheduling + successful `D05` poll/publication.

### Step 10 — Automatic ESPHome Recovery (After Full Outage)

1. Following global failure (`f timeout`, `f crc`, or `f trunc`), type `n` in the simulator console (without rebooting ESP32 or restarting simulator).
2. Observe and confirm actual completion before advancing (`~25–45 s` preliminary observation estimate for full Phase 1 + dynamic recovery, not a guaranteed deadline):
   - Confirm Phase 1 completes a valid 16-group sweep (`outcome=OK`) and `srne_modbus_communication_health` returns **`ON`**.
   - That `OFF -> ON` transition triggers Phase 2's recovery edge for non-exception failed groups (`now + 2000ms` + stagger + cooperative scheduling + HA publication).
   - Any group carrying a prior Modbus exception (`srne_p2_exc_fail[g]`) recovers only after **its remaining exception backoff + scheduling + successful transaction/HA publication time** (`s` shows `Active Failure Mode: normal`).

### Step 11 — Polling Cadence & Analytical Occupancy Comparison

Understand exact timing boundaries from [`docs/MODBUS-REFERENCE.md`](../docs/MODBUS-REFERENCE.md) and [`audits/SRNE-04G-R1-Architecture-Correction.md`](../audits/SRNE-04G-R1-Architecture-Correction.md) (`C24`):

- **Measured request cadence vs. calculated scheduling occupancy vs. electrical wire activity**:
  - Simulator console timestamps measure **inter-request arrival cadence** (`P1` ~10 s sweep cadence, `P2` dynamic ~30 s nominal cadence). They do **not** independently measure electrical RS485 bus utilization or slave response latency (`T_resp`).
  - The percentages below (`9600,N,8,1`, provisional `turnaround_time: 200ms`) are **calculated transaction scheduling occupancy** and **available scheduling headroom** — they include assumed slave latency (`T_resp`) plus configured hub turnaround delays (`200ms + 3.65 ms`) and are **not direct electrical wire measurements**:
    - `0–100 ms` assumed `T_resp`: **44.3%–64.3%** combined `30s` scheduling occupancy (**35.7%–55.7%** scheduling headroom; Phase 1 alone `35.4%–51.4%`).
    - `50 ms` nominal assumed `T_resp`: **54.3%** combined `30s` occupancy (`54.4%` 1-hr avg; **45.7%** headroom; Phase 1 alone `43.4%`).
    - `250 ms` (**illustrative analytical high-latency condition**, not a verified worst-case hardware limit): **94.3%** combined `30s` occupancy (**5.7%** headroom; Phase 1 alone `75.4%`, with Phase 2 yielding dynamically via queue availability, Phase 1 flags, and the `700ms` guard).

Run normal communication (`S1_solar_charging`, `--log-level INFO`) cleanly for **3 full minutes** (`180 s`):
- Verify measured simulator timestamps maintain clean **~10 s** Phase 1 cadence and cooperative **~30 s** Phase 2 dynamic cadence without stalling, collisions with `send_wait_time: 300ms` / `turnaround_time: 200ms`, watchdog resets, heap errors, or normal-mode CRC failures (`s` -> `Invalid CRC Frames: 0`).
- Type `q` in simulator console to verify clean graceful shutdown (serial port released cleanly).

---

## 5. Evidence Collection & Formal PASS / FAIL Acceptance Criteria

Record and archive under a dedicated bench evidence report (`SRNE-03V`):
1. Adapter identity + positively identified USB-RS485 COM port proof (`serial.tools.list_ports -v` unplug/replug diff + Device Manager; any positively identified USB-RS485 port is acceptable), verified unpowered **Component No. 16** termination jumper inspection (`NC` vs `120R`), and two-wire `A+`/`B-` wiring confirmation (zero `GND` bridge to `7–36V DC (-)`).
2. Pre-traffic Home Assistant protection proof: actual verified `sensor.*` (`71`) and `binary_sensor.*` (`2`) IDs from **Developer Tools -> States**, plus staging HA or verified `recorder` exclusion confirmation recorded *before* Step 3 (and optional/conditional cleanup confirmation only if synthetic data was recorded to a shared instance).
3. Simulator console capture showing startup banner, verified `outcome=OK` normal `P1`/`P2` cycles, all 5 transitions (`s` status), fault injections (`f status`), recovery (`n`), 3-minute measured request cadence timestamps, and `q` shutdown.
4. ESPHome UART/Modbus logs covering normal polling, selective timeout/exception stepped backoff, full timeout invalidation (`35` Phase 1 entities invalidated + `srne_uptime` staying online), CRC/truncation rejection, and automatic recovery.
5. Home Assistant settled entity snapshots across `S1`–`S5` (verifying negative currents, `-2.5 °C` ambient temp, lower-8-bit strings, `srne_fault_status`, literal `"Unavailable"` text sensors vs `unavailable` numeric/`binary_sensor` states).

### Go / No-Go Acceptance Gate

| Criterion | PASS Requirement | FAIL Trigger |
| --- | --- | --- |
| Physical RS485 Wiring & RTU Link | Positively identified USB-RS485 port, isolated two-wire `A+`/`B-` wiring (no DC `(-)`/`GND` bridge), unpowered `Component No. 16` inspection, independent `5V` USB-C power, and stable `9600,N,8,1` `FC03` traffic at provisional `200ms` turnaround with `0` normal-mode framing errors | Ground/isolation bridge, duplicate external `120 Ω` resistor over enabled `120R` termination, persistent timeouts, normal-mode CRC errors, or garbled frames |
| Settled Entity Accuracy (`S1`–`S5`) & HA Hygiene | Simulator traffic stayed OFF until actual `sensor.*`/`binary_sensor.*` IDs and Recorder protection were verified; after settled sweeps, all `73` public entities (`59` numeric [`58` Modbus + `1` local], `2` binary, `12` text) match `srne-expected-entities.json` without production LTS pollution | Synthetic data polluted production LTS, or settled entity values show address shifts, sign inversions, broken string masks, or missing entities |
| Fault Isolation & Stepped Backoff | `f gtimeout bms` / `f exc` keeps `srne_modbus_communication_health = ON` and Phase 1 unaffected; isolated Phase 2 groups follow YAML stepped bounded backoff (`3s/60s/120s/300s` or `60s/120s/300s` exception) | Selective Phase 2 fault drops Phase 1 freshness, stalls polling, or zeroes invalid sensors |
| Complete-Sweep Invalidation & Exclusions | `f timeout`, `f crc`, `f trunc` invalidate **`35`** Phase 1 entities cleanly (`health = OFF`, `srne_fault_status = unavailable`, `srne_operating_mode` = literal `"Unavailable"`, `32` numeric sensors = `unavailable`), exclude `srne_uptime` (stays online/incrementing), and invalidate Phase 2 individually on failure/`3×` freshness | Entities fall back to `0`, `srne_uptime` invalidates incorrectly, or ESP32 reboots/hangs |
| Verified Recovery After Settled Delays | Following `n`, Phase 1 recovers after completing a `16`-group sweep, `OFF -> ON` fast-reschedules non-exception failed Phase 2 groups, and selective/exception-backoff groups recover after remaining backoff + scheduling + successful poll + HA publication without ESP32 or simulator reboot | Requires manual ESP32 reset or port reopen to resume, or backed-off groups fail to recover after remaining backoff + scheduling window |
| Measured Request Cadence Stability | 3-minute normal run maintains stable **~10 s** Phase 1 and cooperative **~30 s** Phase 2 measured request cadence from simulator timestamps (distinct from calculated occupancy / electrical bus activity) with zero watchdog/heap errors or dropped sweeps (`> 30s`) | Bus collisions, overflowing queues, stale Phase 1 sweeps (`> 30s`), or watchdog/heap resets |

Only after **all 6 criteria PASS** should physical RS485 connection planning for the real **SRNE SPI-16K-UP** inverter begin.
