# SRNE-01B - Monitoring Coverage

2026-11-25. P = Modbus V2.04; W = website V00 manual; S = seller V01 manual. Page references are PDF pages. See Audit Summary for filenames and evidence definitions.

No user-maintained desired Home Assistant entity list or Home Assistant project is present in this workspace. The table below audits a candidate monitoring set derived from the requested categories and the manuals' real-time display tables (W p28, S p27). These are proposed entity concepts, not existing user entity IDs. No Home Assistant project was inspected or changed, and no configuration was created.

**DIRECT / DOCUMENTED** means a series-protocol measurement exists. It does not prove availability on the installed SPI-16K-UP. **CALCULATED / INFERRED** means a derived entity is possible subject to stated assumptions. **UNDOCUMENTED / UNVERIFIED** means the supplied documents do not establish a usable measurement/encoding. All actual device support remains UNVERIFIED until separately approved validation.

## Candidate entity coverage

| Entity concept | Classification | Register / calculation | Constraints and original references |
|---|---|---|---|
| PV1 voltage/current/power | DIRECT / DOCUMENTED | 0107 / 0108 / 0109 | 0.1 V, 0.1 A, 1 W; P p9 P01. Dual MPPT hardware confirmed W p4/p55, S p4/p59. |
| PV2 voltage/current/power | DIRECT / DOCUMENTED | 010F / 0110 / 0111 | Same scaling; P p9. No PV3/PV4 defined. |
| Total PV power | DIRECT / DOCUMENTED with unit inference | 010A | Name Total PV Power, scale 1, unit `-`; W is INFERRED. Alternative PV1+PV2 is CALCULATED and may differ due update timing (P p9). |
| PV charging current | DIRECT / DOCUMENTED | 0224 | 0.1 A, battery-side charging current; not PV-array input current (P p10). |
| Total charging power | DIRECT / DOCUMENTED | 010E | PV charging + utility charging, W. Not a signed battery net-power reading (P p9). Generator inclusion not defined. |
| Battery voltage / signed net current | DIRECT / DOCUMENTED | 0101 / 0102 | 0.1 V / 0.1 A; current positive discharge, negative charge (P p9). |
| Battery net DC power | CALCULATED / INFERRED | scaled 0101 * scaled 0102 | Positive discharge; negative charge; includes measurement/timing error. No dedicated signed battery-power register in current table, despite manual display (W p28/S p27). |
| Separate charge/discharge power | CALCULATED / INFERRED | max(-V*I,0) / max(V*I,0) | Derive from 0102 sign only; do not use unsigned 0113 for direction. |
| SOC / SOH / rated and remaining capacity / cycles | DIRECT / DOCUMENTED | 0100 / 0104 / 0105 / 0106 / 010C | SOC described as percent though unit `-`; SOH remark repeats remaining-capacity wording. BMS dependency/algorithm, accuracy and capacity source not specified (P p9). |
| Battery temperature | DIRECT / DOCUMENTED, availability uncertain | 0103 | Signed 0.1 degrees C. Reserved physical sensor input in manuals does not establish fitted sensor (P p9; W p47/S p44). |
| BMS voltage/current/temperature | DIRECT / DOCUMENTED | 0112 / 0113 / 0114 | 0.1 V/A/degrees C. 0113 unsigned without sign rule; requires compatible BMS (P p9; W pp33-34/S p31). |
| BMS charge voltage and charge/discharge current limits | DIRECT / DOCUMENTED | 0115 / 0116 / 0117 | 0.1 V/A/A; battery communication quality/freshness not defined (P p9). |
| BMS alarm/protection raw words | DIRECT / DOCUMENTED raw only | 0118-011B | Upper/lower 16-bit words explicitly named. Bit labels absent; semantic per-alarm entities UNVERIFIED (P p9). Do not apply the low-word-first scalar rule to reverse explicitly labeled upper/lower words. |
| Grid L1 / L2 voltage and current | DIRECT / DOCUMENTED family, SPI mapping INFERRED | 0213/0214; 022A/0238 | 0.1 V/A; A->L1 and B->L2 inferred from related load labels and split-phase hardware (P p10; W p54/S p58). |
| Grid frequency | DIRECT / DOCUMENTED | 0215 | 0.01 Hz (P p10). |
| Grid L1 / L2 real power | DIRECT / DOCUMENTED with unit conflict | 023A / 023B | Signed; positive export, negative import. Unit column A conflicts with name/display W (A01, P p10). |
| Grid L1 / L2 apparent power | DIRECT / DOCUMENTED | 023D / 023E | VA (P p10). |
| Net total grid power | CALCULATED / INFERRED | P_L1 + P_L2 | Requires A01 resolution and correct CT/meter placement. Net positive export / negative import. Parallel total 0252-0253 also documented but exact system scope UNVERIFIED (P pp10-11). |
| Net import / net export power | CALCULATED / INFERRED | max(-P_net,0) / max(P_net,0) | Net-at-service behavior differs from summing per-leg imports/exports; choose only after entity requirements and metering convention are reviewed. |
| Inverter L1 / L2 voltage | DIRECT / DOCUMENTED family, SPI mapping INFERRED | 0216 / 022C | 0.1 V (P p10). |
| Inverter L1 / L2 current | DIRECT / DOCUMENTED | 0217 / 022E | Inverter **inductor** currents, not the dedicated load-current readings (P p10). |
| Inverter output frequency | DIRECT / DOCUMENTED | 0218 | 0.01 Hz (P p10). |
| L1 / L2 load current / real power / apparent power / load percentage | DIRECT / DOCUMENTED | 0219/021B/021C/021F; 0230/0232/0234/0236 | Signed active W may be negative in parallel systems; current 0.1 A, apparent VA, percentage 1% (P p10). Relationship to manual UPS versus Load labels needs confirmation. |
| Total unit load real/apparent power | CALCULATED / INFERRED | L1 + L2 channel sums | Real-power sum meaningful after load-scope validation. Sum of per-leg apparent powers is a selected accounting measure, not automatically a system PF denominator. Overall load percentage 024C is direct but has erroneous W unit (P pp10-11). |
| Line-to-line voltage | CALCULATED / INFERRED | 180 degrees: V_L1N+V_L2N; otherwise vector magnitude | Only valid if phase angle is known. At 120 degrees, sqrt(V1^2+V2^2-2*V1*V2*cos(120 degrees)) gives about 208 V for two 120 V legs. No dedicated line-to-line voltage or angle telemetry established (W p36/S p34 item68). |
| Home Load L1 / L2 and total | DIRECT / DOCUMENTED; total CALCULATED | 0240 / 0241; sum | W, unsigned. CT-dependent model feature described S pp31-32 and pp42-43. Exact inclusion of UPS/secondary circuits and measurement location UNVERIFIED. Do not sum Home Load and UPS as separate circuits without topology proof. |
| Secondary-load L1 / L2 real/apparent/current | DIRECT / DOCUMENTED | 0243/0246/0249; 0244/0247/024A | W / VA / 0.1 A; available when generator port operates as AC_OUT (P p10; W p37/S p34 item81). |
| Generator AC input per-leg voltage/current/power | UNDOCUMENTED / UNVERIFIED for a single unit | No dedicated, clearly named single-unit input register set | Do not relabel secondary-load output channels as generator input. 0254-0255 is parallel-system generator-port total power; sign/direction and availability unresolved (P p11). |
| Bypass state / time | State CALCULATED / INFERRED; times DIRECT | 0210 utility status; F03F today / F04B cumulative | Utility mode does not separately expose every relay/contact. Time units minute/hour respectively (P pp10,14). |
| Raw CT1 / CT2 current and detection result | UNDOCUMENTED / UNVERIFIED | E42B/E438/E439 are settings, not raw CT sensor telemetry | CT ratio, auto detection enable and manual direction exist. No explicit CT1/CT2 current register, automatic-detection result or calibration status is defined (P p14; W pp45-46/S pp42-43). |
| Temperatures A/B/C and ambient | DIRECT / DOCUMENTED | 0220 / 0221 / 0222 / 0223 | Signed 0.1 degrees C; P labels DC-DC/DC-AC/transformer/ambient. Physical PV/INV/BAT display correspondence UNVERIFIED (P p10; W p28/S p27). |
| DC bus total / positive / negative | DIRECT / DOCUMENTED | 0212 / 0228 / 0229 | 0.1 V; positive/negative bus explicitly apply to split-phase integrated units (P p10). |
| Operating mode, priorities and schedules as readback | DIRECT / DOCUMENTED family; SPI enum combinations UNVERIFIED | 0210; E037/E039/E204/E20F; E026-E033; E03B-E050 | Read using 03 only where R/RW; reading a setting does not authorize a control. Split-phase status uses 0 init, 1 standby, 2 utility, 3 inverter, rather than generic 0-10 (P pp10,12). |
| Fault codes and alarms | DIRECT / DOCUMENTED | 0204-0207 | Four concurrent raw code words; 0 = no fault; manual label/radix mapping requires A25 clarification; use model manuals (P p9, W pp50-52/S pp53-54). |
| Raw current fault bits / flow diagram | DIRECT raw / semantic UNVERIFIED | 0200-0203 / 020B | Internal-debug fault bitmap has no bit definitions. Flow flag has no decoding. No reliable individual bits or animated power-flow entity established (P p9). |
| Fault history / captured measurements | DIRECT structured records / incomplete | F800-F9FF | 32 listed records, 16 words each; prose says 16 records. Code and occurrence time documented; twelve snapshot values unnamed (P pp14-15). |
| Parallel count / totals | DIRECT family / SPI availability UNVERIFIED | 024D; 024E-024F UPS; 0250-0251 Home Load; 0252-0253 grid; 0254-0255 generator | Signed two-word totals, low word first; count unit incorrectly W. Both manuals allow up to six units; per-system aggregation scope unproven (P p11; W p55/S p59). |
| Firmware / model / serial / address | DIRECT / DOCUMENTED | 0014-0017 / 001B / 0035-0048 / 001A | Firmware/hardware are independent version words; serial lower byte/word. Model code lookup absent. Protocol-version readback 001C separate from model code (P p9). |
| Relay states, generator dry-contact state, fan speed, RSD status, per-cell battery telemetry, battery runtime | UNDOCUMENTED / UNVERIFIED | No explicit register definitions | Fan fault code is not RPM. Dry-contact physical function is not a register. Runtime would require usable energy and load assumptions not supplied. No invented entities. |

