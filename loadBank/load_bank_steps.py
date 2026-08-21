"""OpenTAP test steps for the loadBank instrument."""

import json

import OpenTap
from opentap import TestStep, attribute, property
from System import Boolean, Double, String
from System.Collections.Generic import List
from System.ComponentModel import Browsable

from .load_bank import LoadBank


def _require_instrument(step) -> LoadBank:
    if step.Instrument is None:
        raise RuntimeError("Select a loadBank instrument in Step Settings")
    return step.Instrument


def _publish_mapping(step, table_name, mapping):
    columns = list(mapping.keys())
    values = [mapping[name] for name in columns]
    step.PublishResult(table_name, columns, values)


def _set_error(step, operation, exc):
    step.log.Error("{0} failed: {1}", operation, str(exc))
    step.UpgradeVerdict(OpenTap.Verdict.Error)


def _phase_choices():
    values = List[String]()
    values.Add("A")
    values.Add("B")
    values.Add("C")
    return values


def _mode_choices():
    values = List[String]()
    values.Add("Inductive")
    values.Add("Capacitive")
    return values


def _voltage_choices():
    values = List[String]()
    values.Add("120")
    values.Add("240")
    return values


@attribute(OpenTap.Display("LoadBank Set Real Power", "Set resistive real power for one phase.", "Load Bank\\Commands"))
class LoadBankSetRealPower(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )

    AvailablePhases = property(List[String], None).add_attribute(Browsable(False))
    Phase = property(String, "A").add_attribute(
        OpenTap.AvailableValues("AvailablePhases")
    ).add_attribute(
        OpenTap.Display("Phase", "A, B, or C.", "Real Power", 1)
    )

    RealPowerInput = property(Double, 1000.0).add_attribute(
        OpenTap.Display("Real power input", "Target power based on 101 V usage.", "Real Power", 2)
    ).add_attribute(OpenTap.Unit("W"))

    def __init__(self):
        super().__init__()
        self.AvailablePhases = _phase_choices()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            result = instrument.set_real_power(str(self.Phase), float(self.RealPowerInput))
            _publish_mapping(
                self,
                "LoadBank Real Power",
                {
                    "Phase": result["phase"],
                    "RealPowerInput(W)": result["real_power_input"],
                    "RealPowerCommand(W)": result["real_power_command"],
                    "Achieved(W)": result["achieved"],
                    "Difference(W)": result["difference"],
                    "Slave": result["slave_id"],
                    "StartAddress": result["start_address"],
                    "EnabledAddresses": json.dumps(result["enabled_addresses"]),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Set Real Power", exc)


@attribute(OpenTap.Display("LoadBank Set Reactive Power", "Set inductive/capacitive reactive power for one phase.", "Load Bank\\Commands"))
class LoadBankSetReactivePower(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )

    AvailablePhases = property(List[String], None).add_attribute(Browsable(False))
    Phase = property(String, "A").add_attribute(
        OpenTap.AvailableValues("AvailablePhases")
    ).add_attribute(
        OpenTap.Display("Phase", "A, B, or C.", "Reactive Power", 1)
    )

    AvailableModes = property(List[String], None).add_attribute(Browsable(False))
    Mode = property(String, "Inductive").add_attribute(
        OpenTap.AvailableValues("AvailableModes")
    ).add_attribute(
        OpenTap.Display("Mode", "Inductive or Capacitive.", "Reactive Power", 2)
    )

    ReactivePower = property(Double, 1000.0).add_attribute(
        OpenTap.Display("Reactive power", "Target reactive power magnitude.", "Reactive Power", 3)
    ).add_attribute(OpenTap.Unit("var"))

    def __init__(self):
        super().__init__()
        self.AvailablePhases = _phase_choices()
        self.AvailableModes = _mode_choices()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            result = instrument.set_reactive_power(str(self.Phase), float(self.ReactivePower), str(self.Mode))
            _publish_mapping(
                self,
                "LoadBank Reactive Power",
                {
                    "Phase": result["phase"],
                    "Mode": result["mode"],
                    "ReactivePowerInput(var)": result["reactive_power_input"],
                    "Achieved(var)": result["achieved"],
                    "Difference(var)": result["difference"],
                    "Slave": result["slave_id"],
                    "StartAddress": result["start_address"],
                    "EnabledAddresses": json.dumps(result["enabled_addresses"]),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Set Reactive Power", exc)


@attribute(OpenTap.Display("LoadBank Select Voltage", "Select 120 V or 240 V on the load bank.", "Load Bank\\Commands"))
class LoadBankSelectVoltage(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )

    AvailableLevels = property(List[String], None).add_attribute(Browsable(False))
    VoltageLevel = property(String, "120").add_attribute(
        OpenTap.AvailableValues("AvailableLevels")
    ).add_attribute(
        OpenTap.Display("Voltage level", "120 or 240.", "Voltage", 1)
    )

    def __init__(self):
        super().__init__()
        self.AvailableLevels = _voltage_choices()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            level = int(str(self.VoltageLevel).strip())
            instrument.select_voltage_level(level)
            _publish_mapping(self, "LoadBank Voltage", {"SelectedVoltage": level})
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Select Voltage", exc)


@attribute(OpenTap.Display("LoadBank Set Power Switch", "Turn the main power switch ON/OFF.", "Load Bank\\Commands"))
class LoadBankSetPowerSwitch(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )
    PowerSwitchOn = property(Boolean, True).add_attribute(
        OpenTap.Display("Enabled", "True=ON, False=OFF.", "Switch", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.set_power_switch(bool(self.PowerSwitchOn))
            _publish_mapping(self, "LoadBank Power Switch", {"Enabled": bool(self.PowerSwitchOn)})
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Set Power Switch", exc)


@attribute(OpenTap.Display("LoadBank Set Load Switch", "Turn the load switch ON/OFF.", "Load Bank\\Commands"))
class LoadBankSetLoadSwitch(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )
    LoadSwitchOn = property(Boolean, True).add_attribute(
        OpenTap.Display("Enabled", "True=ON, False=OFF.", "Switch", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.set_load_switch(bool(self.LoadSwitchOn))
            _publish_mapping(self, "LoadBank Load Switch", {"Enabled": bool(self.LoadSwitchOn)})
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Set Load Switch", exc)


@attribute(OpenTap.Display("LoadBank Reset Loads", "Reset load relay groups.", "Load Bank\\Commands"))
class LoadBankResetLoads(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )
    ResetAllGroups = property(Boolean, False).add_attribute(
        OpenTap.Display("Reset all groups", "If true reset AR/AL/AC/BR/BL/BC/CR/CL/CC; else reset AR/BR/CR only.", "Reset", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            if bool(self.ResetAllGroups):
                instrument.reset_all_load_groups()
            else:
                instrument.reset_real_power_loads()
            _publish_mapping(self, "LoadBank Reset", {"ResetAllGroups": bool(self.ResetAllGroups)})
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Reset Loads", exc)


@attribute(OpenTap.Display("LoadBank Read Temperatures", "Read inlet/load-band temperatures and alarm setpoints.", "Load Bank\\Diagnostics"))
class LoadBankReadTemperatures(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            _publish_mapping(
                self,
                "LoadBank Temperatures",
                {
                    "AirOutletTemp(C)": instrument.read_air_outlet_temperature_c(),
                    "LoadbandTemp(C)": instrument.read_loadband_temperature_c(),
                    "AirOutletAlarm(C)": instrument.read_air_outlet_alarm_c(),
                    "LoadbandAlarm(C)": instrument.read_loadband_alarm_c(),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Read Temperatures", exc)


@attribute(OpenTap.Display("LoadBank Write Temperature Alarms", "Set temperature alarm thresholds.", "Load Bank\\Commands"))
class LoadBankWriteTemperatureAlarms(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )
    AirOutletAlarm = property(Double, 75.0).add_attribute(
        OpenTap.Display("Air outlet alarm", "Temperature alarm threshold.", "Alarms", 1)
    ).add_attribute(OpenTap.Unit("C"))
    LoadbandAlarm = property(Double, 75.0).add_attribute(
        OpenTap.Display("Loadband alarm", "Temperature alarm threshold.", "Alarms", 2)
    ).add_attribute(OpenTap.Unit("C"))

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.write_air_outlet_alarm_c(float(self.AirOutletAlarm))
            instrument.write_loadband_alarm_c(float(self.LoadbandAlarm))
            _publish_mapping(
                self,
                "LoadBank Temperature Alarms",
                {
                    "AirOutletAlarm(C)": float(self.AirOutletAlarm),
                    "LoadbandAlarm(C)": float(self.LoadbandAlarm),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Write Temperature Alarms", exc)


@attribute(OpenTap.Display("LoadBank Read Inductance Alarm", "Read X1 inductance alarm input.", "Load Bank\\Diagnostics"))
class LoadBankReadInductanceAlarm(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            alarm = bool(instrument.read_inductance_alarm())
            _publish_mapping(self, "LoadBank Inputs", {"X1_InductanceAlarm": alarm})
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Read Inductance Alarm", exc)


@attribute(OpenTap.Display("LoadBank Read Phase Measurements", "Read float measurements from slave 04/05/06.", "Load Bank\\Diagnostics"))
class LoadBankReadPhaseMeasurements(TestStep):
    Instrument = property(LoadBank, None).add_attribute(
        OpenTap.Display("loadBank", "loadBank instrument resource.", "Resources", 1)
    )

    AvailablePhases = property(List[String], None).add_attribute(Browsable(False))
    Phase = property(String, "A").add_attribute(
        OpenTap.AvailableValues("AvailablePhases")
    ).add_attribute(
        OpenTap.Display("Phase", "A, B, or C measurement block.", "Measurement", 1)
    )

    def __init__(self):
        super().__init__()
        self.AvailablePhases = _phase_choices()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            data = instrument.read_phase_measurements(str(self.Phase))
            _publish_mapping(self, "LoadBank Phase Measurements", data)
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "LoadBank Read Phase Measurements", exc)
