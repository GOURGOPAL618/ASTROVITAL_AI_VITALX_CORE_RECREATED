# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 01: DATA VAULT — SPACE SHUTTLE DSO ARCHIVE SPECIFICATION
### DETAILED SUPPLEMENTARY OBJECTIVES ON CARDIOVASCULAR DECONDITIONING & FLUID SHIFTS

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-DATA-SHUTTLE-04
 SUBSYSTEM LOCATION: 01_DATA_VAULT/04_SHUTTLE_DSO_ARCHIVE/
 ARCHIVAL SOURCE: NASA Space Shuttle Human Research Program / LSDA
 FLIGHT MISSIONS: STS-31 (Hubble Deployment), STS-45 (ATLAS-1), Multi-Mission Fleet
 DETAILED SUPPLEMENTARY OBJECTIVES: DSO 328, DSO 462, DSO 479, DSO 621
 CLINICAL DOMAINS: Orthostatic Intolerance, Baroreflex, LBNP, Vestibular Adaptation
 PRIMARY FORMATS: Microsoft Excel (.xlsx), Tagged Image File (.tif), PDF
 INTEGRITY CHECKSUM: MD5 Manifest Verification
 CERTIFICATION STANDARD: DO-178C LEVEL C (DAL C) / NASA-STD-3001
 AUTHOR & LEAD: TEAM VITALX CORE
 DATE OF RATIFICATION: NOVEMBER 14, 2026
================================================================================
```

---

## 1. Subsystem Scope & Operational Flight Heritage

During the NASA Space Shuttle Program (STS), Detailed Supplementary Objectives (DSOs) were standardized clinical research protocols conducted on astronauts to quantify microgravity-induced physiological adaptations.

The `04_SHUTTLE_DSO_ARCHIVE` serves as the primary empirical training and validation ground for ASTROVITAL’s **80% Biophysical Supreme Head** (specifically Innovation 1: Cephalad Fluid Shift Hydrodynamic Engine and Cardiac Deconditioning Models). The clinical parameters captured during STS missions establish the mathematical limits of orthostatic intolerance and baroreflex degradation upon gravitational transition.

---

## 2. Directory Tree & DSO Module Inventory

```
01_DATA_VAULT/04_SHUTTLE_DSO_ARCHIVE/
│
├── DSO 328_1794510813954/
│   ├── f1a8e52e_de1_c1ef_58e2_1404b2ea8d6e.md5sum
│   └── DSO 328__20100512015812847/
│       └── DSO 328__20100512015812847.pdf (33,983 bytes)
│
├── DSO 462_1794510890250/
│   ├── 1960a77d_e2c_b9c6_911c_b35f9012c402.md5sum
│   ├── JMDSO_462_1/JMDSO_462_1.tif (75,194 bytes)
│   ├── JMDSO_462_2/JMDSO_462_2.tif (74,740 bytes)
│   ├── JMDSO_462_3/JMDSO_462_3.tif (75,872 bytes)
│   ├── JMDSO_462_4/JMDSO_462_4.tif (87,494 bytes)
│   ├── JMDSO_462_5/JMDSO_462_5.tif (80,714 bytes)
│   └── JMDSO_462_6/JMDSO_462_6.tif (75,246 bytes)
│
├── DSO 479_1794510657642/
│   ├── d5c2cd69_93a_a802_c441_d2f1c105182c.md5sum
│   └── DSO 479__2500136903/
│       └── DSO_479__2500136903.xlsx_STS-31_DSO_479_2010_250_050919.xlsx (12,128 bytes)
│
└── DSO 621_1794511011146/
    ├── 37df3930_25e_1d61_ae5b_16d5fcc78655.md5sum
    ├── DSO 621__2180117851/DSO_621__2180117851.tif_STS-45_DSO_621_2010_218_010846.tif
    ├── DSO 621__2180130375/DSO_621__2180130375.tif_STS-45_DSO_621_2010_218_010842.tif
    ├── DSO 621__218125493/DSO_621__218125493.tif_STS-45_DSO_621_2010_218_010845.tif
    └── JMDSO_621_1/JMDSO_621_11.tiff_STS-45_DSO_621_2011_20_070111.tiff
```

---

## 3. Detailed Supplementary Objectives (DSO) Clinical Taxonomy

| DSO Identifier | Mission / Cohort | Scientific Protocol Name | Primary Physiological Biomarkers | Biophysical Relevance |
| :---: | :---: | :--- | :--- | :--- |
| **DSO 328** | Multi-STS Fleet | Inflight / Postflight Baroreceptor Reflex Function | Carotid-cardiac baroreflex slope ($G_{\text{baro}}$), ECG R-R interval vs. systolic pressure | Predicts post-landing presyncope and orthostatic collapse |
| **DSO 462** | Multi-STS Fleet | Space Motion Sickness & Neuro-Vestibular Adaptation | Saccadic velocity, otolith-ocular gain, motion sickness rating score | Informs `inno6_biomarker_ranker` during Early Microgravity phase |
| **DSO 479** | STS-31 (Hubble) | Fluid / Electrolyte Shifts & Stand Test Tolerance | Supine vs. 10-min Standing SBP, DBP, Heart Rate, Total Body Water | Calibrates `inno1_hydrodynamic_fluid` compartment models |
| **DSO 621** | STS-45 (ATLAS-1) | In-Flight Lower Body Negative Pressure (LBNP) | Venous compliance, peripheral resistance, stroke volume index | Direct input for microgravity cardiac stroke volume deconditioning |

---

## 4. Hemodynamic Modeling & Calibration Equations

### 4.1 Carotid Baroreceptor Reflex Gain ($G_{\text{baro}}$) from DSO 328
The sigmoidal baroreflex response curve is modeled as:

$$RR(P_{\text{carotid}}) = RR_{\min} + \frac{RR_{\max} - RR_{\min}}{1 + \exp\left( -k \cdot (P_{\text{carotid}} - P_{0}) \right)}$$

where maximal reflex gain evaluated at operating point $P_0$ is:

$$G_{\text{baro}} = \left. \frac{d(RR)}{d(P_{\text{carotid}})} \right|_{P_0} = \frac{k \cdot (RR_{\max} - RR_{\min})}{4}$$

DSO 328 demonstrates a $30 - 45\%$ reduction in $G_{\text{baro}}$ following 7–14 days of microgravity, directly justifying ASTROVITAL's elevated sensitivity weights for diastolic blood pressure and RMSSD during the `DEORBIT_REENTRY` flight phase.

### 4.2 Orthostatic Intolerance Delta ($\Delta \text{HR}_{\text{stand}}$) from DSO 479
$$\Delta \text{HR}_{\text{stand}} = \text{HR}_{\text{stand, 10min}} - \text{HR}_{\text{supine}}$$
$$\text{Presyncope Risk Index} = \frac{\Delta \text{HR}_{\text{stand}}}{30.0} + \frac{15.0}{\max(1.0, \text{SBP}_{\text{stand}} - \text{DBP}_{\text{stand}})}$$

---

## 5. Ingestion Adapter Extraction Pipeline (Phase 2)

In `02_AI_CORE/01_src/ingestion_adapter.py`, the `ArchiveParser` extracts Shuttle DSO data via `_parse_shuttle_dso_cardiovascular()`:

```python
# Extraction Pipeline:
1. Scan '04_SHUTTLE_DSO_ARCHIVE' for DSO 479 (.xlsx) and DSO 328 clinical files.
2. Read 'Stand Test' worksheet from STS-31 DSO 479.
3. Extract supine and standing HR, SBP, and DBP profiles.
4. Normalize into 12D uniform time-series tensor.
```
