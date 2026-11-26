"""Offline unit and in-memory Modbus RTU protocol tests for srne_modbus_simulator."""

from __future__ import annotations

import asyncio
import contextlib
import io
import json
import logging
import shutil
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from pymodbus.constants import ExcCodes
from pymodbus.exceptions import NoSuchIdException
from pymodbus.framer import FramerRTU

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import srne_modbus_simulator as sim  # noqa: E402


def build_rtu_frame(dev_id: int, pdu_bytes: bytes) -> bytes:
    """Wrap raw function-code+payload PDU in Modbus RTU slave ID + big-endian swapped CRC-16."""
    body = bytes([dev_id]) + pdu_bytes
    crc = FramerRTU.compute_CRC(body)
    return body + crc.to_bytes(2, "big")


def verify_and_unwrap_rtu_frame(frame: bytes) -> tuple[int, int, bytes]:
    """Validate Modbus RTU CRC-16 and return (dev_id, function_code, payload_after_fc)."""
    if len(frame) < 4:
        raise AssertionError(f"RTU frame shorter than 4 bytes: {frame.hex(' ')}")
    crc_val = (frame[-2] << 8) | frame[-1]
    if not FramerRTU.check_CRC(frame[:-2], crc_val):
        raise AssertionError(f"Invalid RTU CRC on frame: {frame.hex(' ')}")
    return frame[0], frame[1], frame[2:-2]


class _InMemoryRTUTransport(asyncio.Transport):
    """Minimal asyncio.Transport double capturing server RTU wire bytes into an asyncio.Queue."""

    def __init__(self, loop: asyncio.AbstractEventLoop) -> None:
        super().__init__()
        self._loop = loop
        self.written_frames: asyncio.Queue[bytes] = asyncio.Queue()
        self.closed = False

    def write(self, data: bytes | bytearray | memoryview) -> None:
        self.written_frames.put_nowait(bytes(data))

    def is_closing(self) -> bool:
        return self.closed

    def close(self) -> None:
        self.closed = True


