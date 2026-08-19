"""OpenTAP DUT representing the inverter formerly wrapped by techapp.py."""

import json
import threading
import time
from datetime import datetime

import OpenTap
import opentap
from opentap import Dut, attribute, property
from System import Boolean, Double, Int32, String
from websockets.sync.client import connect

from .common import log_info, log_warning


@attribute(OpenTap.Display("Inverter", "Inverter DUT controlled over WebSocket.", "Inverter Automation"))
class Inverter(Dut):
    IpAddress = property(String, "127.0.0.1").add_attribute(
        OpenTap.Display("IP address", "IPv4 address or hostname of the inverter.", "Connection", 1)
    )
    Port = property(Int32, 3000).add_attribute(
        OpenTap.Display("Port", "WebSocket server port.", "Connection", 2)
    )
    Path = property(String, "").add_attribute(
        OpenTap.Display("Path", "Optional WebSocket path without a leading slash.", "Connection", 3)
    )
    ConnectionTimeout = property(Double, 10.0).add_attribute(
        OpenTap.Display("Connection timeout", "Maximum connection time.", "Timing", 1)
    ).add_attribute(OpenTap.Unit("s"))
    PayloadTimeout = property(Double, 15.0).add_attribute(
        OpenTap.Display("Payload timeout", "Maximum wait for requested telemetry.", "Timing", 2)
    ).add_attribute(OpenTap.Unit("s"))
    SafeControlOffOnClose = property(Boolean, True).add_attribute(
        OpenTap.Display("Send control_off on close", "Safety cleanup before disconnecting.", "Safety", 1)
    )

    def __init__(self):
        super().__init__()
        self.connected = False
        self.last_error = None
        self.last_status_change = None
        self.current_uri = ""
        self.first_payload = None
        self.second_payload = None
        self.third_payload = None
        self.latest_payload = None
        self.last_payload_time = None
        self.connection_number = 0
        self.discarded_payload_count = 0
        self.last_discarded_payload_time = None
        self.last_discard_reason = None
        self.last_command = None
        self.last_command_time = None
        self.alertsList = None
        self.tripsList = None
        self.hwTripsList = None
        self._message_index = 0
        self._websocket = None
        self._receiver = None
        self._stop_receiver = threading.Event()
        self._send_lock = threading.Lock()
        self._payload_lock = threading.Lock()

        self.Rules.Add(opentap.Rule("IpAddress", lambda: bool(str(self.IpAddress).strip()), lambda: "IP address cannot be empty."))
        self.Rules.Add(opentap.Rule("Port", lambda: 1 <= self.Port <= 65535, lambda: "Port must be between 1 and 65535."))
        self.Rules.Add(opentap.Rule("ConnectionTimeout", lambda: self.ConnectionTimeout > 0, lambda: "Connection timeout must be positive."))
        self.Rules.Add(opentap.Rule("PayloadTimeout", lambda: self.PayloadTimeout > 0, lambda: "Payload timeout must be positive."))

    def _uri(self):
        path = str(self.Path).strip().lstrip("/")
        return "ws://{0}:{1}{2}".format(self.IpAddress, self.Port, "/" + path if path else "")

    def __str__(self):
        return "Inverter is configured with {0}:{1}".format(self.IpAddress, self.Port)

    def Open(self):
        super().Open()
        self.current_uri = self._uri()
        log_info("Connecting inverter DUT to {0}", self.current_uri)
        self._stop_receiver.clear()
        self._websocket = connect(self.current_uri, open_timeout=float(self.ConnectionTimeout))
        self.connected = True
        self.last_error = None
        self.last_status_change = datetime.utcnow().isoformat()
        self.connection_number += 1
        self._message_index = 0
        with self._payload_lock:
            self.first_payload = None
            self.second_payload = None
            self.third_payload = None
            self.latest_payload = None
        self._receiver = threading.Thread(target=self._receive_loop, name="inverter-dut-receiver", daemon=True)
        self._receiver.start()

    def connect(self):
        """Compatibility method matching techapp.connect()."""
        if not self.connected:
            self.Open()
        return self.status()

    def _receive_loop(self):
        while not self._stop_receiver.is_set():
            try:
                message = self._websocket.recv(timeout=0.25)
            except TimeoutError:
                continue
            except Exception as exc:
                if not self._stop_receiver.is_set():
                    self.last_error = str(exc)
                    self.connected = False
                    self.last_status_change = datetime.utcnow().isoformat()
                return

            try:
                payload = json.loads(message) if isinstance(message, str) else message
            except (TypeError, ValueError):
                payload = None
            if not isinstance(payload, dict):
                self.discarded_payload_count += 1
                self.last_discarded_payload_time = datetime.utcnow().isoformat()
                self.last_discard_reason = "Payload is not a JSON object"
                continue

            with self._payload_lock:
                self._message_index += 1
                self.last_payload_time = datetime.utcnow().isoformat()
                self.last_discard_reason = None
                if self._message_index == 1:
                    self.first_payload = payload
                elif self._message_index == 2:
                    self.second_payload = payload
                elif self._message_index == 3:
                    self.third_payload = payload
                else:
                    self.latest_payload = payload

    def Close(self):
        websocket = self._websocket
        if websocket is not None and self.SafeControlOffOnClose:
            try:
                self.control_off()
            except Exception as exc:
                log_warning("Safety cleanup control_off failed: {0}", str(exc))
        self._stop_receiver.set()
        if websocket is not None:
            try:
                websocket.close()
            except Exception as exc:
                log_warning("WebSocket close failed: {0}", str(exc))
        if self._receiver is not None:
            self._receiver.join(timeout=2.0)
        self.connected = False
        self.last_status_change = datetime.utcnow().isoformat()
        self._websocket = None
        self._receiver = None
        super().Close()

    def status(self):
        return {"connected": self.connected, "endpoint": self.current_uri, "last_error": self.last_error, "last_status_change": self.last_status_change}

    def payload_status(self):
        with self._payload_lock:
            return {
                "connection_number": self.connection_number,
                "first_payload": self.first_payload,
                "second_payload": self.second_payload,
                "third_payload": self.third_payload,
                "latest_payload": self.latest_payload,
                "last_payload_time": self.last_payload_time,
                "discarded_payload_count": self.discarded_payload_count,
                "last_discarded_payload_time": self.last_discarded_payload_time,
                "last_discard_reason": self.last_discard_reason,
            }

    def latest_payload_snapshot(self):
        """Return a copy of the newest available payload dictionary."""
        with self._payload_lock:
            payloads = [self.latest_payload, self.third_payload, self.second_payload, self.first_payload]
            for payload in payloads:
                if isinstance(payload, dict):
                    return dict(payload)
        return {}

    def payload_keys(self):
        """Return sorted keys from the latest available payload."""
        return sorted(self.latest_payload_snapshot().keys())

    def get_payload_value(self, key, default=None):
        """Read one value from the latest available payload by key."""
        payload = self.latest_payload_snapshot()
        return payload.get(key, default)

    def disconnect(self):
        self.Close()

    def _send_command(self, command):
        if not self.connected or self._websocket is None:
            raise RuntimeError("Inverter WebSocket is not connected")
        with self._send_lock:
            self._websocket.send(command)
        self.last_command = command
        self.last_command_time = datetime.utcnow().isoformat()
        return command

    def control_on(self): return self._send_command("control_on")
    def control_off(self): return self._send_command("control_off")
    def inverter_reset(self): return self._send_command("inverter_reset")
    def dsp_clear_sensor_error(self): return self._send_command("dsp_clear_sensor_error")
    def battery_relay_open(self): return self._send_command("battery_poweroff")
    def battery_wakeup(self): return self._send_command("battery_wakeup")
    def battery_shutdown(self): return self._send_command("battery_shutdown")
    def default_mode(self): return self._send_command("default_mode")
    def set_load_following_mode(self): return self._send_command("set_load_following_mode")

    def _wait_for_payload_key(self, key):
        deadline = time.monotonic() + float(self.PayloadTimeout)
        while time.monotonic() < deadline:
            payload = self.latest_payload_snapshot()
            if key in payload:
                return payload[key]
            time.sleep(0.1)
        raise TimeoutError("Telemetry key '{0}' was not received within {1} s".format(key, self.PayloadTimeout))

    def get_alerts(self):
        self.alertsList = self._wait_for_payload_key("alertsList")
        return self.alertsList

    def get_trips(self):
        self.tripsList = self._wait_for_payload_key("tripsList")
        return self.tripsList

    def get_hw_trips(self):
        self.hwTripsList = self._wait_for_payload_key("hwTripsList")
        return self.hwTripsList

    def check_state(self):
        if self.tripsList in (None, []) and self.hwTripsList in (None, []):
            return "Normal"
        return "Fault"
