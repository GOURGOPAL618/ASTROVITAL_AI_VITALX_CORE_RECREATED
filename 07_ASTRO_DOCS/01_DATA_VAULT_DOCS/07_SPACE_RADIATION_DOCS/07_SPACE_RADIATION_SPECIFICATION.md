# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 01: DATA VAULT — SPACE RADIATION & GENELAB ARCHIVE SPECIFICATION
### NASA OSDR OSD-1010 ISA-TAB TRANSCRIPTOMICS & IONIZING RADIATION DOSIMETRY

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-DATA-RADIATION-07
 SUBSYSTEM LOCATION: 01_DATA_VAULT/07_SPACE_RADIATION_ARCHIVE/
 ARCHIVAL SOURCE: NASA Open Science Data Repository (OSDR / GeneLab)
 ACCESSION ID: OSD-1010 (Spaceflight Radiation & Microgravity Transcriptomics)
 METADATA STANDARD: ISA-Tab (Investigation / Study / Assay Framework)
 ASSAY PLATFORM: Illumina NextSeq (RNA-Seq Transcriptomic Profiling)
 SPECTROMETRY / QA: NanoDrop A260/A280 & A260/A230 Spectrophotometric Purity
 CERTIFICATION STANDARD: DO-178C LEVEL C (DAL C) / NASA-STD-3001
 AUTHOR & LEAD: TEAM VITALX CORE
 DATE OF RATIFICATION: NOVEMBER 14, 2026
================================================================================
```

---

## 1. Subsystem Scope & Deep Space Radiobiological Context

Galactic Cosmic Rays (GCR) and Solar Particle Events (SPE) present the single most hazardous environmental challenge to human crews during beyond-LEO transit to Mars or the Moon. Ionizing deep space radiation consists of high-energy protons and High-Z, High-Energy (HZE) nuclei (e.g., $^{56}\text{Fe}$, $^{28}\text{Si}$) that penetrate spacecraft shielding, inducing cellular DNA double-strand breaks (DSBs), endothelial apoptosis, and chronic systemic oxidative stress.

The `07_SPACE_RADIATION_ARCHIVE` curates NASA Open Science Data Repository (OSDR / GeneLab) study **OSD-1010**, formatted under the internationally recognized **ISA-Tab** (Investigation, Study, Assay) standard. In ASTROVITAL, this archive establishes:
- The biophysical link between cumulative radiation dose equivalents ($H$ in $\text{mSv}$) and autonomic instability.
- Microvascular permeability changes that exacerbate cephalad fluid shift and SANS.
- Multi-omics baseline references for cellular stress markers.

---

## 2. Directory Tree & ISA-Tab File Structure

```
01_DATA_VAULT/07_SPACE_RADIATION_ARCHIVE/
│
└── OSD-1010_metadata_OSD-1010-ISA/
    ├── i_Investigation.txt (19,352 bytes)
    │   └── Investigation Metadata, Ontologies, Protocols, Study Design
    │
    ├── s_OSD-1010.txt (38,323 bytes, 84 Columns)
    │   └── Sample Characteristics, Spaceflight Factors, Organism Phenotypes
    │
    └── a_OSD-1010_transcription-profiling_rna-sequencing-(rna-seq)_illumina.txt
        └── (16,470 bytes, 36 Columns) - NextSeq RNA-Seq Extraction & QA Logs
```

---

## 3. ISA-Tab Metadata Schema Specification

### 3.1 Investigation Level (`i_Investigation.txt`)
Contains formal experimental design, ontology source references (NCBITaxon, EFO, OBI), publication citations, and protocol declarations (sample collection, RNA isolation, library construction, sequencing).

### 3.2 Study Sample Level (`s_OSD-1010.txt` - 84 Attributes)
Links biological specimens to spaceflight environmental exposures:

| Column Name | Category | Biological / Physical Significance |
| :--- | :--- | :--- |
| `Source Name` | Sample Identity | Primary aerospace biological subject / specimen identifier |
| `Sample Name` | Aliquot Tag | Unique assay tracking code |
| `Characteristics[Organism]` | Taxonomy | Model organism species (`Mus musculus` / `Homo sapiens`) |
| `Characteristics[Material Type]`| Histology | Tissue type (e.g., *Vascular Endothelium, Cardiac Myocytes, Retina*) |
| `Factor Value[Spaceflight]` | Flight Condition | `Space Flight (Microgravity + GCR)` vs. `Ground Control (1G)` |
| `Factor Value[Radiation Dose]` | Dosimetry | Absorbed dose ($\text{mGy}$) and dose equivalent ($\text{mSv}$) |

### 3.3 Assay Level (`a_OSD-1010_..._illumina.txt` - 36 Attributes)
Tracks library preparation, spectrophotometric purity ratios, and sequencing platform parameters:
- `Parameter Value[QA Instrument]`: High-sensitivity spectrophotometer / Bioanalyzer.
- `Parameter Value[A260/A280]`: RNA optical purity ($1.8 - 2.1$ nominal).
- `Parameter Value[A260/A230]`: Phenol/salt contaminant ratio ($> 2.0$ nominal).
- `Extract Name` & `Raw Data File`: FastQ run identifiers and paired-end read indices.

---

## 4. Radiobiological Dosimetry Formulations

### 4.1 Cumulative Dose Equivalent & Linear Energy Transfer (LET)
The absorbed dose $D$ in Grays ($\text{Gy}$) is converted to equivalent biological dose $H$ in Sieverts ($\text{Sv}$) via radiation quality factor $Q(L)$:

$$H = \int Q(L) \cdot D(L) \, dL$$

where $L$ is Linear Energy Transfer ($\text{keV}/\mu\text{m}$). For deep space GCR, $Q \approx 10 - 20$, dramatically amplifying endothelial damage per unit dose compared to terrestrial gamma rays.

### 4.2 Endothelial Permeability & Fluid Shift Coupling
Radiation-induced endothelial glycocalyx degradation scales microvascular fluid filtration $J_v$ according to the Starling-Kedem-Katchalsky equation:

$$J_v = L_p \cdot A \cdot \left[ (P_c - P_i) - \sigma \cdot (\pi_c - \pi_i) \right]$$

where cumulative GCR dose $H$ reduces the reflection coefficient $\sigma(H) = \sigma_0 \cdot \exp(-k_r \cdot H)$, accelerating headward interstitial edema and ICP elevation.
