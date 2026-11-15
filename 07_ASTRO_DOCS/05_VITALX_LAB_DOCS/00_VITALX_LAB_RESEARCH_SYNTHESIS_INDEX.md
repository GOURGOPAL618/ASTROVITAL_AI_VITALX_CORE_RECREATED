# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 05: VITALX LAB — RESEARCH SYNTHESIS & EXPERIMENTAL LAB INDEX
### JUPYTER RESEARCH NOTEBOOKS, DATA SYNTHESIS, SIGNAL CLEANING & BIOMARKER DIVERGENCE

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-INDEX-LAB-00
 SUBSYSTEM LOCATION: 05_VITALX_LAB/ & 07_ASTRO_DOCS/05_VITALX_LAB_DOCS/
 CERTIFICATION STANDARD: RTCA DO-178C LEVEL C (DAL C) / NASA-STD-3001
 RESEARCH MODULES: 3 Production Jupyter Notebooks | 8 Publication-Grade Figures
 ARTIFACT TYPES: High-Res PNG Visualizers, Parquet Datasets, JSON Metrics
 LEAD RESEARCHER & ARCHITECT: GOURGOPAL MOHAPATRA (TEAM VITALX CORE)
 DATE OF RATIFICATION: NOVEMBER 15, 2026
================================================================================
```

---

## 1. Executive Summary & Lab Scope

The `05_VITALX_LAB` research environment serves as the scientific and empirical testbed for the ASTROVITAL AI architecture. While production code in `02_AI_CORE`, `03_DECISION_CORE`, and `04_ASTRONAUT_COCKPIT` is strictly frozen and deterministic under DO-178C DAL C, `05_VITALX_LAB` contains the exploratory research workflows, multi-mission synthesis pipelines, spectral signal quality analyses, and biomarker divergence algorithms.

```
05_VITALX_LAB/
│
├── 01_multi_mission_data_synthesis.ipynb     <-- Multi-Mission Ingestion & 12D Tensor Synthesis
├── 02_inno3_signal_cleaning_validation.ipynb <-- Inno 3 Adaptive Denoising & SQI Certification
└── 03_inno6_biomarker_divergence.ipynb       <-- Inno 6 Dynamic Dirichlet Sensitivity Optimization
```

---

## 2. Research Notebook Verification Catalog

| Notebook ID | Notebook Title | Executable Script Driver | Primary Output Figures | Summary JSON |
| :---: | :--- | :--- | :--- | :--- |
| **NOTEBOOK-01** | **Multi-Mission Data Synthesis** | `scripts/build_and_run_notebook_01.py` | `figure_01_artemis_cabin_environment.png`<br>`figure_02_shuttle_dso_cardiovascular.png`<br>`figure_03_master_12channel_telemetry.png`<br>`figure_04_correlation_matrix.png` | [`01_multi_mission_data_synthesis_summary.json`](summaries/01_multi_mission_data_synthesis_summary.json) |
| **NOTEBOOK-02** | **Inno 3 Signal Cleaning Validation** | `scripts/build_and_run_notebook_02.py` | `figure_01_baseline_drift_compensation.png`<br>`figure_02_spectral_noise_attenuation.png`<br>`figure_03_motion_cancellation_traces.png`<br>`figure_04_sqi_channel_certification.png` | [`02_inno3_signal_cleaning_summary.json`](summaries/02_inno3_signal_cleaning_summary.json) |
| **NOTEBOOK-03** | **Inno 6 Biomarker Divergence** | `scripts/build_and_run_notebook_03.py` | Biomarker Sensitivity Heatmaps & Gradient Trajectories | `03_inno6_biomarker_divergence_summary.json` |

---

## 3. Publication Figures & Experimental Artifacts

All generated figures in `07_ASTRO_DOCS/05_VITALX_LAB_DOCS/figures/` are rendered in 300 DPI publication quality with dark aerospace glass styling:
- **`figure_01_artemis_cabin_environment.png` (460 KB):** Artemis II Orion cabin temperature, relative humidity, and dew point correlation over 75,396 records.
- **`figure_02_shuttle_dso_cardiovascular.png` (847 KB):** Space Shuttle DSO 479 supine vs. standing orthostatic stress delta profiles.
- **`figure_03_master_12channel_telemetry.png` (1.15 MB):** Unified 72-hour Artemis Lunar Transit 12-channel time-series tensor ($N=4,320$ records).
- **`figure_04_correlation_matrix.png` (363 KB):** Full Pearson correlation matrix showing cross-coupling across vital signs and environmental covariates.
- **`figure_01_baseline_drift_compensation.png` (1.05 MB):** Polynomial detrending removing thermal baseline drift while preserving cardiac waveforms.
- **`figure_02_spectral_noise_attenuation.png` (460 KB):** Power Spectral Density (PSD) showing 60 Hz hum and high-frequency noise attenuation.
- **`figure_03_motion_cancellation_traces.png` (861 KB):** Multi-axis IMU adaptive motion artifact cancellation during simulated space launch.
- **`figure_04_sqi_channel_certification.png` (221 KB):** Radar chart of Signal Quality Index ($SQI \ge 0.95$) certifying flight readiness across all channels.