class TestFixtureLoadingAndValidation(unittest.TestCase):
    """Application-level tests covering synthetic fixture loading and structural checks."""

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()

    def test_all_five_scenarios_and_counts_load(self) -> None:
        expected_ids = {
            "S1_solar_charging",
            "S2_battery_discharging",
            "S3_utility_zero_solar",
            "S4_standby",
            "S5_active_fault",
        }
        self.assertEqual(len(self.fixtures.groups), 40)
        self.assertEqual(len(self.fixtures.approved_addresses), 107)
        self.assertEqual(set(self.fixtures.scenarios.keys()), expected_ids)
        self.assertEqual(self.fixtures.expected_entity_count, 73)

    def test_missing_fixture_directory_fails_safely(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "does-not-exist"
            with self.assertRaises(sim.FixtureValidationError):
                sim.load_and_validate_fixtures(missing)

    def test_missing_and_corrupt_fixture_files_fail_safely(self) -> None:
        src_dir = sim.DEFAULT_FIXTURES_DIR
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            for name in (
                "srne-register-groups.json",
                "srne-synthetic-scenarios.json",
                "srne-expected-entities.json",
            ):
                shutil.copy2(src_dir / name, tmp / name)

            # Corrupt JSON syntax
            (tmp / "srne-synthetic-scenarios.json").write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(sim.FixtureValidationError):
                sim.load_and_validate_fixtures(tmp)

            # Restore and reject bool disguised as int uint16
            shutil.copy2(src_dir / "srne-synthetic-scenarios.json", tmp / "srne-synthetic-scenarios.json")
            sc_doc = json.loads((tmp / "srne-synthetic-scenarios.json").read_text(encoding="utf-8"))
            sc_doc["scenarios"][0]["registers"]["0x0100"]["raw_u16"] = True
            (tmp / "srne-synthetic-scenarios.json").write_text(json.dumps(sc_doc), encoding="utf-8")
            with self.assertRaises(sim.FixtureValidationError):
                sim.load_and_validate_fixtures(tmp)

            # Out-of-range uint16 (> 65535)
            shutil.copy2(src_dir / "srne-synthetic-scenarios.json", tmp / "srne-synthetic-scenarios.json")
            sc_doc = json.loads((tmp / "srne-synthetic-scenarios.json").read_text(encoding="utf-8"))
            sc_doc["scenarios"][0]["registers"]["0x0100"]["raw_u16"] = 65536
            (tmp / "srne-synthetic-scenarios.json").write_text(json.dumps(sc_doc), encoding="utf-8")
            with self.assertRaises(sim.FixtureValidationError):
                sim.load_and_validate_fixtures(tmp)


class TestReadOnlyContextApplicationLevel(unittest.IsolatedAsyncioTestCase):
    """Application-level tests exercising SRNEReadOnlyContext directly."""

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()

    async def test_all_40_groups_across_all_5_scenarios(self) -> None:
        for sid, scenario in self.fixtures.scenarios.items():
            ctx = sim.SRNEReadOnlyContext(scenario, self.fixtures.groups)
            for grp in self.fixtures.groups:
                vals = await ctx.async_getValues(1, 3, grp.start_address, grp.register_count)
                self.assertEqual(
                    vals,
                    list(scenario.group_payloads[grp.group_id]),
                    msg=f"Mismatch for {sid}/{grp.group_id}",
                )

    async def test_exact_boundaries_signed16_and_string_upper_bytes(self) -> None:
        s1 = self.fixtures.scenarios["S1_solar_charging"]
        ctx1 = sim.SRNEReadOnlyContext(s1, self.fixtures.groups)
        self.assertEqual(await ctx1.async_getValues(1, 3, 0x000B, 1), [4])
        self.assertEqual(await ctx1.async_getValues(1, 3, 0xF04E, 1), [21])
        # Negative signed16 battery current (-85.0 A => -850 => 0xFCAE)
        self.assertEqual(await ctx1.async_getValues(1, 3, 0x0102, 1), [0xFCAE])

        # String registers intentionally preserve non-zero upper bytes
        build_words = await ctx1.async_getValues(1, 3, 0x0021, 20)
        assert isinstance(build_words, list)
        self.assertTrue(any((w >> 8) != 0 for w in build_words))
        self.assertEqual("".join(chr(w & 0xFF) for w in build_words if (w & 0xFF) != 0), "2025-11-15 10:30:00")

        s4 = self.fixtures.scenarios["S4_standby"]
        ctx4 = sim.SRNEReadOnlyContext(s4, self.fixtures.groups)
        # Negative signed16 ambient temperature (-2.5 degC => -25 => 0xFFE7)
        self.assertEqual(await ctx4.async_getValues(1, 3, 0x0223, 1), [0xFFE7])

    async def test_gap_quantity_write_and_unknown_device_rejections(self) -> None:
        s1 = self.fixtures.scenarios["S1_solar_charging"]
        ctx = sim.SRNEReadOnlyContext(s1, self.fixtures.groups)

        # Undocumented gaps return ILLEGAL_ADDRESS (0x02)
        self.assertEqual(await ctx.async_getValues(1, 3, 0x0104, 1), ExcCodes.ILLEGAL_ADDRESS)
        self.assertEqual(await ctx.async_getValues(1, 3, 0x0103, 2), ExcCodes.ILLEGAL_ADDRESS)
        self.assertEqual(await ctx.async_getValues(1, 3, 0x000A, 1), ExcCodes.ILLEGAL_ADDRESS)
        self.assertEqual(await ctx.async_getValues(1, 3, 0xF04F, 1), ExcCodes.ILLEGAL_ADDRESS)

        # Invalid quantities return ILLEGAL_VALUE (0x03)
        self.assertEqual(await ctx.async_getValues(1, 3, 0x0100, 0), ExcCodes.ILLEGAL_VALUE)
        self.assertEqual(await ctx.async_getValues(1, 3, 0x0021, 33), ExcCodes.ILLEGAL_VALUE)

        # Unsupported function codes and writes return ILLEGAL_FUNCTION (0x01)
        self.assertEqual(await ctx.async_getValues(1, 4, 0x0100, 1), ExcCodes.ILLEGAL_FUNCTION)
        self.assertEqual(await ctx.async_setValues(1, 6, 0xE003, [50]), ExcCodes.ILLEGAL_FUNCTION)
        self.assertEqual(await ctx.async_getValues(1, 3, 0xE003, 1), [48])

        # Immutable mapping blocks direct mutation
        with self.assertRaises(TypeError):
            ctx.registers[0x0100] = 999  # type: ignore[index]

        # Unknown device_id raises NoSuchIdException
        with self.assertRaises(NoSuchIdException):
            await ctx.async_getValues(2, 3, 0x0100, 1)


class TestProtocolLevelRTUWireFrames(unittest.IsolatedAsyncioTestCase):
    """Protocol-level in-memory tests sending and verifying raw Modbus RTU frames with CRC-16.

    These tests exercise PyModbus's actual ``FramerRTU``, ``DecodePDU``,
    ``SRNEModbusSerialServer``, and ``SRNERequestHandler`` over an in-memory
    ``asyncio.Transport`` double without opening any serial port.
    """

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()

    def _create_in_memory_handler(
        self, scenario_id: str = "S1_solar_charging"
    ) -> tuple[sim.SRNERequestHandler, _InMemoryRTUTransport, sim.SRNEModbusSerialServer]:
        scenario = self.fixtures.scenarios[scenario_id]
        ctx = sim.SRNEReadOnlyContext(scenario, self.fixtures.groups, device_id=1)
        server = sim.SRNEModbusSerialServer(ctx, port="NULLMODEM:0", timeout=1.0)
        handler = server.callback_new_connection()
        transport = _InMemoryRTUTransport(asyncio.get_running_loop())
        handler.connection_made(transport)
        return handler, transport, server

    async def _send_rtu_and_receive(
        self,
        handler: sim.SRNERequestHandler,
        transport: _InMemoryRTUTransport,
        dev_id: int,
        pdu_bytes: bytes,
    ) -> tuple[int, int, bytes]:
        frame = build_rtu_frame(dev_id, pdu_bytes)
        handler.data_received(frame)
        raw_reply = await asyncio.wait_for(transport.written_frames.get(), timeout=1.0)
        return verify_and_unwrap_rtu_frame(raw_reply)

    async def test_all_40_groups_all_5_scenarios_over_rtu_wire(self) -> None:
        for sid, scenario in self.fixtures.scenarios.items():
            handler, transport, server = self._create_in_memory_handler(sid)
            try:
                for grp in self.fixtures.groups:
                    req_pdu = struct.pack(">BHH", 3, grp.start_address, grp.register_count)
                    resp_dev, resp_fc, payload = await self._send_rtu_and_receive(
                        handler, transport, 1, req_pdu
                    )
                    self.assertEqual(resp_dev, 1, msg=f"{sid}/{grp.group_id}")
                    self.assertEqual(resp_fc, 3, msg=f"{sid}/{grp.group_id}")
                    expected_words = scenario.group_payloads[grp.group_id]
                    self.assertEqual(payload[0], len(expected_words) * 2)
                    wire_words = list(
                        struct.unpack(f">{len(expected_words)}H", payload[1:])
                    )
                    self.assertEqual(wire_words, list(expected_words), msg=f"{sid}/{grp.group_id}")
            finally:
                await server.shutdown()

    async def test_rtu_wire_addressing_signed16_and_string_upper_bytes(self) -> None:
        handler, transport, server = self._create_in_memory_handler("S1_solar_charging")
        try:
            # First approved word (0x000B) and last approved word (0xF04E)
            _, fc1, p1 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0x000B, 1))
            self.assertEqual((fc1, p1), (3, b"\x02\x00\x04"))

            _, fc2, p2 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0xF04E, 1))
            self.assertEqual((fc2, p2), (3, b"\x02\x00\x15"))

            # Signed16 raw big-endian encoding: -850 -> 0xFCAE
            _, fc3, p3 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0x0102, 1))
            self.assertEqual((fc3, p3), (3, b"\x02\xfc\xae"))

            # String block preserves upper bytes on the wire
            _, fc4, p4 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0x0035, 20))
            self.assertEqual(fc4, 3)
            self.assertEqual(p4[0], 40)
            sn_words = list(struct.unpack(">20H", p4[1:]))
            self.assertTrue(any((w >> 8) != 0 for w in sn_words))
            self.assertEqual(
                "".join(chr(w & 0xFF) for w in sn_words if (w & 0xFF) != 0),
                "SYNTH-SPI16K-0001",
            )
        finally:
            await server.shutdown()

    async def test_rtu_wire_gap_and_invalid_quantity_exceptions(self) -> None:
        handler, transport, server = self._create_in_memory_handler("S4_standby")
        try:
            # Negative temperature on wire: -25 -> 0xFFE7
            _, fc_temp, p_temp = await self._send_rtu_and_receive(
                handler, transport, 1, struct.pack(">BHH", 3, 0x0223, 1)
            )
            self.assertEqual((fc_temp, p_temp), (3, b"\x02\xff\xe7"))

            # Gap and out-of-range reads -> Exception 0x83 / 0x02
            for start, cnt in ((0x0000, 1), (0x0103, 2), (0x0104, 1), (0xF04F, 1)):
                _, fc, payload = await self._send_rtu_and_receive(
                    handler, transport, 1, struct.pack(">BHH", 3, start, cnt)
                )
                self.assertEqual((fc, payload), (0x83, bytes([ExcCodes.ILLEGAL_ADDRESS])), msg=f"0x{start:04X}+{cnt}")

            # Invalid quantities (0, 33, 125, 126) -> Exception 0x83 / 0x03
            for start, cnt in ((0x0100, 0), (0x0021, 33), (0x0100, 125), (0x0100, 126)):
                _, fc, payload = await self._send_rtu_and_receive(
                    handler, transport, 1, struct.pack(">BHH", 3, start, cnt)
                )
                self.assertEqual((fc, payload), (0x83, bytes([ExcCodes.ILLEGAL_VALUE])), msg=f"0x{start:04X} cnt={cnt}")
        finally:
            await server.shutdown()

    async def test_rtu_wire_write_and_unsupported_fcs_rejected_without_mutation(self) -> None:
        handler, transport, server = self._create_in_memory_handler("S1_solar_charging")
        try:
            # Baseline read of 0xE003 (48) and 0x0100 (74)
            _, fc_b1, p_b1 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0xE003, 1))
            self.assertEqual((fc_b1, p_b1), (3, b"\x02\x00\x30"))

            write_and_unsupported_pdus = [
                (0x01, struct.pack(">BHH", 1, 0x0000, 1)),                           # FC01 Read Coils
                (0x02, struct.pack(">BHH", 2, 0x0000, 1)),                           # FC02 Read Discrete Inputs
                (0x04, struct.pack(">BHH", 4, 0x0100, 1)),                           # FC04 Read Input Registers
                (0x05, struct.pack(">BHH", 5, 0x0000, 0xFF00)),                      # FC05 Write Single Coil
                (0x06, struct.pack(">BHH", 6, 0xE003, 99)),                          # FC06 Write Single Register
                (0x07, struct.pack(">B", 7)),                                        # FC07 Read Exception Status
                (0x09, struct.pack(">BHH", 9, 0x0100, 1)),                           # FC09 Unregistered FC
                (0x0F, struct.pack(">BHHBB", 15, 0x0000, 1, 1, 1)),                  # FC15 Write Multiple Coils
                (0x10, struct.pack(">BHHBH", 16, 0x0100, 1, 2, 99)),                 # FC16 Write Multiple Registers
                (0x11, struct.pack(">B", 17)),                                       # FC17 Report Device ID
                (0x16, struct.pack(">BHHH", 22, 0x0100, 0xFFFF, 0x0001)),            # FC22 Mask Write Register
                (0x17, struct.pack(">BHHHHBH", 23, 0x0100, 1, 0xE003, 1, 2, 99)),    # FC23 Read/Write Multiple Registers
            ]
            for fc_sent, pdu in write_and_unsupported_pdus:
                resp_dev, resp_fc, payload = await self._send_rtu_and_receive(handler, transport, 1, pdu)
                self.assertEqual(resp_dev, 1)
                self.assertEqual(resp_fc, fc_sent | 0x80, msg=f"Expected exception for FC{fc_sent}")
                self.assertEqual(payload, bytes([ExcCodes.ILLEGAL_FUNCTION]), msg=f"FC{fc_sent}")

            # Verify zero mutation on 0xE003 and 0x0100 after all write attempts
            _, fc_a1, p_a1 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0xE003, 1))
            _, fc_a2, p_a2 = await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 1))
            self.assertEqual((fc_a1, p_a1), (3, b"\x02\x00\x30"))
            self.assertEqual((fc_a2, p_a2), (3, b"\x02\x00\x4a"))
        finally:
            await server.shutdown()

    async def test_rtu_wrong_slave_bad_crc_and_request_logging(self) -> None:
        handler, transport, server = self._create_in_memory_handler("S1_solar_charging")
        logger = logging.getLogger(sim.LOGGER_NAME)
        prev_level = logger.level
        logger.setLevel(logging.DEBUG)
        try:
            # Non-matching slave ID produces no response
            handler.data_received(build_rtu_frame(2, struct.pack(">BHH", 3, 0x0100, 1)))
            await asyncio.sleep(0.05)
            self.assertTrue(transport.written_frames.empty())

            # Corrupted CRC produces no response
            bad_frame = bytearray(build_rtu_frame(1, struct.pack(">BHH", 3, 0x0100, 1)))
            bad_frame[-1] ^= 0xFF
            handler.data_received(bytes(bad_frame))
            await asyncio.sleep(0.05)
            self.assertTrue(transport.written_frames.empty())

            # Verify INFO, DEBUG raw words, and WARNING rejection logging
            with self.assertLogs(sim.LOGGER_NAME, level="DEBUG") as cm:
                await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 2))
                await self._send_rtu_and_receive(handler, transport, 1, struct.pack(">BHH", 6, 0xE003, 12))
            joined = "\n".join(cm.output)
            self.assertIn("fc=0x03 (3)", joined)
            self.assertIn("start=0x0100 (256)", joined)
            self.assertIn("count=2", joined)
            self.assertIn("outcome=OK", joined)
            self.assertIn("0x004A", joined)
            self.assertIn("0x0218", joined)
            self.assertIn("WRITE_REJECTED_READ_ONLY", joined)
            self.assertIn("exception=0x01", joined)
        finally:
            logger.setLevel(prev_level)
            await server.shutdown()


