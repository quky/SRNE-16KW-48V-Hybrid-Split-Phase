# SRNE-04D-R1 - ESPHome 2026.11.1 Compatibility Correction

Completed 2026-11-25 for owner review. Target: ESPHome **2026.11.1**. Only the monitoring package and this report changed. The correction is based on the exact upstream2026.11.1 sources and local static preservation checks. **Corrected target-version configuration validation and firmware compilation have not been performed.** No new firmware was deployed.

## Version and validation status

| Check | Status |
|---|---|
| Installed Windows ESPHome version | **2026.7.0**, verified from installed package metadata |
| Windows validation/compilation of previous package | PASS reported by owner; not rerun or relabeled as a result for this correction |
| HA2026.11.1 validation of previous package | PASS reported by owner |
| HA2026.11.1 compilation of previous package | FAIL reported by owner, including span-to-vector callback errors |
| Exact2026.11.1 source inspection for this correction | Completed |
| Corrected YAML parsing and static preservation checks | PASS |
| Corrected full configuration validation under2026.11.1 | **NOT RUN** |
| Corrected ESPHome2026.11.1 firmware compilation | **NOT RUN; compatibility not yet proven** |
| Physical/simulator communication testing | NOT RUN |
| Firmware deployment | NOT PERFORMED |

Windows requires an owner-managed upgrade/alignment to2026.11.1 before local validation or compilation can establish target-version results. No software was installed, downloaded as an executable/package, upgraded or switched automatically. The exact upstream source files were fetched read-only for inspection; they were not installed. The local2026.7.0 schema lacks reuse_previous_range, so its old PASS does not establish acceptance of this target-only YAML. A corrected legacy config run was not used as misleading validation.

## R1-01 - Callback ownership boundary

All **16** internal Modbus reader callbacks now pass:

`std::vector<uint8_t>(data.begin(), data.end())`

as the final argument to the existing srne_phase1_accept_group script. Its payload parameter remains uint8_t[], which ESPHome scripts represent as a vector. Nothing else in the script interface or callback's group index, start address, expected word count or cache offset changed.

The tagged2026.11.1 [Modbus lambda generator](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/__init__.py) generates a std::span<const uint8_t> data parameter; the [text-reader header](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/text_sensor/modbus_textsensor.h) confirms the same callback signature. A span is a view and does not implicitly become an owning vector. The iterator constructor explicitly copies every byte in order, including zero and high-bit bytes, into owned storage before the script call. It performs no string conversion, truncation, offset selection or byte swapping. Allocation/copy of a small payload is intentional; no span reference is retained after callback return.

The exact response-length check `payload.size() != size_t(word_count * 2)` is unchanged and still happens before decoding/indexing. Pending-request matching, scan mask, signed16 decoding, multipliers, cache positions and all calculations remain unchanged. The constructor is source-compatible with both span and vector input containers, but that does not make the new range configuration compatible with the old Windows schema. No firmware compilation claim is inferred from this C++ source check.

## R1-02 - Directional range isolation

Replaced every deprecated force_new_range:true key with **reuse_previous_range:false**, on ALL16 readers. Applying it only at one group boundary would be insufficient: the next reader could otherwise extend that range. Since the following reader also has false, each intended block remains independent.

The2026.11.1 [migration/schema code](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/__init__.py) maps false to RangeReuse::NEVER. In the target [range builder](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/modbus_controller.cpp), can_join rejects that reuse mode; a later item can still extend a range unless that later item also refuses reuse. Same-start sharing is handled separately, so the static check also confirms16 distinct start addresses. No following auto-reuse or duplicate-start reader exists in this package. These are source-derived grouping checks, not wire observations.

## R1-03 - Response-size-derived request lengths

Removed **16** deprecated register_count settings only after comparing each prior count with the target derivation. All existing response_size values remain unchanged.

These readers are platform modbus_controller **text sensors**, internally assigned SensorValueType::RAW by the target [ModbusTextSensor constructor](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/text_sensor/modbus_textsensor.h). No unsupported scalar value_type option was added to text sensors. HEXBYTES remains their encoding; it does not change the raw callback payload or the requested word count.

Target [SensorItem::entity_count()](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/modbus_controller.h) derives non-binary RAW width from **(response_bytes+1)/2**, integer division. response_size supplies response_bytes and is measured in **BYTES**, not words or hex characters. Its mapping is visible in the target [text-sensor code generator](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/modbus_controller/text_sensor/__init__.py). Every current size is positive/even, so8bytes=4words,6=3,4=2 and2=1 exactly. No odd-byte rounding assumption is needed here.

## All affected callbacks and preserved groups

Line numbers refer to the corrected package. Each row has holding-register FC03 reads and reuse_previous_range:false. Cache offsets and expected counts are unchanged script arguments; the deleted YAML count is replaced by an equivalent derived wire width.

