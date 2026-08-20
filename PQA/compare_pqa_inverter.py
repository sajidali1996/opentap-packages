from enum import Enum

from System import Double, String
from System.Collections.Generic import List
from System.ComponentModel import Browsable
import OpenTap
from opentap import TestStep, attribute, property

from .pqa import PQA

try:
    from InverterAutomation.inverter_dut import Inverter as InverterDutType
except Exception:
    InverterDutType = OpenTap.Dut


class PqaInverterComparisonOperator(Enum):
    GreaterThan = (">", "PQA value must be greater than inverter value.")
    GreaterOrEqual = (">=", "PQA value must be greater than or equal to inverter value.")
    LessThan = ("<", "PQA value must be less than inverter value.")
    LessOrEqual = ("<=", "PQA value must be less than or equal to inverter value.")
    Equal = ("==", "PQA value must equal inverter value within tolerance.")
    NotEqual = ("!=", "PQA value must differ from inverter value by more than tolerance.")

    def __str__(self):
        return self.value[0]

    def describe(self):
        return self.value[1]


_INVERTER_PAYLOAD_KEYS = [
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


_PQA_MEASUREMENTS = [
    "Urms1", "Irms1", "P1", "Q1", "S1", "PF1", "FREQ1",
    "Urms2", "Irms2", "P2", "Q2", "S2", "PF2", "FREQ2",
    "Urms3", "Irms3", "P3", "Q3", "S3", "PF3", "FREQ3",
    "Urms4", "Irms4", "P4", "Q4", "S4", "PF4", "FREQ4",
]


def _build_choices(values):
    choices = List[String]()
    for value in values:
        choices.Add(value)
    return choices


def _compare_numeric(pqa_value, inverter_value, operator, tolerance):
    if operator == PqaInverterComparisonOperator.GreaterThan:
        return pqa_value > inverter_value
    if operator == PqaInverterComparisonOperator.GreaterOrEqual:
        return pqa_value >= inverter_value
    if operator == PqaInverterComparisonOperator.LessThan:
        return pqa_value < inverter_value
    if operator == PqaInverterComparisonOperator.LessOrEqual:
        return pqa_value <= inverter_value
    if operator == PqaInverterComparisonOperator.Equal:
        return abs(pqa_value - inverter_value) <= tolerance
    if operator == PqaInverterComparisonOperator.NotEqual:
        return abs(pqa_value - inverter_value) > tolerance
    raise ValueError("Unsupported comparison operator")


@attribute(
    OpenTap.Display(
        "Compare PQA and Inverter",
        "Compare a selected PQA measurement with a selected latest inverter payload key.",
        "PQA"
    )
)
class ComparePqaAndInverter(TestStep):

    Instrument = property(PQA, None).add_attribute(
        OpenTap.Display("PQA", "PQA instrument resource.", "Resources")
    )

    Inverter = property(InverterDutType, None).add_attribute(
        OpenTap.Display("Inverter DUT", "DUT that provides latest_payload_snapshot().", "Resources")
    )

    AvailableInverterKeys = property(List[String], None).add_attribute(Browsable(False))
    InverterKey = property(String, "vgrid1Rms").add_attribute(
        OpenTap.AvailableValues("AvailableInverterKeys")
    ).add_attribute(
        OpenTap.Display("Inverter key", "Latest payload key to compare.", "Comparison", 1)
    )

    AvailablePqaMeasurements = property(List[String], None).add_attribute(Browsable(False))
    PqaMeasurement = property(String, "Urms1").add_attribute(
        OpenTap.AvailableValues("AvailablePqaMeasurements")
    ).add_attribute(
        OpenTap.Display("PQA measurement", "PW3390 measurement item to compare.", "Comparison", 2)
    )

    Operator = property(
        PqaInverterComparisonOperator,
        PqaInverterComparisonOperator.Equal,
    ).add_attribute(
        OpenTap.Display("Operator", "Comparison operator.", "Comparison", 3)
    )

    Tolerance = property(Double, 0.001).add_attribute(
        OpenTap.Display(
            "Tolerance",
            "Used for == and != comparisons.",
            "Comparison",
            4,
        )
    )

    InverterValue = property(Double, 0.0).add_attribute(
        OpenTap.Display("Inverter value", "Numeric value from selected inverter key.", "Outputs")
    ).add_attribute(OpenTap.Output())

    PqaValue = property(Double, 0.0).add_attribute(
        OpenTap.Display("PQA value", "Numeric value from selected PQA measurement.", "Outputs")
    ).add_attribute(OpenTap.Output())

    def __init__(self):
        super().__init__()
        self.AvailableInverterKeys = _build_choices(_INVERTER_PAYLOAD_KEYS)
        self.AvailablePqaMeasurements = _build_choices(_PQA_MEASUREMENTS)

    def Run(self):
        if self.Instrument is None:
            raise RuntimeError("Select a PQA instrument")
        if self.Inverter is None:
            raise RuntimeError("Select an Inverter DUT")

        payload_reader = getattr(self.Inverter, "latest_payload_snapshot", None)
        if not callable(payload_reader):
            raise RuntimeError("Selected DUT does not support latest_payload_snapshot()")

        payload = payload_reader()
        if not payload:
            raise RuntimeError("No inverter payload is available yet")

        key = str(self.InverterKey)
        if key not in payload:
            raise RuntimeError("Payload key '{0}' was not found".format(key))

        try:
            self.InverterValue = float(payload[key])
        except Exception:
            raise RuntimeError(
                "Payload key '{0}' value is not numeric: {1}".format(key, str(payload[key]))
            )

        measurement = str(self.PqaMeasurement).strip()
        if not measurement:
            raise RuntimeError("Select a PQA measurement")

        pqa_data = self.Instrument.ReadMeasurements([measurement])
        self.PqaValue = float(pqa_data[measurement])

        tolerance = abs(float(self.Tolerance))
        passed = _compare_numeric(self.PqaValue, self.InverterValue, self.Operator, tolerance)

        self.PublishResult(
            "PQA vs Inverter",
            ["PQA Measurement", "PQA Value", "Inverter Key", "Inverter Value", "Operator", "Tolerance", "Passed"],
            [measurement, self.PqaValue, key, self.InverterValue, str(self.Operator), tolerance, passed],
        )

        self.log.Info(
            "Compare: PQA {0}={1} {2} Inverter[{3}]={4}, tolerance={5}, result={6}",
            measurement,
            self.PqaValue,
            str(self.Operator),
            key,
            self.InverterValue,
            tolerance,
            "PASS" if passed else "FAIL",
        )

        if passed:
            self.UpgradeVerdict(OpenTap.Verdict.Pass)
        else:
            self.UpgradeVerdict(OpenTap.Verdict.Fail)