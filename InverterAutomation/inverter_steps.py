"""Editor-safe, draggable OpenTAP steps for the Inverter DUT.

Every discoverable step inherits directly from TestStep.  OpenTAP's Python
type discovery can become unstable when visible steps inherit through Python
helper classes, even when those helpers are marked non-browsable.
"""

import json
import time

import OpenTap
from opentap import TestStep, attribute, property
from System import Boolean, Double, String

from .common import log_error, log_info, log_warning
from .inverter_dut import Inverter


def _require_dut(step):
    if step.Inverter is None:
        raise RuntimeError("Select an Inverter DUT in Step Settings")
    return step.Inverter


def _run_command(step, method_name):
    dut = _require_dut(step)
    result = getattr(dut, method_name)()
    log_info("{0} completed: {1}", method_name, str(result))
    step.UpgradeVerdict(OpenTap.Verdict.Pass)
    


def _run_read(step, method_name, result_name):
    dut = _require_dut(step)
    result = getattr(dut, method_name)()
    text = json.dumps(result, sort_keys=True) if isinstance(result, (dict, list)) else str(result)
    log_info("{0}: {1}", result_name, text)
    step.PublishResult(result_name, ["Value"], [text])
    step.UpgradeVerdict(OpenTap.Verdict.Pass)


def _set_error(step, operation, exc):
    log_error("{0} failed: {1}", operation, str(exc))
    step.UpgradeVerdict(OpenTap.Verdict.Error)


def _payloads_from_status(status):
    if not isinstance(status, dict):
        return []
    return [
        status.get("latest_payload"),
        status.get("third_payload"),
        status.get("second_payload"),
        status.get("first_payload"),
    ]


def _to_text(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True)
    return str(value)


def _to_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text == "true":
            return True
        if text == "false":
            return False
    return None


@attribute(OpenTap.Display("Control On", "Send control_on.", "Inverter Automation\\Commands"))
class SendControlOn(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "control_on")
        except Exception as exc:
            _set_error(self, "control_on", exc)


@attribute(OpenTap.Display("Control Off", "Send control_off.", "Inverter Automation\\Commands"))
class SendControlOff(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "control_off")
        except Exception as exc:
            _set_error(self, "control_off", exc)


@attribute(OpenTap.Display("Inverter Reset", "Send inverter_reset.", "Inverter Automation\\Commands"))
class InverterReset(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "inverter_reset")
        except Exception as exc:
            _set_error(self, "inverter_reset", exc)


@attribute(OpenTap.Display("Clear DSP Sensor Error", "Send dsp_clear_sensor_error.", "Inverter Automation\\Commands"))
class ClearDspSensorError(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "dsp_clear_sensor_error")
        except Exception as exc:
            _set_error(self, "dsp_clear_sensor_error", exc)


@attribute(OpenTap.Display("Battery Relay Open", "Send battery_poweroff.", "Inverter Automation\\Commands"))
class BatteryRelayOpen(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "battery_relay_open")
        except Exception as exc:
            _set_error(self, "battery_relay_open", exc)


@attribute(OpenTap.Display("Battery Wakeup", "Send battery_wakeup.", "Inverter Automation\\Commands"))
class BatteryWakeup(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "battery_wakeup")
            #log_info("Battery wakeup command sent successfully.KKKKKKKKKKKKKKKKKK")
        except Exception as exc:
            _set_error(self, "battery_wakeup", exc)


@attribute(OpenTap.Display("Battery Shutdown", "Send battery_shutdown.", "Inverter Automation\\Commands"))
class BatteryShutdown(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "battery_shutdown")
        except Exception as exc:
            _set_error(self, "battery_shutdown", exc)


@attribute(OpenTap.Display("Default Mode", "Send default_mode.", "Inverter Automation\\Commands"))
class DefaultMode(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "default_mode")
        except Exception as exc:
            _set_error(self, "default_mode", exc)


