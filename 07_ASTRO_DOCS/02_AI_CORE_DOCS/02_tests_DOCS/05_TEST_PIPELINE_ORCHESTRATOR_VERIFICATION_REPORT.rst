.. _test_pipeline_orchestrator_verification_report:

================================================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
================================================================================
SUBSYSTEM 02: AI CORE — UNIT TEST VERIFICATION REPORT
TEST SUITE: test_pipeline_orchestrator.py (23 Tests Passed · 100% Coverage)
================================================================================

.. note::
   **REPORT IDENTIFIER:** ASTROVITAL-TEST-REP-05 : PIPELINE ORCHESTRATOR TEST VERIFICATION
   **SUBSYSTEM LOCATION:** 02_AI_CORE/02_tests/test_pipeline_orchestrator.py
   **CERTIFICATION STANDARD:** DO-178C DESIGN ASSURANCE LEVEL C (DAL C)
   **TARGET MODULE:** 02_AI_CORE/01_src/pipeline_orchestrator.py (138 Statements)
   **TEST RESULTS:** 23 / 23 PASSED (100.0% Pass Rate) | 100% Statement Coverage
   **AUDITOR & LEAD ARCHITECT:** Commander Gouragopal Mohapatra (GOURGOPAL618)
   **DATE OF CERTIFICATION:** November 14, 2026

--------------------------------------------------------------------------------
1. Executive Summary & Verification Methodology
--------------------------------------------------------------------------------

This report documents the verification of ``pipeline_orchestrator.py`` across
5 operational orchestration stages:

* **Stage 1: Initialization & Dependency Validation (Tests 01–02):** Sub-component injection, rule hash checks, defensive exceptions.
* **Stage 2: Telemetry Frame Ingestion & Denoising (Tests 03–08):** Dict/Series/DataFrame intake, stabilizer execution, skip bypass mode.
* **Stage 3: Sanity Gate, Sensitivity & Triage Evaluation (Tests 09–14):** Boundary clamping, sensitivity ranking, triage state escalation across 12 canonical rules.
* **Stage 4: Cockpit Payload & Stream Processing (Tests 15–17):** HUD payload dispatch, locker routing, multi-row DataFrame stream processing.
* **Stage 5: CMO Override & System Health Metrics (Tests 18–23):** CMO override assertion, release, rolling telemetry health counters, FIFO audit history.