## Energy and historical coverage

All entries below are DOCUMENTED series counters in P p14 P09; exact SPI support, reset/rollover behavior, counter persistence, daily boundary and energy-path inclusion are UNVERIFIED. CSV expands every word and retains original unit/scale. Two-word scalar counters are unsigned low word first, 0.1 kWh unless Ah is stated. Never label an Ah counter as kWh.

| Energy entity | Direct register(s) | Interpretation / limitation |
|---|---|---|
| PV today / cumulative | F02F / F038-F039 | 0.1 kWh |
| Load today / cumulative | F030 / F03A-F03B | 0.1 kWh; exact UPS/Home/secondary-load accounting unspecified |
| Grid-connected today / exported cumulative | F02C / F032-F033 | 0.1 kWh; today named grid-connected, cumulative explicitly export |
| Battery charge/discharge today | F04D / F04E | 0.1 kWh |
| Battery charge/discharge cumulative | F050-F051 / F052-F053 | 0.1 kWh |
| Battery charge/discharge capacity today | F02D / F02E | 1 Ah |
| Battery charge/discharge capacity cumulative | F034-F035 / F036-F037 | 1 Ah |
| Utility-to-battery charge today | F03C Ah; F04C named kWh | F03C scale1 Ah; F04C unit/scale conflict A20 prevents certified kWh conversion |
| Utility-to-battery charge cumulative | F046-F047 Ah; F054-F055 kWh | 1 Ah and 0.1 kWh respectively |
| Utility-to-load today / cumulative | F03D / F048-F049 | 0.1 kWh; F048 utility-versus-battery remark conflict A19 |
| Generator-to-load today / cumulative | F056 / F058-F059 | 0.1 kWh |
| Generator-to-charge today / cumulative | F057 / F05A-F05B | 0.1 kWh |
| Generator operating hours today / cumulative | F05C / F05D | 1 h; daily counter one-hour resolution |
| Seven-day PV/load/utility-to-load histories | F000-F006 / F01C-F022 / F023-F029 | One 0.1 kWh word per day, yesterday through seven days ago |
| Seven-day battery charge/discharge/utility charge histories | F007-F00D / F00E-F014 / F015-F01B | One Ah word per day, not energy in kWh |
| Inverter today / cumulative runtime | F03E / F04A | Minutes / hours |
| Bypass today / cumulative runtime | F03F / F04B | Minutes / hours |
| Operating days, power-on time, last equalization time | F031; F040-F042; F043-F045 | Day count and packed RTC structures; F02A recent-date row is contradictory, A18 |