class TestCLIAndNoSerialAccess(unittest.TestCase):
    """CLI tests ensuring offline modes work cleanly and never touch serial hardware."""

    def test_list_and_validate_modes_do_not_access_serial(self) -> None:
        def _forbid_serial(*_args, **_kwargs):
            raise AssertionError("Serial hardware API must not be invoked in offline modes")

        with (
            mock.patch("serial.Serial", side_effect=_forbid_serial),
            mock.patch("serial.serial_for_url", side_effect=_forbid_serial),
            mock.patch("pymodbus.transport.serialtransport.create_serial_connection", side_effect=_forbid_serial),
        ):
            buf_list = io.StringIO()
            with contextlib.redirect_stdout(buf_list):
                rc_list = sim.main(["--list-scenarios"])
            self.assertEqual(rc_list, 0)
            self.assertIn(sim.STARTUP_BANNER, buf_list.getvalue())
            self.assertIn("S1_solar_charging [default]", buf_list.getvalue())

            buf_val = io.StringIO()
            with contextlib.redirect_stdout(buf_val):
                rc_val = sim.main(["--validate-only", "--scenario", "S5_active_fault"])
            self.assertEqual(rc_val, 0)
            self.assertIn("Validation OK: scenario='S5_active_fault'", buf_val.getvalue())
            self.assertIn("groups=40, registers=107, entities=73", buf_val.getvalue())

            # Missing --port exits with error code 2 without touching serial
            buf_err = io.StringIO()
            with contextlib.redirect_stderr(buf_err):
                rc_noport = sim.main([])
            self.assertEqual(rc_noport, 2)
            self.assertIn("--port is required", buf_err.getvalue())

            # Unknown scenario exits cleanly with code 2
            buf_bad = io.StringIO()
            with contextlib.redirect_stderr(buf_bad):
                rc_bad = sim.main(["--validate-only", "--scenario", "NO_SUCH_SCENARIO"])
            self.assertEqual(rc_bad, 2)

    def test_help_and_startup_banner_contents(self) -> None:
        buf_help = io.StringIO()
        with contextlib.redirect_stdout(buf_help):
            with self.assertRaises(SystemExit) as cm:
                sim.main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        help_text = buf_help.getvalue()
        for flag in ("--port", "--scenario", "--list-scenarios", "--validate-only", "--log-level"):
            self.assertIn(flag, help_text)

        fixtures = sim.load_and_validate_fixtures()
        banner = sim.format_startup_banner(
            fixtures.scenarios["S1_solar_charging"],
            port="COM9",
        )
        self.assertIn(sim.STARTUP_BANNER, banner)
        self.assertIn("S1_solar_charging", banner)
        self.assertIn("9600,N,8,1", banner)
        self.assertIn("1 (0x01)", banner)
        self.assertIn("40 approved FC03 groups / 107 unique words", banner)
        self.assertIn("FC03 ONLY", banner)


