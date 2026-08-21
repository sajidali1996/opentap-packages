Inverter Automation OpenTAP Technical Audit and Gap Analysis
Date: 2026-08-21

1. Executive summary
- The project is at a medium maturity level for editor-only authoring.
- All four target plugin areas exist and load in OpenTAP editor: InverterAutomation, PQA, loadBank, gridSimulator.
- Core command and measurement coverage is present, but advanced reusable workflow capabilities are incomplete.
- Main limiting factor: many device steps publish tabular results but do not expose strongly typed OpenTap output properties for downstream chaining.
- Main strategic need: a shared generic step library for calculations, waits, retries, robust cleanup, and richer assertions.

2. Repository and package architecture
OpenTAP and package versions (confirmed):
- OpenTAP 9.34.0+f498d3b6 from OpenTAP/package.xml
- Python 3.2.1+135d85ed from Python/package.xml
- Expressions 1.7.1+e0dbf00d from Expressions/package.xml
- CSV 9.14.2+44a9bac5 from CSV/package.xml
- CLI verification command executed: tap.exe package list --installed

Plugin boundaries and implementation language:
- Python plugins:
  - InverterAutomation/inverter_dut.py and InverterAutomation/inverter_steps.py
  - PQA/pqa.py, PQA/steps.py, PQA/compare_pqa_inverter.py, PQA/numeric_assert.py, PQA/store_numeric_value.py
  - loadBank/load_bank.py and loadBank/load_bank_steps.py
  - gridSimulator/grid_simulator.py and gridSimulator/grid_simulator_steps.py

Resource types:
- DUT:
  - InverterAutomation/inverter_dut.py - class Inverter
- Instruments:
  - PQA/pqa.py - class PQA
  - loadBank/load_bank.py - class LoadBank
  - gridSimulator/grid_simulator.py - class GridSimulator

Communication layers and protocols:
- Inverter DUT: WebSocket sync client
  - InverterAutomation/inverter_dut.py - Inverter.Open, Inverter._receive_loop, Inverter._send_command
- PQA: TCP socket protocol
  - PQA/pw3390_transport.py - PW3390TcpTransport
- loadBank: Modbus RTU serial via pymodbus
  - loadBank/load_bank.py - LoadBank._request and Modbus read/write wrappers
- gridSimulator: custom serial frame protocol with checksum
  - gridSimulator/grid_simulator.py - GridSimulator._build_frame, _read_frame, _parse_frame

Result listeners and reporting foundations:
- CSV listener installed from CSV/package.xml
- OpenTAP text log listener installed from OpenTAP/package.xml

Configuration storage:
- Confirmed in runtime OpenTAP settings (bench instruments and DUT settings persisted by editor), not as source files in this repository.

How values and verdicts propagate:
- PQA has explicit output properties in several steps.
- InverterAutomation, loadBank, and gridSimulator primarily use PublishResult tables.
- Verdict model across custom steps: Pass on success, Error on exceptions, with Fail used in explicit assertion/verification steps.

Timeouts, cleanup, and recovery:
- Inverter has configurable connection and payload timeouts and safety control_off on close.
- PQA transport has socket timeout behavior and explicit protocol exceptions.
- loadBank and gridSimulator have connection and protocol exceptions.
- No shared generic retry/health/reconnect orchestration step package found.

3. Plugin by plugin step inventory

3.1 InverterAutomation
Steps discovered:
- Control On
- Control Off
- Inverter Reset
- Clear DSP Sensor Error
- Battery Relay Open
- Battery Wakeup
- Battery Shutdown
- Default Mode
- Set Load Following Mode
- send Inverter command
- apply masking
- Read Connection Status
- Read Payload Status
- Read Latest Payload
- Read Alerts
- Read Trips
- Read Hardware Trips
- Check State
- Verify Control On
- Verify Payload Key

Evidence:
- InverterAutomation/inverter_steps.py - classes SendControlOn through VerifyPayloadKey

Assessment:
- Connect/disconnect: partial (resource lifecycle in DUT, no dedicated connect/disconnect step)
- On/off and command execution: supported
- Fault read/reset: partial to supported depending on command availability
- Wait for condition: partial (Verify Control On only)
- Output reuse: limited (mostly PublishResult, no typed outputs)

3.2 PQA
Steps discovered:
- Read PQA Measurements
- Compare PQA and Inverter
- Numeric Assert
- Store Numeric Value

