# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 05: VITALX LAB — INNO 6 BIOMARKER DIVERGENCE REPORT
### DYNAMIC DIRICHLET PRIORS, SHANNON ENTROPY DIVERGENCE & SENSITIVITY GRADIENTS

---

```
================================================================================
 RESEARCH REPORT DESIGNATOR: ASTROVITAL-LAB-RANK-03
 SOURCE NOTEBOOK: 05_VITALX_LAB/03_inno6_biomarker_divergence.ipynb
 DRIVER SCRIPT: 07_ASTRO_DOCS/05_VITALX_LAB_DOCS/scripts/build_and_run_notebook_03.py
 TARGET SUBSYSTEM: 02_AI_CORE/01_src/inno6_biomarker_ranker.py
 VERIFICATION STANDARD: RTCA DO-178C LEVEL C / NASA-STD-3001
 MISSION PHASE MODELS: 8 Flight Operational Context Profiles
 FORMULATION: W_raw = alpha * W_context + beta * W_deviation + gamma * W_entropy
 SIMPLEX NORMALIZATION: Sum(w_i) = 1.0 with w_min >= 0.01 Floor Guarantee
 AUTHOR & LEAD ARCHITECT: GOURGOPAL MOHAPATRA (TEAM VITALX CORE)
 DATE OF RATIFICATION: NOVEMBER 15, 2026
================================================================================
```

---

## 1. Scientific Objective & Sensitivity Formulation

Notebook 03 analyzes the mathematical dynamics of the **Multi-Criteria Dynamic Biomarker Sensitivity Ranker (`inno6_biomarker_ranker.py`)**. In deep space flight, different biomarkers carry wildly different diagnostic significance depending on the active flight phase (e.g. `EARLY_MICROGRAVITY` vs `EXTRAVEHICULAR_ACTIVITY` vs `DEORBIT_REENTRY`).

The multi-criteria ranking formulation combines three independent mathematical domains:

$$\mathbf{w}_{\text{raw}} = \alpha \cdot \mathbf{w}_{\text{context}} + \beta \cdot \mathbf{w}_{\text{deviation}} + \gamma \cdot \mathbf{w}_{\text{entropy}}$$

where:
1. $\mathbf{w}_{\text{context}}$ ($\alpha = 0.35$): Dirichlet distribution prior weights conditioned on the 8 discrete mission phases.
2. $\mathbf{w}_{\text{deviation}}$ ($\beta = 0.45$): Robust median absolute deviation (MAD) modified Z-scores quantifying departure from resting homeostasis.
3. $\mathbf{w}_{\text{entropy}}$ ($\gamma = 0.20$): Shannon entropy divergence capturing non-linear spectral dispersion across a rolling time window.

$$\mathbf{w}_{\text{final}} = \text{SimplexNormalize}\left( \max(\mathbf{w}_{\text{raw}}, w_{\min}) \right) \quad \text{such that } \sum_{i=1}^{12} w_i = 1.0, \quad w_{\min} \ge 0.01$$

---

## 2. Experimental Verification across 8 Mission Phases

The ranker was subjected to synthetic multi-mission trajectory simulations across all 8 operational phases:
1. `PRE_LAUNCH`: Focuses on baseline autonomic anxiety and cardiovascular stability.
2. `LAUNCH_ASCENT`: Elevates motion artifact tolerance and heart rate slew sensitivity.
3. `EARLY_MICROGRAVITY`: Elevates cephalad fluid shift markers (SBP, DBP, RMSSD, Core Temp) by $+85\%$.
4. `LONG_DURATION_TRANSIT`: Shifts attention toward chronic sleep debt, metabolic stability, and heart rate variability.
5. `EXTRAVEHICULAR_ACTIVITY (EVA)`: Prioritizes metabolic oxygen consumption, respiration rate, and SpO2.
6. `LUNAR_SURFACE_OPS`: Balances kinematic fatigue with musculoskeletal load markers.
7. `DEORBIT_REENTRY`: Elevates orthostatic intolerance markers and pulse pressure sensitivity.
8. `POST_LANDING_RECOVERY`: Directs focus toward cerebral perfusion recovery and vestibular adaptation.

The experimental results confirm that zero rank collapse occurs, with every channel maintaining $\ge 0.01$ minimum sensitivity floor across all operational transitions.
