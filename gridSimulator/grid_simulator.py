"""OpenTAP Instrument plugin for a Xinhua AC grid simulator over serial."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import threading
from typing import Any, Optional

import OpenTap
import opentap
from opentap import Instrument, attribute, property
from System import Boolean, Double, Int32, String

try:
    serial: Optional[Any] = importlib.import_module("serial")
except ImportError:  # pragma: no cover - dependency is installed in runtime env.
    serial = None


@dataclass
class XinhuaFrame:
    command_class: int
    command_word: int
    payload: bytes


@attribute(
    OpenTap.Display(
        "gridSimulator",
        "Xinhua AC grid simulator over serial remote protocol.",
        "Instruments",
    )
)
class GridSimulator(Instrument):
    FRAME_HEADER = 0x7B
    FRAME_END = 0x7D

    CLASS_CONTROL = 0x0F
    CLASS_QUERY = 0xF0
    CLASS_SET = 0x5A
    CLASS_ERROR = 0x99

    WORD_AC_STOP = 0x00
    WORD_AC_START = 0xFF
    WORD_STOP_ALARM = 0x03

    WORD_QUERY_ENV_MEAS = 0xAC
    WORD_QUERY_OUTPUT_MEAS = 0xAF
    WORD_QUERY_STATE = 0xEB
    WORD_QUERY_MODEL = 0xED
    WORD_ONLINE_REGULATION = 0x50

    SerialPort = property(String, "COM3").add_attribute(
        OpenTap.Display("Serial port", "Serial port, for example COM3.", "Connection", 1)
    )
    BaudRate = property(Int32, 38400).add_attribute(
        OpenTap.Display("Baud rate", "Remote protocol baud rate.", "Connection", 2)
    )
    SlaveAddress = property(Int32, 1).add_attribute(
        OpenTap.Display("Address", "Device address in range 1-255.", "Connection", 3)
    )
    Timeout = property(Double, 3.0).add_attribute(
        OpenTap.Display("Timeout", "Serial read/write timeout.", "Connection", 4)
    ).add_attribute(OpenTap.Unit("s"))
    MaxVoltage = property(Double, 110.0).add_attribute(
        OpenTap.Display("Max voltage", "Voltage limit used by online regulation validation.", "Limits", 1)
    ).add_attribute(OpenTap.Unit("V"))
    QueryIdentityOnOpen = property(Boolean, True).add_attribute(
        OpenTap.Display("Query identity on open", "Query and log model name when opening the instrument.", "Behavior", 1)
    )

    def __init__(self):
        super().__init__()
        self.Name = "gridSimulator"
        self._serial = None
        self._lock = threading.Lock()
        self._model = "UNKNOWN"

        self.Rules.Add(
            opentap.Rule(
                "SerialPort",
                lambda: bool(str(self.SerialPort).strip()),
                lambda: "Serial port is required.",
            )
        )
        self.Rules.Add(
            opentap.Rule(
                "BaudRate",
                lambda: int(self.BaudRate) > 0,
                lambda: "Baud rate must be positive.",
            )
        )
        self.Rules.Add(
            opentap.Rule(
                "SlaveAddress",
                lambda: 1 <= int(self.SlaveAddress) <= 255,
                lambda: "Address must be between 1 and 255.",
            )
        )
        self.Rules.Add(
            opentap.Rule(
                "Timeout",
                lambda: float(self.Timeout) > 0.0,
                lambda: "Timeout must be positive.",
            )
        )
        self.Rules.Add(
            opentap.Rule(
                "MaxVoltage",
                lambda: 0.0 < float(self.MaxVoltage) <= 300.0,
                lambda: "Max voltage must be in range (0, 300].",
            )
        )

    def Open(self):
        super().Open()
        if self.is_connected():
            return
        if serial is None:
            raise RuntimeError("pyserial is required. Install it with: pip install pyserial")

        port_name = self._normalize_port_name(str(self.SerialPort))
        try:
            self._serial = serial.Serial(
                port=port_name,
                baudrate=int(self.BaudRate),
                timeout=float(self.Timeout),
                write_timeout=float(self.Timeout),
            )
        except Exception as exc:
            raise RuntimeError("Unable to open serial port '{0}': {1}".format(port_name, str(exc)))

        if bool(self.QueryIdentityOnOpen):
            self._model = self.query_model()
            self.log.Info("Connected to gridSimulator model '{0}' on {1}", self._model, port_name)
        else:
            self.log.Info("Connected to gridSimulator on {0}", port_name)

    def Close(self):
        try:
            with self._lock:
                if self._serial is not None:
                    try:
                        self._serial.close()
                    except Exception as exc:
                        self.log.Warning("Error while closing serial connection: {0}", str(exc))
                self._serial = None
        finally:
            super().Close()

    def is_connected(self):
        return self._serial is not None and bool(getattr(self._serial, "is_open", True))

    def query_model(self):
        frame = self._transaction(self.CLASS_QUERY, self.WORD_QUERY_MODEL)
        model = frame.payload.decode("ascii", errors="ignore").strip("\x00 ").strip()
        return model if model else "UNKNOWN"

    def start_output(self):
        self._transaction(self.CLASS_CONTROL, self.WORD_AC_START)

    def stop_output(self):
        self._transaction(self.CLASS_CONTROL, self.WORD_AC_STOP)

    def stop_alarm(self):
        self._transaction(self.CLASS_CONTROL, self.WORD_STOP_ALARM)

    def regulate_output(self, voltage_v, frequency_hz, wave_code=0, start_if_needed=True):
        payload = self._build_online_regulation_payload(
            voltages=(float(voltage_v), float(voltage_v), float(voltage_v)),
            frequencies=(float(frequency_hz), float(frequency_hz), float(frequency_hz)),
            wave_codes=(int(wave_code), int(wave_code), int(wave_code)),
        )
        self._run_online_regulation(payload, bool(start_if_needed))

    def regulate_output_three_phase(
        self,
        voltages,
        frequencies,
        wave_codes=(0, 0, 0),
        start_if_needed=True,
    ):
        payload = self._build_online_regulation_payload(
            voltages=(float(voltages[0]), float(voltages[1]), float(voltages[2])),
            frequencies=(float(frequencies[0]), float(frequencies[1]), float(frequencies[2])),
            wave_codes=(int(wave_codes[0]), int(wave_codes[1]), int(wave_codes[2])),
        )
        self._run_online_regulation(payload, bool(start_if_needed))

    def _run_online_regulation(self, payload, start_if_needed):
        try:
            self._transaction(self.CLASS_SET, self.WORD_ONLINE_REGULATION, payload)
        except RuntimeError as exc:
            if start_if_needed and self._is_state_error(exc):
                self.start_output()
                self._transaction(self.CLASS_SET, self.WORD_ONLINE_REGULATION, payload)
                return
            raise

    @staticmethod
    def _is_state_error(exc):
        return "code=4" in str(exc)

    def query_instrument_state(self):
        frame = self._transaction(self.CLASS_QUERY, self.WORD_QUERY_STATE)
        if len(frame.payload) < 1:
            raise RuntimeError("State query returned empty payload")
        return {
            "state_code": int(frame.payload[0]),
            "state_data": frame.payload[1:],
        }

    def query_environment_measurements(self):
        frame = self._transaction(self.CLASS_QUERY, self.WORD_QUERY_ENV_MEAS)
        payload = frame.payload
        if len(payload) < 14:
            raise RuntimeError("Environment measurement payload too short")

        return {
            "phase_voltage_u_v": int.from_bytes(payload[0:2], "big") / 10.0,
            "phase_voltage_v_v": int.from_bytes(payload[2:4], "big") / 10.0,
            "phase_voltage_w_v": int.from_bytes(payload[4:6], "big") / 10.0,
            "line_voltage_uv_v": int.from_bytes(payload[6:8], "big") / 10.0,
            "line_voltage_vw_v": int.from_bytes(payload[8:10], "big") / 10.0,
            "line_voltage_uw_v": int.from_bytes(payload[10:12], "big") / 10.0,
            "igbt_temperature_c": int(payload[12]),
            "transformer_temperature_c": int(payload[13]),
        }

    def query_output_measurements(self):
        frame = self._transaction(self.CLASS_QUERY, self.WORD_QUERY_OUTPUT_MEAS)
        payload = frame.payload
        if len(payload) < 55:
            raise RuntimeError("Output measurement payload too short")

        result = {"output_mode": int(payload[0])}
        for prefix, offset in (("u", 1), ("v", 19), ("w", 37)):
            phase = self._parse_phase_measurements(payload, offset)
            result["phase_{0}_voltage_v".format(prefix)] = phase["voltage_v"]
            result["phase_{0}_current_a".format(prefix)] = phase["current_a"]
            result["phase_{0}_frequency_hz".format(prefix)] = phase["frequency_hz"]
            result["phase_{0}_active_power_w".format(prefix)] = phase["active_power_w"]
            result["phase_{0}_apparent_power_va".format(prefix)] = phase["apparent_power_va"]
            result["phase_{0}_power_factor".format(prefix)] = phase["power_factor"]
            result["phase_{0}_crest_factor".format(prefix)] = phase["crest_factor"]
            result["phase_{0}_peak_current_a".format(prefix)] = phase["peak_current_a"]
        return result

    def _parse_phase_measurements(self, payload, offset):
        block = payload[offset : offset + 18]
        if len(block) != 18:
            raise RuntimeError("Phase measurement block is incomplete")
        return {
            "voltage_v": int.from_bytes(block[0:2], "big") / 10.0,
            "current_a": int.from_bytes(block[2:4], "big") / 10.0,
            "frequency_hz": int.from_bytes(block[4:6], "big") / 10.0,
            "active_power_w": self._decode_signed_24(block[6:9]),
            "apparent_power_va": int.from_bytes(block[9:12], "big"),
            "power_factor": int.from_bytes(block[12:14], "big") / 1000.0,
            "crest_factor": int.from_bytes(block[14:16], "big") / 1000.0,
            "peak_current_a": int.from_bytes(block[16:18], "big") / 10.0,
        }

    def _transaction(self, command_class, command_word, payload=b""):
        with self._lock:
            self._ensure_connected()
            request = self._build_frame(int(command_class), int(command_word), payload)
            self._write_bytes(request)
            response = self._read_frame()
            return self._parse_frame(response, int(command_class), int(command_word))

    def _build_frame(self, command_class, command_word, payload):
        address = int(self.SlaveAddress)
        if address < 1 or address > 255:
            raise RuntimeError("Address must be in range 1..255")

        raw_payload = bytes(payload or b"")
        total_bytes = 8 + len(raw_payload)
        body = bytes(
            [
                (total_bytes >> 8) & 0xFF,
                total_bytes & 0xFF,
                address & 0xFF,
                command_class & 0xFF,
                command_word & 0xFF,
            ]
        ) + raw_payload

        checksum = sum(body) & 0xFF
        return bytes([self.FRAME_HEADER]) + body + bytes([checksum, self.FRAME_END])

    def _read_frame(self):
        header = self._recv_exact(1)
        if header[0] != self.FRAME_HEADER:
            raise RuntimeError("Invalid frame header: {0:02X}".format(header[0]))

        length_bytes = self._recv_exact(2)
        total_bytes = int.from_bytes(length_bytes, "big")
        if total_bytes < 8:
            raise RuntimeError("Invalid frame length: {0}".format(total_bytes))

        remainder = self._recv_exact(total_bytes - 3)
        return header + length_bytes + remainder

    def _parse_frame(self, frame, expected_class, expected_word):
        if len(frame) < 8:
            raise RuntimeError("Response frame is too short")
        if frame[-1] != self.FRAME_END:
            raise RuntimeError("Invalid frame terminator")

        total_bytes = int.from_bytes(frame[1:3], "big")
        if total_bytes != len(frame):
            raise RuntimeError(
                "Frame length mismatch expected={0} actual={1}".format(total_bytes, len(frame))
            )

        received_checksum = frame[-2]
        computed_checksum = sum(frame[1:-2]) & 0xFF
        if received_checksum != computed_checksum:
            raise RuntimeError(
                "Checksum mismatch rx={0:02X} calc={1:02X}".format(received_checksum, computed_checksum)
            )

        command_class = frame[4]
        command_word = frame[5]
        payload = frame[6:-2]

        if command_class == self.CLASS_ERROR:
            error_code = payload[0] if payload else -1
            raise RuntimeError(
                "Grid simulator protocol error for command {0:02X}: code={1}".format(
                    command_word,
                    error_code,
                )
            )

        if command_class != expected_class:
            raise RuntimeError(
                "Unexpected command class in response: {0:02X}".format(command_class)
            )
        if command_word != expected_word:
            raise RuntimeError(
                "Unexpected command word in response: {0:02X}".format(command_word)
            )

        if command_class != self.CLASS_QUERY and payload and payload[0] != 0x00:
            raise RuntimeError(
                "Set/control command failed with status={0:02X}".format(payload[0])
            )

        return XinhuaFrame(
            command_class=command_class,
            command_word=command_word,
            payload=payload,
        )

    def _recv_exact(self, size):
        chunks = bytearray()
        while len(chunks) < size:
            packet = self._read_bytes(size - len(chunks))
            if not packet:
                raise TimeoutError("Timed out waiting for grid simulator response")
            chunks.extend(packet)
        return bytes(chunks)

    def _write_bytes(self, payload):
        self._ensure_connected()
        written = self._serial.write(payload)
        if written != len(payload):
            raise RuntimeError(
                "Short write over serial: expected={0} written={1}".format(len(payload), written)
            )

    def _read_bytes(self, size):
        self._ensure_connected()
        return self._serial.read(size)

    @staticmethod
    def _decode_signed_24(value):
        if len(value) != 3:
            raise RuntimeError("Invalid signed-24 value length")
        raw = int.from_bytes(value, "big", signed=False)
        return -(raw & 0x7FFFFF) if (raw & 0x800000) else raw

    def _build_online_regulation_payload(self, voltages, frequencies, wave_codes):
        if not (len(voltages) == len(frequencies) == len(wave_codes) == 3):
            raise RuntimeError("Online regulation requires exactly three phase values")

        encoded = bytearray()
        max_voltage = float(self.MaxVoltage)
        for index in range(3):
            voltage = float(voltages[index])
            frequency = float(frequencies[index])
            wave_code = int(wave_codes[index])

            if voltage < 0.0 or voltage > max_voltage:
                raise RuntimeError(
                    "Voltage out of range for phase {0}: {1}. Max allowed: {2}".format(
                        index + 1,
                        voltage,
                        max_voltage,
                    )
                )
            if frequency < 45.0 or frequency > 240.0:
                raise RuntimeError(
                    "Frequency out of range for phase {0}: {1}".format(index + 1, frequency)
                )
            if wave_code < 0 or wave_code > 10:
                raise RuntimeError(
                    "Wave code out of range for phase {0}: {1}".format(index + 1, wave_code)
                )

            voltage_raw = int(round(voltage * 10.0))
            frequency_raw = int(round(frequency * 100.0))
            encoded.extend(voltage_raw.to_bytes(2, "big", signed=False))
            encoded.extend(frequency_raw.to_bytes(2, "big", signed=False))
            encoded.append(wave_code)

        return bytes(encoded)

    @staticmethod
    def _normalize_port_name(port_name):
        cleaned = str(port_name).strip()
        upper = cleaned.upper()
        if upper.startswith("CM") and len(cleaned) > 2 and cleaned[2:].isdigit():
            return "COM{0}".format(cleaned[2:])
        return cleaned

    def _ensure_connected(self):
        if self._serial is None or not bool(getattr(self._serial, "is_open", True)):
            raise RuntimeError("gridSimulator is not connected")
