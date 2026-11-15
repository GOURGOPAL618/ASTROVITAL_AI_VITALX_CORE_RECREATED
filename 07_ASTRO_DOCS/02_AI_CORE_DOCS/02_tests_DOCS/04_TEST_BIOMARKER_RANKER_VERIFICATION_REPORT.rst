.. _test_biomarker_ranker_verification_report:

================================================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
================================================================================
SUBSYSTEM 02: AI CORE — UNIT TEST VERIFICATION REPORT
TEST SUITE: test_biomarker_ranker.py (44 Tests Passed · 100% Coverage)
================================================================================

.. note::
   **REPORT IDENTIFIER:** ASTROVITAL-TEST-REP-04 : BIOMARKER RANKER TEST VERIFICATION
   **SUBSYSTEM LOCATION:** 02_AI_CORE/02_tests/test_biomarker_ranker.py
   **CERTIFICATION STANDARD:** DO-178C DESIGN ASSURANCE LEVEL C (DAL C)
   **TARGET MODULE:** 02_AI_CORE/01_src/inno6_biomarker_ranker.py (321 Statements)
   **TEST RESULTS:** 44 / 44 PASSED (100.0% Pass Rate) | 100% Statement Coverage
   **AUDITOR & LEAD ARCHITECT:** Team VITALX CORE
   **DATE OF CERTIFICATION:** November 14, 2026

--------------------------------------------------------------------------------
1. Executive Summary & Verification Methodology
--------------------------------------------------------------------------------

This report documents the verification of ``inno6_biomarker_ranker.py`` across
4 analytical sensitivity stages:

* **Stage 1: Mission Context Matrix (Tests 01–12):** Mapping 8 spaceflight operational phases to calibrated Dirichlet priors, phase string aliases, defensive exceptions.
* **Stage 2: Physiological Deviation Scorer (Tests 13–24):** Non-parametric MAD scaling, sigmoidal saturation, zero-MAD edge handling, non-finite values.
* **Stage 3: Information Entropy Engine (Tests 25–32):** Shannon entropy, information divergence, short temporal horizons (:math:`M < 3`), flatline detection.
* **Stage 4: Composite Sensitivity Ranker & Exporter (Tests 33–44):** Convex sensitivity fusion, Dirichlet simplex bounds (:math:`\sum w_i = 1.0`), frozen contract export.
