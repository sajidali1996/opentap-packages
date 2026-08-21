# Project Context for LLM Contributors

## 1) What this workspace is
This workspace is an OpenTAP installation Packages directory on Windows.

- Host root: c:/Program Files/OpenTAP/Packages
- It contains a mix of:
  - Official OpenTAP packages distributed as package.xml + binaries/resources.
  - Python plugin source folders used by OpenTAP Python discovery.

OpenTAP core and Python integration are already installed in this workspace:

- OpenTAP package: OpenTAP/package.xml (OpenTAP 9.34.0 build)
- Python package: Python/package.xml (OpenTap.Python 3.2.1 build)

## 2) High-level architecture
OpenTAP is the plugin runtime. Python plugins are loaded through OpenTap.Python and discovered from Python modules.

Important architecture points:

- OpenTAP plugin types include Instrument, DUT, Test Step, Result Listener, and CLI actions.
- Python classes become OpenTAP plugins via attributes such as OpenTap.Display and base classes from opentap.
- package.xml files in official packages declare dependencies, packaged files, and plugin metadata.
- Python source packages here (InverterAutomation, gridSimulator, PQA) are implementation modules used in the runtime environment.

## 3) Key folders and their role
- OpenTAP/: core engine binaries and package manifest.
- Python/: Python runtime bridge for OpenTAP (opentap.py + docs).
- PythonExamples/: reference examples for Python plugin authoring.
- SDK/: C# SDK, package schema, and sample projects/solutions.
- InverterAutomation/: custom inverter DUT + command/verification steps over WebSocket.
- gridSimulator/: custom serial instrument + control/diagnostic steps for Xinhua AC grid simulator.
- PQA/: custom instrument/steps for HIOKI PW3390 plus comparison and numeric utility steps.
- Other package folders (CSV, Editor, Expressions, Results Viewer, etc.) are installed OpenTAP packages.

## 4) Custom Python plugin packages

### 4.1 InverterAutomation
Files:
- InverterAutomation/inverter_dut.py
- InverterAutomation/inverter_steps.py
- InverterAutomation/common.py
- InverterAutomation/VERSION.txt (4.0.0)
- InverterAutomation/__init__.py

Purpose:
- Implements Inverter DUT over WebSocket.
- Exposes command steps, diagnostics, and verification steps.

Notable DUT behavior (inverter_dut.py):
- Connects using websockets.sync.client.connect.
- Maintains background receive thread and payload snapshots:
  - first_payload, second_payload, third_payload, latest_payload.
- Supports command APIs such as control_on/control_off, reset, mode switching, masking, key/value command send.
- Provides telemetry getters and state checks:
  - latest_payload_snapshot, payload_status, get_alerts/get_trips/get_hw_trips, check_state.
- Uses OpenTAP Rules for runtime validation (IP, port, timeouts).

Notable step behavior (inverter_steps.py):
- 20 discoverable TestStep classes, grouped under:
  - Inverter Automation/Commands
  - Inverter Automation/Diagnostics
  - Inverter Automation/Verification
- Steps are direct TestStep subclasses for editor discovery stability.
- Verification includes:
  - waiting for control_status true
  - payload key assertion with bool/number/string comparison logic.

Logging pattern (common.py):
- Uses OpenTap.Log.CreateSource and TraceEvent-compatible emission.
- Formats message text in Python before emitting.
- This avoids Python.NET overload binding pitfalls.

Dependencies:
- Third-party: websockets (sync client API)
- No local requirements.txt in this folder, so dependency management is external/manual.

### 4.2 gridSimulator
Files:
- gridSimulator/grid_simulator.py
- gridSimulator/grid_simulator_steps.py
- gridSimulator/requirements.txt (pyserial>=3.5)
- gridSimulator/__init__.py

Purpose:
- Instrument driver for Xinhua AC grid simulator over serial protocol.
- Command/diagnostic test steps around output regulation and measurement queries.

Instrument behavior (grid_simulator.py):
- Implements framed protocol with header, checksum, and terminator handling.
- Supports control/query/set command classes and protocol-level error handling.
- Provides APIs:
  - start_output, stop_output, stop_alarm
  - regulate_output, regulate_output_three_phase
  - query_instrument_state, query_environment_measurements, query_output_measurements
- Includes validation rules for port, baud, slave address, timeout, voltage range.

Step behavior (grid_simulator_steps.py):
- 8 discoverable steps:
  - start/stop output and alarm
  - single and three-phase output regulation
  - state/environment/output diagnostic reads
- Steps publish structured result tables with PublishResult.

Dependencies:
- Third-party: pyserial (declared in requirements.txt)

