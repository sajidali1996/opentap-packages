"""Inverter Automation OpenTAP plugin package.

OpenTAP discovers the classes directly from ``inverter_dut.py`` and
``inverter_steps.py``. Do not re-export them here because the Python plugin
would register each .NET-backed type twice.
"""