@attribute(OpenTap.Display("Set Load Following Mode", "Send set_load_following_mode.", "Inverter Automation\\Commands"))
class SetLoadFollowingMode(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_command(self, "set_load_following_mode")
        except Exception as exc:
            _set_error(self, "set_load_following_mode", exc)


@attribute(OpenTap.Display("Read Connection Status", "Read status() from the inverter DUT.", "Inverter Automation\\Diagnostics"))
class ReadConnectionStatus(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_read(self, "status", "Connection Status")
        except Exception as exc:
            _set_error(self, "status", exc)


@attribute(OpenTap.Display("Read Payload Status", "Read payload_status() from the inverter DUT.", "Inverter Automation\\Diagnostics"))
class ReadPayloadStatus(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    
    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_read(self, "payload_status", "Payload Status")
        except Exception as exc:
            _set_error(self, "payload_status", exc)


@attribute(OpenTap.Display("Read Latest Payload", "Publish every key from the latest payload.", "Inverter Automation\\Diagnostics"))
class ReadLatestPayload(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            dut = _require_dut(self)
            payload = dut.latest_payload_snapshot()
            #log_info("Latest payload snapshot: {0}", str(payload))

            
            if not payload:
                raise RuntimeError("No payload is available yet")

            keys = sorted(payload.keys())
            values = [_to_text(payload[key]) for key in keys]
            self.PublishResult("Latest Payload", keys, values)
            #log_info("Published {0} payload keys", len(keys))
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "Read Latest Payload", exc)
            


@attribute(OpenTap.Display("Read Alerts", "Read alerts from telemetry.", "Inverter Automation\\Diagnostics"))
class ReadAlerts(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_read(self, "get_alerts", "Alerts")
        except Exception as exc:
            _set_error(self, "get_alerts", exc)


@attribute(OpenTap.Display("Read Trips", "Read trips from telemetry.", "Inverter Automation\\Diagnostics"))
class ReadTrips(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_read(self, "get_trips", "Trips")
        except Exception as exc:
            _set_error(self, "get_trips", exc)


@attribute(OpenTap.Display("Read Hardware Trips", "Read hardware trips from telemetry.", "Inverter Automation\\Diagnostics"))
class ReadHardwareTrips(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_read(self, "get_hw_trips", "Hardware Trips")
        except Exception as exc:
            _set_error(self, "get_hw_trips", exc)


@attribute(OpenTap.Display("Check State", "Run check_state on the inverter DUT.", "Inverter Automation\\Diagnostics"))
class CheckState(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            _run_read(self, "check_state", "Inverter State")
        except Exception as exc:
            _set_error(self, "check_state", exc)


@attribute(OpenTap.Display("Verify Control On", "Wait for control_status to become true.", "Inverter Automation\\Verification"))
class VerifyControlOn(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    Timeout = property(Double, 15.0).add_attribute(OpenTap.Display("Timeout", "Maximum verification time.", "Timing", 1)).add_attribute(OpenTap.Unit("s"))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            dut = _require_dut(self)
            deadline = time.monotonic() + float(self.Timeout)
            last = None
            while time.monotonic() < deadline:
                status = dut.payload_status()
                for payload in _payloads_from_status(status):
                    if isinstance(payload, dict) and "control_status" in payload:
                        last = payload["control_status"]
                        is_on = last is True or (isinstance(last, str) and last.strip().lower() == "true")
                        if is_on:
                            self.PublishResult("Control Status", ["Expected", "Actual"], [True, str(last)])
                            self.UpgradeVerdict(OpenTap.Verdict.Pass)
                            return
                time.sleep(0.1)
            log_error("control_status did not become true. Last value: {0}", str(last))
            self.UpgradeVerdict(OpenTap.Verdict.Fail)
        except Exception as exc:
            _set_error(self, "Verify Control On", exc)


@attribute(OpenTap.Display("Verify Payload Key", "Assert one payload key against an expected value.", "Inverter Automation\\Verification"))
class VerifyPayloadKey(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    Key = property(String, "control_status").add_attribute(OpenTap.Display("Key", "Payload key to verify.", "Verification", 1))
    ExpectedValue = property(String, "true").add_attribute(OpenTap.Display("Expected value", "Expected payload value as text.", "Verification", 2))
    NumericTolerance = property(Double, 0.0).add_attribute(OpenTap.Display("Numeric tolerance", "Allowed absolute difference for numeric values.", "Verification", 3))
    IgnoreCase = property(Boolean, True).add_attribute(OpenTap.Display("Ignore case", "Case-insensitive compare for string values.", "Verification", 4))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            dut = _require_dut(self)
            payload = dut.latest_payload_snapshot()
            if not payload:
                raise RuntimeError("No payload is available yet")
            if self.Key not in payload:
                raise RuntimeError("Payload key '{0}' was not found".format(self.Key))

            actual = payload[self.Key]
            expected_text = str(self.ExpectedValue)

            actual_bool = _to_bool(actual)
            expected_bool = _to_bool(expected_text)
            if actual_bool is not None and expected_bool is not None:
                passed = actual_bool == expected_bool
            else:
                passed = False
                try:
                    actual_num = float(actual)
                    expected_num = float(expected_text)
                    passed = abs(actual_num - expected_num) <= float(self.NumericTolerance)
                except Exception:
                    actual_text = _to_text(actual)
                    if bool(self.IgnoreCase):
                        passed = actual_text.strip().lower() == expected_text.strip().lower()
                    else:
                        passed = actual_text == expected_text

            self.PublishResult("Payload Key Check", ["Key", "Expected", "Actual", "Pass"], [str(self.Key), expected_text, _to_text(actual), passed])
            if passed:
                self.UpgradeVerdict(OpenTap.Verdict.Pass)
            else:
                log_error("Payload key check failed for '{0}'. Expected: {1}, Actual: {2}", str(self.Key), expected_text, _to_text(actual))
                self.UpgradeVerdict(OpenTap.Verdict.Fail)
        except Exception as exc:
            _set_error(self, "Verify Payload Key", exc)