| Reader suffix | Callback line | Start | Inclusive end | response_size bytes | Derived words | Cache offset | reuse_previous_range |
|---|---:|---|---|---:|---:|---:|---|
| 01 | 623 | 0x0100 | 0x0103 | 8 | 4 | 0 | false |
| 02 | 637 | 0x0107 | 0x0109 | 6 | 3 | 4 | false |
| 03 | 651 | 0x010F | 0x0111 | 6 | 3 | 7 | false |
| 04 | 665 | 0x0204 | 0x0207 | 8 | 4 | 10 | false |
| 05 | 679 | 0x0210 | 0x0210 | 2 | 1 | 14 | false |
| 06 | 693 | 0x0213 | 0x0216 | 8 | 4 | 15 | false |
| 07 | 707 | 0x0218 | 0x0219 | 4 | 2 | 19 | false |
| 08 | 721 | 0x021B | 0x021B | 2 | 1 | 21 | false |
| 09 | 735 | 0x0221 | 0x0221 | 2 | 1 | 22 | false |
| 10 | 749 | 0x022A | 0x022A | 2 | 1 | 23 | false |
| 11 | 763 | 0x022C | 0x022C | 2 | 1 | 24 | false |
| 12 | 777 | 0x0230 | 0x0230 | 2 | 1 | 25 | false |
| 13 | 791 | 0x0232 | 0x0232 | 2 | 1 | 26 | false |
| 14 | 805 | 0x0238 | 0x0238 | 2 | 1 | 27 | false |
| 15 | 819 | 0xF02F | 0xF030 | 4 | 2 | 28 | false |
| 16 | 833 | 0xF04D | 0xF04E | 4 | 2 | 30 | false |

Totals preserved: **16 FC03 groups,32 unique register words, maximum4 words per request**. The four-word limit is below the protocol's32-word per-request maximum. No address gaps or semantic-HOLD words are introduced.

## R1-04 - OTA efficiency warning

The target [ESPHome OTA final validator](https://github.com/esphome/esphome/blob/2026.11.1/esphome/components/esphome/ota/__init__.py) emits an efficiency warning when an OTA password is configured alongside an API static encryption key, recommending OTA encryption to reduce flash/RAM overhead. This is an efficiency recommendation, not the span/vector C++ compile error. Source inspection explains the owner's reported warning; this correction did not rerun HA validation or measure memory savings.

**OTA authentication, API encryption and all credentials remain unchanged.** No migration, password removal, encryption-key reuse or OTA policy change was performed. The warning is intentionally left for a separate owner decision; no secret value or resolved configuration is included here.

## Preservation verification

- Exactly36 approved public IDs:28 DIRECT,5 CALCULATED,3 DIAGNOSTIC. Package supplies35 and the existing bench uptime remains the36th. No extra public entities.
- Uptime name/ID, the package include, all UART/Modbus configuration and credential references are preserved because the entire bench YAML is byte-identical to its pre-correction contents.
- Reader start addresses, raw-encoding choice, expected data bytes, script argument counts/cache offsets, high-byte-first decoding, source multipliers, signedness and calculations are unchanged.
- The pending-request policy,1000ms application completion guard,100ms watchdog,10s configurable poll interval, three-period freshness window, full-sweep gate, NaN invalidation and fault-unknown behavior are unchanged. Operating-state text still uses its explicit Unavailable marker on failure.
- Daily energy state classes remain empty. Output load remains distinguished from whole-home consumption.
- All eight AMBIGUOUS and the one UNSUPPORTED entity remain absent; no held dependencies are polled. No controls, switches, numbers, buttons, selectors, custom PDUs or write commands were added.
- Comments mentioning the old forced-range behavior were updated to describe the target isolation semantics and byte units. No unrelated refactoring.

Checks compared old/new parsed YAML while allowing only the16 vector conversions,16 isolation-key replacements and16 redundant-count removals. All remaining parsed entity/script/policy content matched; the controller's one comment change was normalized for that comparison. A separate allowlist check confirmed public IDs, exact approved word set, non-overlapping ranges, payload lengths and cache offsets. These checks do not execute the target ESPHome range builder or simulate Modbus traffic.

## Outstanding owner validation

1. Align the Windows toolchain to2026.11.1 if local target validation/building is desired; this was not performed automatically.
2. Re-synchronize the corrected package through the owner's existing process and compare its new SHA256 with HA's copy. HA/Samba files were not modified by this task, and the previously synchronized package hashes predate this correction.
3. Run full2026.11.1 configuration validation and a firmware build on the corrected files. Check that the16 span/vector compile errors and both deprecated range-option warnings are gone. The unchanged OTA efficiency warning may remain.
4. Inspect generated/runtime request groups and confirm FC03, the16 starts and lengths above,32 total words and maximum4 per request. Target compilation and grouping must not be marked PASS solely from these static checks.
5. Physical stale-data, failure/recovery and inverter register support validation remains pending. No deployment is requested or performed here.

Stop for owner review after SRNE-04D-R1. No moon landing, just a reliable inverter integration!

### File fingerprints

- Corrected package SHA256: `4fb4a88f47a051abd4621299ad31e7dc111ed903dd5bfa9b04d2befc2f638b80`
- Pre-correction package SHA256: `e3d4c82b3c2bffc08d38f04a9eecd969b913b89ec730a827545683e3c5200fae`
- Unchanged bench YAML SHA256 (before and after): `30cb9a0d3913c8af706a5653643b1bf3a6e095c85c2410155dfa1abc75154510`
