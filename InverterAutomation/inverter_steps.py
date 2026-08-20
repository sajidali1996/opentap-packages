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
from System.Collections.Generic import List
from System.ComponentModel import Browsable

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


def _parse_command_value(text):
    raw = str(text).strip()
    if raw == "":
        raise RuntimeError("Value cannot be empty")
    try:
        return json.loads(raw)
    except Exception:
        lowered = raw.lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
        if lowered == "null":
            return None
        return raw


_INVERTER_COMMAND_KEYS = [
    "pfset",
    "voltageSuppLimit",
    "gridOvLimit",
    "gridUvLimit",
    "ovrTime",
    "uvrTime",
    "gridOfLimit",
    "gridUfLimit",
    "ofrTime",
    "ufrTime",
    "rOfr",
    "reconnectBlockTimer",
    "fFQLimit",
    "fFQSlope",
    "pvConvStatus",
    "batConvStatus",
    "inverter_config_screen",
    "prefVpp",
]


def _build_inverter_command_key_choices():
    choices = List[String]()
    for key in _INVERTER_COMMAND_KEYS:
        choices.Add(key)
    return choices


_MASKING_FUNCTIONS = [
    "ovr",
    "uvr",
    "ofr",
    "ufr",
    "passiveIslandDetection",
    "activeIslandDetection",
    "frequencyFeedback",
    "stepInjection",
    "forcedStandbyState",
    "forcedNormalState",
    "reversePowerProtection",
    "powerFactorSwitching",
    "voltageRiseSuppression",
    "bypassCtTest",
]


def _build_masking_function_choices():
    choices = List[String]()
    for name in _MASKING_FUNCTIONS:
        choices.Add(name)
    return choices


def _notify_property_changed(obj, property_name):
    callback = getattr(obj, "OnPropertyChanged", None)
    if callable(callback):
        callback(property_name)


_VERIFY_PAYLOAD_KEYS = [
    "alerts",
    "alertsList",
    "Amb Temperature",
    "bat",
    "bat_available?",
    "bat_relay",
    "Battery Temperature",
    "batteryChargedToday",
    "batteryContribution",
    "batteryDischargedToday",
    "batteryState",
    "bms_bypass",
    "bms_comm",
    "CM4 Temperature",
    "cm4_v",
    "control_status",
    "dailyAcOutputYield",
    "dailyFeedinEnergy",
    "dailyPurchaseEnergy",
    "dailyPvYield",
    "designCapacity",
    "disconnecting_TechApp",
    "dsp_v",
    "dspAlertBitfield1",
    "dspAlertBitfield2",
    "dspControlStatusBitfield",
    "dspFaultBitfield1",
    "dspFaultBitfield2",
    "dspStateMachine",
    "dspStateMachine1",
    "dspStateMachine2",
    "dspStateMachine3",
    "dspUpTime",
    "eventTime",
    "export_status",
    "fgrid",
    "fixed_schedule_available",
    "grid",
    "grid_relay",
    "gridContribution",
    "gridPower",
    "gridPowerAdjusted",
    "gridState",
    "hotspotSsid",
    "hw_trip",
    "hwFaultBitField1",
    "hwFaultBitField2",
    "hwTripsList",
    "i_charge_max",
    "i_discharge_max",
    "ibat",
    "igrid1Max",
    "igrid1Rms",
    "igrid2Max",
    "igrid2Rms",
    "iinv1Dc",
    "iinv1Max",
    "iinv1Rms",
    "iinv2Max",
    "iinv2Rms",
    "InternetConnected",
    "inv_comm",
    "inv_mode",
    "Inverter Temperature",
    "inverter_status",
    "ipv1",
    "ipv1Max",
    "ipv2",
    "ipv2Max",
    "ipv3",
    "ipv3Max",
    "ipv4",
    "load_relay",
    "loadPower",
    "loadPowerAdjusted",
    "macAddress",
    "ntp_time_sync",
    "pBat",
    "pBat_Ac",
    "pgrid1",
    "pgrid2",
    "pinv1",
    "pinv2",
    "pPv",
    "pPv_Ac",
    "pPv1",
    "pPv2",
    "pPv3",
    "pv",
    "PV Temperature",
    "pv_available?",
    "pvContribution",
    "rackAmount",
    "rated_capacity",
    "RcServerConnected",
    "SeCloudConnected",
    "SES_feedback_bitfield",
    "SES_Version",
    "SimModApp",
    "sisw_v",
    "soc",
    "soh",
    "stackCurrent",
    "stackPower",
    "stackVoltage",
    "sup_trip",
    "tripsList",
    "update_schedule_available",
    "vbat",
    "vbus",
    "vbusC1",
    "vbusC1Max",
    "vbusC2",
    "vbusC2Max",
    "vbusMax",
    "vgrid1Rms",
    "vgrid2Rms",
    "vinv1Max",
    "vinv1Rms",
    "vinv2Max",
    "vinv2Rms",
    "vpv1",
    "vpv1Max",
    "vpv2",
    "vpv2Max",
    "vpv3",
    "vpv3Max",
    "vpv4",
]


