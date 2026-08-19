"""OpenTAP Instrument implementation for a HIOKI PW3390 Power Analyzer."""

from __future__ import annotations

from System import Boolean, Int32, String
import OpenTap
from opentap import Instrument, attribute, property

from .pw3390_transport import PW3390ProtocolError, PW3390TcpTransport, parse_measurement_response


@attribute(
    OpenTap.Display(
        "PQA",
        "HIOKI PW3390 power quality/power analyzer over its LAN command interface.",
        "Instruments",
    )
)
class PQA(Instrument):
    IpAddress = property(String, "192.168.1.100").add_attribute(
        OpenTap.Display("IP Address", "LAN address configured on the PW3390.", "Connection")
    )
    Port = property(Int32, 3390).add_attribute(
        OpenTap.Display("TCP Port", "PW3390 command port (fixed at 3390).", "Connection")
    )
    TimeoutMs = property(Int32, 5000).add_attribute(
        OpenTap.Display("Timeout", "Socket read/connect timeout in milliseconds.", "Connection")
    ).add_attribute(OpenTap.Unit("ms"))
    VerifyIdentity = property(Boolean, True).add_attribute(
        OpenTap.Display("Verify Identity", "Require *IDN? to identify a HIOKI PW3390.", "Connection")
    )
    LockFrontPanel = property(Boolean, False).add_attribute(
        OpenTap.Display("Lock Front Panel", "Enable key lock while the test plan is running.", "Connection")
    )

    def __init__(self):
        super(PQA, self).__init__()
        self.Name = "PQA"
        self._transport = None
        self._identity = ""

    def Open(self):
        super(PQA, self).Open()
        self._transport = PW3390TcpTransport(
            str(self.IpAddress), int(self.Port), float(self.TimeoutMs) / 1000.0
        )
        try:
            self._transport.connect()
            # Force header-off responses so measurement parsing is deterministic.
            self._transport.command(":HEADER OFF")
            self._identity = self._transport.query("*IDN?")
            if self.VerifyIdentity:
                identity_upper = self._identity.upper()
                if "HIOKI" not in identity_upper or "PW3390" not in identity_upper:
                    raise PW3390ProtocolError(
                        "Unexpected instrument identity: {!r}".format(self._identity)
                    )
            if self.LockFrontPanel:
                self._transport.command(":KEYLOCK ON")
            self.log.Info("Connected to {0}", self._identity)
        except Exception:
            if self._transport is not None:
                self._transport.close()
            self._transport = None
            raise

    def Close(self):
        try:
            if self._transport is not None:
                if self.LockFrontPanel:
                    try:
                        self._transport.command(":KEYLOCK OFF")
                    except Exception as exc:
                        self.log.Warning("Could not unlock PW3390 front panel: {0}", str(exc))
                self._transport.close()
        finally:
            self._transport = None
            super(PQA, self).Close()

    def _require_transport(self):
        if self._transport is None or not self._transport.connected:
            raise RuntimeError("PQA is not open")
        return self._transport

    def Write(self, command):
        """Send a command that does not return data."""
        self._require_transport().command(str(command))

    def Query(self, query):
        """Send a query and return its raw header-off response."""
        return self._require_transport().query(str(query))

    def ReadMeasurements(self, items):
        """Read 1..64 PW3390 fundamental measurement item parameters."""
        names = [str(item).strip() for item in items]
        if not names or len(names) > 64 or any(not name for name in names):
            raise ValueError("ReadMeasurements requires 1 to 64 non-empty item names")
        response = self.Query(":MEASURE? " + ",".join(names))
        return parse_measurement_response(response, names)

    def _read_one(self, item):
        return self.ReadMeasurements([item])[item]

    def GetIdentity(self):
        """Return the identity captured when the instrument was opened."""
        return self._identity

    def GetVoltageRms(self, channel):
        return self._read_one("Urms{}".format(self._validate_channel(channel)))

    def GetCurrentRms(self, channel):
        return self._read_one("Irms{}".format(self._validate_channel(channel)))

    def GetActivePower(self, channel):
        return self._read_one("P{}".format(self._validate_channel(channel)))

    def GetReactivePower(self, channel):
        return self._read_one("Q{}".format(self._validate_channel(channel)))

    def GetApparentPower(self, channel):
        return self._read_one("S{}".format(self._validate_channel(channel)))

    def GetPowerFactor(self, channel):
        return self._read_one("PF{}".format(self._validate_channel(channel)))

    def GetFrequency(self, channel):
        return self._read_one("FREQ{}".format(self._validate_channel(channel)))

    @staticmethod
    def _validate_channel(channel):
        value = int(channel)
        if value < 1 or value > 4:
            raise ValueError("PW3390 channel must be 1, 2, 3, or 4")
        return value
