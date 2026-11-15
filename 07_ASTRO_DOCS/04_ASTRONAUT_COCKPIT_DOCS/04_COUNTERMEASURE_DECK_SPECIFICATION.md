# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 04: ASTRONAUT COCKPIT — COUNTERMEASURE DECK SPECIFICATION
### ORION MEDICAL LOCKER ROUTING (L1-L5), ACTIONABLE CHECKLISTS & EXECUTION TIMERS

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-COCKPIT-DECK-04
 SUBSYSTEM LOCATION: 04_ASTRONAUT_COCKPIT/01_components/countermeasure_deck.py
 MIRROR TEST SUITE: 04_ASTRONAUT_COCKPIT/test_countermeasure_deck.py
 CERTIFICATION STANDARD: RTCA DO-178C LEVEL C (DAL C) / NASA-STD-3001 VOL 2
 CODE METRICS: 133 Statements | 0 Uncovered | 100.0% Statement Coverage
 TEST METRICS: 10 Unit Tests | 10 PASSED (100% Pass Rate)
 EXECUTION LATENCY: 0.98 seconds
 AUTHOR & LEAD ARCHITECT: GOURGOPAL MOHAPATRA (TEAM VITALX CORE)
 DATE OF RATIFICATION: NOVEMBER 15, 2026
================================================================================
```

---

## 1. Functional Purpose & Clinical Directives

The `countermeasure_deck.py` component translates high-level clinical triage states into step-by-step executable medical procedures for astronauts. It features:
1. **Physical Equipment Locker Mapping:**
   - **$L_1$:** Resuscitation & Automated External Defibrillator (`MED-01`)
   - **$L_2$:** Pharmacopeia, IV Saline & Injectables (`PHARM-01`)
   - **$L_3$:** Emergency Oxygen Masks & Rebreathers (`ENV-01`)
   - **$L_4$:** Thermal Cold/Warm Packs & Wound Dressings (`PHYS-01`)
   - **$L_5$:** Chibis LBNP Suit, Anti-G Straining Garments (`DIAG-01`)
2. **Actionable Checklist Cards:** Step numbering, step title, explicit execution window in seconds (e.g. `[EXECUTE IN 30s]`), and completion checkmarks.
3. **Clinical Priority Badge:** Displays rule priority, clinical rationale, and expected physiological response.

---

## 2. Requirements Traceability Matrix

| Requirement ID | Verification Scope | Implementation Function | Test Mapping | Status |
| :--- | :--- | :--- | :--- | :---: |
| **REQ-DECK-01** | Physical Equipment Locker Metadata Integrity ($L_1 \dots L_5$) | `LOCKER_METADATA` | `test_01` | **PASS (100%)** |
| **REQ-DECK-02** | Default Emergency Checklist Generation across Severities | `get_default_checklist()` | `test_02` | **PASS (100%)** |
| **REQ-DECK-03** | Countermeasure Deck HTML Rendering (Nominal & Emergency) | `render_countermeasure_deck_html()` | `test_03` to `test_06` | **PASS (100%)** |
| **REQ-DECK-04** | Streamlit Component Rendering & Checklist Checkboxes | `render_countermeasure_deck()` | `test_07` to `test_10` | **PASS (100%)** |

---

## 3. DO-178C Level C Statement Coverage

```text
=============================== tests coverage ================================
Name                                                       Stmts   Miss  Cover
------------------------------------------------------------------------------
04_ASTRONAUT_COCKPIT\01_components\countermeasure_deck.py    133      0   100%
------------------------------------------------------------------------------
TOTAL                                                        133      0   100%
============================= 10 passed in 0.98s ==============================
```
100.0% statement coverage achieved across all 133 executable statements.
