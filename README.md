# SRNE 16kW Hybrid Split-Phase — ESPHome & Home Assistant

Independent, open-source ESPHome and Home Assistant integration for the
SRNE SPI-16K-UP 16kW, 48V, 120/240V split-phase hybrid inverter.

## Project Status

Development in progress. Physical inverter validation pending.

- SRNE-01: Official Modbus V2.04 documentation audit completed.
- SRNE-02: Project structure and repository preparation in progress.
- SRNE-03: Waveshare ESP32-S3-RS485-CAN-U bench testing pending.

## Hardware

- SRNE SPI-16K-UP inverter
- Waveshare ESP32-S3-RS485-CAN-U
- External SRNE CT set (planned)

The Waveshare board accepts 7–36V DC. Do not connect directly
to a 48V battery bank.

## Features Planned

- Dual MPPT solar monitoring
- Battery voltage, current, SOC and power
- Grid and split-phase L1/L2 monitoring
- Home Load and inverter output measurements
- Operating modes and fault diagnostics
- Energy production and consumption statistics
- Home Assistant dashboard and automations
- Fully local operation

## Modbus Protocol

Based on the official SRNE Modbus Monitoring Protocol V2.04.

Register definitions are documented candidates. Compatibility with
the physical SPI-16K-UP firmware remains unverified.

All Modbus write operations are disabled during initial development.

## Repository Structure

- audits/ — Protocol audit and register inventory
- documentation/ — Technical documentation
- esphome/ — ESPHome firmware
- hardware/ — Hardware configuration and wiring
- homeassistant/ — Dashboard and automations
- tests/ — Validation and test fixtures
- scripts/ — Development utilities

## Safety

This project is experimental and is not affiliated with SRNE.

Do not use unverified measurements for safety-critical decisions.
Do not enable inverter configuration writes without physical validation.

## Reference Project

https://github.com/quky/Anenji-12KW-48V-Hybrid-split-phas

The Anenji integration is a separate project and is not modified
by this development.
