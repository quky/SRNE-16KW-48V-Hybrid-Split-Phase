# Installation & Hardware Setup Guide

> [!CAUTION]
> **Physical Inverter Connection Pending Validation**
> The ESPHome configuration in this repository has been compiled under **ESPHome `2026.11.1`**, verified disconnected in Home Assistant, and tested offline against synthetic fixtures covering the implemented register subset (`SRNE-04E-H`). **Physical installation and telemetry validation on a live SRNE SPI-16K-UP inverter remain pending.** Always isolate power safely and verify every wire and continuity check before energizing hardware.

This guide explains how to prepare the Waveshare gateway, configure ESPHome secrets, deploy the modular YAML configuration, and verify entities in Home Assistant. For illustrated wiring diagrams, SVG callouts, and component photographs/sketches, refer to the authoritative **Universal Inverter Flow** guides rather than duplicating them here:

- [Illustrated SRNE `SPI-16K-UP` Hardware Installation Guide](https://github.com/quky/universal-inverter-flow/blob/main/docs/inverters/srne-spi-16k-up.md)
- [Illustrated Hardware Bill of Materials](https://github.com/quky/universal-inverter-flow/blob/main/docs/hardware/bill-of-materials.md)
- [Standalone ESPHome & Dashboard Examples](https://github.com/quky/universal-inverter-flow/tree/main/docs/examples/srne)

---

## 1. Required Hardware & Power Safety Rules

- **Gateway**: **Waveshare `ESP32-S3-RS485-CAN-U`** (`SKU 34781`, external `2.4 GHz` antenna variant; `16 MB` Flash, onboard `TX=GPIO17`, `RX=GPIO18`, RS485 flow control `GPIO21`).
  - **Attach the external `2.4 GHz` antenna before applying power** to avoid RF stage damage and poor Wi-Fi connectivity.
- **Power Supply**: Use an **independent, regulated, region-certified `5 V` USB-C power supply** plugged into the Waveshare USB-C port for steady-state operation.
  - **Do NOT power the board from SRNE `Pin 1 (5V)`** without independently verifying continuous current capacity and electrical isolation compatibility.
  - **Do NOT connect the Waveshare gateway directly to a `48 V` battery bank** (even the board's separate screw power input is rated only for `7–36 V DC`). Leave the `7–36 V DC` block disconnected when powering via USB-C.
- **Initial Programming Cable**: A verified **USB-C data + power cable** (`USB_SERIAL_JTAG`) for first-time firmware flashing (disconnect after Wi-Fi + OTA provisioning succeeds).
- **RS485 Cable**: Standard straight-through **CAT5e / CAT6 patch cable** with one factory RJ45 plug inserted into **SRNE WiFi Port 1** and the opposite end cut and stripped for screw terminals.

---

## 2. Two-Wire RS485 Wiring & Mandatory Continuity Checks

### Port & Pinout (`WiFi Port 1` Only)

Insert the factory RJ45 plug strictly into **SRNE `WiFi Port 1`** (never plug into the lithium BMS `RS485/CAN` port or `Meter/CT/PAR` port, which carry incompatible electrical signals).

Both **T568A** and **T568B** Ethernet patch cables assign identical colors to `Pins 7 & 8`:

| RJ45 Pin (`WiFi Port 1`) | SRNE Manual Signal | T568A / T568B Color | Waveshare Terminal | Action |
| ---: | --- | --- | --- | --- |
| **1** | `5V` | White/Orange *(or T568A diff)* | — | Trim & **individually insulate** |
| **2** | `GND` | Orange *(or T568A diff)* | — | Trim & **individually insulate** (2-wire RS485 only) |
| **3–6** | Unused | — | — | Trim & **individually insulate each conductor** |
| **7** | **`RS485-A`** | **White / Brown** | **`A+`** | Land on Waveshare **`A+`** |
| **8** | **`RS485-B`** | **Brown** | **`B−`** | Land on Waveshare **`B−`** |

> [!WARNING]
> **Never Connect Communication `GND` to Waveshare `7–36 V DC (−)`**
> The Waveshare isolated communication strip contains **only `A+`, `B−`, `CAN-H`, and `CAN-L`** — there is **no isolated RS485 `GND` terminal**. The `−` (`GND`) screw on the separate `7–36 V DC` power terminal is the board's power return, **not** an isolated RS485 signal ground. Keep `Pin 2 (GND)` disconnected and insulated in this two-wire setup.

### Selectable RS485 Termination Jumper (`Component No. 16`)

- Inside the Waveshare enclosure, **Component No. 16** selects the internal `120 Ω` RS485 termination (`NC` = disconnected vs. `120R` = enabled), and **Component No. 17** controls CAN termination (leave untouched).
- **Physical factory jumper position is unverified**: Do not assume whether `Component No. 16` ships set to `NC` or `120R`. De-energize completely and unplug all power/cables before opening the enclosure to inspect `Component No. 16` using the [Waveshare Wiki](https://www.waveshare.com/wiki/ESP32-S3-RS485-CAN).
- **Prohibition on duplicate endpoint termination**: Do **not** add an external discrete `120 Ω` termination resistor across the Waveshare `A+`/`B−` terminals when onboard `120R` termination (`Component No. 16`) is enabled. (Distinguish proper `120 Ω` end-of-bus impedance matching for signal reflections from EMI mitigation via twisted-pair wiring and physical routing separation.)

### Mandatory Disconnected Multimeter Verification

Before connecting either end of the prepared cable to hardware, perform every measurement **with the prepared cable completely disconnected from both the inverter and the Waveshare board** (and with all equipment unpowered):

1. Verify **individual insulation** on all unused conductors (`Pins 1–6`, including `Pin 1 = 5V` and `Pin 2 = GND`) using heat-shrink tubing or sealed wire caps.
2. Check **continuity** from **RJ45 Pin 7** to the **`White / Brown`** lead (`A+`).
3. Check **continuity** from **RJ45 Pin 8** to the **`Brown`** lead (`B−`).
4. Verify **open circuit (`OL`)** between `A+` and `B−`, and between `A+`/`B−` and **all unused conductors (`Pins 1–6`)**. *(Connected `120 Ω` termination resistors on an attached inverter or Waveshare board can legitimately produce finite resistance readings across `A+` and `B−`; always test the cable disconnected.)*

For step-by-step illustrated RJ45 orientation and wiring checks, see the [Universal Inverter Flow SRNE Hardware Guide](https://github.com/quky/universal-inverter-flow/blob/main/docs/inverters/srne-spi-16k-up.md#3-rj45-pinout-t568at568b-wiring--mandatory-continuity-check).

---

## 3. ESPHome Software Configuration (`2026.11.1`)

### Tested Toolchain & Board Target

- **ESPHome**: Verified under **ESPHome `2026.11.1`** (ESP-IDF framework `5.5.6`).
- **Board**: `esp32-s3-devkitc-1`, `flash_size: 16MB`, `logger: hardware_uart: USB_SERIAL_JTAG`.
- **Modular configuration in this repository (`73` public entities total)**:
  - [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml) — hardware UART (`GPIO17`/`GPIO18`, `9600,N,8,1`), Modbus (`GPIO21`, `send_wait_time: 300ms`, provisional `turnaround_time: 200ms`), **1 local public entity** (`srne_uptime`), Wi-Fi/API/OTA, and includes both packages below:
  - [`esphome/packages/srne-phase1-monitoring.yaml`](../esphome/packages/srne-phase1-monitoring.yaml) — **35 public entities** (`32` numeric `sensor` + `2` `binary_sensor` + `1` `text_sensor`; `16` `internal: true` raw readers excluded) + `16` `FC03` groups (`32` words) (`35 + 1 local uptime = 36 Phase 1 public entities`)
  - [`esphome/packages/srne-phase2-diagnostics.yaml`](../esphome/packages/srne-phase2-diagnostics.yaml) — **37 public entities** (`26` numeric `sensor` + `11` `text_sensor`; `24` cooperative `FC03` groups / `75` words)
- *(Alternative single-file deployment)*: If you prefer a self-contained YAML outside this repo's modular package layout, see [Universal Inverter Flow's `srne-esp32-esphome.yaml`](https://github.com/quky/universal-inverter-flow/blob/main/docs/examples/srne/srne-esp32-esphome.yaml).

### Required `esphome/secrets.yaml` Keys (Placeholders Only)

Create `esphome/secrets.yaml` locally (never commit it; it is listed in `.gitignore`) with these four keys derived directly from [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml):

```yaml
wifi_ssid: "YOUR_24GHZ_WIFI_SSID"
wifi_password: "YOUR_WIFI_PASSWORD"
srne_api_key: "YOUR_BASE64_32BYTE_ENCRYPTION_KEY"
srne_ota_password: "YOUR_OTA_PASSWORD"
```

Replace `YOUR_BASE64_32BYTE_ENCRYPTION_KEY` with a valid Base64-encoded 32-byte key (e.g., `openssl rand -base64 32`) before validating or compiling.

### Initial Flash & Home Assistant Integration

1. Attach the external `2.4 GHz` antenna and connect the Waveshare board to your computer via the **USB-C data cable**.
2. Compile and flash using ESPHome CLI or Home Assistant **ESPHome Device Builder** targeting [`esphome/srne-bench-test.yaml`](../esphome/srne-bench-test.yaml).
3. Disconnect the USB-C data cable and power the gateway using the **independent regulated `5 V` USB-C power supply**. Subsequent firmware updates can use Wi-Fi OTA.
4. In Home Assistant (**Settings → Devices & Services → ESPHome**), adopt the device and enter your `srne_api_key` encryption key.
5. Open Home Assistant **Developer Tools → States** and verify the actual assigned entity IDs (e.g., `sensor.srne_bench_test_battery_soc`, `binary_sensor.srne_bench_test_modbus_communication_health`), noting that ESPHome `text_sensor` entities appear under Home Assistant's **`sensor.*`** domain (`text_sensor.*` is not a Home Assistant entity domain) and that entity IDs reflect `friendly_name` (`SRNE Bench Test` in this repo vs. `SRNE Inverter` in UIF's standalone example) and any registry assignments.

---

## 4. Separate Paths: Synthetic Bench Testing vs. Physical Inverter Setup

### Path A — Synthetic RS485 Bench Testing (USB-to-RS485 Simulator)

Use this path to exercise RS485 framing, all 73 entities, scenario switching, and fault/recovery behavior **without** a physical inverter:

1. **Positively identify your USB-to-RS485 adapter port** before wiring or running the simulator (plug/unplug comparison via `serial.tools.list_ports -v` and Windows Device Manager; `srne_modbus_simulator.py` never auto-selects a COM port), then wire only `A+` ↔ `A+` and `B−` ↔ `B−` (no `GND` wired to `7–36V DC (−)`) following [`tests/README.md`](../tests/README.md) and [`tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](../tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md).
2. **Protect Home Assistant Production Statistics BEFORE starting synthetic traffic**:
   - **Keep synthetic simulator traffic disabled** (do not start `srne_modbus_simulator.py --port ...`) until you have verified the node's actual entity IDs under **Developer Tools → States** (`sensor.*` and `binary_sensor.*`; ESPHome `text_sensor` entities use Home Assistant **`sensor.*`**) and verified statistics isolation.
   - **Preferred options**: Test against a **dedicated staging/bench Home Assistant instance**, **or** configure verified `recorder` exclusions targeting the confirmed `sensor.*` and `binary_sensor.*` entity IDs in a shared instance before starting simulator traffic.
   - **Energy Dashboard exclusion is insufficient**: While the four Phase 1 daily energy entities use conservative `state_class: ""`, numeric sensors with `state_class: measurement` **still record Home Assistant Recorder state history and Long-Term Statistics (LTS)** even if omitted from the Energy Dashboard.
   - **Optional, conditional post-test cleanup (destructive action)**: Cleanup is needed **only if** synthetic data was actually recorded into a shared/production Home Assistant database. Running `recorder.purge_entities` or deleting entries in **Developer Tools → Statistics** **permanently and irreversibly deletes** historical state graphs and LTS for any matched entities — back up Home Assistant first and confirm exact verified entity IDs before executing any purge.

### Path B — Future Physical SRNE `SPI-16K-UP` Inverter Connection *(Pending Validation)*

> [!IMPORTANT]
> **Status: Pending Physical Validation.** Do not execute unattended production deployment until initial read-only commissioning on a real **SRNE SPI-16K-UP** verifies `WiFi Port 1` communication, `turnaround_time: 200ms` stability, live BMS/MPPT register availability, and string/enum decoding.

When transitioning from bench tests to physical inverter commissioning:

1. Disconnect any bench USB-to-RS485 adapter completely.
2. De-energize the Waveshare gateway and shut down/isolate the SRNE inverter safely per the manufacturer's manual.
3. With all equipment unpowered, inspect **Component No. 16** termination jumper inside the Waveshare gateway (ensure no duplicate external `120 Ω` resistor is added if `120R` is enabled), then connect the disconnected-verified **WiFi Port 1** cable (`Pin 7` → `A+`, `Pin 8` → `B−`, `Pins 1–6` individually insulated).
4. Restore inverter power according to the **manufacturer's startup procedure** and power the Waveshare gateway via its independent regulated `5 V` USB-C supply **before** verifying live read-only `FC03` polling health in ESPHome logs and Home Assistant or integrating with [Universal Inverter Flow](https://github.com/quky/universal-inverter-flow/tree/main/docs/examples/srne).