Evidence:
- PQA/steps.py - ReadPqaMeasurements
- PQA/compare_pqa_inverter.py - ComparePqaAndInverter
- PQA/numeric_assert.py - NumericAssert
- PQA/store_numeric_value.py - StoreNumericValue

Assessment:
- Core fundamental measurement read: supported
- Channel selection: supported
- Multiple measurements per operation: supported
- Generic numeric assert and value storage: supported (numeric scope)
- Start/stop recording, waveform/transient capture, harmonics/energy workflows: not evidenced in current custom steps
- Output reuse: good compared to other plugins due explicit OpenTap outputs

3.3 loadBank
Steps discovered:
- LoadBank Set Real Power
- LoadBank Set Reactive Power
- LoadBank Select Voltage
- LoadBank Set Power Switch
- LoadBank Set Load Switch
- LoadBank Reset Loads
- LoadBank Read Temperatures
- LoadBank Write Temperature Alarms
- LoadBank Read Inductance Alarm
- LoadBank Read Phase Measurements

Evidence:
- loadBank/load_bank_steps.py - classes LoadBankSetRealPower through LoadBankReadPhaseMeasurements

Assessment:
- Active and reactive load control: supported
- Phase specific loading: supported
- 120V to 101V conversion included: supported
  - loadBank/load_bank.py - LoadBank.convert_real_power_command
  - Formula applied: RealPower_command = round((120^2/101^2) * RealPower_input)
- Ramp/step profile orchestration as reusable editor primitives: missing
- Commanded vs achieved verification as a dedicated assert step: partial
- Output reuse: limited (results are mostly published tables)

3.4 gridSimulator
Steps discovered:
- GridSim Start Output
- GridSim Stop Output
- GridSim Stop Alarm
- GridSim Set Output
- GridSim Set Output 3-Phase
- GridSim Read State
- GridSim Read Environment
- GridSim Read Output

Evidence:
- gridSimulator/grid_simulator_steps.py - classes GridSimStartOutput through GridSimReadOutput

Assessment:
- Set and read key electrical conditions: supported
- Balanced and unbalanced static configuration: supported
- Disturbance profile generation (dips, swells, interruptions, freq events): not evidenced as dedicated reusable steps
- Output reuse: limited (mostly table publishing)

4. Editor-only capability matrix
Fully supported:
- Resource configuration in editor
- Basic command sequencing
- Delay, repeat, basic branching via built-in OpenTAP flow control
- CSV result export

Partially supported:
- Generic calculations and expressions (Expressions package present, but no project-level generic calculator step)
- Generic assertions beyond numeric compare
- Data driven operation (CSV sweep available, richer data loop policy tooling absent)
- Robust setup/teardown guarantees for all failure modes
- Unattended recovery from transient communication failures

Not supported or not evidenced:
- Generic wait-until-stable with hold duration
- Built-in percent-error and range assert primitives in project package
- Time-aligned synchronized multi-instrument sampling utility
- Dedicated grid disturbance profile step family

Unable to verify in static audit:
- Hardware timing fidelity, synchronization accuracy, and long-duration reliability under bench load

5. Representative scenario assessment
Scenario A Basic voltage validation: currently possible.
- Typical step chain:
  - InverterAutomation Control On
  - OpenTAP Delay
  - PQA Read PQA Measurements
  - PQA Numeric Assert

Scenario B Power measurement accuracy: partially possible.
- Core actions possible.
- Missing convenience for percentage error and consolidated KPI publishing.

Scenario C Load-step response: partially possible with significant manual composition.
- Missing reusable response-time, overshoot, and settling-time primitives.

Scenario D Grid disturbance: partially possible.
- Static setpoint controls exist.
- Dedicated disturbance profile and trip/recovery timing workflow missing.

Scenario E Data-driven regression: partially possible.
- CSV Sweep exists.
- Failure policy handling and consolidated reporting workflow need improvement.

6. Detailed gap analysis
High impact gaps:
- Inconsistent use of OpenTap outputs across plugins
- Missing shared generic step library for wait, calculate, retry, range and percent asserts
- Missing reusable safe teardown and emergency shutdown orchestration
- Missing dynamic event and response-metric step family
- Custom plugin packaging/versioning discipline is weak (custom source folders without package.xml)

Reliability and maintainability gaps:
- Repeated helper code patterns across plugin step files
- Limited explicit cancellation handling in custom loops
- Limited communication recovery strategy at workflow level

