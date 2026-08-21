# Step-by-Step Modification Plan

## Scope
- This is the authoritative reference plan for all modifications.
- Progress, decisions, and verification status are logged in ModificationLog.md.
- Objective: reach a safe, testable, backwards-compatible, editor-first workflow.

## Step statuses
- [x] Step 1: Baseline lock and compatibility contract
- [x] Step 2: Fix signed 24-bit power decoding in grid simulator
- [x] Step 3: Correct inverter Check State semantics
- [ ] Step 4: Implement safe de-energizing close behavior
- [ ] Step 5: Separate command sent from state achieved verification
- [ ] Step 6: Add cancellation-aware waits and polling
- [ ] Step 7: Add typed outputs across inverter/load/grid steps
- [ ] Step 8: Correct load-bank achieved-power semantics and verification
- [ ] Step 9: Standardize reuse of installed OpenTAP flow-control features
- [ ] Step 10: Add only missing generic primitives
- [ ] Step 11: Package and dependency hardening
- [ ] Step 12: Automated tests and release gates

## Step 1 details (completed)

### Purpose
- Freeze editor-facing compatibility surface before functional changes.
- Ensure existing plans continue to load and run without rename breakage.

### Locked compatibility contract
- Locked resource type baseline: quality/step_surface_lock.json
- Locked step surface baseline: quality/step_surface_lock.json
- Validation script: quality/Validate-StepSurface.ps1

### Step 1 acceptance criteria
- Resource class names and display names are captured and validated.
- Editor-visible TestStep class names, display names, and group paths are captured and validated.
- A script returns non-zero on compatibility drift.

## Mandatory change gate for every next step

### Before coding
1. Update this plan status only when a step starts.
2. Add a new log entry in ModificationLog.md with target step and intended changes.

### After coding
1. Run compatibility lock validation:
   - powershell -NoProfile -ExecutionPolicy Bypass -File quality/Validate-StepSurface.ps1
2. Run static checks on changed files.
3. Run focused behavioral tests for changed steps and resources.
4. Record exact commands and outcomes in ModificationLog.md.
5. Only move to next step if all required checks pass or a blocker is explicitly logged.

## Backwards compatibility policy
- Existing class names and existing editor display names are preserved unless an explicit migration is approved.
- New safer behavior is introduced behind additive settings where needed.
- No removal of legacy behavior until migration criteria are met and logged.

## Planned step-by-step sequence

### Step 2
- Change: gridSimulator/grid_simulator.py - GridSimulator._decode_signed_24 protocol sign-bit + magnitude fix (hardware validated).
- Verification: deterministic decoder vectors and regression checks.

### Step 3
- Change: InverterAutomation/inverter_dut.py - Inverter.check_state must evaluate fresh payload state, not stale cached fields.
- Verification: payload-driven truth table for Normal/Fault/NoData.

### Step 4
- Change: safe close behavior in loadBank and gridSimulator resource Close flows.
- Verification: fail/cancel path de-energization tests.

### Step 5
- Change: additive command-and-verify steps; keep current command steps for compatibility.
- Verification: pass only after achieved-state confirmation.

### Step 6
- Change: cancellation checks in custom polling loops.
- Verification: abort responsiveness and cleanup integrity.

### Step 7
- Change: typed OpenTap outputs for key inverter/load/grid readback steps.
- Verification: output chaining in editor test plans.

### Step 8
- Change: clarify nominal vs measured achieved load semantics and add tolerance-based verification.
- Verification: mismatch and tolerance scenarios.

### Step 9
- Change: reuse installed Delay/Repeat/If/Sweep/CSV features before custom duplication.
- Verification: scenario templates using built-ins plus minimal custom logic.

### Step 10
- Change: add only missing shared primitives (range, percent error, wait until, stable wait, health/reconnect, event marker).
- Verification: unit and plan-level smoke tests.

### Step 11
- Change: package metadata and deployable dependency strategy.
- Verification: fresh machine install and discovery tests.

### Step 12
- Change: automated tests and release gates.
- Verification: CI-style pass criteria and failure blocking.
