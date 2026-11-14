.. _astrovital_spec_data_apollo_03:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Apollo 7 Mission Archive Specification
-----------------------------------------------------------------
Historic Lunar-Era Clinical Baselines & Biomedical Time-Series Curation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-APOLLO-03
:Subsystem Location: ``01_DATA_VAULT/03_APOLLO_ARCHIVE/``
:Archival Source: NASA Life Sciences Data Archive (LSDA / JSC)
:Flight Mission: Apollo 7 (First Crewed Apollo Mission, 11-Day LEO Test Flight)
:Crew Members: Schirra (CDR), Eisele (CMP), Cunningham (LMP)
:Archive Packages: AP001 (1794509583979 / 1794509667987) & AP003 (1794509522074)
:Primary Formats: Microsoft Excel (.xls), Tagged Image File (.tif), JPEG (.jpg)
:Integrity Checksum: MD5 Manifest Verification
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001
:Author & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Historical & Clinical Significance
=====================================

The Apollo 7 mission (October 11–22, 1968) represents the foundational human spaceflight benchmark for continuous in-flight clinical monitoring and upper-respiratory viral adaptation in microgravity. During the 163-orbit, 260-hour flight, crew members experienced significant cephalad fluid shifts, facial edema, nasal congestion, and cardiovascular deconditioning.

In ASTROVITAL VITALX CORE, the ``03_APOLLO_ARCHIVE`` provides the **ground-truth baseline for human cardiovascular adaptation and viral distress** during early spaceflight. It supplies historical resting baselines for:

- Heart rate chronotropic distribution under microgravity entry.
- Pre-flight vs. Post-flight orthostatic blood pressure variations.
- Body temperature deviations during mission-acquired upper respiratory tract infections.

2. Directory Tree & Archive Inventory
=====================================

.. code-block:: text

   01_DATA_VAULT/03_APOLLO_ARCHIVE/
   │
   ├── AP001_1794509583979/
   │   ├── 987cc7a9_6df_072d_8ab2_40883d1d714f.md5sum
   │   ├── AP001__2810653853/
   │   │   └── AP001.xls_Apollo_7_AP001_2013_281_071043.xls (41,472 bytes)
   │   ├── J0001106/
   │   │   └── JMAPAP001_115.xls (17,408 bytes)
   │   ├── JMAPAP001_113/
   │   │   └── JMAPAP001_113.jpg (105,461 bytes)
   │   ├── JMAPAP001_116/
   │   │   └── JMAPAP001_116.jpg (125,055 bytes)
   │   └── JMAPAP001_119/
   │       └── JMAPAP001_119.jpg (101,216 bytes)
   │
   ├── AP001_1794509667987/  (Cryptographically verified redundant mirror)
   │   └── [Identical AP001 structure and verified MD5 hashes]
   │
   └── AP003_1794509522074/
       ├── 9689e3d0_65e_d288_f44b_bcef07e84d57.md5sum
       ├── JMAPAP003_237/JMAPAP003_237.tif (1,796,512 bytes)
       ├── JMAPAP003_238/JMAPAP003_238.tif (1,915,644 bytes)
       ├── JMAPAP003_239/JMAPAP003_239.tif (1,795,608 bytes)
       ├── JMAPAP003_241/JMAPAP003241.tif (1,693,820 bytes)
       ├── JMAPAP003_242/JMAPAP003_242.tif (1,989,032 bytes)
       ├── JMAPAP003_243/JMAPAP003_243.tif (1,491,928 bytes)
       ├── JMAPAP003_244/JMAPAP003_244.tif (1,487,696 bytes)
       └── JMAPAP003_245/JMAPAP003_245.xls (14,336 bytes)

3. Data Dictionary & Worksheets Specification
=============================================

Master Clinical Logbook (``AP001.xls``)
---------------------------------------
This master clinical logbook contains 4 dedicated clinical evaluation worksheets:

.. list-table:: Apollo 7 Clinical Examination Worksheets
   :widths: 25 35 25 15
   :header-rows: 1

   * - Sheet Name
     - Clinical Scope
     - Recorded Parameters
     - Temporal Phase
   * - ``Preflight Phys Exam``
     - Baseline terrestrial health check
     - Resting HR, SBP/DBP, ECG rhythm
     - :math:`L-30\text{d} \dots L-1\text{d}`
   * - ``Postflight Phys Exam``
     - Immediate recovery assessment
     - Orthostatic stand test HR/BP, ataxia
     - :math:`R+0\text{h} \dots R+48\text{h}`
   * - ``Inflight Monitoring``
     - Operational telemetry acquisition
     - HR, respiration, oral temperature
     - Flight Days 1 to 11
   * - ``Medical ScreeningExam``
     - Comprehensive pathology screening
     - Hematology, blood glucose, urinalysis
     - Pre-mission baseline

4. Ingestion Adapter Extraction Pipeline (Phase 2)
==================================================

In ``02_AI_CORE/01_src/ingestion_adapter.py``, the ``ArchiveParser`` extracts Apollo data via ``_parse_apollo_clinical_baseline()``:

.. code-block:: python

   # Ingestion Logic Mapping:
   1. Scan '03_APOLLO_ARCHIVE' for .xls/.xlsx clinical files.
   2. If files are binary spreadsheets, extract 'Inflight Monitoring' / 'Preflight' sheets.
   3. If tabular text/CSV or fallback synthetic baseline:
      - heart_rate = 72.0 bpm (resting microgravity)
      - blood_pressure_systolic = 118.0 mmHg
      - blood_pressure_diastolic = 76.0 mmHg
      - core_temp = 37.1 deg C
   4. Assemble into synchronized pandas DataFrame with ISO-8601 timestamps.

5. Cryptographic Integrity Verification
=======================================

Every file in ``03_APOLLO_ARCHIVE`` is verified against the NASA LSDA MD5 manifest:

.. math::

   \text{MD5}(F_{\text{AP001}}) = \text{MD5\_Manifest}(F_{\text{AP001}})

.. math::

   \text{MD5}(F_{\text{AP003}}) = \text{MD5\_Manifest}(F_{\text{AP003}})

Zero file corruption, truncated headers, or byte alterations are permitted.