7. Recommended additional reusable steps
Priority recommendations:
- Generic Value Assert
- Numeric Range Assert
- Percentage Error Assert
- Calculate Expression
- Wait Until
- Wait Until Stable
- Retry Wrapper
- Communication Health Check
- Guaranteed Teardown
- Emergency Shutdown
- Time-aligned Multi-Measurement Snapshot
- Response-time and Settling-time metric steps

Suggested target:
- New shared package (for example AutomationCoreSteps) for generic workflows
- Keep device-specific transport and command APIs in existing plugin packages

8. Architecture and package organization recommendations
- Keep drivers in instrument/DUT classes:
  - InverterAutomation/inverter_dut.py
  - PQA/pqa.py
  - loadBank/load_bank.py
  - gridSimulator/grid_simulator.py
- Keep device-specific operation steps in each package.
- Move reusable workflow primitives to one shared package.
- Standardize:
  - timeout behavior
  - retry policy hooks
  - cancellation handling
  - output property conventions
  - error and verdict semantics
- Add package metadata/versioning for custom plugins to improve deployment consistency.

9. Prioritized implementation roadmap
Phase 1 Critical foundation
- Add custom package manifests and version discipline for custom plugins.
- Create shared generic step package skeleton.
- Implement guaranteed teardown and emergency shutdown.
- Standardize timeout and cancellation behavior in custom loops.

Phase 2 Generic editor capabilities
- Add generic calculate, range assert, percent-error assert, wait-until, wait-until-stable, retry.
- Add communication health check and reconnect primitives.

Phase 3 Instrument and DUT completeness
- Add missing typed outputs to key inverter/load/grid steps.
- Add load achieved verification utilities.
- Add grid disturbance profile and timing-oriented inverter validation helpers.

Phase 4 Reporting and regression usability
- Standardize KPI and result naming conventions.
- Build regression templates for data-driven suites.
- Add operator-facing playbooks and examples.

Phase 5 Advanced automation
- Add synchronized multi-instrument capture.
- Add response, overshoot, settling, and recovery metric primitives.
- Harden unattended endurance execution with robust recovery policies.

10. Risks and technical debt
- Advanced regression can become fragile without generic retries and guaranteed teardown.
- Typed output inconsistency can force users into ad hoc custom code.
- Dynamic test characterization remains backend-heavy without timing and disturbance primitives.
- Deployment consistency risk from source-only custom plugin folders without package manifests.

11. Quick wins
- Add OpenTap output properties to high-value read steps in loadBank and gridSimulator.
- Add percent-error and range assert generic steps.
- Add generic wait-until step with timeout and polling controls.
- Add retry wrapper around communication-sensitive child steps.

12. Questions requiring hardware or stakeholder confirmation
- Required timing precision and synchronization tolerance for dynamic tests.
- Disturbance profile requirements for grid compliance scenarios.
- Preferred regression failure policy (stop first fail vs continue with quarantine).
- Reporting format requirements beyond CSV and text logs.

Final decision answers
1) Closeness to editor-only authoring:
- Medium.

2) Five most important gaps:
- Shared generic workflow step library is missing.
- Typed output coverage is uneven.
- Dynamic timing and disturbance primitives are missing.
- Recovery and cancellation strategy is not unified.
- Custom plugin packaging/versioning is incomplete.

3) Minimum additions for largest immediate benefit:
- Generic calculate, wait, percent/range assert, retry, and guaranteed teardown.
- Expand typed outputs for existing high-value device steps.

4) Steps to redesign or consolidate:
- Consolidate duplicate helper patterns.
- Redesign key read/control steps to expose reusable typed outputs.

5) Realistic support for daily and regression validation without routine backend changes:
- Yes for many daily tests now.
- Full coverage requires the reusable additions above.

6) What to implement first:
- Phase 1 foundation: shared package, guaranteed teardown and emergency safety, then Phase 2 generic authoring primitives.

Commands and checks executed during audit
- tap.exe package list --installed
- VS Code diagnostics over InverterAutomation, PQA, gridSimulator, loadBank
- Static source inspection of all plugin classes and step implementations
- Search for package metadata, docs, and test plan files

Checks that could not be performed
- Hardware-in-the-loop validation of timing behavior and long-duration reliability
- Bench-specific protocol edge conditions and load/grid disturbance fidelity