class _QueuedInputStream:
    """Thread-safe line-oriented stream double for testing async console input without stdin."""

    def __init__(self) -> None:
        self._items: list[str] = []
        import threading
        self._cond = threading.Condition()

    def push(self, text: str) -> None:
        with self._cond:
            self._items.append(text)
            self._cond.notify_all()

    def readline(self) -> str:
        with self._cond:
            while not self._items:
                self._cond.wait()
            return self._items.pop(0)


class TestRuntimeScenarioControlsApplicationLevel(unittest.IsolatedAsyncioTestCase):
    """Application-level tests for atomic scenario switching and console command handling."""

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()

    async def test_atomic_snapshot_replacement_and_repeated_selection(self) -> None:
        ctx = sim.SRNEReadOnlyContext(
            self.fixtures.scenarios["S1_solar_charging"],
            self.fixtures.groups,
            scenarios=self.fixtures.scenarios,
        )
        self.assertEqual(ctx.switch_count, 0)
        s1_regs = ctx.registers
        self.assertEqual(await ctx.async_getValues(1, 3, 0x0102, 1), [0xFCAE])

        # Switch across all remaining scenarios
        for idx, sid in enumerate(
            ("S2_battery_discharging", "S3_utility_zero_solar", "S4_standby", "S5_active_fault"),
            start=1,
        ):
            changed, prev_sc, new_sc = ctx.switch_scenario(sid)
            self.assertTrue(changed)
            self.assertEqual(new_sc.scenario_id, sid)
            self.assertEqual(ctx.scenario.scenario_id, sid)
            self.assertEqual(ctx.switch_count, idx)
            self.assertIsNot(ctx.registers, s1_regs)
            self.assertNotEqual(prev_sc.scenario_id, new_sc.scenario_id)

        # Previous immutable snapshot reference remained untouched
        self.assertEqual(s1_regs[0x0102], 0xFCAE)

        # Repeated selection does not increment switch_count or mutate snapshot
        changed_repeat, prev_rep, new_rep = ctx.switch_scenario("S5_active_fault")
        self.assertFalse(changed_repeat)
        self.assertEqual(prev_rep.scenario_id, "S5_active_fault")
        self.assertEqual(new_rep.scenario_id, "S5_active_fault")
        self.assertEqual(ctx.switch_count, 4)

        # Unknown scenario fails safely without modifying active state
        with self.assertRaises(KeyError):
            ctx.switch_scenario("NONEXISTENT_SCENARIO")
        self.assertEqual(ctx.scenario.scenario_id, "S5_active_fault")
        self.assertEqual(ctx.switch_count, 4)

    async def test_console_commands_status_help_invalid_and_logging(self) -> None:
        ctx = sim.SRNEReadOnlyContext(
            self.fixtures.scenarios["S1_solar_charging"],
            self.fixtures.groups,
            scenarios=self.fixtures.scenarios,
            started_at=0.0,
        )
        out = io.StringIO()
        shutdown_called = False

        def _on_shutdown() -> None:
            nonlocal shutdown_called
            shutdown_called = True

        ctrl = sim.InteractiveConsoleController(
            ctx,
            port="COM9",
            logger=logging.getLogger(sim.LOGGER_NAME),
            output_stream=out,
            shutdown_callback=_on_shutdown,
        )

        # Help and status commands
        self.assertTrue(ctrl.process_command("h"))
        help_txt = out.getvalue()
        for key in ("1 - S1_solar_charging", "2 - S2_battery_discharging", "3 - S3_utility_zero_solar", "4 - S4_standby", "5 - S5_active_fault", "s -", "h -", "q -"):
            self.assertIn(key, help_txt)

        # Invalid commands leave active scenario and switch_count unchanged
        with self.assertLogs(sim.LOGGER_NAME, level="INFO") as cm:
            self.assertTrue(ctrl.process_command(""))
            self.assertTrue(ctrl.process_command("9"))
            self.assertTrue(ctrl.process_command("invalid_cmd"))
            self.assertEqual(ctx.scenario.scenario_id, "S1_solar_charging")
            self.assertEqual(ctx.switch_count, 0)

            self.assertTrue(ctrl.process_command("3"))
            self.assertTrue(ctrl.process_command("3"))  # repeated same scenario
            self.assertTrue(ctrl.process_command("s"))
            self.assertFalse(ctrl.process_command("q"))

        self.assertTrue(shutdown_called)
        self.assertEqual(ctx.scenario.scenario_id, "S3_utility_zero_solar")
        self.assertEqual(ctx.switch_count, 1)

        out_txt = out.getvalue()
        self.assertIn("Active Scenario      : S3_utility_zero_solar", out_txt)
        self.assertIn("Device Address       : 1 (0x01)", out_txt)
        self.assertIn("Serial Configuration : port=COM9  9600,N,8,1", out_txt)
        self.assertIn("40 approved FC03 groups / 107 unique words", out_txt)
        self.assertIn("Scenario Switch Count: 1", out_txt)
        self.assertIn("Elapsed Runtime", out_txt)

        log_txt = "\n".join(cm.output)
        self.assertIn("Scenario transition: S1_solar_charging -> S3_utility_zero_solar", log_txt)
        self.assertIn("Invalid interactive console command ignored", log_txt)