A whole-site grid-import **energy** counter is not unambiguously defined. F03D/F048 describe load contribution and exclude or ambiguously account for other routes; F054 is utility battery charging. Adding them is not proven to equal point-of-connection import. Integrating a validated signed total grid-power measurement over time is CALCULATED / INFERRED and would require gap handling, sampling validation and the A01 unit resolution. Ah-to-kWh conversion using one fixed battery voltage is not a documented substitute for energy counters.

No Home Assistant state class, device class, Energy Dashboard compatibility or total-increasing guarantee is established by these PDFs. Daily counters reset by definition; cumulative reset/overflow rules are not specified. Any future integration must distinguish counter reset from consumption, preserve units, and mark stale/unavailable values appropriately. These are INFERRED design requirements, not implemented functionality.

## Category and applicability rules

The CSV has a multi-valued category column covering PV/MPPT, battery, grid, L1/L2, load, bypass, CT, temperatures, energy counters, operating modes and faults, plus generator and metadata. Categories are INFERRED organization based on the documented names; they do not change source definitions.

DOCUMENTED invalid/unused: gray-text rows under P p9 note1, notably 021A load PF, 021D DC component, RV customized 0226/0227, E014-E01A temperature/heating settings and reserved metadata/settings. Gray battery-capacity setting E002 is distinct from valid-looking measured rated capacity 0105. CSV preserves all 43 gray word addresses.

Model support is strongest at the **feature** level: dual MPPT, 48 V battery, L1/L2 split-phase, grid bypass, generator/secondary port, CT and parallel operation are described by both manuals. Exact register support remains a separate issue. Phase-C fields are not an extra physical leg on one unit; 0225 specifically targets high-voltage parallel systems; E21C names customized marine models; FA00 Italy test data is not confirmed for this model. Revision-only calibration/upgrade mentions have no complete current definitions.
