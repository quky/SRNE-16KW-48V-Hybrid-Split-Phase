# SRNE-01B - Communication Specification

Audit date: 2026-11-25. Source keys: P = official Modbus V2.04, W = website-sourced V00 manual, S = seller-sourced V01 manual. Full filenames, versions and page conventions are in the Audit Summary. All page references below are 1-based PDF pages.

## Documented transport and addressing

| Property | DOCUMENTED definition | Original reference |
|---|---|---|
| Transport | RS485, Modbus RTU, single master and multiple slaves | P p3 sections 1-3 |
| Serial | 9600 baud, no parity, 8 data bits, 1 stop bit (9600,N,8,1) | P p3 section 2 |
| Default slave | 1; configurable | P p3 section 2; W p33 / S p31 item 30 |
| Normal slave addresses | 01-FE hex, decimal 1-254 | P p3 section 3 |
| Broadcast | 00 hex, named master broadcast; response and write behavior not specified | P p3 section 3 |
| Universal address | FF hex/255, documented for one-to-one connection; inverter replies with its actual address | P p3 section 2 |
| Read address | 001A is read-only device-address display | P p9 P00 |
| Address setting | E200 is RW, range 1-254, default 1 | P p12 P07 |
| Maximum operation | No more than 32 registers in one read or write operation | P p3 section 1 and frame count; P p4 exception 0A |
| Functions | 03 hex read multiple registers; 06 hex write single register; 10 hex write multiple registers. Other functions invalid | P pp3-4 |

INFERRED: use the table's hexadecimal address directly as the 16-bit address field. The example starts at 0200 with count 0020, so the addresses are not decimal 4xxxx reference numbers. A client field's one-based versus zero-based configuration convention is client-specific and UNVERIFIED here. Decimal equivalents in the CSV are arithmetic conversions, not alternate register maps. Function 04 input-register reading, coils, discrete inputs and Modbus TCP are not documented.

## Documented frame layout

P p3 section 3.1: read request = slave, 03, start high, start low, count high, count low, CRC low, CRC high. The example is `01 03 02 00 00 20 45 AA`. Read reply = actual slave, 03, byte count 2*N, then N words with high byte before low byte, then CRC low/high. Exception reply = actual slave, 83, exception code, CRC low/high.

P p4 section 3.2: multiple-write request = slave, 10, start high/low, count high/low, byte count 2*N, N values high-byte first, CRC low/high. Reply echoes slave, 10, start and count, CRC. Exception function = 90. Section 3.3: single-write request and normal response use slave, 06, address high/low, value high/low, CRC; exception function = 86. These are documentation transcriptions only; no executable write implementation was created.

## CRC and numeric encoding

DOCUMENTED (P p3 section 3; pp5-7 section 4): CRC covers the slave address through the final data byte, excluding the CRC itself. Send the CRC's low byte first, then its high byte. The bitwise example starts at FFFF, XORs each byte and applies reflected polynomial A001 for eight shifts. Several lookup-table examples on pp5-7 are duplicated or visibly incomplete; the bitwise description is the clearest complete algorithm. The CRC is not the same byte order as each register value.

DOCUMENTED (P p8; p9 note 2): actual value = raw register value * scale multiplier. General text also describes decimal factors 10/100/1000; the table explicitly gives multipliers 0.1/0.01/0.001. A 32-bit scalar uses the lower register for its low 16 bits and the next address for its high 16 bits. Example: lower word 5678, upper word 1234 represents 12345678 hex. Register bytes themselves remain high byte first. Do not turn every length-2 row into a 32-bit scalar: versions, dates, arrays and structured records have their own layouts.

P p8 lists voltage/current as 16-bit unsigned, signed current and temperature ranges as -32767 to 32767, frequency as unsigned and energy as 16/32-bit unsigned. P p9 explicitly makes battery current 0102 signed: positive discharge, negative charging. BMS current 0113 is explicitly unsigned, with no direction convention; do not apply 0102's rule to it. P p10 makes load active powers signed and grid active powers signed with positive export / negative import. Table-specific signedness overrides general headings for transcription, while contradictions remain unresolved.