class TestProtocolLevelRuntimeSwitchingRTU(unittest.IsolatedAsyncioTestCase):
    """In-memory RTU wire tests verifying live scenario transitions without server restart."""

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()

    async def _wire_exchange(
        self,
        handler: sim.SRNERequestHandler,
        transport: _InMemoryRTUTransport,
        dev_id: int,
        pdu: bytes,
    ) -> tuple[int, int, bytes]:
        handler.data_received(build_rtu_frame(dev_id, pdu))
        raw_reply = await asyncio.wait_for(transport.written_frames.get(), timeout=1.0)
        return verify_and_unwrap_rtu_frame(raw_reply)

    async def test_live_rtu_switching_all_5_scenarios_and_40_groups_preserving_readonly(self) -> None:
        ctx = sim.SRNEReadOnlyContext(
            self.fixtures.scenarios["S1_solar_charging"],
            self.fixtures.groups,
            scenarios=self.fixtures.scenarios,
            device_id=1,
        )
        server = sim.SRNEModbusSerialServer(ctx, port="NULLMODEM:0", timeout=1.0)
        handler = server.callback_new_connection()
        transport = _InMemoryRTUTransport(asyncio.get_running_loop())
        handler.connection_made(transport)
        out = io.StringIO()
        ctrl = sim.InteractiveConsoleController(
            ctx,
            port="NULLMODEM:0",
            logger=logging.getLogger(sim.LOGGER_NAME),
            output_stream=out,
        )

        try:
            for key, sid in sim.INTERACTIVE_SCENARIO_KEYS.items():
                self.assertTrue(ctrl.process_command(key))
                expected_scenario = self.fixtures.scenarios[sid]
                for grp in self.fixtures.groups:
                    dev, fc, payload = await self._wire_exchange(
                        handler,
                        transport,
                        1,
                        struct.pack(">BHH", 3, grp.start_address, grp.register_count),
                    )
                    self.assertEqual((dev, fc), (1, 3), msg=f"{sid}/{grp.group_id}")
                    expected_words = expected_scenario.group_payloads[grp.group_id]
                    wire_words = list(struct.unpack(f">{len(expected_words)}H", payload[1:]))
                    self.assertEqual(wire_words, list(expected_words), msg=f"{sid}/{grp.group_id}")

                # Confirm FC03-only & gap protections still reject over the same handler after switch
                _, fc_wr, p_wr = await self._wire_exchange(
                    handler, transport, 1, struct.pack(">BHH", 6, 0xE003, 123)
                )
                self.assertEqual((fc_wr, p_wr), (0x86, bytes([ExcCodes.ILLEGAL_FUNCTION])))

                _, fc_gap, p_gap = await self._wire_exchange(
                    handler, transport, 1, struct.pack(">BHH", 3, 0x0104, 1)
                )
                self.assertEqual((fc_gap, p_gap), (0x83, bytes([ExcCodes.ILLEGAL_ADDRESS])))
        finally:
            await server.shutdown()

    async def test_nonblocking_async_console_task_and_eof_shutdown(self) -> None:
        ctx = sim.SRNEReadOnlyContext(
            self.fixtures.scenarios["S1_solar_charging"],
            self.fixtures.groups,
            scenarios=self.fixtures.scenarios,
            device_id=1,
        )
        server = sim.SRNEModbusSerialServer(ctx, port="NULLMODEM:0", timeout=1.0)
        handler = server.callback_new_connection()
        transport = _InMemoryRTUTransport(asyncio.get_running_loop())
        handler.connection_made(transport)

        stream = _QueuedInputStream()
        out = io.StringIO()
        shutdown_event = asyncio.Event()
        ctrl = sim.InteractiveConsoleController(
            ctx,
            port="NULLMODEM:0",
            logger=logging.getLogger(sim.LOGGER_NAME),
            output_stream=out,
            shutdown_callback=shutdown_event.set,
        )

        console_task = asyncio.create_task(ctrl.run(input_stream=stream))
        try:
            # Switch to S2 asynchronously while serving RTU reads on the same loop
            stream.push("2\n")
            await asyncio.sleep(0.05)
            _, fc2, p2 = await self._wire_exchange(handler, transport, 1, struct.pack(">BHH", 3, 0x0102, 1))
            self.assertEqual((fc2, p2), (3, b"\x02\x02\xee"))  # +75.0 A in S2_battery_discharging

            # Invalid input does not break loop or switch scenario
            stream.push("bogus\n")
            await asyncio.sleep(0.05)
            self.assertFalse(shutdown_event.is_set())
            self.assertEqual(ctx.scenario.scenario_id, "S2_battery_discharging")

            # Switch to S4 (-2.5 degC => 0xFFE7 at 0x0223) then quit cleanly via q
            stream.push("4\n")
            await asyncio.sleep(0.05)
            _, fc4, p4 = await self._wire_exchange(handler, transport, 1, struct.pack(">BHH", 3, 0x0223, 1))
            self.assertEqual((fc4, p4), (3, b"\x02\xff\xe7"))

            stream.push("q\n")
            await asyncio.wait_for(console_task, timeout=1.0)
            self.assertTrue(shutdown_event.is_set())
        finally:
            if not console_task.done():
                console_task.cancel()
            await server.shutdown()

        # Verify EOF triggers graceful shutdown without errors
        eof_shutdown = asyncio.Event()
        eof_ctrl = sim.InteractiveConsoleController(
            ctx,
            port="NULLMODEM:0",
            logger=logging.getLogger(sim.LOGGER_NAME),
            output_stream=io.StringIO(),
            shutdown_callback=eof_shutdown.set,
        )
        await asyncio.wait_for(eof_ctrl.run(input_stream=io.StringIO("")), timeout=1.0)
        self.assertTrue(eof_shutdown.is_set())

    def test_interactive_cli_flags_and_no_serial_access(self) -> None:
        def _forbid_serial(*_args, **_kwargs):
            raise AssertionError("Serial hardware API must not be invoked in offline CLI checks")

        with (
            mock.patch("serial.Serial", side_effect=_forbid_serial),
            mock.patch("serial.serial_for_url", side_effect=_forbid_serial),
            mock.patch("pymodbus.transport.serialtransport.create_serial_connection", side_effect=_forbid_serial),
        ):
            buf_help = io.StringIO()
            with contextlib.redirect_stdout(buf_help):
                with self.assertRaises(SystemExit) as cm:
                    sim.main(["--help"])
            self.assertEqual(cm.exception.code, 0)
            self.assertIn("--interactive", buf_help.getvalue())

            buf_val = io.StringIO()
            with contextlib.redirect_stdout(buf_val):
                rc_val = sim.main(["--validate-only", "--interactive", "--scenario", "S4_standby"])
            self.assertEqual(rc_val, 0)
            self.assertIn("Validation OK: scenario='S4_standby'", buf_val.getvalue())

            buf_err = io.StringIO()
            with contextlib.redirect_stderr(buf_err):
                rc_err = sim.main(["--interactive"])
            self.assertEqual(rc_err, 2)
            self.assertIn("--port is required", buf_err.getvalue())


