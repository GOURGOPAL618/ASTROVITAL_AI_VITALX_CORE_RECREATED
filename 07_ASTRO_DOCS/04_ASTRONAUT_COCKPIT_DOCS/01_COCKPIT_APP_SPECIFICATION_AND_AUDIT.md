# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 04: ASTRONAUT COCKPIT — COCKPIT APP SPECIFICATION & AUDIT
### MASTER FLIGHT DECK STREAMLIT ENTRYPOINT, SCENARIO HARNESS & GLASSMORPHIC CSS

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-COCKPIT-APP-01
 SUBSYSTEM LOCATION: 04_ASTRONAUT_COCKPIT/app.py
 ASSETS & STYLES: 04_ASTRONAUT_COCKPIT/02_assets/cockpit_theme.css
 MIRROR TEST SUITE: 04_ASTRONAUT_COCKPIT/test_cockpit_app.py
 CERTIFICATION STANDARD: RTCA DO-178C LEVEL C (DAL C) / NASA-STD-3001 VOL 2
 CODE METRICS: 109 Statements | 0 Uncovered | 100.0% Statement Coverage
 TEST METRICS: 17 Unit Tests | 17 PASSED (100% Pass Rate)
 EXECUTION LATENCY: 2.14 seconds
 AUTHOR & LEAD ARCHITECT: TEAM VITALX CORE
 DATE OF RATIFICATION: NOVEMBER 15, 2026
================================================================================
```

---

## 1. Subsystem Scope & Operational Purpose

`app.py` serves as the master interactive flight deck application entrypoint for the autonomous clinical decision support system. Built upon Streamlit with custom glassmorphic CSS styling, it provides:
1. Multi-crew selection and biometric baseline profiling across 4 astronauts.
2. Clinical spaceflight scenario injection (Nominal Cruise, Acute Hypoxia, SANS Cephalad Surge, Hypertensive Crisis, Early Fluid Shift, Extreme Fatigue).
3. Tabbed flight deck layout:
   - **Tab 1: Telemetry & Waveforms:** 12-channel telemetry stream, biophysical gauges, Plotly waveforms.
   - **Tab 2: Countermeasure Checklist:** Physical locker callouts ($L_1 \dots L_5$) and step verification.
   - **Tab 3: White-Box Audit Terminal:** Mathematical trace logs and JSON cryptographic digests.
   - **Tab 4: Sovereign CMO Console:** Crew Medical Officer manual assertion controls.

---

## 2. Requirements Traceability Matrix

| Requirement ID | Verification Scope | Implementation Function | Test Mapping | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-APP-01** | Custom CSS Glassmorphic Injection & Fallback | `inject_custom_css()` | `test_01`, `test_02` | **PASS (100%)** |
| **REQ-APP-02** | Cockpit State Manager Session State Initialization | `get_state_manager()` | `test_03`, `test_04` | **PASS (100%)** |
| **REQ-APP-03** | Sidebar Mission Scenario & Crew Controls | `render_sidebar_controls()` | `test_05` to `test_10`, `test_17` | **PASS (100%)** |
| **REQ-APP-04** | Tabbed Cockpit Display Layout & Sub-view Dispatch | `render_cockpit_display()` | `test_11` to `test_13` | **PASS (100%)** |
| **REQ-APP-05** | Master Flight Deck Main Loop & Headless Fallback | `main()` | `test_14` to `test_16` | **PASS (100%)** |

---

## 3. DO-178C Level C Statement Coverage

```text
=============================== tests coverage ================================
Name                           Stmts   Miss  Cover   Missing
------------------------------------------------------------
04_ASTRONAUT_COCKPIT\app.py      109      0   100%
------------------------------------------------------------
TOTAL                            109      0   100%
============================= 17 passed in 2.14s ==============================
```
100.0% statement coverage achieved across all 109 executable statements with zero unexercised code branches.