DOCUMENTED (P p8): battery voltage **settings** are expressed on a 12 V equivalent basis. A 48 V system's 57.6 V setting is 14.4 V equivalent, raw 144 with scale 0.1. This is separate from measured battery voltage 0101, which directly uses raw * 0.1 V (P p9). UNVERIFIED: scheduled voltage settings E041-E046 appear in full-pack volts (40-59.5, defaults 57.6/42), conflicting with the global statement; see A06. No automatic normalization rule is prescribed for those conflicting rows.

P p9: build-time and serial-number strings use the lower 8 bits of each word; upper 8 bits invalid. Encoding, termination and padding are unspecified. RTC 020C-020E packs year/month, day/hour, minute/second (high/low bytes; P p10). Calendar base/century, time zone and daylight-saving behavior are not specified. Scheduled time is hour * 256 + minute; 23:59 = 5947 (P p12), not decimal HHMM.

## Exceptions

DOCUMENTED in P p4 section 3.4; these vendor labels must not be replaced with generic library meanings for the same numbers.

| Hex code | Vendor meaning | Documented reason |
|---|---|---|
| 01 | Illegal Function | Slave may not support function |
| 02 | Illegal Data Address | Address outside slave's valid range |
| 03 | Illegal Data Value | Value outside defined range |
| 04 | Operation Failed | Invalid setting or present state disallows command |
| 05 | Incorrect Password | Incorrect value written to password-verification address |
| 06 | Data Frame Error | Incorrect length or CRC mismatch |
| 07 | Parameter Is Read-Only | Attempt to modify read-only parameter |
| 08 | Parameter Locked During Operation | Parameter cannot change while operating |
| 09 | Password Protection | Password set, lock not unlocked; read or write may be blocked |
| 0A | Invalid Length | More than 32 registers requested |
| 0B | Insufficient Permission | Permission insufficient |

INFERRED handling for a future read-only client: validate actual address, function, byte count and CRC before decoding; preserve exception codes as diagnostics; treat an exception as unavailable data, never a zero measurement. Do not assume undocumented holes are readable. A timeout/CRC failure is not evidence that a particular register is absent. No retry or auto-unlock behavior is authorized by this audit.

## Polling limits and gaps

DOCUMENTED limit: 32 register words, including constituent words of arrays/records, per operation. No minimum polling interval, response deadline, inter-request delay, startup delay, simultaneous request allowance, retry count, bus turnaround timing, snapshot consistency guarantee or update cadence is given in the three PDFs. RTU inter-frame timing is referenced by protocol name but no numeric silent-interval requirement is printed. These are UNVERIFIED for this inverter; no arbitrary polling rate is presented as official.

INFERRED future design constraints: keep one master on a physical bus, serialize requests, avoid undocumented gaps, keep paired scalar words together, and do not combine unrelated or unconfirmed ranges merely because their addresses are nearby. Coherency of all values in one response is still UNVERIFIED. No polling was performed.

## Model ports and pin assignments

DOCUMENTED in W p49 section 6.9 and S p45 section 6.8: monitoring WiFi RJ45 has pin 1 = 5V, 2 = GND, 3-6 unused, 7 = RS485-A, 8 = RS485-B. S p45 also shows a four-pin WiFi Port 2: 1 VCC, 2 GND, 3 RS485-A, 4 RS485-B. VCC voltage for that four-pin listing is not stated there. These are physical documentation facts, not instructions to connect hardware.

W p47 / S p44 section 6.7 describe a **battery BMS** RS485/CAN RJ45: 1 B, 2 A, 3 unused, 4 CANH, 5 CANL, 6 unused, 7 A, 8 B. It is not interchangeable with the powered WiFi connector. W p48 section 6.8 describes an optional meter RJ45 with 1 B, 2 A, 3-6 unused, 7 A, 8 B. S p41 still labels a meter port but has no equivalent dedicated meter-communication section. W p33 item 32 says SLA enables PC/remote monitoring; S p31 instead labels default DIS as BMS disabled. They do not establish that every RS485 connector exposes the same protocol or can share a master.

UNVERIFIED: exact monitoring port routed to P's Modbus server in this hardware/firmware, simultaneous BMS/logger access, isolation, termination resistance, biasing, maximum cable length, A/B electrical polarity convention and permission/password requirements. These must be clarified before any later hardware or integration work. No Waveshare interaction occurred.