class TestFailureInjectionApplicationLevel(unittest.TestCase):
    """Application-level tests for FailureInjectionController and console commands."""

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()
        self.ctx = sim.SRNEReadOnlyContext(
            self.fixtures.scenarios["S1_solar_charging"],
            self.fixtures.groups,
            scenarios=self.fixtures.scenarios,
            started_at=0.0,
        )
        self.fc_ctl = sim.FailureInjectionController(self.fixtures.groups)

    def test_default_normal_and_group_alias_resolution(self) -> None:
        self.assertEqual(self.fc_ctl.config.mode, sim.FailureMode.NORMAL)
        self.assertFalse(self.fc_ctl.is_active)
        self.assertEqual(self.fc_ctl.counters.total_injected, 0)

        self.assertEqual(self.fc_ctl.resolve_group_tokens("bms"), frozenset({"P2-D04", "P2-D05"}))
        self.assertEqual(len(self.fc_ctl.resolve_group_tokens("phase1")), 16)
        self.assertEqual(len(self.fc_ctl.resolve_group_tokens("phase2")), 24)
        self.assertEqual(len(self.fc_ctl.resolve_group_tokens("phase2_dynamic")), 12)
        self.assertEqual(len(self.fc_ctl.resolve_group_tokens("phase2_static")), 12)
        self.assertEqual(len(self.fc_ctl.resolve_group_tokens("all")), 40)
        self.assertEqual(
            self.fc_ctl.resolve_group_tokens("p1-r01, p2-d05"),
            frozenset({"P1-R01", "P2-D05"}),
        )

        with self.assertRaises(ValueError):
            self.fc_ctl.resolve_group_tokens("P9-Z99")
        with self.assertRaises(ValueError):
            self.fc_ctl.resolve_group_tokens("")

    def test_console_failure_commands_invalid_handling_and_independence(self) -> None:
        out = io.StringIO()
        ctrl = sim.InteractiveConsoleController(
            self.ctx,
            port="COM9",
            logger=logging.getLogger(sim.LOGGER_NAME),
            output_stream=out,
            failure_controller=self.fc_ctl,
        )

        # Help and group list include all documented failure commands and aliases
        self.assertTrue(ctrl.process_command("h"))
        self.assertTrue(ctrl.process_command("f list"))
        self.assertIn("f timeout", out.getvalue())
        self.assertIn("f gtimeout <groups>", out.getvalue())
        self.assertIn("P2-D05", out.getvalue())

        # Invalid failure commands must not modify active scenario or failure mode
        for bad_cmd in (
            "f bogus",
            "f gtimeout",
            "f gtimeout P9-INVALID",
            "f exc",
            "f exc P2-D04 0x99",
            "f crc P9-UNKNOWN",
            "f groups P1-R01",
            "f timeout extra",
        ):
            self.assertTrue(ctrl.process_command(bad_cmd))
            self.assertEqual(self.fc_ctl.config.mode, sim.FailureMode.NORMAL)
            self.assertEqual(self.ctx.scenario.scenario_id, "S1_solar_charging")

        # Activate selective timeout, switch scenarios independently, then restore via n
        self.assertTrue(ctrl.process_command("f gtimeout bms"))
        self.assertEqual(self.fc_ctl.config.mode, sim.FailureMode.SELECTIVE_TIMEOUT)
        self.assertEqual(self.fc_ctl.config.target_groups, frozenset({"P2-D04", "P2-D05"}))

        self.assertTrue(ctrl.process_command("3"))
        self.assertEqual(self.ctx.scenario.scenario_id, "S3_utility_zero_solar")
        self.assertEqual(self.fc_ctl.config.mode, sim.FailureMode.SELECTIVE_TIMEOUT)

        # Update target groups without changing scenario
        self.assertTrue(ctrl.process_command("f groups P1-R01,P2-D05"))
        self.assertEqual(self.fc_ctl.config.target_groups, frozenset({"P1-R01", "P2-D05"}))
        self.assertEqual(self.ctx.scenario.scenario_id, "S3_utility_zero_solar")

        self.assertTrue(ctrl.process_command("s"))
        self.assertTrue(ctrl.process_command("n"))
        self.assertEqual(self.fc_ctl.config.mode, sim.FailureMode.NORMAL)
        self.assertEqual(self.fc_ctl.counters.recoveries, 1)
        self.assertEqual(self.ctx.scenario.scenario_id, "S3_utility_zero_solar")
        self.assertIn("Active Failure Mode  : selective_timeout", out.getvalue())


