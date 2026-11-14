# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 03: DECISION CORE — BIOPHYSICAL PHYSICS ENGINE SPECIFICATION
### CLOSED-FORM HEMODYNAMICS, INNOVATION 1 CEPHALAD FLUID SHIFTS & CARDIAC REMODELING

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-DEC-BIO-02
 SUBSYSTEM LOCATION: 03_DECISION_CORE/biophysical_physics_engine.py
 MIRROR TEST SUITE: 03_DECISION_CORE/test_biophysical_physics_engine.py
 CERTIFICATION STANDARD: RTCA DO-178C LEVEL C (DAL C)
 CODE METRICS: 162 Statements | 0 Uncovered | 100.0% Statement Coverage
 TEST METRICS: 32 Unit Tests | 32 PASSED (100% Pass Rate)
 EXECUTION LATENCY: 0.82 seconds
 AUTHOR & LEAD: GOURGOPAL MOHAPATRA (TEAM VITALX CORE)
 DATE OF RATIFICATION: NOVEMBER 14, 2026
================================================================================
```

---

## 1. Subsystem Scope & Theoretical Context

The `biophysical_physics_engine.py` module forms the mathematical foundation of ASTROVITAL's **80% Biophysical Supreme Head**. Operating on sanitized 12-dimensional telemetry frames, it derives fundamental, unmeasured hemodynamic and neuro-ocular risk indices using established physical conservation laws and validated aerospace medicine equations.

---

## 2. Mathematical Formulations & Derivations

### 2.1 Closed-Form Hemodynamic Equations
1. **Pulse Pressure ($\text{PP}$):**
   $$\text{PP}(t) = \text{SBP}(t) - \text{DBP}(t) \quad [\text{mmHg}]$$
2. **Mean Arterial Pressure ($\text{MAP}$):**
   $$\text{MAP}(t) = \text{DBP}(t) + \frac{1}{3} \cdot \text{PP}(t) \quad [\text{mmHg}]$$
3. **Allgöwer Shock Index ($\text{SI}$):**
   $$\text{SI}(t) = \frac{\text{HR}(t)}{\text{SBP}(t)} \quad [\text{bpm/mmHg}]$$
   *Clinical Envelope:* Normal: $[0.5, 0.7]$; Mild Shock: $[0.7, 0.9]$; Severe Shock: $> 1.0$.
4. **Modified Shock Index ($\text{MSI}$):**
   $$\text{MSI}(t) = \frac{\text{HR}(t)}{\text{MAP}(t)} \quad [\text{bpm/mmHg}]$$
5. **Cerebral Perfusion Pressure ($\text{CPP}$):**
   $$\text{CPP}(t) = \text{MAP}(t) - \text{ICP}(t) \quad [\text{mmHg}]$$

---

### 2.2 Innovation 1: Cephalad Fluid Shift Hydrodynamic Gradient ($I_{\text{ICP}}$)
In microgravity ($0G$), loss of hydrostatic gradient redistributes $\sim 1.5 - 2.0\text{ L}$ of interstitial fluid from lower extremities into the cephalad and jugular compartments. The headward fluid shift index $I_{\text{ICP}}(t)$ is derived as:

$$I_{\text{ICP}}(t) = w_1 \cdot \frac{\text{MAP}(t)}{\text{MAP}_{\text{baseline}}} + w_2 \cdot \frac{\text{PP}(t)}{\text{PP}_{\text{baseline}}} + w_3 \cdot \left( 1 - \exp\left( -\frac{t_{\text{mission}}}{\tau_{\text{fluid}}} \right) \right)$$

where $w_1 = 0.40, w_2 = 0.35, w_3 = 0.25$, and $\tau_{\text{fluid}} = 43.2\text{ hours}$.

Estimated Intracranial Pressure ($\widehat{\text{ICP}}$) is then calculated as:
$$\widehat{\text{ICP}}(t) = \text{ICP}_{\text{baseline}} + \Delta \text{ICP}_{\max} \cdot \left( \frac{I_{\text{ICP}}(t) - 1.0}{I_{\text{ICP, max}} - 1.0} \right)$$
*SANS Trigger Boundary:* When $\widehat{\text{ICP}}(t) \ge 20.0\text{ mmHg}$, the system alerts `AMBER RULE-06` (Cephalad Fluid Shift / Intracranial Congestion).

---

### 2.3 Innovation 1: Left Ventricular Stroke Volume Decay ($SV$)
Due to cardiovascular unloading and plasma volume contraction during spaceflight:

$$SV(t) = SV_0 \cdot \left[ 1.0 - \delta_{\max} \cdot \left( 1.0 - \exp\left( -\frac{t_{\text{days}}}{\tau_{\text{cardiac}}} \right) \right) \right] \cdot \left( \frac{\text{PP}(t)}{\text{PP}_{\text{baseline}}} \right)^{\beta}$$

where $\delta_{\max} = 0.15$ ($15\%$ max cardiac volume atrophy), $\tau_{\text{cardiac}} = 14.0\text{ days}$, and $\beta = 0.50$.

---

## 3. Requirements Traceability Matrix

| Requirement ID | Verification Scope | Test Mapping | Pass Rate | Status |
| :--- | :--- | :--- | :---: | :---: |
| **REQ-BIO-01** | Accurate Closed-Form Hemodynamics ($\text{PP}, \text{MAP}, \text{SI}, \text{MSI}$) | `test_01` to `test_08` | 100% | **PASS** |
| **REQ-BIO-02** | Cephalad Fluid Shift Hydrodynamic Model | `test_09` to `test_16` | 100% | **PASS** |
| **REQ-BIO-03** | Myocardial Stroke Volume Decay Dynamics | `test_17` to `test_22` | 100% | **PASS** |
| **REQ-BIO-04** | Telemetry Frame Biophysical Enrichment | `test_23` to `test_28` | 100% | **PASS** |
| **REQ-BIO-05** | Division-by-Zero & NaN Defensive Interlocks | `test_29` to `test_32` | 100% | **PASS** |

---

## 4. DO-178C Level C Statement Coverage

```text
=============================== tests coverage ================================
Name                                           Stmts   Miss  Cover   Missing
----------------------------------------------------------------------------
03_DECISION_CORE\biophysical_physics_engine.py   162      0   100%
----------------------------------------------------------------------------
TOTAL                                            162      0   100%
============================= 32 passed in 0.82s ==============================
```
