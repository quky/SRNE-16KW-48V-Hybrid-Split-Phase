# SRNE 16kW Split-Phase Hybrid Inverter — ESPHome & Home Assistant

Independent, open-source **strictly read-only (`FC03`)** ESPHome integration and offline Modbus RTU test suite for the **SRNE SPI-16K-UP** 16 kW, 48 V, 120/240 V split-phase hybrid inverter running on a DIN-rail **Waveshare ESP32-S3-RS485-CAN-U** (`SKU 34781`) gateway.

> [!IMPORTANT]
> **Independent Project Disclaimer & Validation Status**
> This project is an independent community integration and is not affiliated with, endorsed by, or supported by SRNE Solar.
> **Physical validation on a live SRNE SPI-16K-UP inverter remains pending.** All register definitions are derived from official manufacturer documentation (`SRNE Modbus Monitoring Protocol V2.04`). Offline automated tests and synthetic RTU simulation cover only the **implemented register mappings** (`40` `FC03` groups / `107` register words / `73` public entities) against deterministic synthetic fixtures — **not** the complete manufacturer register inventory (`1,011` audit entries) and **not** live hardware compatibility. Do **not** assume live hardware compatibility or enable writable inverter controls until physical validation is completed.

---

## Development & Validation Status

Each verification layer below reflects its exact current evidence boundary:

| Validation Stage | Status | Evidence Basis |
| --- | --- | --- |
| Documented Manufacturer Protocol (`SRNE-01B`) | **Completed (Docs)** | Protocol specification, full manufacturer register inventory (`1,011` entries, `A01`–`A25` ambiguities), and write-risk audit in [`audits/`](audits/SRNE-01B-Audit-Summary.md) |
| Software Implementation (Phase 1 + Phase 2) | **Completed (Read-Only FC03)** | [`esphome/srne-bench-test.yaml`](esphome/srne-bench-test.yaml) + modular packages exposing **73 public entities** across the **40 implemented `FC03` groups / 107 register words** |
| ESPHome Config & Compilation | **Verified (`2026.11.1`)** | Config validation, ESP-IDF compilation, and OTA deployment verified in [`audits/SRNE-04G-Implementation-Summary.md`](audits/SRNE-04G-Implementation-Summary.md) |
| Home Assistant Exposure (Disconnected) | **Verified (Disconnected)** | All 36 Phase 1 and 37 Phase 2 public entities (`73` total) verified exposed with deterministic invalidation markers in Home Assistant |
| Offline Synthetic RTU Simulator (`SRNE-04E-H`) | **Completed (`24/24` Historical PASS)** | Standalone PyModbus 3.16.2 simulator validating the **implemented register subset** (`40` groups / `107` words) across 5 scenarios and 6 modes; historical `24/24` offline/in-memory unit tests passed in [`audits/SRNE-04E-H-Final-Offline-Validation.md`](audits/SRNE-04E-H-Final-Offline-Validation.md) |
| External Synthetic RS485 Bench Testing | **Referenced Externally** | Published [Universal Inverter Flow SRNE Examples](https://github.com/quky/universal-inverter-flow/tree/main/docs/examples/srne) state synthetic USB-to-RS485 bench verification |
| Repository-Archived `SRNE-03V` Bench Report | **Pending Execution / Archival** | [Bench Test Procedure](tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md) is finalized; **no executed `SRNE-03V` report is archived in this repository yet** |
| Physical SRNE `SPI-16K-UP` Validation | **Pending (Not Started)** | Zero live inverter telemetry or physical `WiFi Port 1` bus measurements have been collected |

---

## Hardware Requirements

| Role | Component | Key Requirement |
| --- | --- | --- |
| **Inverter** | SRNE `SPI-16K-UP` (16 kW, 48 V, 120/240 V split-phase) | Target monitoring port: **WiFi Port 1 (RJ45)** (`Pin 7 = RS485-A`, `Pin 8 = RS485-B`) |
| **Gateway** | **Waveshare `ESP32-S3-RS485-CAN-U`** (`SKU 34781`, external antenna) | Attach external 2.4 GHz antenna **before** powering; inspect internal `120 Ω` jumper `Component No. 16` unpowered |
| **Power** | Independent regulated **`5 V` USB-C power supply** | Do **not** power from SRNE `Pin 1 (5V)` or connect directly to a `48 V` battery bank |
| **Cable** | Standard CAT5e/CAT6 patch cable (one end stripped) | **Two-wire isolated RS485 only (`A+`/`B−`)**; individually insulate unused `Pins 1–6` (including `Pin 2 = GND`); never land `GND` on DC `−` |
| **Initial Flash** | USB-C data cable (`USB_SERIAL_JTAG`) | Required only for initial wired ESPHome flash; subsequent updates use Wi-Fi OTA |
| **Bench Only** | USB-to-RS485 adapter *(available bench hardware)* | Used on a synthetic development bench with [`scripts/srne_modbus_simulator.py`](scripts/srne_modbus_simulator.py) |

See [`docs/INSTALLATION.md`](docs/INSTALLATION.md) for setup instructions, and refer to Universal Inverter Flow's illustrated hardware documentation:
- [Illustrated SRNE Hardware Guide](https://github.com/quky/universal-inverter-flow/blob/main/docs/inverters/srne-spi-16k-up.md)
- [Illustrated Hardware Bill of Materials](https://github.com/quky/universal-inverter-flow/blob/main/docs/hardware/bill-of-materials.md)

---

## Quick-Start Overview

1. **Review safety & wiring**: Attach the external antenna to the Waveshare `SKU 34781`, inspect termination unpowered, verify two-wire `A+`/`B−` preparation, and prepare an independent `5 V` USB-C supply ([Installation Guide](docs/INSTALLATION.md)).
2. **Add ESPHome secrets**: Create a local `esphome/secrets.yaml` (gitignored) with `wifi_ssid`, `wifi_password`, `srne_api_key`, and `srne_ota_password`.
3. **Compile & flash ESPHome (`2026.11.1`)**: Use [`esphome/srne-bench-test.yaml`](esphome/srne-bench-test.yaml) (includes Phase 1 + Phase 2 packages), or start from the standalone [Universal Inverter Flow SRNE Examples](https://github.com/quky/universal-inverter-flow/tree/main/docs/examples/srne).
4. **Adopt in Home Assistant & protect statistics**: Verify actual assigned entity IDs under **Developer Tools → States** (`sensor.*` and `binary_sensor.*`) and confirm dedicated staging HA or `recorder` exclusions **before** starting any synthetic simulator RS485 traffic ([Installation Guide](docs/INSTALLATION.md#4-separate-paths-synthetic-bench-testing-vs-physical-inverter-setup)).
5. **Offline simulator validation (zero serial access)**: Validate fixtures and inspect CLI usage offline with `--validate-only` (and `--list-scenarios`) per [`tests/README.md`](tests/README.md).
6. **Physical synthetic RS485 bench test (serial port required)**: Positively identify your USB-to-RS485 adapter port, start `scripts/srne_modbus_simulator.py --port COMx --interactive` (substituting your verified port), and follow [`tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md).

---

## Implemented Monitoring & Diagnostics (73 Public Entities)

This repository implements **73 public ESPHome entities** (**36 Phase 1 + 37 Phase 2**) strictly via read-only Modbus `FC03` requests plus one local ESPHome uptime entity (`srne_uptime`) and one runtime sweep-health indicator (`srne_modbus_communication_health`):

- **YAML Type Breakdown**: **59** ESPHome `sensor` entities (`58` Modbus-derived + `1` local `srne_uptime`), **2** `binary_sensor` entities (`srne_fault_status`, `srne_modbus_communication_health`), and **12** `text_sensor` entities (`1` Phase 1 + `11` Phase 2). In Home Assistant, ESPHome `text_sensor` entities appear under **`sensor.*`** (`71` `sensor.*` + `2` `binary_sensor.*`).

| Category | Phase | Count | Highlights |
| --- | --- | ---: | --- |
| **PV Dual-MPPT** | Phase 1 | 7 | PV1/PV2 voltage, current, power, and calculated `Total PV Power` |
| **Battery & Calculated Flow** | Phase 1 | 7 | SOC, voltage, signed current (`+` discharge / `−` charge), temperature, `Battery Net/Charging/Discharging Power` |
| **Split-Phase Grid & Output** | Phase 1 | 13 | Grid L1/L2 voltage & current, grid frequency, Output L1/L2 voltage, current, power, `Total Output Power`, output frequency |
| **Daily Energy Counters** | Phase 1 | 4 | Daily Solar, Load, Battery Charge, and Battery Discharge energy (`kWh`, conservative `state_class: ""`) |
| **Core Status, Health & Uptime** | Phase 1 | 5 | Inverter temperature (Heatsink B), `Fault Status`, `Operating Mode`, `Modbus Communication Health`, plus local `Uptime` (`srne-bench-test.yaml`) |
| **Battery & BMS Diagnostics** | Phase 2 | 10 | Rated/remaining capacity, cycle count, charging status, total charging power, BMS voltage, temperature, and charge/discharge limits |
| **Power Stage, Temps & Counters** | Phase 2 | 16 | Total/+/- DC bus voltages, PV & utility charging currents, Heatsink A/C & ambient temps, grid countdown, password status, daily/cumulative runtime & days |
| **Device Identity & Config (RO)** | Phase 2 | 11 | Product type, APP software & control-board hardware versions, address, model code, protocol version, build time, serial number, rated battery V & operating/parallel/BMS modes (read via `FC03` only) |

Full per-entity details and the YAML-derived matrix are reconciled in [`docs/ENTITIES.md`](docs/ENTITIES.md).

---

## Read-Only Modbus Architecture

- **Protocol**: Official SRNE Modbus Monitoring Protocol V2.04 basis (`9600,N,8,1`, slave `0x01`, **FC03 Read Holding Registers only**).
- **Packet sizing**: Implemented maximum request length is **20 words** (`0x0021` / `0x0035`), within the manufacturer V2.04 maximum of **32 words** per transaction.
- **Implemented register footprint**: **40 `FC03` register groups** covering **107 unique register words** (**16 Phase 1 readers / 32 words** at `10s`; **24 Phase 2 cooperative dispatch groups / 75 words** at `30s` dynamic / `300s` mode / `3600s` static).
- **Zero write operations (`FC06`/`FC16`)**: Write commands and writable ESPHome controls (`number`, `select`, `switch`, `button`) are excluded. Four manufacturer-designated `RW` configuration registers (`0xE003`, `0xE037`, `0xE201`, `0xE215`) are read strictly via `FC03`.
- **Shared-bus safeguards**: Single `modbus_controller` for Phase 1 (`10s` sweep priority, `30s` freshness invalidation, complete-sweep-gated publication) paired with a cooperative single-in-flight `modbus_client.read_holding_registers` scheduler for Phase 2 that yields to Phase 1 and isolates failures via stepped, bounded backoff.
- **Timing configuration**: Hub parameters set `send_wait_time: 300ms` (response-wait timeout) and provisional `turnaround_time: 200ms` (inter-transaction quiet turnaround delay replacing ESPHome's `600ms` default), alongside separate application watchdogs (`1000ms` Phase 1 guard, `2000ms` Phase 2 watchdog).

See [`docs/MODBUS-REFERENCE.md`](docs/MODBUS-REFERENCE.md) for framing, transaction scheduling occupancy calculations, sign conventions, and preserved ambiguities.

---

## Synthetic Simulator & Offline Automated Tests

[`scripts/srne_modbus_simulator.py`](scripts/srne_modbus_simulator.py) provides a standalone Windows-compatible PyModbus `3.16.2` RTU simulator for bench and offline verification of the **implemented register mappings** (`40` `FC03` groups / `107` words):

- **Five deterministic scenarios**: `S1_solar_charging` (default), `S2_battery_discharging`, `S3_utility_zero_solar`, `S4_standby` (incl. `-2.5 °C` signed temp test), and `S5_active_fault`.
- **Six communication modes (`--interactive`)**: `normal`, `silent_timeout`, `selective_timeout` (e.g., `bms` groups `P2-D04`/`P2-D05`), `selective_exception`, encoded RTU `invalid_crc`, and `truncated_frame`, with restartless live recovery (`n`).
- **Strict FC03-only safety**: Rejects writes (`FC05`/`06`/`15`/`16`/`22`/`23`) and unsupported FCs with Modbus `0x01` across every failure mode without register mutation.
- **Historical recorded test baseline (`SRNE-04E-H`)**: As recorded in [`audits/SRNE-04E-H-Final-Offline-Validation.md`](audits/SRNE-04E-H-Final-Offline-Validation.md), all **24** automated tests (including **400** in-memory RTU wire round-trips across all 40 groups and 5 scenarios) and `pip check` passed offline under Python `3.14.3` prior to physical bench testing. Setup and CLI instructions are in [`tests/README.md`](tests/README.md).

---

## Universal Inverter Flow Integration

Designed to feed the open-source **[Universal Inverter Flow](https://github.com/quky/universal-inverter-flow)** Home Assistant Lovelace card:

- **SRNE Card & ESPHome Examples**: [Universal Inverter Flow SRNE Examples](https://github.com/quky/universal-inverter-flow/tree/main/docs/examples/srne) (`mode: manual`, `split_phase`, `ac_voltage_reference: l_l`, `battery.power_mode: signed_positive_discharge`, mapping 23 of the 73 exposed ESPHome entities).
- **Entity-prefix & output-boundary notes**: Ensure Home Assistant dashboard entity IDs match your verified prefix in **Developer Tools → States**, and note that **`srne_output_total_power` always measures inverter LOAD / UPS output (`0x021B` + `0x0232`)** — external whole-home CT measurements must be mapped separately in Home Assistant and do not change the inverter register measurement boundary ([`docs/MODBUS-REFERENCE.md`](docs/MODBUS-REFERENCE.md#4-sign-conventions--measurement-boundaries)).

---

## Repository Structure

```text
.
├── README.md                              # Project overview & documentation hub (this file)
├── docs/
│   ├── INSTALLATION.md                    # Hardware wiring precautions, ESPHome setup & stats safety
│   ├── ENTITIES.md                        # Reconciled catalog of all 73 public entities
│   └── MODBUS-REFERENCE.md                # Protocol V2.04 spec, scheduling, occupancy & ambiguities
├── esphome/
│   ├── srne-bench-test.yaml               # Bench entrypoint (UART/Modbus config + 1 local uptime + packages)
│   └── packages/
│       ├── srne-phase1-monitoring.yaml    # 35 Phase 1 Modbus/health entities (+ 1 local uptime = 36 Phase 1; 16 FC03 groups, 32 words)
│       └── srne-phase2-diagnostics.yaml   # 37 Phase 2 public entities (24 FC03 groups, 75 words)
├── scripts/
│   └── srne_modbus_simulator.py           # Read-only PyModbus 3.16.2 RTU simulator (5 scenarios, 6 modes)
├── tests/
│   ├── README.md                          # Python 3.14.3 venv setup, CLI guide, scenarios & test layers
│   ├── SRNE-03V-Physical-RS485-Bench-Test-Procedure.md  # Sequential physical RS485 bench test runbook
│   ├── requirements-simulator.txt         # Pinned simulator dependencies (pymodbus 3.16.2, pyserial 3.5)
│   ├── test_srne_modbus_simulator.py      # Offline application & in-memory RTU protocol unittest suite
│   └── fixtures/                          # Deterministic register groups, scenarios & expected entities
└── audits/                                # Protocol audits, mappings, architecture & validation records
```

> Local manufacturer PDFs (`documentation/official/*.pdf`) and `esphome/secrets.yaml` are gitignored local-only files and are not published in this repository.

---

## Documentation Navigation

- **Installation & Hardware Setup**: [`docs/INSTALLATION.md`](docs/INSTALLATION.md) · [UIF Illustrated Hardware Guide](https://github.com/quky/universal-inverter-flow/blob/main/docs/inverters/srne-spi-16k-up.md) · [UIF Hardware BOM](https://github.com/quky/universal-inverter-flow/blob/main/docs/hardware/bill-of-materials.md)
- **Entity Reference**: [`docs/ENTITIES.md`](docs/ENTITIES.md) · [`audits/SRNE-04A-Phase1-Entity-Mapping.csv`](audits/SRNE-04A-Phase1-Entity-Mapping.csv) · [`audits/SRNE-04F-Extended-Diagnostic-Mapping.csv`](audits/SRNE-04F-Extended-Diagnostic-Mapping.csv)
- **Modbus & Architecture**: [`docs/MODBUS-REFERENCE.md`](docs/MODBUS-REFERENCE.md) · [`audits/SRNE-01B-Communication-Specification.md`](audits/SRNE-01B-Communication-Specification.md) · [`audits/SRNE-04G-R1-Architecture-Correction.md`](audits/SRNE-04G-R1-Architecture-Correction.md)
- **Simulator & Bench Testing**: [`tests/README.md`](tests/README.md) · [`audits/SRNE-04E-H-Final-Offline-Validation.md`](audits/SRNE-04E-H-Final-Offline-Validation.md) · [`tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md)

---

## Known Limitations, Safety Boundaries & Roadmap

- **Physical inverter unvalidated**: Do **not** rely on unverified telemetry for safety-critical or financial/control decisions. Turnaround timing (`200ms` provisional), optional BMS register availability, `0x001C` version encoding, fault-code text decoding, and `WiFi Port 1` electrical compatibility require live inverter verification.
- **Implemented subset scope**: Synthetic testing validates only the `40` implemented `FC03` register groups (`107` words / `73` public entities) against synthetic fixtures, not the complete manufacturer register inventory or live hardware behavior.
- **No write support**: Register write commands (`FC06`/`FC16`) and writable controls are excluded.
- **No repository-archived `SRNE-03V` report**: Physical USB-RS485 bench evidence has not yet been archived in [`audits/`](audits/).

### Roadmap

1. Execute [`tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md`](tests/SRNE-03V-Physical-RS485-Bench-Test-Procedure.md) with the available USB-to-RS485 bench hardware and archive the completed `SRNE-03V` evidence report in [`audits/`](audits/).
2. Perform live **SRNE SPI-16K-UP** read-only validation (`WiFi Port 1`, turnaround tuning, real BMS/MPPT telemetry, and fault-code verification).
3. Evaluate daily energy `state_class: total_increasing` behavior and unresolved protocol ambiguities against live inverter logs before considering optional read-only/control expansions.

---

## Reference Project (Anenji)

A separate, **physically validated** 12 kW split-phase Anenji ESPHome integration is maintained independently at:

- **[quky/Anenji-12KW-48V-Hybrid-split-phas](https://github.com/quky/Anenji-12KW-48V-Hybrid-split-phas)**

That project is separate and is not modified by this repository.