class TestProtocolLevelFailureInjectionRTU(unittest.IsolatedAsyncioTestCase):
    """Protocol-level RTU wire tests verifying silence, exceptions, CRC/truncation, recovery, and RO safety."""

    def setUp(self) -> None:
        self.fixtures = sim.load_and_validate_fixtures()

    def _make_rig(
        self, scenario_id: str = "S1_solar_charging"
    ) -> tuple[
        sim.SRNEReadOnlyContext,
        sim.FailureInjectionController,
        sim.InteractiveConsoleController,
        sim.SRNEModbusSerialServer,
        sim.SRNERequestHandler,
        _InMemoryRTUTransport,
        io.StringIO,
        asyncio.Event,
    ]:
        ctx = sim.SRNEReadOnlyContext(
            self.fixtures.scenarios[scenario_id],
            self.fixtures.groups,
            scenarios=self.fixtures.scenarios,
            device_id=1,
            started_at=0.0,
        )
        fc_ctl = sim.FailureInjectionController(self.fixtures.groups)
        server = sim.SRNEModbusSerialServer(
            ctx, port="NULLMODEM:0", timeout=1.0, failure_controller=fc_ctl
        )
        handler = server.callback_new_connection()
        transport = _InMemoryRTUTransport(asyncio.get_running_loop())
        handler.connection_made(transport)
        out = io.StringIO()
        quit_ev = asyncio.Event()
        console = sim.InteractiveConsoleController(
            ctx,
            port="NULLMODEM:0",
            logger=logging.getLogger(sim.LOGGER_NAME),
            output_stream=out,
            shutdown_callback=quit_ev.set,
            failure_controller=fc_ctl,
        )
        return ctx, fc_ctl, console, server, handler, transport, out, quit_ev

    async def _send_raw(
        self, handler: sim.SRNERequestHandler, transport: _InMemoryRTUTransport, dev_id: int, pdu: bytes
    ) -> bytes:
        handler.data_received(build_rtu_frame(dev_id, pdu))
        return await asyncio.wait_for(transport.written_frames.get(), timeout=1.0)

    async def _assert_silent(
        self, handler: sim.SRNERequestHandler, transport: _InMemoryRTUTransport, addr: int, count: int
    ) -> None:
        handler.data_received(build_rtu_frame(1, struct.pack(">BHH", 3, addr, count)))
        await asyncio.sleep(0.05)
        self.assertTrue(
            transport.written_frames.empty(),
            msg=f"Expected silence for 0x{addr:04X}+{count}, got bytes",
        )

    async def test_complete_silence_and_selective_bms_timeout_with_recovery(self) -> None:
        ctx, fc_ctl, console, server, handler, transport, _, _ = self._make_rig("S1_solar_charging")
        try:
            # 1. Global silent timeout -> both Phase 1 and BMS silent
            self.assertTrue(console.process_command("f timeout"))
            await self._assert_silent(handler, transport, 0x0100, 4)  # P1-R01
            await self._assert_silent(handler, transport, 0x0114, 4)  # P2-D05
            self.assertEqual(fc_ctl.counters.silent_timeouts, 2)

            # Recover without restart -> both succeed
            self.assertTrue(console.process_command("n"))
            dev, fc, p1_raw = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 4))
            )
            self.assertEqual((dev, fc), (1, 3))
            self.assertEqual(list(struct.unpack(">4H", p1_raw[1:])), list(ctx.scenario.group_payloads["P1-R01"]))

            # 2. Selective BMS timeout -> P2-D04 and P2-D05 silent; P1-R01, P2-D01, P2-S06 unaffected
            self.assertTrue(console.process_command("f gtimeout bms"))
            await self._assert_silent(handler, transport, 0x0112, 1)  # P2-D04
            await self._assert_silent(handler, transport, 0x0114, 4)  # P2-D05
            self.assertEqual(fc_ctl.counters.selective_timeouts, 2)

            for grp_id in ("P1-R01", "P2-D01", "P2-S06"):
                spec = next(g for g in self.fixtures.groups if g.group_id == grp_id)
                _, fc_ok, payload_ok = verify_and_unwrap_rtu_frame(
                    await self._send_raw(
                        handler, transport, 1, struct.pack(">BHH", 3, spec.start_address, spec.register_count)
                    )
                )
                self.assertEqual(fc_ok, 3)
                self.assertEqual(
                    list(struct.unpack(f">{spec.register_count}H", payload_ok[1:])),
                    list(ctx.scenario.group_payloads[grp_id]),
                )

            # Recover again -> P2-D05 succeeds immediately on same handler
            self.assertTrue(console.process_command("f normal"))
            _, fc_rec, p_rec = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0114, 4))
            )
            self.assertEqual(fc_rec, 3)
            self.assertEqual(list(struct.unpack(">4H", p_rec[1:])), list(ctx.scenario.group_payloads["P2-D05"]))
            self.assertEqual(fc_ctl.counters.recoveries, 2)
        finally:
            await server.shutdown()

    async def test_selective_exception_invalid_crc_and_truncated_wire_frames(self) -> None:
        from pymodbus.pdu import DecodePDU

        ctx, fc_ctl, console, server, handler, transport, _, _ = self._make_rig("S1_solar_charging")
        client_framer = FramerRTU(DecodePDU(is_server=False))
        try:
            # 1. Selective Modbus exception 0x02 and 0x04 on targeted groups only
            self.assertTrue(console.process_command("f exc P2-D05 0x02"))
            _, fc_e1, p_e1 = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0114, 4))
            )
            self.assertEqual((fc_e1, p_e1), (0x83, b"\x02"))

            # Unaffected P1-R01 returns normal CRC-valid response
            _, fc_u1, _ = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 4))
            )
            self.assertEqual(fc_u1, 3)

            self.assertTrue(console.process_command("f exc P1-R02 0x04"))
            _, fc_e2, p_e2 = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0107, 3))
            )
            self.assertEqual((fc_e2, p_e2), (0x83, b"\x04"))

            # 2. Wire-level INVALID_CRC (selective on P1-R01, then global)
            self.assertTrue(console.process_command("f crc P1-R01"))
            bad_crc_wire = await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 4))
            # Authentic length (1 + 1 + 1 + 8 + 2 = 13 bytes) and authentic payload, corrupted CRC
            self.assertEqual(len(bad_crc_wire), 13)
            self.assertEqual(bad_crc_wire[0:3], b"\x01\x03\x08")
            self.assertEqual(
                list(struct.unpack(">4H", bad_crc_wire[3:11])),
                list(ctx.scenario.group_payloads["P1-R01"]),
            )
            self.assertFalse(FramerRTU.check_CRC(bad_crc_wire[:-2], (bad_crc_wire[-2] << 8) | bad_crc_wire[-1]))
            _, client_pdu = client_framer.handleFrame(bad_crc_wire, 1, 0)
            self.assertIsNone(client_pdu)

            # Unaffected group P1-R02 passes valid CRC while selective CRC fault is on P1-R01
            ok_crc_wire = await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0107, 3))
            _, fc_ok, _ = verify_and_unwrap_rtu_frame(ok_crc_wire)
            self.assertEqual(fc_ok, 3)

            # 3. Wire-level TRUNCATED_FRAME (selective on P2-D05, then global)
            self.assertTrue(console.process_command("f trunc P2-D05"))
            trunc_wire = await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0114, 4))
            # Normal 4-word FC03 RTU frame is 13 bytes; truncated by 3 => 10 bytes
            self.assertEqual(len(trunc_wire), 10)
            _, trunc_pdu = client_framer.handleFrame(trunc_wire, 1, 0)
            self.assertIsNone(trunc_pdu)

            # Restore normal communication without restart
            self.assertTrue(console.process_command("n"))
            good_wire = await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0114, 4))
            self.assertEqual(len(good_wire), 13)
            _, client_good_pdu = client_framer.handleFrame(good_wire, 1, 0)
            self.assertIsNotNone(client_good_pdu)
            self.assertEqual(fc_ctl.counters.selective_exceptions, 2)
            self.assertEqual(fc_ctl.counters.invalid_crc_frames, 1)
            self.assertEqual(fc_ctl.counters.truncated_frames, 1)
            self.assertEqual(fc_ctl.counters.recoveries, 1)
        finally:
            await server.shutdown()

    async def test_scenario_switching_and_readonly_safety_under_all_failure_modes(self) -> None:
        ctx, fc_ctl, console, server, handler, transport, _, _ = self._make_rig("S1_solar_charging")
        try:
            # Activate selective BMS timeout, then switch scenario 1 -> 4 independently
            self.assertTrue(console.process_command("f gtimeout bms"))
            self.assertTrue(console.process_command("4"))
            await self._assert_silent(handler, transport, 0x0112, 1)  # P2-D04 remains silent

            # Unaffected P2-D10 reflects S4_standby (-2.5 degC => 0xFFE7 at 0x0223)
            _, fc_d10, p_d10 = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0222, 3))
            )
            self.assertEqual(fc_d10, 3)
            self.assertEqual(list(struct.unpack(">3H", p_d10[1:])), [48, 0xFFE7, 0])

            # Restore normal -> P2-D04 returns S4_standby BMS voltage (54.0 V => 540)
            self.assertTrue(console.process_command("n"))
            _, fc_d04, p_d04 = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0112, 1))
            )
            self.assertEqual((fc_d04, list(struct.unpack(">H", p_d04[1:]))), (3, [540]))

            # Verify FC03-only write rejection (0x01) holds across ALL 6 modes with zero mutation
            mode_commands = [
                ("n", sim.FailureMode.NORMAL),
                ("f timeout", sim.FailureMode.SILENT_TIMEOUT),
                ("f gtimeout bms", sim.FailureMode.SELECTIVE_TIMEOUT),
                ("f exc bms 0x02", sim.FailureMode.SELECTIVE_EXCEPTION),
                ("f crc", sim.FailureMode.INVALID_CRC),
                ("f trunc", sim.FailureMode.TRUNCATED_FRAME),
            ]
            write_pdus = [
                (0x06, struct.pack(">BHH", 6, 0xE003, 99)),
                (0x10, struct.pack(">BHHBH", 16, 0x0100, 1, 2, 777)),
                (0x16, struct.pack(">BHHH", 22, 0x0100, 0xFFFF, 0x0001)),
                (0x17, struct.pack(">BHHHHBH", 23, 0x0100, 1, 0xE003, 1, 2, 99)),
            ]
            for cmd, expected_mode in mode_commands:
                self.assertTrue(console.process_command(cmd))
                self.assertEqual(fc_ctl.config.mode, expected_mode)
                for req_fc, pdu in write_pdus:
                    resp_dev, resp_fc, payload = verify_and_unwrap_rtu_frame(
                        await self._send_raw(handler, transport, 1, pdu)
                    )
                    self.assertEqual((resp_dev, resp_fc, payload), (1, req_fc | 0x80, b"\x01"))

            # Confirm zero register mutation after writes across all failure modes
            self.assertTrue(console.process_command("n"))
            _, _, p_e003 = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0xE003, 1))
            )
            self.assertEqual(p_e003, b"\x02\x00\x30")
            self.assertEqual(ctx.registers[0x0100], 100)  # S4_standby SOC preserved
        finally:
            await server.shutdown()

    async def test_concurrent_console_failure_lifecycle_counters_and_quit(self) -> None:
        ctx, fc_ctl, console, server, handler, transport, out, quit_ev = self._make_rig("S1_solar_charging")
        stream = _QueuedInputStream()
        task = asyncio.create_task(console.run(input_stream=stream))
        try:
            stream.push("f exc P1-R01 0x03\n")
            await asyncio.sleep(0.05)
            _, fc_ex, p_ex = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 4))
            )
            self.assertEqual((fc_ex, p_ex), (0x83, b"\x03"))

            stream.push("2\n")
            await asyncio.sleep(0.05)
            stream.push("n\n")
            await asyncio.sleep(0.05)
            _, fc_ok, p_ok = verify_and_unwrap_rtu_frame(
                await self._send_raw(handler, transport, 1, struct.pack(">BHH", 3, 0x0100, 4))
            )
            self.assertEqual(fc_ok, 3)
            self.assertEqual(
                list(struct.unpack(">4H", p_ok[1:])),
                list(self.fixtures.scenarios["S2_battery_discharging"].group_payloads["P1-R01"]),
            )

            stream.push("f status\n")
            stream.push("q\n")
            await asyncio.wait_for(task, timeout=1.0)
            self.assertTrue(quit_ev.is_set())
            self.assertEqual(fc_ctl.counters.selective_exceptions, 1)
            self.assertEqual(fc_ctl.counters.recoveries, 1)
            self.assertIn("Active Failure Mode  : normal", out.getvalue())
            self.assertIn("Restorations/Recover : 1", out.getvalue())
        finally:
            if not task.done():
                task.cancel()
            await server.shutdown()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
