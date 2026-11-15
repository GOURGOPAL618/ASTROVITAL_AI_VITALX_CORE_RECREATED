.. _decision_core_subsystem_verification_index:

================================================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
================================================================================
SUBSYSTEM 03: DECISION CORE — MASTER SUBSYSTEM VERIFICATION INDEX
================================================================================

.. note::
   **SPECIFICATION DESIGNATOR:** ASTROVITAL-INDEX-DECISION-00
   **SUBSYSTEM LOCATION:** 03_DECISION_CORE/
   **ARCHITECTURAL PILLAR:** The 80% Biophysical Supreme Head (Exclusive Clinical Authority)
   **CERTIFICATION STANDARD:** RTCA DO-178C LEVEL C (DAL C - Major Safety Impact)
   **PRODUCTION MODULES:** 4 Source Modules | 3 JSON Data Assets | 5 Test Suites
   **CODE METRICS:** 596 Executable Statements | 0 Uncovered | 100.0% Statement Coverage
   **TEST METRICS:** 137 Unit & E2E Integration Tests (100% Pass Rate in 3.34s)
   **AUTHOR & AIRWORTHINESS LEAD:** Commander Gouragopal Mohapatra (GOURGOPAL618)
   **DATE OF RATIFICATION:** November 14, 2026

--------------------------------------------------------------------------------
1. Executive Summary: The 80% Biophysical Supreme Head
--------------------------------------------------------------------------------

The ``03_DECISION_CORE`` subsystem serves as the **Supreme Clinical Decision Authority**
within ASTROVITAL. While the 20% Adaptive AI auxiliary layer (``02_AI_CORE``) denoises
and ranks incoming telemetry, **100% of clinical decisions, alert states, and
countermeasure deployments reside exclusively within 03_DECISION_CORE**.

This deterministic, white-box architecture eliminates the life-threatening risks of
black-box neural network hallucinations during deep space medical emergencies.

--------------------------------------------------------------------------------
2. Subsystem Module Ledger & Coverage Table
--------------------------------------------------------------------------------

+-------+---------------------------------------------+------------+--------------+--------------------+
| Mod # | Production Source Module                    | Statements | Tests Passed | Statement Coverage |
+=======+=============================================+============+==============+====================+
| 01    | ``rule_schema_validator.py``                | 219        | 41 / 41      | **100.0%**         |
+-------+---------------------------------------------+------------+--------------+--------------------+
| 02    | ``biophysical_physics_engine.py``           | 162        | 32 / 32      | **100.0%**         |
+-------+---------------------------------------------+------------+--------------+--------------------+
| 03    | ``triage_model_engine.py``                  | 122        | 30 / 30      | **100.0%**         |
+-------+---------------------------------------------+------------+--------------+--------------------+
| 04    | ``cockpit_countermeasure_dispatcher.py``    | 93         | 24 / 24      | **100.0%**         |
+-------+---------------------------------------------+------------+--------------+--------------------+
| E2E   | Multi-module Flight Scenarios               | --         | 10 / 10      | **100.0%**         |
+-------+---------------------------------------------+------------+--------------+--------------------+
| TOTAL | **ALL 4 DECISION CORE MODULES**             | **596**    | **137 / 137**| **100.0%**         |
+-------+---------------------------------------------+------------+--------------+--------------------+

--------------------------------------------------------------------------------
3. The 12 Canonical Clinical Triage Rules
--------------------------------------------------------------------------------

* **RED (Critical Emergency):**
  * ``RULE-01``: Acute Asystole / Hemodynamic Collapse (Locker L1, L2)
  * ``RULE-02``: Critical Hypoxemia / Depressurization (Locker L3)
  * ``RULE-03``: Severe Shock State (Cardiogenic/Hypovolemic) (Locker L2)
  * ``RULE-04``: Hypertensive Crisis / Acute SANS Surge (Locker L2)
  * ``RULE-05``: Extreme Core Hyperthermia / Space Fever (Locker L4)

* **AMBER (Compensatory Stress):**
  * ``RULE-06``: Cephalad Fluid Shift / Intracranial Congestion (Locker L5)
  * ``RULE-07``: Cardiovascular Deconditioning / Pre-Syncope (Locker L5)
  * ``RULE-08``: Compensatory Autonomic Tachycardia (Cabin)
  * ``RULE-09``: Moderate Bradycardia / Sinus Sparing (Locker L1)
  * ``RULE-10``: Metabolic Fuel Depletion / Hypoglycemia (Locker L2)
  * ``RULE-11``: Microvascular Hypoperfusion / Vasoconstriction (Locker L4)

* **GREEN (Nominal Equilibrium):**
  * ``RULE-12``: Nominal Autonomous Microgravity Adaptation (Silent)
