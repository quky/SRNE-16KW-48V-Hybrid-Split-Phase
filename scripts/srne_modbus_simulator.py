"""Standalone read-only Modbus RTU simulator for SRNE SPI-16K-UP synthetic fixtures.

This module implements an offline/RS485 Modbus RTU server backed by immutable
synthetic register fixtures from SRNE-04E-D. It enforces strict FC03-only,
non-mutating register access and intentionally rejects all write and
unsupported function codes with Modbus exception 0x01 (Illegal Function).
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import logging
import os
import sys
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, TextIO

if os.name == "nt":
    import msvcrt
else:  # pragma: no cover - non-Windows platforms
    msvcrt = None  # type: ignore[assignment]

from pymodbus.constants import ExcCodes
from pymodbus.exceptions import NoSuchIdException
from pymodbus.framer import FramerRTU, FramerType
from pymodbus.pdu import ExceptionResponse, ModbusPDU
from pymodbus.server import ModbusSerialServer
from pymodbus.server.requesthandler import ServerRequestHandler
from pymodbus.simulator import DataType, SimData, SimDevice

try:
    from serial import SerialException
except ImportError:  # pragma: no cover - pyserial is pinned in requirements-simulator.txt
    SerialException = OSError  # type: ignore[misc, assignment]


DEFAULT_DEVICE_ADDRESS = 1
DEFAULT_BAUDRATE = 9600
DEFAULT_BYTESIZE = 8
DEFAULT_PARITY = "N"
DEFAULT_STOPBITS = 1
DEFAULT_TIMEOUT = 3.0
DEFAULT_SCENARIO = "S1_solar_charging"
MAX_WORDS_PER_REQUEST = 32

EXPECTED_GROUP_COUNT = 40
EXPECTED_REGISTER_COUNT = 107
EXPECTED_SCENARIO_COUNT = 5
EXPECTED_ENTITY_COUNT = 73

STARTUP_BANNER = "SYNTHETIC SRNE SIMULATOR — NOT A PHYSICAL INVERTER"
LOGGER_NAME = "srne_simulator"

WRITE_FUNCTION_CODES = frozenset({5, 6, 15, 16, 21, 22, 23})
DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures"

INTERACTIVE_SCENARIO_KEYS: MappingProxyType[str, str] = MappingProxyType({
    "1": "S1_solar_charging",
    "2": "S2_battery_discharging",
    "3": "S3_utility_zero_solar",
    "4": "S4_standby",
    "5": "S5_active_fault",
})

_EXPRESSION_LABELS: dict[int, str] = {
    ExcCodes.ILLEGAL_FUNCTION: "ILLEGAL_FUNCTION (0x01)",
    ExcCodes.ILLEGAL_ADDRESS: "ILLEGAL_ADDRESS (0x02)",
    ExcCodes.ILLEGAL_VALUE: "ILLEGAL_VALUE (0x03)",
}


class FixtureValidationError(ValueError):
    """Raised when synthetic Modbus fixture files are missing, malformed, or inconsistent."""


@dataclass(frozen=True)
class RegisterGroupSpec:
    """Validated specification of one approved contiguous FC03 register group."""

    group_id: str
    phase_tier: str
    start_address: int
    register_count: int
    poll_interval_s: int
    access_policy: str


@dataclass(frozen=True)
class ScenarioData:
    """Immutable register snapshot for a single synthetic inverter scenario."""

    scenario_id: str
    title: str
    description: str
    slave_address: int
    registers: MappingProxyType[int, int]
    group_payloads: MappingProxyType[str, tuple[int, ...]]


@dataclass(frozen=True)
class LoadedFixtures:
    """Validated bundle of register groups, synthetic scenarios, and expected entity metadata."""

    groups: tuple[RegisterGroupSpec, ...]
    approved_addresses: frozenset[int]
    scenarios: MappingProxyType[str, ScenarioData]
    expected_entity_count: int


def _is_strict_int(value: Any) -> bool:
    """Return True if value is an int and not a bool."""
    return isinstance(value, int) and not isinstance(value, bool)


def _read_json_file(path: Path) -> dict[str, Any]:
    """Read and parse a required JSON fixture object."""
    if not path.is_file():
        raise FixtureValidationError(f"Required fixture file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureValidationError(f"Failed to parse JSON fixture {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FixtureValidationError(f"Fixture {path} must contain a JSON object")
    return data


def _parse_hex_address(value: Any, context: str) -> int:
    """Parse and validate a hex register string like '0x0100'."""
    if not isinstance(value, str) or not value.startswith(("0x", "0X")):
        raise FixtureValidationError(f"{context}: invalid hex address {value!r}")
    try:
        parsed = int(value, 16)
    except ValueError as exc:
        raise FixtureValidationError(f"{context}: invalid hex address {value!r}") from exc
    if not 0 <= parsed <= 0xFFFF:
        raise FixtureValidationError(f"{context}: address 0x{parsed:04X} out of 16-bit bounds")
    return parsed


def _validate_groups(groups_doc: dict[str, Any]) -> tuple[tuple[RegisterGroupSpec, ...], frozenset[int]]:
    """Validate register groups JSON and extract exact approved addresses."""
    raw_groups = groups_doc.get("groups")
    if not isinstance(raw_groups, list):
        raise FixtureValidationError("srne-register-groups.json missing 'groups' list")
    if len(raw_groups) != EXPECTED_GROUP_COUNT:
        raise FixtureValidationError(
            f"Expected {EXPECTED_GROUP_COUNT} register groups, found {len(raw_groups)}"
        )

    parsed_groups: list[RegisterGroupSpec] = []
    seen_group_ids: set[str] = set()
    approved_addrs: set[int] = set()

    for idx, entry in enumerate(raw_groups):
        if not isinstance(entry, dict):
            raise FixtureValidationError(f"Group entry {idx} must be a JSON object")
        gid = entry.get("group_id")
        if not isinstance(gid, str) or not gid:
            raise FixtureValidationError(f"Group entry {idx} missing valid 'group_id'")
        if gid in seen_group_ids:
            raise FixtureValidationError(f"Duplicate group_id: {gid}")
        seen_group_ids.add(gid)

        if entry.get("function_code") != 3:
            raise FixtureValidationError(f"Group {gid}: expected function_code=3, got {entry.get('function_code')!r}")
        if entry.get("slave_address") != DEFAULT_DEVICE_ADDRESS:
            raise FixtureValidationError(
                f"Group {gid}: expected slave_address={DEFAULT_DEVICE_ADDRESS}, got {entry.get('slave_address')!r}"
            )

        start_dec = entry.get("start_address_dec")
        start_hex = _parse_hex_address(entry.get("start_address_hex"), f"Group {gid}")
        if not _is_strict_int(start_dec) or start_dec != start_hex:
            raise FixtureValidationError(
                f"Group {gid}: start_address_dec ({start_dec!r}) != start_address_hex (0x{start_hex:04X})"
            )

        count = entry.get("register_count")
        if not _is_strict_int(count) or not (1 <= count <= MAX_WORDS_PER_REQUEST):
            raise FixtureValidationError(
                f"Group {gid}: register_count {count!r} outside 1..{MAX_WORDS_PER_REQUEST}"
            )

        regs = entry.get("registers")
        if not isinstance(regs, list) or len(regs) != count:
            raise FixtureValidationError(
                f"Group {gid}: registers list length does not match register_count={count}"
            )

        for offset, reg in enumerate(regs):
            if not isinstance(reg, dict):
                raise FixtureValidationError(f"Group {gid} register {offset} must be an object")
            reg_dec = reg.get("address_dec")
            reg_hex = _parse_hex_address(reg.get("address_hex"), f"Group {gid} reg {offset}")
            expected_addr = start_dec + offset
            if not _is_strict_int(reg_dec) or reg_dec != reg_hex or reg_dec != expected_addr:
                raise FixtureValidationError(
                    f"Group {gid} reg {offset}: expected address 0x{expected_addr:04X} ({expected_addr}), "
                    f"got {reg.get('address_hex')!r}/{reg_dec!r}"
                )
            if reg_dec in approved_addrs:
                raise FixtureValidationError(f"Duplicate register address 0x{reg_dec:04X} across groups")
            approved_addrs.add(reg_dec)

        poll_s = entry.get("poll_interval_s")
        if not _is_strict_int(poll_s) or poll_s <= 0:
            raise FixtureValidationError(f"Group {gid}: invalid poll_interval_s={poll_s!r}")

        parsed_groups.append(
            RegisterGroupSpec(
                group_id=gid,
                phase_tier=str(entry.get("phase_tier", "")),
                start_address=start_dec,
                register_count=count,
                poll_interval_s=poll_s,
                access_policy=str(entry.get("access_policy", "")),
            )
        )

    if len(approved_addrs) != EXPECTED_REGISTER_COUNT:
        raise FixtureValidationError(
            f"Expected {EXPECTED_REGISTER_COUNT} unique approved registers, found {len(approved_addrs)}"
        )

    return tuple(parsed_groups), frozenset(approved_addrs)


def _validate_scenarios(
    scenarios_doc: dict[str, Any],
    groups: tuple[RegisterGroupSpec, ...],
    approved_addresses: frozenset[int],
) -> MappingProxyType[str, ScenarioData]:
    """Validate synthetic scenarios JSON against approved register definitions."""
    raw_scenarios = scenarios_doc.get("scenarios")
    if not isinstance(raw_scenarios, list):
        raise FixtureValidationError("srne-synthetic-scenarios.json missing 'scenarios' list")
    if len(raw_scenarios) != EXPECTED_SCENARIO_COUNT:
        raise FixtureValidationError(
            f"Expected {EXPECTED_SCENARIO_COUNT} scenarios, found {len(raw_scenarios)}"
        )

    expected_hex_keys = {f"0x{addr:04X}" for addr in approved_addresses}
    expected_group_ids = {g.group_id for g in groups}
    scenarios: dict[str, ScenarioData] = {}

    for idx, entry in enumerate(raw_scenarios):
        if not isinstance(entry, dict):
            raise FixtureValidationError(f"Scenario entry {idx} must be a JSON object")
        sid = entry.get("scenario_id")
        if not isinstance(sid, str) or not sid:
            raise FixtureValidationError(f"Scenario entry {idx} missing valid 'scenario_id'")
        if sid in scenarios:
            raise FixtureValidationError(f"Duplicate scenario_id: {sid}")

        slave_addr = entry.get("slave_address")
        if slave_addr != DEFAULT_DEVICE_ADDRESS:
            raise FixtureValidationError(
                f"Scenario {sid}: expected slave_address={DEFAULT_DEVICE_ADDRESS}, got {slave_addr!r}"
            )

        raw_regs = entry.get("registers")
        if not isinstance(raw_regs, dict):
            raise FixtureValidationError(f"Scenario {sid}: missing 'registers' mapping")
        actual_keys = set(raw_regs.keys())
        if actual_keys != expected_hex_keys:
            missing = sorted(expected_hex_keys - actual_keys)[:5]
            extra = sorted(actual_keys - expected_hex_keys)[:5]
            raise FixtureValidationError(
                f"Scenario {sid}: register set mismatch (missing={missing}, extra={extra})"
            )

        reg_map: dict[int, int] = {}
        for hex_key, info in raw_regs.items():
            addr = _parse_hex_address(hex_key, f"Scenario {sid}")
            if not isinstance(info, dict):
                raise FixtureValidationError(f"Scenario {sid} {hex_key}: value must be an object")
            addr_dec = info.get("address_dec")
            if not _is_strict_int(addr_dec) or addr_dec != addr:
                raise FixtureValidationError(
                    f"Scenario {sid} {hex_key}: address_dec {addr_dec!r} != {addr}"
                )
            raw_u16 = info.get("raw_u16")
            if not _is_strict_int(raw_u16) or not (0 <= raw_u16 <= 0xFFFF):
                raise FixtureValidationError(
                    f"Scenario {sid} {hex_key}: raw_u16 {raw_u16!r} outside 0..65535"
                )
            expected_raw_hex = f"0x{raw_u16:04X}"
            if info.get("raw_hex") != expected_raw_hex:
                raise FixtureValidationError(
                    f"Scenario {sid} {hex_key}: raw_hex {info.get('raw_hex')!r} != {expected_raw_hex!r}"
                )
            reg_map[addr] = raw_u16

        raw_payloads = entry.get("group_payloads")
        if not isinstance(raw_payloads, dict):
            raise FixtureValidationError(f"Scenario {sid}: missing 'group_payloads' mapping")
        if set(raw_payloads.keys()) != expected_group_ids:
            raise FixtureValidationError(f"Scenario {sid}: group_payloads keys do not match 40 approved groups")

        immutable_payloads: dict[str, tuple[int, ...]] = {}
        for grp in groups:
            payload = raw_payloads[grp.group_id]
            if not isinstance(payload, list) or len(payload) != grp.register_count:
                raise FixtureValidationError(
                    f"Scenario {sid} {grp.group_id}: expected {grp.register_count} words"
                )
            if not all(_is_strict_int(w) and 0 <= w <= 0xFFFF for w in payload):
                raise FixtureValidationError(
                    f"Scenario {sid} {grp.group_id}: payload contains invalid uint16 element"
                )
            expected_slice = tuple(reg_map[grp.start_address + i] for i in range(grp.register_count))
            if tuple(payload) != expected_slice:
                raise FixtureValidationError(
                    f"Scenario {sid} {grp.group_id}: group_payloads diverges from flat registers map"
                )
            immutable_payloads[grp.group_id] = expected_slice

        scenarios[sid] = ScenarioData(
            scenario_id=sid,
            title=str(entry.get("title", "")),
            description=str(entry.get("description", "")),
            slave_address=slave_addr,
            registers=MappingProxyType(reg_map),
            group_payloads=MappingProxyType(immutable_payloads),
        )

    if DEFAULT_SCENARIO not in scenarios:
        raise FixtureValidationError(f"Default scenario {DEFAULT_SCENARIO!r} missing from scenarios fixture")

    return MappingProxyType(scenarios)


def _validate_expected_entities(
    expected_doc: dict[str, Any], scenario_ids: Sequence[str]
) -> int:
    """Validate expected entities JSON summary and scenario alignment."""
    summary = expected_doc.get("summary")
    if not isinstance(summary, dict):
        raise FixtureValidationError("srne-expected-entities.json missing 'summary' object")
    total = summary.get("total_public_entities")
    if total != EXPECTED_ENTITY_COUNT:
        raise FixtureValidationError(
            f"Expected total_public_entities={EXPECTED_ENTITY_COUNT}, got {total!r}"
        )
    exp_scenarios = expected_doc.get("scenarios")
    if not isinstance(exp_scenarios, dict) or set(exp_scenarios.keys()) != set(scenario_ids):
        raise FixtureValidationError(
            "srne-expected-entities.json scenarios do not match srne-synthetic-scenarios.json"
        )
    return total


def load_and_validate_fixtures(fixtures_dir: Path | None = None) -> LoadedFixtures:
    """Load and cross-validate all SRNE-04E-D synthetic fixture JSON files."""
    base_dir = fixtures_dir if fixtures_dir is not None else DEFAULT_FIXTURES_DIR
    if not base_dir.is_dir():
        raise FixtureValidationError(f"Fixtures directory does not exist: {base_dir}")

    groups_doc = _read_json_file(base_dir / "srne-register-groups.json")
    scenarios_doc = _read_json_file(base_dir / "srne-synthetic-scenarios.json")
    expected_doc = _read_json_file(base_dir / "srne-expected-entities.json")

    groups, approved_addresses = _validate_groups(groups_doc)
    scenarios = _validate_scenarios(scenarios_doc, groups, approved_addresses)
    entity_count = _validate_expected_entities(expected_doc, tuple(scenarios.keys()))

    return LoadedFixtures(
        groups=groups,
        approved_addresses=approved_addresses,
        scenarios=scenarios,
        expected_entity_count=entity_count,
    )


@dataclass(frozen=True)
class ActiveSnapshot:
    """Immutable snapshot pairing the active scenario with its switch count."""

    scenario: ScenarioData
    switch_count: int = 0


class SRNEReadOnlyContext:
    """Immutable FC03-only datastore implementing exact zero-based wire addressing.

    Unlike PyModbus's default ``SimDevice``/``SimCore``, this context:
    - Does not fill undocumented register gaps with zeros.
    - Returns ``ExcCodes.ILLEGAL_FUNCTION`` (0x01) for any function code != 3 or write attempt.
    - Enforces ``1 <= count <= MAX_WORDS_PER_REQUEST`` (32) with ``ExcCodes.ILLEGAL_VALUE`` (0x03).
    - Rejects any request touching an unapproved address with ``ExcCodes.ILLEGAL_ADDRESS`` (0x02).
    - Supports atomic replacement of the entire active immutable scenario snapshot without
      mutating register entries or restarting the server. Single-response atomicity is guaranteed;
      multi-request ESPHome polling sweeps may span a transition until subsequent polls complete.
    """

    def __init__(
        self,
        scenario: ScenarioData,
        groups: tuple[RegisterGroupSpec, ...],
        *,
        device_id: int = DEFAULT_DEVICE_ADDRESS,
        max_words: int = MAX_WORDS_PER_REQUEST,
        scenarios: MappingProxyType[str, ScenarioData] | None = None,
        started_at: float | None = None,
    ) -> None:
        if not (1 <= device_id <= 247):
            raise ValueError(f"Invalid Modbus slave device_id={device_id}; expected 1..247")
        if max_words < 1 or max_words > 125:
            raise ValueError(f"Invalid max_words={max_words}")
        if scenarios is None:
            scenarios_map: MappingProxyType[str, ScenarioData] = MappingProxyType(
                {scenario.scenario_id: scenario}
            )
        else:
            if scenario.scenario_id not in scenarios:
                raise ValueError(
                    f"Initial scenario {scenario.scenario_id!r} not present in preloaded scenarios"
                )
            scenarios_map = scenarios
        self.device_id = device_id
        self.groups = groups
        self.max_words = max_words
        self._scenarios = scenarios_map
        self._active_snapshot = ActiveSnapshot(scenario=scenario, switch_count=0)
        self._started_at = time.monotonic() if started_at is None else started_at

    @property
    def scenario(self) -> ScenarioData:
        """Currently active immutable scenario."""
        return self._active_snapshot.scenario

    @property
    def registers(self) -> MappingProxyType[int, int]:
        """Read-only view of all approved raw uint16 register values in the active snapshot."""
        return self._active_snapshot.scenario.registers

    @property
    def switch_count(self) -> int:
        """Number of completed scenario transitions since startup."""
        return self._active_snapshot.switch_count

    @property
    def elapsed_seconds(self) -> float:
        """Elapsed simulator runtime in seconds."""
        return max(0.0, time.monotonic() - self._started_at)

    @property
    def available_scenarios(self) -> MappingProxyType[str, ScenarioData]:
        """All preloaded immutable scenarios."""
        return self._scenarios

    def switch_scenario(self, scenario_id: str) -> tuple[bool, ScenarioData, ScenarioData]:
        """Atomically replace the active immutable scenario snapshot.

        Returns ``(changed, previous_scenario, current_scenario)``. Selecting the already
        active scenario leaves ``switch_count`` unchanged and returns ``changed=False``.
        """
        target = self._scenarios.get(scenario_id)
        if target is None:
            raise KeyError(f"Unknown scenario_id={scenario_id!r}")
        current = self._active_snapshot
        if target.scenario_id == current.scenario.scenario_id:
            return False, current.scenario, target
        self._active_snapshot = ActiveSnapshot(
            scenario=target,
            switch_count=current.switch_count + 1,
        )
        return True, current.scenario, target

    def device_ids(self) -> list[int]:
        """Return configured Modbus slave device IDs (implements server context contract)."""
        return [self.device_id]

    async def async_getValues(
        self, device_id: int, func_code: int, address: int, count: int = 1
    ) -> list[int] | ExcCodes:
        """Read contiguous approved FC03 registers atomically from one consistent snapshot."""
        if device_id != self.device_id:
            raise NoSuchIdException(f"Unknown Modbus device_id={device_id}")
        if func_code != 3:
            return ExcCodes.ILLEGAL_FUNCTION
        if not (1 <= count <= self.max_words):
            return ExcCodes.ILLEGAL_VALUE
        if address < 0 or address + count - 1 > 0xFFFF:
            return ExcCodes.ILLEGAL_ADDRESS
        # Capture one immutable snapshot reference for the entire response.
        registers = self._active_snapshot.scenario.registers
        for addr in range(address, address + count):
            if addr not in registers:
                return ExcCodes.ILLEGAL_ADDRESS
        return [registers[addr] for addr in range(address, address + count)]

    async def async_setValues(
        self,
        device_id: int,
        func_code: int,
        address: int,
        values: Sequence[int] | Sequence[bool],
    ) -> ExcCodes:
        """Reject all write attempts without mutating simulator state."""
        _ = (func_code, address, values)
        if device_id != self.device_id:
            raise NoSuchIdException(f"Unknown Modbus device_id={device_id}")
        return ExcCodes.ILLEGAL_FUNCTION


def _extract_request_bounds(pdu: ModbusPDU) -> tuple[int | None, int | None]:
    """Extract starting register address and word count from decoded request PDU."""
    fc = pdu.function_code
    if fc in (7, 11, 12, 17, 43):
        return None, None
    if fc == 23:
        return getattr(pdu, "read_address", None), getattr(pdu, "read_count", None)
    addr = getattr(pdu, "address", None)
    if fc in (5, 6, 22):
        return addr, 1
    return addr, getattr(pdu, "count", None)


def _format_addr_count(addr: int | None, count: int | None) -> tuple[str, str]:
    """Format start address and count fields safely for structured request logs."""
    addr_str = f"0x{addr:04X} ({addr})" if isinstance(addr, int) else "n/a"
    count_str = str(count) if isinstance(count, int) else "n/a"
    return addr_str, count_str


class SRNERequestHandler(ServerRequestHandler):
    """Protocol-level request handler enforcing strict FC03-only Modbus RTU behavior."""

    server: SRNEModbusSerialServer

    def callback_data(self, data: bytes, addr: tuple | None = None) -> int:
        """Handle incoming RTU bytes, rejecting unregistered function codes with 0x01 if addressed to us."""
        used = super().callback_data(data, addr)
        if (
            used == 0
            and len(data) >= FramerRTU.MIN_SIZE
            and data[0] == self.server.device_id
            and data[1] < 0x80
            and data[1] not in self.server.decoder.pdu_table
        ):
            crc_val = (int(data[-2]) << 8) | int(data[-1])
            if FramerRTU.check_CRC(data[:-2], crc_val):
                fc = int(data[1])
                self.server.logger.warning(
                    "Modbus request REJECTED dev=%d fc=0x%02X (%d) start=n/a count=n/a "
                    "reason=UNREGISTERED_FUNCTION_CODE exception=0x01 (ILLEGAL_FUNCTION)",
                    data[0],
                    fc,
                    fc,
                )
                response = ExceptionResponse(fc, ExcCodes.ILLEGAL_FUNCTION, device_id=data[0])
                self.server_send(response, addr)
                return len(data)
        return used

    async def handle_request(self, pdu: ModbusPDU) -> None:
        """Process one decoded Modbus PDU with strict FC03-only guard and detailed logging."""
        dev_id = pdu.dev_id
        fc = pdu.function_code
        addr, count = _extract_request_bounds(pdu)
        addr_str, count_str = _format_addr_count(addr, count)

        if dev_id != self.server.device_id:
            self.server.logger.debug(
                "Ignored request for non-matching dev=%d (expected dev=%d) fc=0x%02X (%d) start=%s count=%s",
                dev_id,
                self.server.device_id,
                fc,
                fc,
                addr_str,
                count_str,
            )
            return

        if fc != 3:
            reason = "WRITE_REJECTED_READ_ONLY" if fc in WRITE_FUNCTION_CODES else "UNSUPPORTED_FUNCTION_CODE"
            self.server.logger.warning(
                "Modbus request REJECTED dev=%d fc=0x%02X (%d) start=%s count=%s reason=%s "
                "exception=0x01 (ILLEGAL_FUNCTION)",
                dev_id,
                fc,
                fc,
                addr_str,
                count_str,
                reason,
            )
            response = ExceptionResponse(
                fc,
                ExcCodes.ILLEGAL_FUNCTION,
                device_id=dev_id,
                transaction=pdu.transaction_id,
            )
            self.server_send(response, self.last_addr)
            return

        try:
            response = await pdu.datastore_update(self.server.context, dev_id)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover - defensive guard
            self.server.logger.error(
                "Internal datastore error dev=%d fc=0x%02X (%d) start=%s count=%s: %s",
                dev_id,
                fc,
                fc,
                addr_str,
                count_str,
                exc,
            )
            response = ExceptionResponse(fc, ExcCodes.DEVICE_FAILURE)

        response.transaction_id = pdu.transaction_id
        response.dev_id = dev_id

        if isinstance(response, ExceptionResponse):
            exc_code = response.exception_code
            exc_label = _EXPRESSION_LABELS.get(exc_code, f"0x{exc_code:02X}")
            self.server.logger.warning(
                "Modbus request REJECTED dev=%d fc=0x%02X (%d) start=%s count=%s "
                "reason=FC03_VALIDATION_FAILED exception=%s",
                dev_id,
                fc,
                fc,
                addr_str,
                count_str,
                exc_label,
            )
        else:
            regs = list(getattr(response, "registers", []))
            self.server.logger.info(
                "Modbus request OK dev=%d fc=0x%02X (%d) start=%s count=%s outcome=OK",
                dev_id,
                fc,
                fc,
                addr_str,
                count_str,
            )
            self.server.logger.debug(
                "Modbus response raw words dev=%d fc=0x%02X start=%s count=%d hex=%s dec=%s",
                dev_id,
                fc,
                addr_str,
                len(regs),
                [f"0x{w:04X}" for w in regs],
                regs,
            )

        self.server_send(response, self.last_addr)


class SRNEModbusSerialServer(ModbusSerialServer):
    """PyModbus 3.16.2 Modbus RTU serial server wired directly to SRNEReadOnlyContext."""

    def __init__(
        self,
        context: SRNEReadOnlyContext,
        *,
        port: str,
        baudrate: int = DEFAULT_BAUDRATE,
        bytesize: int = DEFAULT_BYTESIZE,
        parity: str = DEFAULT_PARITY,
        stopbits: int = DEFAULT_STOPBITS,
        timeout: float = DEFAULT_TIMEOUT,
        logger: logging.Logger | None = None,
    ) -> None:
        # Construct a minimal placeholder SimDevice so ModbusBaseServer initializes
        # cleanly without deprecated ModbusServerContext warnings, then replace self.context.
        placeholder = SimDevice(
            id=context.device_id,
            simdata=[SimData(address=0x000B, values=[0], datatype=DataType.REGISTERS, readonly=True)],
        )
        super().__init__(
            placeholder,
            framer=FramerType.RTU,
            port=port,
            stopbits=stopbits,
            bytesize=bytesize,
            parity=parity,
            baudrate=baudrate,
            timeout=timeout,
            ignore_missing_devices=True,
            broadcast_enable=False,
        )
        self.context = context  # type: ignore[assignment]
        self.srne_context = context
        self.device_id = context.device_id
        self.logger = logger or logging.getLogger(LOGGER_NAME)

    def callback_new_connection(self) -> SRNERequestHandler:
        """Instantiate our strict FC03-only RTU request handler."""
        return SRNERequestHandler(
            self, self.trace_packet, self.trace_pdu, self.trace_connect
        )


def configure_logging(level_name: str) -> logging.Logger:
    """Configure timestamped simulator logging without leaking host/credential details."""
    numeric_level = getattr(logging, level_name.upper(), logging.INFO)
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(numeric_level)
    logger.propagate = False
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)

    pymodbus_logger = logging.getLogger("pymodbus")
    pymodbus_logger.setLevel(logging.DEBUG if numeric_level <= logging.DEBUG else logging.WARNING)
    return logger


def format_elapsed(seconds: float) -> str:
    """Format elapsed runtime seconds concisely as HH:MM:SS (X.Xs)."""
    total_int = int(max(0.0, seconds))
    hours, rem = divmod(total_int, 3600)
    minutes, secs = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d} ({seconds:.1f}s)"


class InteractiveConsoleController:
    """Non-blocking interactive console controller for runtime scenario switching."""

    def __init__(
        self,
        context: SRNEReadOnlyContext,
        *,
        port: str,
        logger: logging.Logger,
        output_stream: TextIO | None = None,
        shutdown_callback: Callable[[], None] | None = None,
    ) -> None:
        self.context = context
        self.port = port
        self.logger = logger
        self._out: TextIO = output_stream if output_stream is not None else sys.stdout
        self._shutdown_callback = shutdown_callback

    def _write(self, text: str) -> None:
        self._out.write(text + "\n")
        self._out.flush()

    def format_help(self) -> str:
        """Return interactive operator command summary."""
        lines = [
            "Interactive Commands:",
            "  1 - S1_solar_charging",
            "  2 - S2_battery_discharging",
            "  3 - S3_utility_zero_solar",
            "  4 - S4_standby",
            "  5 - S5_active_fault",
            "  s - Display current simulator status",
            "  h - Display available commands",
            "  q - Gracefully stop the simulator",
        ]
        return "\n".join(lines)

    def format_status(self) -> str:
        """Return current synthetic simulator status summary."""
        active = self.context.scenario
        lines = [
            "--- Simulator Status ---",
            f"Active Scenario      : {active.scenario_id} — {active.title}",
            f"Scenario Description : {active.description}",
            f"Device Address       : {self.context.device_id} (0x{self.context.device_id:02X})",
            f"Serial Configuration : port={self.port}  {DEFAULT_BAUDRATE},{DEFAULT_PARITY},{DEFAULT_BYTESIZE},{DEFAULT_STOPBITS} (Modbus RTU)",
            f"Register Coverage    : {len(self.context.groups)} approved FC03 groups / {len(self.context.registers)} unique words / max {self.context.max_words} words/req",
            f"Scenario Switch Count: {self.context.switch_count}",
            f"Elapsed Runtime      : {format_elapsed(self.context.elapsed_seconds)}",
            "Read-Only Policy     : FC03 ONLY (atomic per-response snapshot; no register mutation)",
            "------------------------",
        ]
        return "\n".join(lines)

    def process_command(self, raw_line: str) -> bool:
        """Process one console line; return False only when simulator should stop."""
        cmd = raw_line.strip().lower()
        if not cmd:
            return True

        if cmd in INTERACTIVE_SCENARIO_KEYS:
            target_id = INTERACTIVE_SCENARIO_KEYS[cmd]
            changed, prev_sc, new_sc = self.context.switch_scenario(target_id)
            if changed:
                self.logger.info(
                    "Scenario transition: %s -> %s (switch_count=%d)",
                    prev_sc.scenario_id,
                    new_sc.scenario_id,
                    self.context.switch_count,
                )
                self._write(
                    f"Switched scenario: {prev_sc.scenario_id} -> {new_sc.scenario_id} "
                    f"(switch_count={self.context.switch_count}; atomic per FC03 response)"
                )
            else:
                self.logger.info(
                    "Scenario %s already active (no transition; switch_count=%d)",
                    new_sc.scenario_id,
                    self.context.switch_count,
                )
                self._write(
                    f"Scenario {new_sc.scenario_id} is already active (switch_count={self.context.switch_count})."
                )
            return True

        if cmd == "s":
            self._write(self.format_status())
            return True

        if cmd == "h":
            self._write(self.format_help())
            return True

        if cmd == "q":
            self.logger.info("Interactive quit command ('q') received; shutting down gracefully.")
            self._write("Graceful shutdown requested...")
            if self._shutdown_callback is not None:
                self._shutdown_callback()
            return False

        self.logger.warning("Invalid interactive console command ignored: %r", raw_line.strip())
        self._write(f"Invalid command {raw_line.strip()!r}. Type 'h' for available commands.")
        return True

    def _console_reader_worker(
        self,
        loop: asyncio.AbstractEventLoop,
        queue: asyncio.Queue[str | None],
        input_stream: TextIO | None,
        stop_event: threading.Event,
    ) -> None:
        """Read console lines or Windows keypresses without blocking the asyncio loop."""
        use_windows_tty = (
            input_stream is None
            and os.name == "nt"
            and msvcrt is not None
            and sys.stdin is not None
            and sys.stdin.isatty()
        )
        if use_windows_tty and msvcrt is not None:
            chars: list[str] = []
            while not stop_event.is_set():
                if not msvcrt.kbhit():
                    time.sleep(0.05)
                    continue
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    # Consume second scan code byte of extended key cleanly.
                    if msvcrt.kbhit():
                        msvcrt.getwch()
                    continue
                if ch == "\x03":
                    loop.call_soon_threadsafe(queue.put_nowait, "q")
                    return
                if ch == "\x1a":
                    loop.call_soon_threadsafe(queue.put_nowait, None)
                    return
                if ch in ("\r", "\n"):
                    sys.stdout.write("\n")
                    sys.stdout.flush()
                    line = "".join(chars)
                    chars.clear()
                    loop.call_soon_threadsafe(queue.put_nowait, line)
                elif ch == "\x08":
                    if chars:
                        chars.pop()
                        sys.stdout.write("\b \b")
                        sys.stdout.flush()
                else:
                    chars.append(ch)
                    sys.stdout.write(ch)
                    sys.stdout.flush()
            return

        stream: TextIO = input_stream if input_stream is not None else sys.stdin
        while not stop_event.is_set():
            try:
                line = stream.readline()
            except (OSError, ValueError):
                break
            if line == "":
                with contextlib.suppress(RuntimeError):
                    loop.call_soon_threadsafe(queue.put_nowait, None)
                break
            with contextlib.suppress(RuntimeError):
                loop.call_soon_threadsafe(queue.put_nowait, line)

    async def run(
        self,
        input_stream: TextIO | None = None,
        *,
        stop_event: threading.Event | None = None,
    ) -> None:
        """Run interactive console loop concurrently with Modbus RTU serving."""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue[str | None] = asyncio.Queue()
        signal_stop = stop_event if stop_event is not None else threading.Event()
        thread = threading.Thread(
            target=self._console_reader_worker,
            args=(loop, queue, input_stream, signal_stop),
            name="srne-console-reader",
            daemon=True,
        )
        self._write("Interactive console active. Type 'h' for help, 's' for status, 'q' to quit.")
        thread.start()
        try:
            while not signal_stop.is_set():
                item = await queue.get()
                if item is None:
                    self.logger.info("Interactive console reached EOF; shutting down gracefully.")
                    if self._shutdown_callback is not None:
                        self._shutdown_callback()
                    break
                if not self.process_command(item):
                    break
        finally:
            signal_stop.set()
            if input_stream is not None:
                thread.join(timeout=0.5)


def format_startup_banner(
    scenario: ScenarioData,
    *,
    port: str,
    device_id: int = DEFAULT_DEVICE_ADDRESS,
    group_count: int = EXPECTED_GROUP_COUNT,
    register_count: int = EXPECTED_REGISTER_COUNT,
    interactive: bool = False,
) -> str:
    """Build prominent operator startup banner distinguishing synthetic simulation from hardware."""
    lines = [
        "=" * 72,
        STARTUP_BANNER,
        "=" * 72,
        f"Scenario         : {scenario.scenario_id} — {scenario.title}",
        f"Serial Config    : port={port}  {DEFAULT_BAUDRATE},{DEFAULT_PARITY},{DEFAULT_BYTESIZE},{DEFAULT_STOPBITS}  (Modbus RTU)",
        f"Device Address   : {device_id} (0x{device_id:02X})",
        f"Register Coverage: {group_count} approved FC03 groups / {register_count} unique words / max {MAX_WORDS_PER_REQUEST} words/req",
        "Read-Only Policy : FC03 ONLY; writes (FC05/06/15/16/22/23) and other FCs return exception 0x01; gaps return 0x02",
    ]
    if interactive:
        lines.append(
            "Interactive Mode : ENABLED (keys 1-5 switch scenarios, s=status, h=help, q=quit; atomic per FC03 response)"
        )
    lines.append("=" * 72)
    return "\n".join(lines)


def build_arg_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for the standalone SRNE Modbus RTU simulator."""
    parser = argparse.ArgumentParser(
        description=(
            "Standalone read-only Modbus RTU simulator for SRNE SPI-16K-UP synthetic fixtures "
            "(FC03 only; explicitly requires --port when starting the serial server)."
        )
    )
    parser.add_argument(
        "--port",
        default=None,
        help="Explicit serial COM port to open (for example COM5). Never auto-selected.",
    )
    parser.add_argument(
        "--scenario",
        default=DEFAULT_SCENARIO,
        help=f"Synthetic scenario ID to serve initially (default: {DEFAULT_SCENARIO}).",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List all approved synthetic scenarios and exit without opening a serial port.",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Load and validate fixtures and selected scenario without opening a serial port.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Enable interactive console controls (1-5 switch scenario, s status, h help, q quit) without restarting.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "debug", "info", "warning", "error"],
        help="Logging verbosity (default: INFO; use DEBUG for returned raw register words).",
    )
    parser.add_argument(
        "--fixtures-dir",
        type=Path,
        default=None,
        help="Optional override path to synthetic fixture JSON files.",
    )
    return parser


