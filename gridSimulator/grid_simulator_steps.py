"""OpenTAP command and diagnostics steps for gridSimulator instrument."""

import json

import OpenTap
from opentap import TestStep, attribute, property
from System import Boolean, Double, Int32

from .grid_simulator import GridSimulator


def _require_instrument(step):
    if step.Instrument is None:
        raise RuntimeError("Select a gridSimulator instrument in Step Settings")
    return step.Instrument


def _set_error(step, operation, exc):
    step.log.Error("{0} failed: {1}", operation, str(exc))
    step.UpgradeVerdict(OpenTap.Verdict.Error)


def _publish_mapping(step, table_name, mapping):
    columns = list(mapping.keys())
    values = [mapping[column] for column in columns]
    step.PublishResult(table_name, columns, values)


@attribute(OpenTap.Display("GridSim Start Output", "Send AC start command.", "Grid Simulator\\Commands"))
class GridSimStartOutput(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )
    AllowAlreadyRunning = property(Boolean, True).add_attribute(
        OpenTap.Display(
            "Allow already running",
            "Treat protocol state error code 4 as success when output is already ON.",
            "Behavior",
            1,
        )
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            started_now = instrument.start_output(bool(self.AllowAlreadyRunning))
            if started_now:
                self.log.Info("Grid simulator output started")
            else:
                self.log.Info("Grid simulator output was already running")
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            if "code=4" in str(exc):
                self.log.Warning(
                    "Start returned state error code 4. Check current output state/alarm state "
                    "with GridSim Read State, and use GridSim Stop Alarm if needed."
                )
            _set_error(self, "GridSim Start Output", exc)


@attribute(OpenTap.Display("GridSim Stop Output", "Send AC stop command.", "Grid Simulator\\Commands"))
class GridSimStopOutput(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )
    AllowAlreadyStopped = property(Boolean, True).add_attribute(
        OpenTap.Display(
            "Allow already stopped",
            "Treat protocol state error code 4 as success when output is already OFF.",
            "Behavior",
            1,
        )
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            stopped_now = instrument.stop_output(bool(self.AllowAlreadyStopped))
            if stopped_now:
                self.log.Info("Grid simulator output stopped")
            else:
                self.log.Info("Grid simulator output was already stopped")
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Stop Output", exc)


@attribute(OpenTap.Display("GridSim Stop Alarm", "Send stop alarm command.", "Grid Simulator\\Commands"))
class GridSimStopAlarm(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )
    AllowNoActiveAlarm = property(Boolean, True).add_attribute(
        OpenTap.Display(
            "Allow no active alarm",
            "Treat protocol state error code 4 as success when no alarm is active.",
            "Behavior",
            1,
        )
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            cleared_now = instrument.stop_alarm(bool(self.AllowNoActiveAlarm))
            if cleared_now:
                self.log.Info("Grid simulator alarm stop command sent")
            else:
                self.log.Info("No active alarm to clear")
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Stop Alarm", exc)


@attribute(
    OpenTap.Display(
        "GridSim Set Output",
        "Online regulation for all three phases with the same voltage/frequency/wave.",
        "Grid Simulator\\Commands",
    )
)
class GridSimSetOutput(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )
    Voltage = property(Double, 101.0).add_attribute(
        OpenTap.Display("Voltage", "Output voltage applied to all phases.", "Regulation", 1)
    ).add_attribute(OpenTap.Unit("V"))
    Frequency = property(Double, 50.0).add_attribute(
        OpenTap.Display("Frequency", "Output frequency applied to all phases.", "Regulation", 2)
    ).add_attribute(OpenTap.Unit("Hz"))
    WaveCode = property(Int32, 0).add_attribute(
        OpenTap.Display("Wave code", "0=sine, 1-10=stored wave groups.", "Regulation", 3)
    )
    StartIfNeeded = property(Boolean, True).add_attribute(
        OpenTap.Display("Start if needed", "Automatically start output if regulation returns state error code 4.", "Regulation", 4)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.regulate_output(
                float(self.Voltage),
                float(self.Frequency),
                int(self.WaveCode),
                bool(self.StartIfNeeded),
            )
            _publish_mapping(
                self,
                "GridSim Set Output",
                {
                    "Voltage(V)": float(self.Voltage),
                    "Frequency(Hz)": float(self.Frequency),
                    "WaveCode": int(self.WaveCode),
                    "StartIfNeeded": bool(self.StartIfNeeded),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Set Output", exc)


@attribute(
    OpenTap.Display(
        "GridSim Set Output 3-Phase",
        "Online regulation with independent per-phase voltage/frequency/wave.",
        "Grid Simulator\\Commands",
    )
)
class GridSimSetOutputThreePhase(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )

    UVoltage = property(Double, 101.0).add_attribute(OpenTap.Display("U voltage", "U phase voltage.", "U Phase", 1)).add_attribute(OpenTap.Unit("V"))
    UFrequency = property(Double, 50.0).add_attribute(OpenTap.Display("U frequency", "U phase frequency.", "U Phase", 2)).add_attribute(OpenTap.Unit("Hz"))
    UWaveCode = property(Int32, 0).add_attribute(OpenTap.Display("U wave code", "U phase wave code.", "U Phase", 3))

    VVoltage = property(Double, 101.0).add_attribute(OpenTap.Display("V voltage", "V phase voltage.", "V Phase", 1)).add_attribute(OpenTap.Unit("V"))
    VFrequency = property(Double, 50.0).add_attribute(OpenTap.Display("V frequency", "V phase frequency.", "V Phase", 2)).add_attribute(OpenTap.Unit("Hz"))
    VWaveCode = property(Int32, 0).add_attribute(OpenTap.Display("V wave code", "V phase wave code.", "V Phase", 3))

    WVoltage = property(Double, 101.0).add_attribute(OpenTap.Display("W voltage", "W phase voltage.", "W Phase", 1)).add_attribute(OpenTap.Unit("V"))
    WFrequency = property(Double, 50.0).add_attribute(OpenTap.Display("W frequency", "W phase frequency.", "W Phase", 2)).add_attribute(OpenTap.Unit("Hz"))
    WWaveCode = property(Int32, 0).add_attribute(OpenTap.Display("W wave code", "W phase wave code.", "W Phase", 3))

    StartIfNeeded = property(Boolean, True).add_attribute(
        OpenTap.Display("Start if needed", "Automatically start output if regulation returns state error code 4.", "Behavior", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.regulate_output_three_phase(
                (float(self.UVoltage), float(self.VVoltage), float(self.WVoltage)),
                (float(self.UFrequency), float(self.VFrequency), float(self.WFrequency)),
                (int(self.UWaveCode), int(self.VWaveCode), int(self.WWaveCode)),
                bool(self.StartIfNeeded),
            )

            payload = {
                "u": {"voltage": float(self.UVoltage), "frequency": float(self.UFrequency), "wave_code": int(self.UWaveCode)},
                "v": {"voltage": float(self.VVoltage), "frequency": float(self.VFrequency), "wave_code": int(self.VWaveCode)},
                "w": {"voltage": float(self.WVoltage), "frequency": float(self.WFrequency), "wave_code": int(self.WWaveCode)},
            }
            _publish_mapping(
                self,
                "GridSim Set Output 3-Phase",
                {
                    "StartIfNeeded": bool(self.StartIfNeeded),
                    "Payload": json.dumps(payload, sort_keys=True),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Set Output 3-Phase", exc)


@attribute(OpenTap.Display("GridSim Read State", "Query instrument state and alarm/status bytes.", "Grid Simulator\\Diagnostics"))
class GridSimReadState(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            state = instrument.query_instrument_state()
            _publish_mapping(
                self,
                "GridSim State",
                {
                    "StateCode": int(state["state_code"]),
                    "StateDataHex": bytes(state["state_data"]).hex().upper(),
                },
            )
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Read State", exc)


@attribute(OpenTap.Display("GridSim Read Environment", "Query input and temperature measurements.", "Grid Simulator\\Diagnostics"))
class GridSimReadEnvironment(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            data = instrument.query_environment_measurements()
            _publish_mapping(self, "GridSim Environment", data)
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Read Environment", exc)


@attribute(OpenTap.Display("GridSim Read Output", "Query output voltage/current/frequency/power measurements.", "Grid Simulator\\Diagnostics"))
class GridSimReadOutput(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )

    OutputMode = property(Int32, 0).add_attribute(
        OpenTap.Display("Output mode", "Raw output mode code returned by grid simulator.", "Outputs", 1)
    ).add_attribute(OpenTap.Output())

    UVoltage = property(Double, 0.0).add_attribute(
        OpenTap.Display("U voltage", "Measured U phase voltage.", "Outputs/U", 1)
    ).add_attribute(OpenTap.Unit("V")).add_attribute(OpenTap.Output())
    UCurrent = property(Double, 0.0).add_attribute(
        OpenTap.Display("U current", "Measured U phase current.", "Outputs/U", 2)
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())
    UFrequency = property(Double, 0.0).add_attribute(
        OpenTap.Display("U frequency", "Measured U phase frequency.", "Outputs/U", 3)
    ).add_attribute(OpenTap.Unit("Hz")).add_attribute(OpenTap.Output())
    UActivePower = property(Double, 0.0).add_attribute(
        OpenTap.Display("U active power", "Measured U phase active power.", "Outputs/U", 4)
    ).add_attribute(OpenTap.Unit("W")).add_attribute(OpenTap.Output())
    UApparentPower = property(Double, 0.0).add_attribute(
        OpenTap.Display("U apparent power", "Measured U phase apparent power.", "Outputs/U", 5)
    ).add_attribute(OpenTap.Unit("VA")).add_attribute(OpenTap.Output())
    UPowerFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("U power factor", "Measured U phase power factor.", "Outputs/U", 6)
    ).add_attribute(OpenTap.Output())
    UCrestFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("U crest factor", "Measured U phase crest factor.", "Outputs/U", 7)
    ).add_attribute(OpenTap.Output())
    UPeakCurrent = property(Double, 0.0).add_attribute(
        OpenTap.Display("U peak current", "Measured U phase peak current.", "Outputs/U", 8)
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())

    VVoltage = property(Double, 0.0).add_attribute(
        OpenTap.Display("V voltage", "Measured V phase voltage.", "Outputs/V", 1)
    ).add_attribute(OpenTap.Unit("V")).add_attribute(OpenTap.Output())
    VCurrent = property(Double, 0.0).add_attribute(
        OpenTap.Display("V current", "Measured V phase current.", "Outputs/V", 2)
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())
    VFrequency = property(Double, 0.0).add_attribute(
        OpenTap.Display("V frequency", "Measured V phase frequency.", "Outputs/V", 3)
    ).add_attribute(OpenTap.Unit("Hz")).add_attribute(OpenTap.Output())
    VActivePower = property(Double, 0.0).add_attribute(
        OpenTap.Display("V active power", "Measured V phase active power.", "Outputs/V", 4)
    ).add_attribute(OpenTap.Unit("W")).add_attribute(OpenTap.Output())
    VApparentPower = property(Double, 0.0).add_attribute(
        OpenTap.Display("V apparent power", "Measured V phase apparent power.", "Outputs/V", 5)
    ).add_attribute(OpenTap.Unit("VA")).add_attribute(OpenTap.Output())
    VPowerFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("V power factor", "Measured V phase power factor.", "Outputs/V", 6)
    ).add_attribute(OpenTap.Output())
    VCrestFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("V crest factor", "Measured V phase crest factor.", "Outputs/V", 7)
    ).add_attribute(OpenTap.Output())
    VPeakCurrent = property(Double, 0.0).add_attribute(
        OpenTap.Display("V peak current", "Measured V phase peak current.", "Outputs/V", 8)
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())

    WVoltage = property(Double, 0.0).add_attribute(
        OpenTap.Display("W voltage", "Measured W phase voltage.", "Outputs/W", 1)
    ).add_attribute(OpenTap.Unit("V")).add_attribute(OpenTap.Output())
    WCurrent = property(Double, 0.0).add_attribute(
        OpenTap.Display("W current", "Measured W phase current.", "Outputs/W", 2)
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())
    WFrequency = property(Double, 0.0).add_attribute(
        OpenTap.Display("W frequency", "Measured W phase frequency.", "Outputs/W", 3)
    ).add_attribute(OpenTap.Unit("Hz")).add_attribute(OpenTap.Output())
    WActivePower = property(Double, 0.0).add_attribute(
        OpenTap.Display("W active power", "Measured W phase active power.", "Outputs/W", 4)
    ).add_attribute(OpenTap.Unit("W")).add_attribute(OpenTap.Output())
    WApparentPower = property(Double, 0.0).add_attribute(
        OpenTap.Display("W apparent power", "Measured W phase apparent power.", "Outputs/W", 5)
    ).add_attribute(OpenTap.Unit("VA")).add_attribute(OpenTap.Output())
    WPowerFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("W power factor", "Measured W phase power factor.", "Outputs/W", 6)
    ).add_attribute(OpenTap.Output())
    WCrestFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("W crest factor", "Measured W phase crest factor.", "Outputs/W", 7)
    ).add_attribute(OpenTap.Output())
    WPeakCurrent = property(Double, 0.0).add_attribute(
        OpenTap.Display("W peak current", "Measured W phase peak current.", "Outputs/W", 8)
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            data = instrument.query_output_measurements()

            self.OutputMode = int(data["output_mode"])

            self.UVoltage = float(data["phase_u_voltage_v"])
            self.UCurrent = float(data["phase_u_current_a"])
            self.UFrequency = float(data["phase_u_frequency_hz"])
            self.UActivePower = float(data["phase_u_active_power_w"])
            self.UApparentPower = float(data["phase_u_apparent_power_va"])
            self.UPowerFactor = float(data["phase_u_power_factor"])
            self.UCrestFactor = float(data["phase_u_crest_factor"])
            self.UPeakCurrent = float(data["phase_u_peak_current_a"])

            self.VVoltage = float(data["phase_v_voltage_v"])
            self.VCurrent = float(data["phase_v_current_a"])
            self.VFrequency = float(data["phase_v_frequency_hz"])
            self.VActivePower = float(data["phase_v_active_power_w"])
            self.VApparentPower = float(data["phase_v_apparent_power_va"])
            self.VPowerFactor = float(data["phase_v_power_factor"])
            self.VCrestFactor = float(data["phase_v_crest_factor"])
            self.VPeakCurrent = float(data["phase_v_peak_current_a"])

            self.WVoltage = float(data["phase_w_voltage_v"])
            self.WCurrent = float(data["phase_w_current_a"])
            self.WFrequency = float(data["phase_w_frequency_hz"])
            self.WActivePower = float(data["phase_w_active_power_w"])
            self.WApparentPower = float(data["phase_w_apparent_power_va"])
            self.WPowerFactor = float(data["phase_w_power_factor"])
            self.WCrestFactor = float(data["phase_w_crest_factor"])
            self.WPeakCurrent = float(data["phase_w_peak_current_a"])

            _publish_mapping(self, "GridSim Output", data)
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Read Output", exc)
