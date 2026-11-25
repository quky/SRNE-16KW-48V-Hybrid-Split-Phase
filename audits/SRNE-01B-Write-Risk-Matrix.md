# SRNE-01B - Write Risk Matrix

Documentation-only audit, 2026-11-25. No writes were implemented or attempted.

DOCUMENTED permissions and source references are copied from V2.04. Risk levels and consequences are INFERRED engineering assessments, not manufacturer risk ratings. A RW/W label does not prove that SPI-16K-UP firmware accepts a write. Gray/invalid and reserved entries remain included to prevent their accidental treatment as safe controls.

The inventory expands each multiword row into individual addresses. This matrix lists each writable table row once, giving its inclusive address range. Protocol-wide write functions are 0x06 (single word) and 0x10 (multiple words), maximum 32 words (P pp3-4). The document does not authorize partial writes of structured records or specify transaction atomicity, persistence, endurance, or safe operating-state sequences. These remain UNVERIFIED.

Critical: output interruption, destructive reset, firmware, electrical protection/topology or undefined operations. High: material battery, routing, diagnostic or operating changes. Moderate: communication, clock or notification changes. There are no proposed writable Home Assistant controls.

E003 is conservatively counted as writable because its permission column is RW, despite its read-only name. E21A is R and therefore excluded from writable counts even though its remark says it can be disabled. See A03/A11.