def _build_payload_key_choices():
    choices = List[String]()
    for key in _VERIFY_PAYLOAD_KEYS:
        choices.Add(key)
    return choices


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


@attribute(OpenTap.Display("send Inverter command", "Send one inverter key/value command as JSON.", "Inverter Automation\\Commands"))
class SendInverterCommand(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    AvailableKeys = property(List[String], None).add_attribute(Browsable(False))
    Key = property(String, "pfset").add_attribute(OpenTap.AvailableValues("AvailableKeys")).add_attribute(OpenTap.Display("Key", "Inverter command key to send.", "Command", 1))
    Value = property(String, "0.95").add_attribute(OpenTap.Display("Value", "Value to send. Use JSON literal format (e.g. 109, 61.8, true, \"text\").", "Command", 2))

    def __init__(self):
        super().__init__()
        self.AvailableKeys = _build_inverter_command_key_choices()

    def Run(self):
        super().Run()
        try:
            dut = _require_dut(self)
            value = _parse_command_value(self.Value)
            result = dut.send_inverter_command(self.Key, value)
            self.PublishResult("Inverter Command", ["Key", "Value", "Command"], [str(self.Key), _to_text(value), str(result)])
            log_info("send_inverter_command completed: {0}", str(result))
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "send_inverter_command", exc)


@attribute(OpenTap.Display("apply masking", "Send selected masking functions as a combined command.", "Inverter Automation\\Commands"))
class ApplyMasking(TestStep):
    Inverter = property(Inverter, None).add_attribute(OpenTap.Display("Inverter", "Inverter DUT used by this step.", "Resources", 1))
    AvailableMaskingFunctions = property(List[String], None).add_attribute(Browsable(False))
    SelectedMaskingFunction = property(String, "ovr").add_attribute(OpenTap.AvailableValues("AvailableMaskingFunctions")).add_attribute(OpenTap.Display("Masking function", "Function selected from dropdown to add.", "Masking", 1))
    MaskingFunctions = property(List[String], None).add_attribute(OpenTap.AvailableValues("AvailableMaskingFunctions")).add_attribute(OpenTap.Display("Selected functions", "Combined masking functions to send.", "Masking", 2))

    def __init__(self):
        super().__init__()
        self.AvailableMaskingFunctions = _build_masking_function_choices()
        self.MaskingFunctions = List[String]()

    @attribute(Browsable(True))
    @attribute(OpenTap.Display("Add Selected", "Add selected masking function to the combined list.", "Masking", 3))
    def AddSelected(self):
        selected = str(self.SelectedMaskingFunction).strip()
        if selected == "":
            return
        if self.MaskingFunctions is None:
            self.MaskingFunctions = List[String]()
        if selected in self.MaskingFunctions:
            log_warning("Masking function '{0}' is already selected", selected)
            return
        self.MaskingFunctions.Add(selected)
        _notify_property_changed(self, "MaskingFunctions")
        log_info("Added masking function: {0}", selected)

    @attribute(Browsable(True))
    @attribute(OpenTap.Display("Remove Last Added", "Remove the last masking function from the combined list.", "Masking", 4))
    def RemoveLastAdded(self):
        if self.MaskingFunctions is None or self.MaskingFunctions.Count == 0:
            log_warning("No masking function to remove")
            return
        index = self.MaskingFunctions.Count - 1
        removed = self.MaskingFunctions[index]
        self.MaskingFunctions.RemoveAt(index)
        _notify_property_changed(self, "MaskingFunctions")
        log_info("Removed masking function: {0}", str(removed))

    def Run(self):
        super().Run()
        try:
            dut = _require_dut(self)
            selected = []
            if self.MaskingFunctions is not None:
                for item in self.MaskingFunctions:
                    text = str(item).strip()
                    if text:
                        selected.append(text)
            if not selected:
                raise RuntimeError("Add at least one masking function before running")

            result = dut.apply_masking(selected)
            payload = {"cmdType": "JetMaskingFunctionArray", "maskingFunctions": selected}
            self.PublishResult("Apply Masking", ["Count", "MaskingFunctions", "Payload", "Command"], [len(selected), json.dumps(selected), json.dumps(payload, separators=(",", ":")), str(result)])
            log_info("apply_masking completed: {0}", str(result))
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "apply_masking", exc)


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
    AvailableKeys = property(List[String], None).add_attribute(Browsable(False))
    Key = property(String, "control_status").add_attribute(OpenTap.AvailableValues("AvailableKeys")).add_attribute(OpenTap.Display("Key", "Payload key to verify.", "Verification", 1))
    ExpectedValue = property(String, "true").add_attribute(OpenTap.Display("Expected value", "Expected payload value as text.", "Verification", 2))
    NumericTolerance = property(Double, 0.0).add_attribute(OpenTap.Display("Numeric tolerance", "Allowed absolute difference for numeric values.", "Verification", 3))
    IgnoreCase = property(Boolean, True).add_attribute(OpenTap.Display("Ignore case", "Case-insensitive compare for string values.", "Verification", 4))

    def __init__(self):
        super().__init__()
        self.AvailableKeys = _build_payload_key_choices()

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
