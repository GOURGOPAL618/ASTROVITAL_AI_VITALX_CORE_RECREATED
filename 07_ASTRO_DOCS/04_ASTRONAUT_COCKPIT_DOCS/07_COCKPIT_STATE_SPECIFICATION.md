# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 04: ASTRONAUT COCKPIT — COCKPIT STATE SPECIFICATION
### THREAD-SAFE TELEMETRY RING BUFFER (120 FRAMES), CREW PROFILES & SCENARIOS

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-COCKPIT-STATE-07
 SUBSYSTEM LOCATION: 04_ASTRONAUT_COCKPIT/01_components/cockpit_state.py
 MIRROR TEST SUITE: 04_ASTRONAUT_COCKPIT/test_cockpit_state.py
 CERTIFICATION STANDARD: RTCA DO-178C LEVEL C (DAL C) / NASA-STD-3001
 BUFFER ARCHITECTURE: Thread-Safe Circular FIFO Ring Buffer (Capacity 120 Frames)
 CREW PROFILES: 4 Astronaut Baseline Biometrics (Armstrong, Aldrin, Collins, Chawla)
 PRESET SCENARIOS: 6 Certified Operational Clinical Spaceflight Scenarios
 CODE METRICS: 135 Statements | 0 Uncovered | 100.0% Statement Coverage
 TEST METRICS: 14 Unit Tests | 14 PASSED (100% Pass Rate)
 EXECUTION LATENCY: 1.12 seconds
 AUTHOR & LEAD ARCHITECT: TEAM VITALX CORE
 DATE OF RATIFICATION: NOVEMBER 15, 2026
================================================================================
```

---

## 1. Functional Purpose & Data Architecture

The `cockpit_state.py` module maintains the runtime state of the flight deck display, providing:
1. **Thread-Safe Telemetry Ring Buffer (`TelemetryRingBuffer`):** Circular FIFO memory maintaining the most recent $N=120$ seconds of telemetry without heap fragmentation.
2. **Standard Crew Baseline Profiles (`CREW_PROFILES`):** Calibrated resting baselines for:
   - `CDR Neil Armstrong` (Commander, Base HR 65, SBP 118, DBP 76, Non-CMO)
   - `PLT Buzz Aldrin` (Pilot, Base HR 70, SBP 122, DBP 78, Non-CMO)
   - `CMO Michael Collins` (Crew Medical Officer, Base HR 62, SBP 115, DBP 74, **Authorized CMO**)
   - `FE Kalpana Chawla` (Flight Engineer, Base HR 68, SBP 116, DBP 75, Non-CMO)
3. **6 Certified Spaceflight Scenarios (`FLIGHT_SCENARIO_PRESETS`):**
   - Scenario 1: `Nominal Cruise (Day 5)` — Stable green baselines.
   - Scenario 2: `Acute EVA Hypoxia` — Extreme drop in $SpO_2$ to $78\%$, triggering `RULE-02 RED`.
   - Scenario 3: `Cephalad Surge (Day 60)` — Headward fluid shift, $I_{\text{ICP}}=1.42$, triggering `RULE-06 AMBER`.
   - Scenario 4: `Hypertensive Crisis` — $SBP=210, DBP=125$, triggering `RULE-04 RED`.
   - Scenario 5: `Early Fluid Shift (Day 25)` — Moderate $I_{\text{ICP}}=1.36$, triggering `RULE-06 AMBER`.
   - Scenario 6: `Extreme Fatigue & Sleep Debt` — Autonomic suppression, triggering `RULE-08 AMBER`.

---

## 2. Requirements Traceability Matrix

| Requirement ID | Verification Scope | Implementation Function | Test Mapping | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-STATE-01** | Crew Baseline Profiles & Integrity Constraints | `CREW_PROFILES` | `test_01` | **PASS (100%)** |
| **REQ-STATE-02** | Flight Scenario Presets Integrity Verification | `FLIGHT_SCENARIO_PRESETS` | `test_02` | **PASS (100%)** |
| **REQ-STATE-03** | Circular Ring Buffer Allocation, Overflow & DataFrame Export | `TelemetryRingBuffer` | `test_03` to `test_06` | **PASS (100%)** |
| **REQ-STATE-04** | Cockpit State Manager Initialization & Crew Selection | `CockpitStateManager` | `test_07`, `test_08` | **PASS (100%)** |
| **REQ-STATE-05** | Canonical Spaceflight Scenario Injection & Simulation Steps | `inject_scenario()`, `step_simulation()` | `test_09`, `test_10` | **PASS (100%)** |
| **REQ-STATE-06** | Checklist Toggle & CMO Override Permission Enforcement | `toggle_checklist_item()`, `apply_cmo_override()` | `test_11` to `test_14` | **PASS (100%)** |

---

## 3. DO-178C Level C Statement Coverage

```text
=============================== tests coverage ================================
Name                                                     Stmts   Miss  Cover
----------------------------------------------------------------------------
04_ASTRONAUT_COCKPIT\01_components\cockpit_state.py        135      0   100%
----------------------------------------------------------------------------
TOTAL                                                      135      0   100%
============================= 14 passed in 1.12s ==============================
```
100.0% statement coverage achieved across all 135 executable statements.