### 4.3 PQA
Files:
- PQA/pqa.py
- PQA/pw3390_transport.py
- PQA/steps.py
- PQA/compare_pqa_inverter.py
- PQA/numeric_assert.py
- PQA/store_numeric_value.py
- PQA/__init__.py

Purpose:
- Instrument support for HIOKI PW3390 over TCP.
- Measurement read step, inverter-vs-PQA comparison step, and generic numeric utility steps.

Instrument behavior (pqa.py + pw3390_transport.py):
- TCP transport with CRLF protocol handling and explicit protocol/connection exceptions.
- On open:
  - sends :HEADER OFF
  - reads *IDN?
  - optionally validates HIOKI/PW3390 identity
  - optionally key-locks front panel
- Measurement API:
  - ReadMeasurements(list of item names)
  - convenience getters for Urms/Irms/P/Q/S/PF/FREQ channel values.

Steps:
- ReadPqaMeasurements: captures common electrical values and publishes one result row.
- ComparePqaAndInverter:
  - pulls selected PQA item and inverter latest payload key
  - compares with configurable operator + tolerance
  - passes/fails verdict based on comparison.
- NumericAssert:
  - generic threshold assertion against any numeric Input output.
- StoreNumericValue:
  - stores manual value or previous-step numeric output for reuse.

Dependencies:
- Standard library only inside transport module.
- OpenTAP/OpenTap Python runtime required.

## 5) Discovery and inheritance constraints (important)
These constraints are explicitly documented in source and should be preserved:

- Do not import/re-export plugin classes in package __init__.py files.
  - Reason: OpenTAP Python scanning can register duplicate CLR-backed plugin types.
- For discoverable steps in InverterAutomation, inherit directly from TestStep.
  - Reason: intermediate Python helper base classes can cause OpenTAP editor discovery instability.

If adding new classes, follow existing patterns to avoid duplicate registration and missing steps in the editor.

## 6) Dependency summary
Detected Python dependencies in this workspace:

- Runtime/plugin dependencies:
  - pyserial>=3.5 (gridSimulator/requirements.txt)
  - websockets (used by InverterAutomation/inverter_dut.py)
- Example-only dependencies:
  - numpy, debugpy (PythonExamples/requirements.txt)

OpenTAP-level package dependencies are expressed through package.xml in official package folders.

## 7) Result and verdict conventions
Common conventions used across custom steps:

- PublishResult for structured tabular outputs (diagnostics, comparisons, stored values).
- UpgradeVerdict:
  - Pass for successful actions/assertions
  - Fail for failed validations/assertions
  - Error for exceptions or invalid runtime setup

This means downstream LLM changes should preserve:
- useful result tables for observability
- explicit verdict transitions in all execution branches

## 8) Inter-package integration points
- PQA/compare_pqa_inverter.py tries to import Inverter DUT type from InverterAutomation.
- If import fails, it falls back to OpenTap.Dut so step remains loadable.

This is an intentional resilience pattern for optional package presence.

## 9) Developer references in workspace
- Python integration doc stub: Python/Readme.md
- OpenTap Python bridge implementation: Python/opentap.py
- SDK schema and examples:
  - SDK/PackageSchema.xsd
  - SDK/Examples/Examples.sln and projects

These are useful when adding new plugin packages or validating package.xml content.

## 10) Practical guidance for future LLM edits
When extending this project:

1. Keep plugin-discovery-safe structure.
- Add discoverable plugin classes in concrete module files, not in __init__.py re-exports.

2. Preserve OpenTAP property metadata patterns.
- Continue using OpenTap.Display, OpenTap.Unit, OpenTap.Output, OpenTap.AvailableValues where applicable.

3. Keep communication layers separated.
- Transport/protocol logic in instrument or DUT class.
- Step classes should orchestrate calls, publish results, and set verdicts.

4. Keep failure paths explicit.
- Convert protocol/runtime failures into clear exceptions or logged step errors.
- Ensure every step resolves to an explicit verdict outcome.

5. Maintain backward-compatible step semantics.
- Existing step names and categories are likely used by saved test plans.
- Prefer additive changes; avoid renaming plugin classes/Display names unless required.

6. Preserve logging compatibility.
- Use the existing TraceSource-based helper pattern in InverterAutomation/common.py when editing inverter logging.

## 11) Known gaps and assumptions
- No dedicated automated Python test suite was found in this Packages workspace.
- InverterAutomation has no local requirements.txt despite websockets usage.
- Some folders in this workspace are packaged binaries/manifests, not editable source projects.

Treat this workspace primarily as an installed OpenTAP environment plus custom Python plugin sources.
