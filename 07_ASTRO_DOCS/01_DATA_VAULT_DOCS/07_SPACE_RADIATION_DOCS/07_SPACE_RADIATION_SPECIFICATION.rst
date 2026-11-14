.. _astrovital_spec_data_radiation_07:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Space Radiation & GeneLab Archive Specification
-------------------------------------------------------------------------
NASA OSDR OSD-1010 ISA-Tab Transcriptomics & Ionizing Radiation Dosimetry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-RADIATION-07
:Subsystem Location: ``01_DATA_VAULT/07_SPACE_RADIATION_ARCHIVE/``
:Archival Source: NASA Open Science Data Repository (OSDR / GeneLab)
:Accession ID: OSD-1010 (Spaceflight Radiation & Microgravity Transcriptomics)
:Metadata Standard: ISA-Tab (Investigation / Study / Assay Framework)
:Assay Platform: Illumina NextSeq (RNA-Seq Transcriptomic Profiling)
:Spectrometry / QA: NanoDrop A260/A280 & A260/A230 Spectrophotometric Purity
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001
:Author & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Subsystem Scope & Deep Space Radiobiological Context
=======================================================

Galactic Cosmic Rays (GCR) and Solar Particle Events (SPE) present the single most hazardous environmental challenge to human crews during beyond-LEO transit to Mars or the Moon. Ionizing deep space radiation consists of high-energy protons and High-Z, High-Energy (HZE) nuclei (e.g., :math:`^{56}\text{Fe}`, :math:`^{28}\text{Si}`) that penetrate spacecraft shielding, inducing cellular DNA double-strand breaks (DSBs), endothelial apoptosis, and chronic systemic oxidative stress.

The ``07_SPACE_RADIATION_ARCHIVE`` curates NASA Open Science Data Repository (OSDR / GeneLab) study **OSD-1010**, formatted under the internationally recognized **ISA-Tab** (Investigation, Study, Assay) standard. In ASTROVITAL, this archive establishes:

- The biophysical link between cumulative radiation dose equivalents (:math:`H` in :math:`\text{mSv}`) and autonomic instability.
- Microvascular permeability changes that exacerbate cephalad fluid shift and SANS.
- Multi-omics baseline references for cellular stress markers.

2. Directory Tree & ISA-Tab File Structure
==========================================

.. code-block:: text

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

3. ISA-Tab Metadata Schema Specification
========================================

Investigation Level (``i_Investigation.txt``)
---------------------------------------------
Contains formal experimental design, ontology source references (NCBITaxon, EFO, OBI), publication citations, and protocol declarations (sample collection, RNA isolation, library construction, sequencing).

Study Sample Level (``s_OSD-1010.txt`` - 84 Attributes)
-------------------------------------------------------
Links biological specimens to spaceflight environmental exposures:

.. list-table:: OSD-1010 Study Sample Attributes
   :widths: 30 25 45
   :header-rows: 1

   * - Column Name
     - Category
     - Biological / Physical Significance
   * - ``Source Name``
     - Sample Identity
     - Primary aerospace biological subject / specimen identifier
   * - ``Sample Name``
     - Aliquot Tag
     - Unique assay tracking code
   * - ``Characteristics[Organism]``
     - Taxonomy
     - Model organism species (``Mus musculus`` / ``Homo sapiens``)
   * - ``Characteristics[Material Type]``
     - Histology
     - Tissue type (e.g., *Vascular Endothelium, Myocytes, Retina*)
   * - ``Factor Value[Spaceflight]``
     - Flight Condition
     - ``Space Flight (Microgravity + GCR)`` vs. ``Ground Control (1G)``
   * - ``Factor Value[Radiation Dose]``
     - Dosimetry
     - Absorbed dose (:math:`\text{mGy}`) and dose equivalent (:math:`\text{mSv}`)

Assay Level (``a_OSD-1010_..._illumina.txt`` - 36 Attributes)
-------------------------------------------------------------
Tracks library preparation, spectrophotometric purity ratios, and sequencing platform parameters:

- ``Parameter Value[QA Instrument]``: High-sensitivity spectrophotometer / Bioanalyzer.
- ``Parameter Value[A260/A280]``: RNA optical purity (:math:`1.8 - 2.1` nominal).
- ``Parameter Value[A260/A230]``: Phenol/salt contaminant ratio (:math:`> 2.0` nominal).
- ``Extract Name`` & ``Raw Data File``: FastQ run identifiers and paired-end read indices.

4. Radiobiological Dosimetry Formulations
=========================================

Cumulative Dose Equivalent & Linear Energy Transfer (LET)
---------------------------------------------------------
The absorbed dose :math:`D` in Grays (:math:`\text{Gy}`) is converted to equivalent biological dose :math:`H` in Sieverts (:math:`\text{Sv}`) via radiation quality factor :math:`Q(L)`:

.. math::

   H = \int Q(L) \cdot D(L) \, dL

where :math:`L` is Linear Energy Transfer (:math:`\text{keV}/\mu\text{m}`). For deep space GCR, :math:`Q \approx 10 - 20`, dramatically amplifying endothelial damage per unit dose compared to terrestrial gamma rays.

Endothelial Permeability & Fluid Shift Coupling
-----------------------------------------------
Radiation-induced endothelial glycocalyx degradation scales microvascular fluid filtration :math:`J_v` according to the Starling-Kedem-Katchalsky equation:

.. math::

   J_v = L_p \cdot A \cdot \left[ (P_c - P_i) - \sigma \cdot (\pi_c - \pi_i) \right]

where cumulative GCR dose :math:`H` reduces the reflection coefficient :math:`\sigma(H) = \sigma_0 \cdot \exp(-k_r \cdot H)`, accelerating headward interstitial edema and ICP elevation.