async def run_server_async(
    context: SRNEReadOnlyContext,
    *,
    port: str,
    logger: logging.Logger,
    interactive: bool = False,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> None:
    """Create and run the ModbusSerialServer with optional non-blocking interactive console."""
    server = SRNEModbusSerialServer(context, port=port, logger=logger)
    if not interactive:
        try:
            await server.serve_forever()
        finally:
            await server.shutdown()
        return

    stop_event = threading.Event()
    server_task = asyncio.create_task(server.serve_forever(), name="srne-rtu-server")

    def _trigger_shutdown() -> None:
        stop_event.set()
        asyncio.create_task(server.shutdown())

    controller = InteractiveConsoleController(
        context,
        port=port,
        logger=logger,
        output_stream=output_stream,
        shutdown_callback=_trigger_shutdown,
    )
    console_task = asyncio.create_task(
        controller.run(input_stream=input_stream, stop_event=stop_event),
        name="srne-console-task",
    )

    try:
        done, _ = await asyncio.wait(
            {server_task, console_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if server_task in done and not server_task.cancelled():
            exc = server_task.exception()
            if exc is not None:
                raise exc
    finally:
        stop_event.set()
        with contextlib.suppress(Exception):
            await server.shutdown()
        for task in (console_task, server_task):
            if not task.done():
                task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint returning explicit process exit code."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    logger = configure_logging(args.log_level)

    try:
        fixtures = load_and_validate_fixtures(args.fixtures_dir)
    except FixtureValidationError as exc:
        print(f"Fixture validation error: {exc}", file=sys.stderr)
        return 1

    if args.list_scenarios:
        print(f"{STARTUP_BANNER}")
        print(f"Available scenarios ({len(fixtures.scenarios)}):")
        for sid, sc in fixtures.scenarios.items():
            marker = " [default]" if sid == DEFAULT_SCENARIO else ""
            print(f"  - {sid}{marker}: {sc.title}")
        return 0

    scenario = fixtures.scenarios.get(args.scenario)
    if scenario is None:
        valid_ids = ", ".join(fixtures.scenarios.keys())
        print(
            f"Error: Unknown scenario {args.scenario!r}. Valid scenarios: {valid_ids}",
            file=sys.stderr,
        )
        return 2

    if args.validate_only:
        print(f"{STARTUP_BANNER}")
        print(
            f"Validation OK: scenario={scenario.scenario_id!r}, "
            f"groups={len(fixtures.groups)}, registers={len(fixtures.approved_addresses)}, "
            f"entities={fixtures.expected_entity_count}, policy=FC03-only (no serial port opened)"
        )
        return 0

    port = args.port.strip() if isinstance(args.port, str) else ""
    if not port:
        print(
            "Error: --port is required to start the serial RTU server "
            "(for example: --port COM5). No serial port is auto-selected.",
            file=sys.stderr,
        )
        return 2

    context = SRNEReadOnlyContext(
        scenario,
        fixtures.groups,
        device_id=DEFAULT_DEVICE_ADDRESS,
        scenarios=fixtures.scenarios,
    )
    print(
        format_startup_banner(
            scenario,
            port=port,
            device_id=DEFAULT_DEVICE_ADDRESS,
            group_count=len(fixtures.groups),
            register_count=len(fixtures.approved_addresses),
            interactive=args.interactive,
        ),
        flush=True,
    )
    logger.info(
        "Starting read-only Modbus RTU simulator on port=%s scenario=%s dev=%d (%d,%s,%d,%d) interactive=%s",
        port,
        scenario.scenario_id,
        DEFAULT_DEVICE_ADDRESS,
        DEFAULT_BAUDRATE,
        DEFAULT_PARITY,
        DEFAULT_BYTESIZE,
        DEFAULT_STOPBITS,
        args.interactive,
    )

    try:
        asyncio.run(
            run_server_async(
                context,
                port=port,
                logger=logger,
                interactive=args.interactive,
            )
        )
    except KeyboardInterrupt:
        logger.info("Shutdown requested via Ctrl+C (KeyboardInterrupt); exiting cleanly.")
        return 0
    except (SerialException, OSError, RuntimeError) as exc:
        logger.error("Serial RTU server failed on port=%s: %s", port, exc)
        print(f"Serial server error on port {port!r}: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
