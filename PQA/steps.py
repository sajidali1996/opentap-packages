"""Example OpenTAP step that publishes a PW3390 channel measurement row."""

from System import Double, Int32
import OpenTap
from opentap import TestStep, attribute, property

from .pqa import PQA


@attribute(
    OpenTap.Display(
        "Read PQA Measurements",
        "Read and publish RMS voltage/current, P, Q, S, PF, and frequency.",
        "PQA",
    )
)
class ReadPqaMeasurements(TestStep):
    Instrument = property(PQA, None).add_attribute(
        OpenTap.Display("PQA", "PQA instrument resource.", "Resources")
    )
    Channel = property(Int32, 1).add_attribute(
        OpenTap.Display("Channel", "PW3390 input channel (1 to 4).", "Measurement")
    )
    VoltageRms = property(Double, 0.0).add_attribute(
        OpenTap.Display("Voltage RMS", "Measured RMS voltage.", "Outputs")
    ).add_attribute(OpenTap.Unit("V")).add_attribute(OpenTap.Output())
    CurrentRms = property(Double, 0.0).add_attribute(
        OpenTap.Display("Current RMS", "Measured RMS current.", "Outputs")
    ).add_attribute(OpenTap.Unit("A")).add_attribute(OpenTap.Output())
    ActivePower = property(Double, 0.0).add_attribute(
        OpenTap.Display("Active Power", "Measured active power.", "Outputs")
    ).add_attribute(OpenTap.Unit("W")).add_attribute(OpenTap.Output())
    ReactivePower = property(Double, 0.0).add_attribute(
        OpenTap.Display("Reactive Power", "Measured reactive power.", "Outputs")
    ).add_attribute(OpenTap.Unit("var")).add_attribute(OpenTap.Output())
    ApparentPower = property(Double, 0.0).add_attribute(
        OpenTap.Display("Apparent Power", "Measured apparent power.", "Outputs")
    ).add_attribute(OpenTap.Unit("VA")).add_attribute(OpenTap.Output())
    PowerFactor = property(Double, 0.0).add_attribute(
        OpenTap.Display("Power Factor", "Measured power factor.", "Outputs")
    ).add_attribute(OpenTap.Output())
    Frequency = property(Double, 0.0).add_attribute(
        OpenTap.Display("Frequency", "Measured input frequency.", "Outputs")
    ).add_attribute(OpenTap.Unit("Hz")).add_attribute(OpenTap.Output())

    def __init__(self):
        super(ReadPqaMeasurements, self).__init__()

    def Run(self):
        if self.Instrument is None:
            raise RuntimeError("Select a PQA instrument")
        channel = self.Instrument._validate_channel(self.Channel)
        names = [
            "Urms{}".format(channel), "Irms{}".format(channel),
            "P{}".format(channel), "Q{}".format(channel),
            "S{}".format(channel), "PF{}".format(channel),
            "FREQ{}".format(channel),
        ]
        data = self.Instrument.ReadMeasurements(names)
        self.VoltageRms = data[names[0]]
        self.CurrentRms = data[names[1]]
        self.ActivePower = data[names[2]]
        self.ReactivePower = data[names[3]]
        self.ApparentPower = data[names[4]]
        self.PowerFactor = data[names[5]]
        self.Frequency = data[names[6]]
        self.PublishResult(
            "PQA Channel {}".format(channel),
            ["Voltage RMS", "Current RMS", "Active Power", "Reactive Power",
             "Apparent Power", "Power Factor", "Frequency"],
            [self.VoltageRms, self.CurrentRms, self.ActivePower,
             self.ReactivePower, self.ApparentPower, self.PowerFactor,
             self.Frequency],
        )
        self.UpgradeVerdict(OpenTap.Verdict.Pass)
