# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 03: DECISION CORE — TRIAGE MODEL ENGINE SPECIFICATION
### DETERMINISTIC STATE MACHINE, INSTANT ESCALATION & DEBOUNCED DE-ESCALATION

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-DEC-TRI-03
 SUBSYSTEM LOCATION: 03_DECISION_CORE/triage_model_engine.py
 MIRROR TEST SUITE: 03_DECISION_CORE/test_triage_model_engine.py
 CERTIFICATION STANDARD: RTCA DO-178C LEVEL C (DAL C)
 CODE METRICS: 122 Statements | 0 Uncovered | 100.0% Statement Coverage
 TEST METRICS: 30 Unit Tests | 30 PASSED (100% Pass Rate)
 EXECUTION LATENCY: 0.74 seconds
 AUTHOR & LEAD: GOURGOPAL MOHAPATRA (TEAM VITALX CORE)
 DATE OF RATIFICATION: NOVEMBER 14, 2026
================================================================================
```

---

## 1. Architectural Scope & State Machine Directives

The `triage_model_engine.py` module evaluates the enriched physiological state vector against the 12 deterministic clinical triage rules in strict priority order ($P_1 \dots P_{12}$).

### 1.1 Mandatory Airworthiness Principles
1. **Instant Escalation:** Transition from $\text{GREEN} \to \text{AMBER}$ or $\text{AMBER} \to \text{RED}$ occurs with **zero latency** upon a single frame breach of any clinical threshold.
2. **Debounced De-escalation (Hysteresis):** To prevent clinical alert flapping and alarm fatigue, transition from $\text{RED}/\text{AMBER} \to \text{GREEN}$ requires **$N_{\text{debounce}} = 5$ consecutive frames** of completely nominal parameters.
3. **Sovereign CMO Manual Override:** The Crew Medical Officer (CMO) can assert an authenticated manual override (`RED`, `AMBER`, or clear) with logged clinical rationale.

```
       +-------------------------------------------------------------+
       |                 DETERMINISTIC STATE MACHINE                 |
       |                                                             |
       |             [ GREEN: Nominal Microgravity State ]           |
       |                       |              ^                      |
       |     Instant Breach    |              | 5-Frame Debounce     |
       |     (Rule 06 - 11)    v              | (All Rules Clear)    |
       |             [ AMBER: Physiologic Warning State ]            |
       |                       |              ^                      |
       |     Instant Breach    |              | 5-Frame Debounce     |
       |     (Rule 01 - 05)    v              | (All RED Clear)      |
       |             [ RED: Critical Emergency State ]               |
       |                                                             |
       |           * CMO Manual Override Can Force Any State *       |
       +-------------------------------------------------------------+
```

---

## 2. Requirements Traceability Matrix

| Requirement ID | Verification Scope | Test Mapping | Pass Rate | Status |
| :--- | :--- | :--- | :---: | :---: |
| **REQ-TRI-01** | Highest-Priority Rule Matching ($P_1 \dots P_{12}$) | `test_01` to `test_08` | 100% | **PASS** |
| **REQ-TRI-02** | Zero-Latency Instant Escalation ($\to \text{RED}/\text{AMBER}$) | `test_09` to `test_14` | 100% | **PASS** |
| **REQ-TRI-03** | 5-Frame Hysteresis Debounced De-escalation | `test_15` to `test_20` | 100% | **PASS** |
| **REQ-TRI-04** | Sovereign CMO Manual Override & Audit Logging | `test_21` to `test_26` | 100% | **PASS** |
| **REQ-TRI-05** | Fallback & Missing Value Defensive Containment | `test_27` to `test_30` | 100% | **PASS** |

---

## 3. Mathematical State Transition Logic

Let state at frame $k$ be $S_k \in \{\text{RED}, \text{AMBER}, \text{GREEN}\}$.
Let instantaneous evaluation of rules be $E_k = \min \{ \text{Priority}(R_i) \mid \text{Eval}(R_i, \mathbf{v}_k) == \text{True} \}$.

$$S_k = \begin{cases}
\text{CMO\_State}, & \text{if CMO Override Active} \\
\text{Severity}(E_k), & \text{if } \text{Severity}(E_k) \succ S_{k-1} \quad \text{(Instant Escalation)} \\
S_{k-1}, & \text{if } \text{Severity}(E_k) \prec S_{k-1} \land C_{\text{debounce}} < 5 \\
\text{Severity}(E_k), & \text{if } \text{Severity}(E_k) \prec S_{k-1} \land C_{\text{debounce}} \ge 5 \quad \text{(De-escalation)}
\end{cases}$$

---

## 4. DO-178C Level C Statement Coverage

```text
=============================== tests coverage ================================
Name                                           Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------
03_DECISION_CORE\triage_model_engine.py          122      0   100%
----------------------------------------------------------------------------
TOTAL                                            122      0   100%
============================= 30 passed in 0.74s ==============================
```
100.0% statement coverage achieved across all 122 executable statements.
