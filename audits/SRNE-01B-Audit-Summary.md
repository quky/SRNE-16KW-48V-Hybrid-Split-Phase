# SRNE-01B - Audit Summary

Completed documentation-only review on 2026-11-25. Scope: the three supplied official PDFs, with Modbus V2.04 as the primary register authority. Exact SPI-16K-UP firmware compatibility is not established by a product-family protocol alone. SRNE-01B stops here for review and approval.

## Source catalog and reference convention

| Key | Supplied file | Identity and authority | Pages read |
|---|---|---|---|
| P | `documentation/official/SRNE_Modbus_Monitoring_Protocol_V2.04_English.pdf` | Energy Storage Inverter Modbus Monitoring Protocol V2.04; revision history dated 2024-12-05; primary source for current register definitions | All 15 PDF pages |
| W | `documentation/official/SPI-16K-UP User Manual from srne weg page.pdf` | Cover V00, 2025-12-16; website provenance supplied by filename, not independently authenticated; datasheet uses ASP model names | All 56 PDF pages |
| S | `documentation/official/SPI-16K-UP User Manual V01 2026-05-08 form seller.pdf` | Cover V01, 2026-05-08; seller provenance supplied by filename; datasheet explicitly uses SPI-16K-UP | All 60 PDF pages |

References use **1-based PDF page numbers**, not a viewer's zero-based index. P's printed numbered pages agree with PDF pages where shown. Manual printed page numbers are PDF page minus 2 (e.g. S PDF p58 = printed p56). Named P00-P10 areas and the starting hexadecimal row address identify original table rows; those area numbers are the document's labels, not Modbus function codes. The current register table is P pp9-15; communication format is pp3-8; history is pp1-2.

DOCUMENTED = explicitly printed in these sources, including contradictions. INFERRED = arithmetic, category, applicability, derived entity or risk interpretation based on the documents. UNVERIFIED = missing definition, unresolved conflict or untested model/firmware compatibility. The inventory keeps source fields separate from applicability and inferred risk. No Anenji map or third-party compatibility assumption was used.

## Inventory totals and counting method

| Measure | Count |
|---|---:|
| Current table entries / logical rows | 383 |
| Individual 16-bit word addresses covered by those rows | 1,000 |
| Read-only table entries / word addresses | 158 / 273 |
| Read/write table entries / word addresses | 212 / 711 |
| Write-only table entries / word addresses | 13 / 16 |
| Writable total (RW + W), table entries / word addresses | 225 / 727 |
| Additional addresses mentioned only in history/footer | 11 |
| Total unique addresses recorded in CSV | 1,011 |
| Gray-invalid table entries / word addresses (included above) | 30 / 43 |

Counts describe the **document's permission column**, not confirmed supported SPI registers or safe writable controls. E003 is counted RW despite its read-only name. E21A is counted R despite its disable remark. Unknown permissions for the 11 mention-only addresses are excluded from R/RW/W totals. The same address with multiple actions (such as DF02) is counted once. No gap, reserved-hole extrapolation, or sample CRC/address value is counted as a newly defined register.

The CSV contains one row per individual word address. `table_start_hex`, `table_length_words` and `word_offset` retain the original multiword grouping, so 32 fault records are not confused with 512 separate fault types. `data_type` describes the parent scalar/string/structured block; a word of a uint32 is not independently a full measurement. Only explicitly numeric two-word totals/counters use scalar composition; software/hardware versions, RTC, history and reserved blocks remain structured. Signed 32-bit parallel totals are an INFERRED composition of the table's Signed + length 2 with P p8 word order. Example addresses used to illustrate word order are not register definitions.

Source scaling, units, display format, signedness, limits and defaults are retained, including blank values represented as NOT STATED and literal `-` where printed. Min/max/default columns are not normalized to raw values because their conventions conflict. Source names are transcribed; normalized spelling does not override a source conflict. Record-specific remarks are supplemented by the shared history layout on P p14. Source permission/function fields describe the series protocol; per-register function acceptance on SPI is UNVERIFIED.

## Main findings

The documents establish model features for dual MPPT, 48 V batteries, L1/L2 split phase, utility bypass, BMS, CT/Home Load, generator/secondary port and parallel operation. P provides candidate measurements for those features, but neither manual supplies an address-by-address SPI applicability declaration.

