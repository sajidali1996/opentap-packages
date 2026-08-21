"""OpenTAP Instrument plugin for a Modbus RTU load bank."""

from __future__ import annotations

import math
import struct
import threading
from typing import Dict, List, Tuple

import OpenTap
import opentap
from opentap import Instrument, attribute, property
from System import Boolean, Double, Int32, String

try:
    from pymodbus.client import ModbusSerialClient
except Exception:  # pragma: no cover - dependency is provided in runtime env.
    ModbusSerialClient = None


_LOAD_WEIGHTS = [100, 200, 200, 500, 1000, 1000, 2000, 2000]


@attribute(
    OpenTap.Display(
        "loadBank",
        "Programmable load bank over Modbus RTU.",
        "Instruments",
    )
)
class LoadBank(Instrument):
    SerialPort = property(String, "COM8").add_attribute(
        OpenTap.Display("Serial port", "Serial port, e.g. COM8.", "Connection", 1)
    )
    BaudRate = property(Int32, 9600).add_attribute(
        OpenTap.Display("Baud rate", "Modbus RTU baud rate.", "Connection", 2)
    )
    Timeout = property(Double, 3.0).add_attribute(
        OpenTap.Display("Timeout", "Read/write timeout.", "Connection", 3)
    ).add_attribute(OpenTap.Unit("s"))
    Parity = property(String, "N").add_attribute(
        OpenTap.Display("Parity", "N=None, E=Even, O=Odd.", "Connection", 4)
    )
    StopBits = property(Int32, 1).add_attribute(
        OpenTap.Display("Stop bits", "Serial stop bits.", "Connection", 5)
    )
    ByteSize = property(Int32, 8).add_attribute(
        OpenTap.Display("Data bits", "Serial data bits.", "Connection", 6)
    )

    # Special requirement from user workflow:
    # RealPower_command = round((120^2/101^2) * RealPower_input)
    Use101VPowerConversion = property(Boolean, True).add_attribute(
        OpenTap.Display(
            "Use 120V->101V conversion",
            "Apply RealPower_command=round((120^2/101^2)*RealPower_input)",
            "Load Logic",
            1,
        )
    )

    SwapFloatWords = property(Boolean, False).add_attribute(
        OpenTap.Display(
            "Swap float words",
            "Swap the two 16-bit words when decoding 32-bit float measurements.",
            "Measurements",
            1,
        )
    )
    SwapFloatBytes = property(Boolean, False).add_attribute(
        OpenTap.Display(
            "Swap float bytes",
            "Swap bytes inside each 16-bit word when decoding 32-bit float measurements.",
            "Measurements",
            2,
        )
    )

    # Coil block map from protocol table (0-based addresses).
    _BLOCKS = {
        "AR": {"slave": 1, "start": 0},
        "AL": {"slave": 1, "start": 8},
        "AC": {"slave": 1, "start": 16},
        "BR": {"slave": 1, "start": 24},
        "BL": {"slave": 2, "start": 0},
        "BC": {"slave": 2, "start": 8},
        "CR": {"slave": 2, "start": 16},
        "CL": {"slave": 2, "start": 24},
        "CC": {"slave": 3, "start": 0},
    }

    _REAL_POWER_BLOCK = {"A": "AR", "B": "BR", "C": "CR"}
    _INDUCTIVE_BLOCK = {"A": "AL", "B": "BL", "C": "CL"}
    _CAPACITIVE_BLOCK = {"A": "AC", "B": "BC", "C": "CC"}

    _METER_SLAVE = {"A": 4, "B": 5, "C": 6}

    def __init__(self):
        super().__init__()
        self.Name = "loadBank"
        self._client = None
        self._lock = threading.RLock()

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
                "Timeout",
                lambda: float(self.Timeout) > 0,
                lambda: "Timeout must be positive.",
            )
        )

    def Open(self):
        super().Open()
        if self._is_connected():
            return
        if ModbusSerialClient is None:
            raise RuntimeError("pymodbus is required. Install dependencies from loadBank/requirements.txt")

        parity = str(self.Parity).strip().upper() or "N"
        if parity not in {"N", "E", "O"}:
            raise RuntimeError("Parity must be one of N, E, O")

        self._client = ModbusSerialClient(
            port=str(self.SerialPort).strip(),
            baudrate=int(self.BaudRate),
            bytesize=int(self.ByteSize),
            parity=parity,
            stopbits=int(self.StopBits),
            timeout=float(self.Timeout),
        )

        if not self._client.connect():
            self._client = None
            raise RuntimeError("Could not open Modbus RTU connection on {}".format(self.SerialPort))

        self.log.Info("Connected to load bank on {0}", str(self.SerialPort))

    def Close(self):
        try:
            with self._lock:
                if self._client is not None:
                    try:
                        self._client.close()
                    except Exception as exc:
                        self.log.Warning("Error while closing load bank connection: {0}", str(exc))
                self._client = None
        finally:
            super().Close()

    def _is_connected(self) -> bool:
        return self._client is not None and bool(getattr(self._client, "connected", True))

    def _ensure_connected(self):
        if not self._is_connected():
            raise RuntimeError("loadBank is not connected")

    def _request(self, method_name: str, slave_id: int, *args):
        with self._lock:
            self._ensure_connected()
            method = getattr(self._client, method_name)

            response = None
            last_type_error = None

            # pymodbus uses different slave-id keywords across versions.
            for keyword in ("slave", "unit", "device_id"):
                try:
                    response = method(*args, **{keyword: int(slave_id)})
                    last_type_error = None
                    break
                except TypeError as exc:
                    last_type_error = exc

            if response is None and last_type_error is not None:
                try:
                    # Compatibility fallback for signatures that still accept positional slave id.
                    response = method(*args, int(slave_id))
                    last_type_error = None
                except TypeError as exc:
                    raise RuntimeError(
                        "Unsupported pymodbus call signature for {}: {}".format(
                            method_name,
                            str(exc),
                        )
                    ) from last_type_error

            if response is None:
                raise RuntimeError("No response for Modbus {}".format(method_name))
            if hasattr(response, "isError") and response.isError():
                raise RuntimeError("Modbus {} failed: {}".format(method_name, response))
            return response

    # ---------- Basic Modbus operations ----------
    def read_coils(self, slave_id: int, start_address: int, count: int) -> List[bool]:
        result = self._request("read_coils", slave_id, int(start_address), int(count))
        bits = list(getattr(result, "bits", []))
        if len(bits) < int(count):
            raise RuntimeError("Short read for coils: expected {} got {}".format(count, len(bits)))
        return [bool(x) for x in bits[: int(count)]]

    def read_discrete_inputs(self, slave_id: int, start_address: int, count: int) -> List[bool]:
        result = self._request("read_discrete_inputs", slave_id, int(start_address), int(count))
        bits = list(getattr(result, "bits", []))
        if len(bits) < int(count):
            raise RuntimeError("Short read for discrete inputs: expected {} got {}".format(count, len(bits)))
        return [bool(x) for x in bits[: int(count)]]

    def write_single_coil(self, slave_id: int, address: int, value: bool):
        self._request("write_coil", slave_id, int(address), bool(value))

    def write_multiple_coils(self, slave_id: int, start_address: int, values: List[bool]):
        self._request("write_coils", slave_id, int(start_address), [bool(v) for v in values])

    def read_holding_registers(self, slave_id: int, start_address: int, count: int) -> List[int]:
        result = self._request("read_holding_registers", slave_id, int(start_address), int(count))
        registers = list(getattr(result, "registers", []))
        if len(registers) < int(count):
            raise RuntimeError("Short read for holding registers: expected {} got {}".format(count, len(registers)))
        return [int(x) for x in registers[: int(count)]]

    def write_holding_register(self, slave_id: int, address: int, value: int):
        self._request("write_register", slave_id, int(address), int(value) & 0xFFFF)

    # ---------- Protocol-specific control ----------
    @staticmethod
    def _normalize_phase(phase) -> str:
        if isinstance(phase, int):
            mapping = {1: "A", 2: "B", 3: "C"}
            if phase not in mapping:
                raise ValueError("Phase must be 1, 2, 3 or A, B, C")
            return mapping[phase]
        text = str(phase).strip().upper()
        if text not in {"A", "B", "C"}:
            raise ValueError("Phase must be A, B, or C")
        return text

    @staticmethod
    def _best_combination(weights: List[int], target: int) -> Tuple[List[int], int]:
        if target <= 0:
            return [], 0

        best_indices: List[int] = []
        best_sum = 0
        best_difference = math.inf

        n = len(weights)
        for mask in range(1, 1 << n):
            current_sum = 0
            current_indices = []
            for bit in range(n):
                if mask & (1 << bit):
                    current_sum += int(weights[bit])
                    current_indices.append(bit)

            difference = abs(int(target) - current_sum)
            if difference < best_difference:
                best_difference = difference
                best_sum = current_sum
                best_indices = current_indices
                if difference == 0:
                    break

        return best_indices, best_sum

    def _apply_block(self, block_name: str, target_value: float) -> Dict[str, object]:
        block = self._BLOCKS[block_name]
        target_int = max(0, int(round(float(target_value))))

        indices, achieved = self._best_combination(_LOAD_WEIGHTS, target_int)

        values = [False] * len(_LOAD_WEIGHTS)
        relay_addresses = []
        for index in indices:
            values[index] = True
            relay_addresses.append(int(block["start"]) + index)

        self.write_multiple_coils(int(block["slave"]), int(block["start"]), values)

        return {
            "block": block_name,
            "slave_id": int(block["slave"]),
            "start_address": int(block["start"]),
            "target": target_int,
            "achieved": int(achieved),
            "difference": int(achieved - target_int),
            "coil_values": values,
            "enabled_addresses": relay_addresses,
        }

    def convert_real_power_command(self, real_power_input: float) -> int:
        if not bool(self.Use101VPowerConversion):
            return int(round(float(real_power_input)))

        # Required conversion formula:
        # RealPower_command = round((120^2/101^2) * RealPower_input)
        return int(round((120.0 ** 2 / 101.0 ** 2) * float(real_power_input)))

    def set_real_power(self, phase, real_power_input: float) -> Dict[str, object]:
        phase_name = self._normalize_phase(phase)
        block_name = self._REAL_POWER_BLOCK[phase_name]

        command_power = self.convert_real_power_command(float(real_power_input))
        result = self._apply_block(block_name, command_power)
        result["phase"] = phase_name
        result["real_power_input"] = float(real_power_input)
        result["real_power_command"] = int(command_power)
        return result

    def set_reactive_power(self, phase, reactive_power: float, mode: str) -> Dict[str, object]:
        phase_name = self._normalize_phase(phase)
        mode_name = str(mode).strip().lower()

        if mode_name == "inductive":
            block_name = self._INDUCTIVE_BLOCK[phase_name]
        elif mode_name == "capacitive":
            block_name = self._CAPACITIVE_BLOCK[phase_name]
        else:
            raise ValueError("Reactive mode must be 'inductive' or 'capacitive'")

        result = self._apply_block(block_name, float(reactive_power))
        result["phase"] = phase_name
        result["reactive_power_input"] = float(reactive_power)
        result["mode"] = mode_name
        return result

    def reset_real_power_loads(self):
        self.write_multiple_coils(1, 0, [False] * 8)    # AR
        self.write_multiple_coils(1, 24, [False] * 8)   # BR
        self.write_multiple_coils(2, 16, [False] * 8)   # CR

    def reset_all_load_groups(self):
        for block in self._BLOCKS.values():
            self.write_multiple_coils(int(block["slave"]), int(block["start"]), [False] * 8)

    def select_voltage_level(self, level_v: int):
        level = int(level_v)
        if level == 120:
            self.write_single_coil(3, 8, True)
            self.write_single_coil(3, 9, False)
            return
        if level == 240:
            self.write_single_coil(3, 8, False)
            self.write_single_coil(3, 9, True)
            return
        raise ValueError("Voltage level must be 120 or 240")

    def set_power_switch(self, on: bool):
        self.write_single_coil(3, 13, bool(on))

    def set_load_switch(self, on: bool):
        self.write_single_coil(3, 14, bool(on))

    # ---------- Temperatures / alarms on Slave 03 ----------
    def read_air_outlet_temperature_c(self) -> float:
        value = self.read_holding_registers(3, 8192, 1)[0]
        return float(self._to_signed_16(value)) / 10.0

    def read_loadband_temperature_c(self) -> float:
        value = self.read_holding_registers(3, 8193, 1)[0]
        return float(self._to_signed_16(value)) / 10.0

    def read_air_outlet_alarm_c(self) -> float:
        value = self.read_holding_registers(3, 8224, 1)[0]
        return float(self._to_signed_16(value)) / 10.0

    def read_loadband_alarm_c(self) -> float:
        value = self.read_holding_registers(3, 8225, 1)[0]
        return float(self._to_signed_16(value)) / 10.0

    def write_air_outlet_alarm_c(self, value_c: float):
        self.write_holding_register(3, 8224, self._from_tenth_c(value_c))

    def write_loadband_alarm_c(self, value_c: float):
        self.write_holding_register(3, 8225, self._from_tenth_c(value_c))

    # ---------- Inputs ----------
    def read_inductance_alarm(self) -> bool:
        return bool(self.read_discrete_inputs(1, 0, 1)[0])

    # ---------- Meter values on Slaves 04/05/06 ----------
    def read_phase_measurements(self, phase) -> Dict[str, float]:
        phase_name = self._normalize_phase(phase)
        slave = self._METER_SLAVE[phase_name]

        return {
            "phase_voltage_1_v": self.read_float32(slave, 42),
            "phase_voltage_2_v": self.read_float32(slave, 44),
            "phase_voltage_3_v": self.read_float32(slave, 46),
            "phase_current_1_a": self.read_float32(slave, 48),
            "phase_current_2_a": self.read_float32(slave, 50),
            "phase_current_3_a": self.read_float32(slave, 52),
            "active_power_1_w": self.read_float32(slave, 54),
            "active_power_2_w": self.read_float32(slave, 56),
            "active_power_3_w": self.read_float32(slave, 58),
            "active_power_total_w": self.read_float32(slave, 60),
            "reactive_power_1_var": self.read_float32(slave, 62),
            "reactive_power_2_var": self.read_float32(slave, 64),
            "reactive_power_3_var": self.read_float32(slave, 66),
            "reactive_power_total_var": self.read_float32(slave, 68),
            "apparent_power_1_va": self.read_float32(slave, 70),
            "apparent_power_2_va": self.read_float32(slave, 72),
            "apparent_power_3_va": self.read_float32(slave, 74),
            "apparent_power_total_va": self.read_float32(slave, 76),
            "power_factor_1": self.read_float32(slave, 78),
            "power_factor_2": self.read_float32(slave, 80),
            "power_factor_3": self.read_float32(slave, 82),
            "power_factor_total": self.read_float32(slave, 84),
            "frequency_hz": self.read_float32(slave, 86),
        }

    def read_float32(self, slave_id: int, start_address: int) -> float:
        regs = self.read_holding_registers(int(slave_id), int(start_address), 2)
        if len(regs) != 2:
            raise RuntimeError("Need exactly two registers for float32")

        words = [int(regs[0]), int(regs[1])]
        if bool(self.SwapFloatWords):
            words = [words[1], words[0]]

        raw = b"".join(word.to_bytes(2, byteorder="big", signed=False) for word in words)

        if bool(self.SwapFloatBytes):
            raw = raw[1:2] + raw[0:1] + raw[3:4] + raw[2:3]

        return float(struct.unpack(">f", raw)[0])

    @staticmethod
    def _to_signed_16(value: int) -> int:
        value_int = int(value) & 0xFFFF
        return value_int - 0x10000 if value_int & 0x8000 else value_int

    @staticmethod
    def _from_tenth_c(value_c: float) -> int:
        scaled = int(round(float(value_c) * 10.0))
        return scaled & 0xFFFF
