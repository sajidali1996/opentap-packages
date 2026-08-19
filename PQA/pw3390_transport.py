"""Dependency-free TCP transport and response parsing for the HIOKI PW3390."""

from __future__ import annotations

import math
import socket
import threading
from typing import Dict, Iterable, List, Optional


class PW3390Error(RuntimeError):
    """Base error raised by the PW3390 driver."""


class PW3390ConnectionError(PW3390Error):
    """Connection or socket I/O error."""


class PW3390ProtocolError(PW3390Error):
    """Malformed or unexpected instrument response."""


def parse_numeric(token: str) -> float:
    """Parse a PW3390 numeric token, including its documented over-range value."""
    value = token.strip()
    if " " in value:
        value = value.rsplit(" ", 1)[-1]
    if value.upper().replace(" ", "") in {"+9999.9E+99", "9999.9E+99"}:
        return math.nan
    try:
        return float(value)
    except ValueError as exc:
        raise PW3390ProtocolError("Invalid numeric response: {!r}".format(token)) from exc


def parse_measurement_response(response: str, items: Iterable[str]) -> Dict[str, float]:
    """Map a header-off ``:MEAS?`` response to the requested item names."""
    names = [str(item).strip() for item in items]
    values = [part.strip() for part in response.strip().split(",")]
    if len(values) != len(names):
        raise PW3390ProtocolError(
            "Expected {} measurement values, received {}: {!r}".format(
                len(names), len(values), response
            )
        )
    return {name: parse_numeric(value) for name, value in zip(names, values)}


class PW3390TcpTransport:
    """Line-oriented TCP client for the PW3390 (CR+LF terminated messages)."""

    def __init__(self, host: str, port: int = 3390, timeout_seconds: float = 5.0):
        self.host = host
        self.port = int(port)
        self.timeout_seconds = float(timeout_seconds)
        self._socket: Optional[socket.socket] = None
        self._receive_buffer = bytearray()
        self._lock = threading.RLock()

    @property
    def connected(self) -> bool:
        return self._socket is not None

    def connect(self) -> None:
        with self._lock:
            self.close()
            try:
                self._socket = socket.create_connection(
                    (self.host, self.port), timeout=self.timeout_seconds
                )
                self._socket.settimeout(self.timeout_seconds)
            except OSError as exc:
                self._socket = None
                raise PW3390ConnectionError(
                    "Could not connect to PW3390 at {}:{}: {}".format(
                        self.host, self.port, exc
                    )
                ) from exc

    def close(self) -> None:
        with self._lock:
            sock, self._socket = self._socket, None
            self._receive_buffer.clear()
            if sock is not None:
                try:
                    sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                sock.close()

    def command(self, command: str) -> None:
        self._send(command)

    def query(self, command: str) -> str:
        with self._lock:
            self._send(command)
            return self._readline()

    def _send(self, command: str) -> None:
        with self._lock:
            if self._socket is None:
                raise PW3390ConnectionError("PW3390 is not connected")
            message = command.strip().encode("ascii") + b"\r\n"
            try:
                self._socket.sendall(message)
            except OSError as exc:
                raise PW3390ConnectionError("PW3390 send failed: {}".format(exc)) from exc

    def _readline(self) -> str:
        terminator = b"\r\n"
        while True:
            position = self._receive_buffer.find(terminator)
            if position >= 0:
                line = bytes(self._receive_buffer[:position])
                del self._receive_buffer[: position + len(terminator)]
                try:
                    return line.decode("ascii").strip()
                except UnicodeDecodeError as exc:
                    raise PW3390ProtocolError("Response was not ASCII") from exc
            if self._socket is None:
                raise PW3390ConnectionError("PW3390 is not connected")
            try:
                chunk = self._socket.recv(4096)
            except socket.timeout as exc:
                raise PW3390ConnectionError("Timed out waiting for PW3390 response") from exc
            except OSError as exc:
                raise PW3390ConnectionError("PW3390 receive failed: {}".format(exc)) from exc
            if not chunk:
                raise PW3390ConnectionError("PW3390 closed the connection")
            self._receive_buffer.extend(chunk)

