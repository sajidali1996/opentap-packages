"""Shared OpenTAP services for the inverter plugin."""

import OpenTap

_SOURCE_NAME = "Inverter Automation"
_SOURCE = OpenTap.Log.CreateSource(_SOURCE_NAME)


def _format_message(message, args):
	text = str(message)
	if not args:
		return text
	try:
		return text.format(*args)
	except Exception:
		# Never fail test execution due to logging format mismatches.
		return "{0} | args={1}".format(text, ", ".join(str(a) for a in args))


def _event_type(level_name):
	if level_name == "Error":
		return OpenTap.LogEventType.Error
	if level_name == "Warning":
		return OpenTap.LogEventType.Warning
	return OpenTap.LogEventType.Information


def _emit(level_name, text):
	trace_event = getattr(_SOURCE, "TraceEvent", None)
	if callable(trace_event):
		trace_event(_event_type(level_name), 0, text)
		return True

	method = getattr(_SOURCE, level_name, None)
	if callable(method):
		method(text)
		return True

	return False


def _log(method_name, fallback_name, message, *args):
	text = _format_message(message, args)
	if _emit(method_name, text):
		return
	_emit(fallback_name, text)


def log_info(message, *args):
	_log("Info", "Warning", message, *args)


def log_warning(message, *args):
	_log("Warning", "Error", message, *args)


def log_error(message, *args):
	_log("Error", "Warning", message, *args)