Critical decoding details are documented: 9600,N,8,1, default slave 1, maximum 32 words/operation, functions 03/06/10, CRC low byte first, register data high byte first, low register word first for 32-bit scalars, discharge-positive battery current at 0102, export-positive grid active power, and special split-phase operating-state codes. The protocol specifies no polling interval or response timeout.

Unresolved functionality includes raw CT current/status, fault/flow/BMS bit mappings, individual generator input channels, relay/dry-contact/RSD state, fan RPM, per-cell BMS data, history snapshot fields and certified whole-site grid import energy. Battery net power, summed per-leg totals, split charge/discharge power and line-to-line voltage are calculated candidates with explicit assumptions, not invented direct registers. The desired-entity list was not supplied; Monitoring Coverage transparently uses a candidate set from the requested categories and official display tables.

There are 25 register/protocol ambiguity groups (A01-A25) and 10 manual/model discrepancy groups (M01-M10). Especially material: grid active-power unit A versus W; E003 RW versus read-only; 12 V normalization versus full-pack scheduled voltage defaults; BMS unsigned current; daily utility charging kWh scale; utility-versus-battery counter meaning; history 16 versus 32 records; settings whose printed ranges conflict with bit masks or word width; and old revision addresses that conflict with current table definitions.

The manuals also disagree on PV absolute maximum/MPPT voltage range (W 650 V / 120-600 V versus S 600 V / 120-550 V), some battery defaults, generator charging default and feature descriptions. Manufacturer clarification must identify the actual hardware revision and matching manual. No hardware rating was chosen from these conflicting values.

## Critical questions before any later integration work

1. Which hardware and main/slave firmware versions are installed, and which V2.04 registers are supported on that exact SPI-16K-UP?
2. Which connector hosts monitoring Modbus, what are its access/password requirements, can a logger coexist, and what timing/polling limits does SRNE specify?
3. What are the correct units/encodings for grid power, BMS current, scheduled battery voltages, setting ranges and the disputed F04C/F048 counters?
4. What are the exact CT/UPS/Home Load/generator energy boundaries, fault/flow/BMS bit definitions and history format/depth?
5. Which manual's PV voltage ratings and SPI-specific current/power defaults apply? What is the exact output-priority/wiring-mode mapping?

These questions are detailed with source references in Ambiguities. They remain UNVERIFIED; no follow-on implementation is authorized by this audit.

## Deliverables and validation

- `SRNE-01B-Register-Inventory.csv`: 1,011 uniquely addressed records, including the 11 incomplete mentions, each with original source page and row or history/footer locator.
- `SRNE-01B-Communication-Specification.md`: transport, addressing, byte/word order, CRC, frames, exceptions, timing gaps and connector distinctions.
- `SRNE-01B-Monitoring-Coverage.md`: direct, calculated and undocumented candidate entity coverage, counters and applicability caveats.
- `SRNE-01B-Write-Risk-Matrix.md`: all 225 writable table rows, inclusive multiword ranges, operational risks and source references; mention-only addresses handled separately.
- `SRNE-01B-Ambiguities.md`: unresolved register definitions, model/manual discrepancies and manufacturer questions.
- `SRNE-01B-Audit-Summary.md`: this report, scope, counts and source fingerprints.

Validation: read all three PDFs through text extraction; visually inspected all seven register-table pages, including colored invalid/recent-addition rows and ambiguous units. Reconciled 383 rows against extracted address/length/permission fields, expanded to 1,000 non-overlapping addresses, added 11 distinct mention-only addresses, checked CSV uniqueness and permission totals, and matched all 225 writable source rows to the risk matrix. Red text was distinguished from gray text; only gray named rows were classified invalid under P p9 note1. Mixed-color individual cells do not by themselves override a row's definition. No live-device tests were performed.

Only the six deliverable documentation files were created in the workspace, all under `audits/`. Original PDFs were not edited. No Git initialization or Git operations, Anenji/Home Assistant changes, firmware/YAML creation, hardware connection/flashing or writable controls were performed.

## Source SHA-256 fingerprints

Fingerprints identify the exact supplied PDFs reviewed; they do not independently authenticate provenance.

- P: `0c49c599a1a45c29bca0362241a8b460b308b07ad586561f943b3b25073e2f50`
- W: `c688cab158750fd7883ccbe00a793896ee651456b4d35195d072f3932b94813c`
- S: `8e3fdd95171e0634b07e4751505895d7a0162001d4795171bdbec9a37d52dbf2`
