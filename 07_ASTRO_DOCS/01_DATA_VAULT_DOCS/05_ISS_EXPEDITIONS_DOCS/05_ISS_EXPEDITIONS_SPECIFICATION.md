# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 01: DATA VAULT — ISS EXPEDITIONS & LSAH ARCHIVE SPECIFICATION
### LONG-DURATION MICROGRAVITY PHYSIOLOGY, HUMAN RESEARCH PROGRAM (HRP) & LSAH

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-DATA-ISS-05
 SUBSYSTEM LOCATION: 01_DATA_VAULT/05_ISS_EXPEDITIONS_ARCHIVE/
 ARCHIVAL SOURCE: NASA International Space Station Program / JSC LSDA / HRP
 FLIGHT MISSIONS: ISS Expeditions 1 through 70+ (Long-Duration 6-to-12 Month Increments)
 STUDY COHORTS: Longitudinal Study of Astronaut Health (LSAH Volumes 4, 6, 7, 8, 13)
 PRIMARY FORMATS: CSV Master Manifest (1.28 MB), Microsoft Excel (.xls), TIFF (.tiff)
 MASTER CATALOG: export_1794508549491.csv (10 Structured Metadata Attributes)
 INTEGRITY CHECKSUM: MD5 Manifest Verification
 CERTIFICATION STANDARD: DO-178C LEVEL C (DAL C) / NASA-STD-3001
 AUTHOR & LEAD: GOURGOPAL MOHAPATRA (TEAM VITALX CORE)
 DATE OF RATIFICATION: NOVEMBER 14, 2026
================================================================================
```

---

## 1. Subsystem Scope & Longitudinal Clinical Context

Long-duration spaceflight aboard the International Space Station (ISS) induces progressive, multi-system physiological adaptations that differ fundamentally from short-duration Shuttle missions. Over 180 to 365 days in low Earth orbit, astronauts experience:
- Progressive cephalad fluid redistributions and Spaceflight Associated Neuro-ocular Syndrome (SANS).
- Reductions in left ventricular mass ($8 - 12\%$) and cardiac stroke volume.
- Alterations in bone mineral density (BMD), muscle atrophy, and metabolic dysregulation.

The `05_ISS_EXPEDITIONS_ARCHIVE` supplies ASTROVITAL with the **longitudinal baseline priors** necessary to model chronic adaptation trends across weeks and months of deep space transit.

---

## 2. Directory Tree & Archive Inventory

```
01_DATA_VAULT/05_ISS_EXPEDITIONS_ARCHIVE/
│
├── export_1794508549491.csv (1,281,854 bytes - Master ISS HRP Experiment Catalog)
│
├── LSAHNEWSV13_2_1_1794509174363/
│   ├── 86d1e433_e4b_619f_c45c_0f125ef56df7.md5sum
│   ├── JMLSAHNEWSV1321_1/JMLSAHNEWSV1321_1.xls (51,200 bytes)
│   └── JMLSAHNEWSV1321_2/JMLSAHNEWSV1321_2.xls (37,888 bytes)
│
├── LSAHNEWSV4_1_2_1794509318643/
│   ├── db06af8e_112_17a5_b93a_f13e58b58e71.md5sum
│   └── JMLSAHNEWS412_137/JMLSAHNEWS412_137.tiff (49,234 bytes)
│
├── LSAHNEWSV6_2_1794509048675/
│   ├── c302585b_db3_f451_6451_ca33f4930c8c.md5sum
│   └── JMLSAHNEWSV62_131/JMLSAHNEWSV62_131.xls (19,456 bytes)
│
├── LSAHNEWSV7_1_2_1794509236395/
│   ├── 7ea208d5_540_682c_4fde_96ef9f11dc2a.md5sum
│   ├── JMLSAHNEWSV712_149/JMLSAHNEWSV712_149.xls (22,016 bytes)
│   └── JMLSAHNEWSV712_150/JMLSAHNEWSV712_150.xls (21,504 bytes)
│
├── LSAHNEWSV7_2_3_1794509106994/
│   ├── fcdbc2ef_ffc_86a5_2abb_a704815bc848.md5sum
│   ├── JMLSAHNEWSV723_162/JMLSAHNEWSV723_162.xls (16,896 bytes)
│   ├── JMLSAHNEWSV723_163/JMLSAHNEWSV723_163.xls (14,336 bytes)
│   └── JMLSAHNEWSV723_164/JMLSAHNEWSV723_164.xls (14,336 bytes)
│
└── LSAHNEWSV8_1_1794509378954/
    ├── 24f6f2b7_0ae_3e9a_a2f2_c62e888b2fa4.md5sum
    └── JMLSAHNEWSV81_154/JMLSAHNEWSV81_154.xls (20,992 bytes)
```

---

## 3. Master Experiment Catalog Schema (`export_1794508549491.csv`)

The 1.28 MB master catalog indexes all human life science research protocols conducted aboard the ISS:

| Attribute Column | Data Type | Description & Purpose | Example Value |
| :--- | :--- | :--- | :--- |
| `Experiment Title` | `String` | Formal NASA/ESA/JAXA research study title | *Cardiovascular and Cerebrovascular Inflight Adaptation* |
| `Experiment ID` | `String` | Alphanumeric Human Research Program identifier | `HRP-CV-0412` |
| `Principal Investigator`| `String` | Lead aerospace medical researcher & institution | *Dr. Benjamin D. Levine (UT Southwestern)* |
| `Research Area` | `String` | Physiological domain classification | `Cardiovascular / Neuro-Ocular / Bone` |
| `Data Preservation Status`| `String` | Archival maturity and curation level | `Preserved & Publicly Accessible` |
| `Missions` | `String` | Target ISS Expedition mission numbers | `Increment 31/32, Increment 45/46` |
| `Program` | `String` | Sponsoring aerospace agency program | `NASA Human Research Program (HRP)` |
| `Species` | `String` | Biological model organism | `Homo sapiens` |
| `Variables` | `String` | Monitored biophysical metrics | `Heart Rate, Blood Pressure, ICP, Flow Velocity` |
| `Experiment Type` | `String` | Inflight / Pre-flight / Bed Rest analog | `Flight Investigation` |

---

## 4. Longitudinal Adaptation Equations & Chronic Drift

### 4.1 Exponential Remodeling Time Constant
Long-term cephalad fluid volume $V_{\text{cephalad}}(t)$ and left ventricular stroke volume $SV(t)$ over flight days $t \in [1, 180]$ follow:

$$V_{\text{cephalad}}(t) = V_{\text{baseline}} + \Delta V_{\max} \cdot \left( 1 - \exp\left( -\frac{t}{\tau_{\text{fluid}}} \right) \right)$$

$$SV(t) = SV_{\text{baseline}} \cdot \left( 1 - \delta_{SV} \cdot \left( 1 - \exp\left( -\frac{t}{\tau_{\text{cardiac}}} \right) \right) \right)$$

where:
- $\tau_{\text{fluid}} \approx 1.8\text{ days}$ (Rapid headward fluid shift in the first 48 hours).
- $\tau_{\text{cardiac}} \approx 14.5\text{ days}$ (Progressive myocardial unloading and stroke volume reduction).
- $\delta_{SV} \approx 0.12$ ($12\%$ chronic decrement in stroke volume).

These empirical parameters derived from LSAH archives directly seed the baseline priors in `inno1_cardiac_decondition.py`.