| Address range | Table name | Permission | Risk (INFERRED) | Potential consequence | Original reference |
|---|---|---|---|---|---|
| 0x020C-0x020E | Current Time | RW | MODERATE | Changes RTC and therefore timed charge/discharge and daily statistics boundaries | P PDF p10, P02 Inverter data, row 0x020C |
| 0xDF00 | Power ON/OFF Control | W | CRITICAL | May interrupt AC output or restart inverter | P PDF p11, P03 Device control, row 0xDF00 |
| 0xDF01 | Reset Control | W | CRITICAL | May interrupt AC output or restart inverter | P PDF p11, P03 Device control, row 0xDF01 |
| 0xDF02 | Restore Factory Defaults | W | CRITICAL / DESTRUCTIVE | May restore settings or erase energy statistics / fault history | P PDF p11, P03 Device control, row 0xDF02 |
| 0xDF03 | Manual AFCI Fault Clear | W | HIGH | Clears arc-fault latch; may permit operation before cause is corrected | P PDF p11, P03 Device control, row 0xDF03 |
| 0xDF04 | Reserved | W | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P03 Device control, row 0xDF04 |
| 0xDF05 | Reserved | W | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P03 Device control, row 0xDF05 |
| 0xDF06-0xDF07 | Firmware Upgrade Command | W | CRITICAL | Firmware upgrade entry; sequence and recovery unspecified | P PDF p11, P03 Device control, row 0xDF06 |
| 0xDF08 | Reserved | W | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P03 Device control, row 0xDF08 |
| 0xDF09-0xDF0B | Reserved | W | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P03 Device control, row 0xDF09 |
| 0xDF0C | USB Flash Drive Insertion Flag | W | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P03 Device control, row 0xDF0C |
| 0xDF0D | Immediate Equalization Charge Command | W | CRITICAL | Can initiate or change elevated-voltage battery equalization; chemistry dependent | P PDF p11, P03 Device control, row 0xDF0D |
| 0xE000 | Reserved | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE000 |
| 0xE001 | PV Maximum Charging Current Setting | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE001 |
| 0xE002 | Battery Nominal Capacity | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE002 |
| 0xE003 | Battery Rated Voltage (Read Only) | RW | CRITICAL / CONFLICT | RW column conflicts with read-only name; nominal voltage is safety-critical | P PDF p11, P05 Battery settings, row 0xE003 |
| 0xE004 | Battery Type | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE004 |
| 0xE005 | Overvoltage Threshold | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE005 |
| 0xE006 | Charging Voltage Limit | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE006 |
| 0xE007 | Equalization Charging Voltage | RW | CRITICAL | Can initiate or change elevated-voltage battery equalization; chemistry dependent | P PDF p11, P05 Battery settings, row 0xE007 |
| 0xE008 | Boost Charging Voltage / Overcharge Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE008 |
| 0xE009 | Float Charging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE009 |
| 0xE00A | Boost-Charge Return Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE00A |
| 0xE00B | Overdischarge Recovery Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE00B |
| 0xE00C | Undervoltage Warning Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE00C |
| 0xE00D | Overdischarge Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE00D |
| 0xE00E | Discharge Voltage Limit | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE00E |
| 0xE00F | Discharge Cut-off SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE00F |
| 0xE010 | Overdischarge Delay Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE010 |
| 0xE011 | Equalization Charging Time | RW | CRITICAL | Can initiate or change elevated-voltage battery equalization; chemistry dependent | P PDF p11, P05 Battery settings, row 0xE011 |
| 0xE012 | Boost Charging Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE012 |
| 0xE013 | Equalization Charging Interval | RW | CRITICAL | Can initiate or change elevated-voltage battery equalization; chemistry dependent | P PDF p11, P05 Battery settings, row 0xE013 |
| 0xE014 | Temperature Compensation Coefficient | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE014 |
| 0xE015 | Maximum Charging Temperature | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE015 |
| 0xE016 | Minimum Charging Temperature | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE016 |
| 0xE017 | Maximum Discharging Temperature | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE017 |
| 0xE018 | Minimum Discharging Temperature | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE018 |
| 0xE019 | Heating Start Temperature | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE019 |
| 0xE01A | Heating Stop Temperature | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p11, P05 Battery settings, row 0xE01A |
| 0xE01B | Utility Transfer Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE01B |
| 0xE01C | Charge Stop Current | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE01C |
| 0xE01D | Charge Stop Capacity | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE01D |
| 0xE01E | Low SOC Alarm | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE01E |
| 0xE01F | Utility Transfer SOC Threshold | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE01F |
| 0xE020 | Battery/Inverter Transfer SOC Threshold | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE020 |
| 0xE021 | Battery Maximum Discharge Current | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p11, P05 Battery settings, row 0xE021 |
| 0xE022 | Inverter Transfer Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE022 |
| 0xE023 | Equalization Charging Timeout | RW | CRITICAL | Can initiate or change elevated-voltage battery equalization; chemistry dependent | P PDF p12, P05 Battery settings, row 0xE023 |
| 0xE024 | Lithium Battery Activation Current | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE024 |
| 0xE025 | BMS Charging Current-Limit Mode Setting | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE025 |
| 0xE026 | Period 1 Charging Start Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE026 |
| 0xE027 | Period 1 Charging End Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE027 |
| 0xE028 | Period 2 Charging Start Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE028 |
| 0xE029 | Period 2 Charging End Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE029 |
| 0xE02A | Period 3 Charging Start Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE02A |
| 0xE02B | Period 3 Charging End Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE02B |
| 0xE02C | Staged Charging Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE02C |
| 0xE02D | Period 1 Discharging Start Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE02D |
| 0xE02E | Period 1 Discharging End Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE02E |
| 0xE02F | Period 2 Discharging Start Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE02F |
| 0xE030 | Period 2 Discharging End Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE030 |
| 0xE031 | Period 3 Discharging Start Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE031 |
| 0xE032 | Period 3 Discharging End Time | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE032 |
| 0xE033 | Staged Discharging Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE033 |
| 0xE034-0xE036 | Reserved | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p12, P05 Battery settings, row 0xE034 |
| 0xE037 | Operating Mode | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE037 |
| 0xE038 | Leakage Current Detection Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE038 |
| 0xE039 | PV Output Priority Setting | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE039 |
| 0xE03A | Battery Temperature Compensation Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE03A |
| 0xE03B | Charging Period 1 Stop-Charging SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE03B |
| 0xE03C | Charging Period 2 Stop-Charging SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE03C |
| 0xE03D | Charging Period 3 Stop-Charging SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE03D |
| 0xE03E | Discharging Period 1 Stop-Discharging SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE03E |
| 0xE03F | Discharging Period 2 Stop-Discharging SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE03F |
| 0xE040 | Discharging Period 3 Stop-Discharging SOC | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE040 |
| 0xE041 | Charging Period 1 Stop-Charging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE041 |
| 0xE042 | Charging Period 2 Stop-Charging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE042 |
| 0xE043 | Charging Period 3 Stop-Charging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE043 |
| 0xE044 | Discharging Period 1 Stop-Discharging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE044 |
| 0xE045 | Discharging Period 2 Stop-Discharging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE045 |
| 0xE046 | Discharging Period 3 Stop-Discharging Voltage | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE046 |
| 0xE047 | Sched. Period 1 Max Discharge Power (W) | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE047 |
| 0xE048 | Sched. Period 2 Max Discharge Power (W) | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE048 |
| 0xE049 | Sched. Period 3 Max Discharge Power (W) | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE049 |
| 0xE04A | Sched. Period 1 Max Charge Power (W) | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE04A |
| 0xE04B | Sched. Period 2 Max Charge Power (W) | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE04B |
| 0xE04C | Sched. Period 3 Max Charge Power (W) | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE04C |
| 0xE04D | Scheduled Charging Energy Source Selection | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE04D |
| 0xE04E | Grid-Connected Discharge SOC Balancing Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE04E |
| 0xE04F | Grid-Connected Charging SOC Balancing Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE04F |
| 0xE050 | SOC Balancing Correction Coefficient | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P05 Battery settings, row 0xE050 |
| 0xE051 | Reserved | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p12, P05 Battery settings, row 0xE051 |
| 0xE200 | Inverter RS485 Address Setting | RW | MODERATE | Changes slave address; monitoring may be lost or address collision created | P PDF p12, P07 Inverter settings, row 0xE200 |
| 0xE201 | Parallel Operation Mode | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p12, P07 Inverter settings, row 0xE201 |
| 0xE202 | User Password Setting | W | HIGH | Changes password or unlocks access; can lock out monitoring / permit settings changes | P PDF p12, P07 Inverter settings, row 0xE202 |
| 0xE203 | Password Entry | W | HIGH | Changes password or unlocks access; can lock out monitoring / permit settings changes | P PDF p12, P07 Inverter settings, row 0xE203 |
| 0xE204 | Output Priority | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE204 |
| 0xE205 | Utility Charging Current Limit | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE205 |
| 0xE206 | Equalization Charging Enable | RW | CRITICAL | Can initiate or change elevated-voltage battery equalization; chemistry dependent | P PDF p12, P07 Inverter settings, row 0xE206 |
| 0xE207 | N-PE Ground Bonding Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p12, P07 Inverter settings, row 0xE207 |
| 0xE208 | Output Voltage (Default: 220 V) | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p12, P07 Inverter settings, row 0xE208 |
| 0xE209 | Output Frequency (Default: 50 Hz) | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p12, P07 Inverter settings, row 0xE209 |
| 0xE20A | Maximum Charging Current | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE20A |
| 0xE20B | AC Input Range | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE20B |
| 0xE20C | Energy-Saving Mode | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE20C |
| 0xE20D | Automatic Restart After Overload | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE20D |
| 0xE20E | Automatic Restart After Overtemperature | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE20E |
| 0xE20F | Charging Priority | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p12, P07 Inverter settings, row 0xE20F |
| 0xE210 | Alarm Control | RW | MODERATE | Can suppress audible source/fault notifications | P PDF p12, P07 Inverter settings, row 0xE210 |
| 0xE211 | Alarm Enable When Input Source Is Interrupted | RW | MODERATE | Can suppress audible source/fault notifications | P PDF p12, P07 Inverter settings, row 0xE211 |
| 0xE212 | Overload Bypass Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE212 |
| 0xE213 | Record Fault Codes | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p13, P07 Inverter settings, row 0xE213 |
| 0xE214 | BMS Fault Shutdown Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE214 |
| 0xE215 | BMS Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE215 |
| 0xE216 | Load Type | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE216 |
| 0xE217 | Reserved | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p13, P07 Inverter settings, row 0xE217 |
| 0xE218 | Inverter Power Derating | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE218 |
| 0xE21B | BMS Protocol | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE21B |
| 0xE21C | Maximum Bypass Input Current | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE21C |
| 0xE21D | Maximum Bypass Input Power | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE21D |
| 0xE21E | Single-Unit Split-Phase AC Wiring Type | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P07 Inverter settings, row 0xE21E |
| 0xE21F | Diesel Generator Operating Mode | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE21F |
| 0xE220 | Diesel Generator Charging Current | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE220 |
| 0xE221 | Diesel Generator Rated Power | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE221 |
| 0xE222 | PV Secondary-Load Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE222 |
| 0xE223 | Utility Secondary-Load Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE223 |
| 0xE224 | Day-of-Week Setting | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE224 |
| 0xE225 | Scheduled Charging Weekday Enable | RW | HIGH | Changes battery limits, power routing, schedules, output continuity, BMS behavior or generator/secondary-port operation | P PDF p13, P07 Inverter settings, row 0xE225 |
| 0xE400 | Grid-Connected Active Power Setting | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE400 |
| 0xE401 | Grid-Connected Power Factor Setting | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE401 |
| 0xE402 | Grid-Connected Reactive Power Setting | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE402 |
| 0xE403 | Grid Standard Setting | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE403 |
| 0xE404 | Grid Undervoltage Protection Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE404 |
| 0xE405 | Grid Undervoltage Protection Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE405 |
| 0xE406 | Grid Undervoltage Recovery Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE406 |
| 0xE407 | Grid Undervoltage Recovery Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE407 |
| 0xE408 | Grid Undervoltage Protection Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE408 |
| 0xE409 | Grid Undervoltage Protection Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE409 |
| 0xE40A | Grid Undervoltage Recovery Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE40A |
| 0xE40B | Grid Undervoltage Recovery Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE40B |
| 0xE40C | Grid Overvoltage Protection Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE40C |
| 0xE40D | Grid Overvoltage Protection Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE40D |
| 0xE40E | Grid Overvoltage Recovery Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE40E |
| 0xE40F | Grid Overvoltage Recovery Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE40F |
| 0xE410 | Grid Overvoltage Protection Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE410 |
| 0xE411 | Grid Overvoltage Protection Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE411 |
| 0xE412 | Grid Overvoltage Recovery Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE412 |
| 0xE413 | Grid Overvoltage Recovery Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE413 |
| 0xE414 | Grid Underfrequency Protection Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE414 |
| 0xE415 | Grid Underfrequency Protection Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE415 |
| 0xE416 | Grid Underfrequency Recovery Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE416 |
| 0xE417 | Grid Underfrequency Recovery Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE417 |
| 0xE418 | Grid Underfrequency Protection Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE418 |
| 0xE419 | Grid Underfrequency Protection Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE419 |
| 0xE41A | Grid Underfrequency Recovery Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE41A |
| 0xE41B | Grid Underfrequency Recovery Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE41B |
| 0xE41C | Grid Overfrequency Protection Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE41C |
| 0xE41D | Grid Overfrequency Protection Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE41D |
| 0xE41E | Grid Overfrequency Recovery Point 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE41E |
| 0xE41F | Grid Overfrequency Recovery Point 1 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE41F |
| 0xE420 | Grid Overfrequency Protection Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE420 |
| 0xE421 | Grid Overfrequency Protection Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE421 |
| 0xE422 | Grid Overfrequency Recovery Point 2 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE422 |
| 0xE423 | Grid Overfrequency Recovery Point 2 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE423 |
| 0xE424 | Grid Reconnection Restart Time (seconds) | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE424 |
| 0xE425 | Insulation Resistance Detection Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE425 |
| 0xE426 | Insulation Resistance Detection Threshold | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE426 |
| 0xE427 | Grid Function Bit Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE427 |
| 0xE428 | User Mode | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p13, P08 Grid settings, row 0xE428 |
| 0xE429 | Parameter Self-Test Step | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE429 |
| 0xE42A | Battery Participation in Grid Connection Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE42A |
| 0xE42B | CT Ratio | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE42B |
| 0xE42C | Anti-Backflow Power Deviation | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE42C |
| 0xE42D | Grid Reconnection Power Ramp-Up Rate | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE42D |
| 0xE42E | Active Power-PF Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE42E |
| 0xE42F | High/Low Voltage Ride-Through | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE42F |
| 0xE430 | Parameter Self-Test Start Command | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE430 |
| 0xE431 | AFCI Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE431 |
| 0xE432 | Normal Grid-Connection Delay Time | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE432 |
| 0xE433 | Normal Grid-Connection Power Ramp-Up Rate | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE433 |
| 0xE434 | Minimum Grid-Connection Voltage | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE434 |
| 0xE435 | Maximum Grid-Connection Voltage | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE435 |
| 0xE436 | Minimum Grid-Connection Frequency | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE436 |
| 0xE437 | Maximum Grid-Connection Frequency | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE437 |
| 0xE438 | CT Automatic Detection Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE438 |
| 0xE439 | CT Manual Setting | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE439 |
| 0xE43A | Grid Function Bit Enable 1 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE43A |
| 0xE43B | DRMS Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE43B |
| 0xE43C | Grid Undervoltage Protection Point 3 | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE43C |
| 0xE43D | Grid Undervoltage Protection Point 3 Delay | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE43D |
| 0xE43E | Energy Meter Enable | RW | CRITICAL | Changes electrical topology, bonding, grid behavior, protection, export, or compliance settings | P PDF p14, P08 Grid settings, row 0xE43E |
| 0xE43F | Reserved | RW | CRITICAL / UNDEFINED | Reserved, invalid or internal semantics; potential undocumented side effects | P PDF p14, P08 Grid settings, row 0xE43F |
| 0xF800-0xF80F | Fault Record 0 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF800 |
| 0xF810-0xF81F | Fault Record 1 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF810 |
| 0xF820-0xF82F | Fault Record 2 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF820 |
| 0xF830-0xF83F | Fault Record 3 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF830 |
| 0xF840-0xF84F | Fault Record 4 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF840 |
| 0xF850-0xF85F | Fault Record 5 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF850 |
| 0xF860-0xF86F | Fault Record 6 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF860 |
| 0xF870-0xF87F | Fault Record 7 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF870 |
| 0xF880-0xF88F | Fault Record 8 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF880 |
| 0xF890-0xF89F | Fault Record 9 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF890 |
| 0xF8A0-0xF8AF | Fault Record 10 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF8A0 |
| 0xF8B0-0xF8BF | Fault Record 11 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF8B0 |
| 0xF8C0-0xF8CF | Fault Record 12 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF8C0 |
| 0xF8D0-0xF8DF | Fault Record 13 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF8D0 |
| 0xF8E0-0xF8EF | Fault Record 14 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF8E0 |
| 0xF8F0-0xF8FF | Fault Record 15 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF8F0 |
| 0xF900-0xF90F | Fault Record 16 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF900 |
| 0xF910-0xF91F | Fault Record 17 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF910 |
| 0xF920-0xF92F | Fault Record 18 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p14, P10 Fault history, row 0xF920 |
| 0xF930-0xF93F | Fault Record 19 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF930 |
| 0xF940-0xF94F | Fault Record 20 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF940 |
| 0xF950-0xF95F | Fault Record 21 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF950 |
| 0xF960-0xF96F | Fault Record 22 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF960 |
| 0xF970-0xF97F | Fault Record 23 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF970 |
| 0xF980-0xF98F | Fault Record 24 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF980 |
| 0xF990-0xF99F | Fault Record 25 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF990 |
| 0xF9A0-0xF9AF | Fault Record 26 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF9A0 |
| 0xF9B0-0xF9BF | Fault Record 27 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF9B0 |
| 0xF9C0-0xF9CF | Fault Record 28 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF9C0 |
| 0xF9D0-0xF9DF | Fault Record 29 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF9D0 |
| 0xF9E0-0xF9EF | Fault Record 30 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF9E0 |
| 0xF9F0-0xF9FF | Fault Record 31 | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xF9F0 |
| 0xFA00-0xFA0F | Italy Parameter Test Record | RW | HIGH / UNDEFINED | RW fault/test records can destroy diagnostic evidence; write format unspecified | P PDF p15, P10 Fault history, row 0xFA00 |

## Undefined mentions outside the current table

All 11 note-only addresses are listed individually in the CSV, with unspecified permissions: DF43/DF44 and E102 (P p1 revision history), E110-E112 and E142-E144 (P p2 revision history), 0438-0439 (P p15 footer). Potential calibration/upgrade effects are CRITICAL / UNDEFINED (INFERRED); writable support itself is UNVERIFIED. They are excluded from documented W/RW counts.

DF02 explicitly accepts AA for factory defaults, BB for energy-statistics erasure and CC for history erasure (P p11). These are three actions at one address, not three registers. DF06 occupies two words; the document gives no upgrade payload. F800-F9FF fault history is RW in the table; its captured-data format and safe write behavior are not specified. FA00-FA0F is an Italy parameter test record, also RW, with no SPI applicability statement.

Source key P and the full source catalog are in the Audit Summary. Every range above is traceable to its original table row; no live-device or third-party compatibility evidence was used.
