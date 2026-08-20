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

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.start_output()
            self.log.Info("Grid simulator output started")
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Start Output", exc)


@attribute(OpenTap.Display("GridSim Stop Output", "Send AC stop command.", "Grid Simulator\\Commands"))
class GridSimStopOutput(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.stop_output()
            self.log.Info("Grid simulator output stopped")
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Stop Output", exc)


@attribute(OpenTap.Display("GridSim Stop Alarm", "Send stop alarm command.", "Grid Simulator\\Commands"))
class GridSimStopAlarm(TestStep):
    Instrument = property(GridSimulator, None).add_attribute(
        OpenTap.Display("gridSimulator", "gridSimulator instrument resource.", "Resources", 1)
    )

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            instrument.stop_alarm()
            self.log.Info("Grid simulator alarm stop command sent")
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

    def __init__(self):
        super().__init__()

    def Run(self):
        super().Run()
        try:
            instrument = _require_instrument(self)
            data = instrument.query_output_measurements()
            _publish_mapping(self, "GridSim Output", data)
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        except Exception as exc:
            _set_error(self, "GridSim Read Output", exc)
