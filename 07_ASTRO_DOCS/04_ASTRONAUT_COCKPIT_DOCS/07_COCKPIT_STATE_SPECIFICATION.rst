.. _cockpit_state_specification:

================================================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
================================================================================
SUBSYSTEM 04: ASTRONAUT COCKPIT — COMPONENT SPECIFICATION
MODULE: cockpit_state.py (Circular FIFO Ring Buffer & Crew Profiles)
================================================================================

.. note::
   **MODULE IDENTIFIER:** ASTROVITAL-COCKPIT-COMP-07 : COCKPIT STATE MANAGER
   **SUBSYSTEM LOCATION:** 04_ASTRONAUT_COCKPIT/01_components/cockpit_state.py
   **CERTIFICATION STANDARD:** DO-178C LEVEL C / NASA-STD-3001
   **TRACEABLE REQUIREMENTS:** LLR-COCKPIT-007 (HLR-BIO-003)
   **VERIFICATION STATUS:** 100% STATEMENT COVERAGE (135/135 STATEMENTS) | 14/14 TESTS PASS
   **AUDITOR & LEAD ARCHITECT:** Commander Gouragopal Mohapatra (GOURGOPAL618)
   **DATE OF CERTIFICATION:** November 15, 2026

--------------------------------------------------------------------------------
1. Component Purpose & State Management Architecture
--------------------------------------------------------------------------------

``cockpit_state.py`` encapsulates the live runtime memory and state containers
of the cockpit application:

1. **Thread-Safe FIFO Ring Buffer:** Bounded 120-frame circular telemetry buffer preventing unbounded memory growth.
2. **Astronaut Baseline Profiles:** Stores individual resting baselines for 4 crew members (CDR, PLT, MS1, MS2).
3. **Flight Scenario Generators:** Houses calibrated deterministic telemetry profiles for 6 emergency scenarios.
4. **Debounce & Escalation Memory:** Tracks consecutive frame counts to govern state machine transitions.
