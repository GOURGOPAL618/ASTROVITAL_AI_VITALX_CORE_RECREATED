.. _astrovital_index_data_vault_00:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Master Catalog & Verification Index
--------------------------------------------------------------
Comprehensive Archival Inventory, Cryptographic Seals & Data Dictionaries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-INDEX-DATA-VAULT-00
:Master Location: ``07_ASTRO_DOCS/01_DATA_VAULT_DOCS/``
:Corresponding Codebase: ``01_DATA_VAULT/`` & ``02_AI_CORE/01_src/ingestion_adapter.py``
:System Certification: RTCA DO-178C Level C (DAL C) / NASA-STD-3001
:Total Archival Modules: 8 Dedicated Subsystems
:Documentation Formats: Dual GitHub-Flavored Markdown (.md) & Sphinx (.rst)
:Lead Architect: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Executive Summary & Vault Architecture
=========================================

The **ASTROVITAL Data Vault (``01_DATA_VAULT``)** serves as the immutable data sanctuary for the ASTROVITAL AI flight decision-support platform. It unites five decades of NASA human spaceflight physiological research—spanning the Apollo lunar exploration era, Space Shuttle orbital missions, long-duration International Space Station (ISS) expeditions, cutting-edge Artemis II cislunar environmental telemetry, and NASA GeneLab deep space ionizing radiation studies.

Every byte entering the ASTROVITAL decision pipeline is rigorously governed under **DO-178C DAL C fault-containment guidelines**. Raw analog inputs, packet streams, and historical tabular sheets are parsed, verified against cryptographic checksums, mapped to physical engineering units, and projected onto a unified :math:`1.0\text{ Hz}` 12-dimensional telemetry tensor.

.. code-block:: text

   01_DATA_VAULT/
   ├── 01_SENSOR_INTAKE/           <-- Real-time telemetry streaming spools & ring buffers
   ├── 02_MISSION_READY/            <-- Standardized 12D Parquet tensors with SHA-256 sidecars
   ├── 03_APOLLO_ARCHIVE/           <-- Apollo 7 clinical monitoring, exam logs & strip-charts
   ├── 04_SHUTTLE_DSO_ARCHIVE/      <-- Space Shuttle DSOs (328, 462, 479, 621) on deconditioning
   ├── 05_ISS_EXPEDITIONS_ARCHIVE/  <-- Long-duration ISS HRP catalog (1.28 MB) & LSAH volumes
   ├── 06_ARTEMIS_II_ARCHIVE/       <-- Orion cabin environmental logs (HOBO 1104/1105) & PDS4 docs
   ├── 07_SPACE_RADIATION_ARCHIVE/  <-- NASA OSDR OSD-1010 ISA-Tab transcriptomics & dosimetry
   └── 08_RAW_ARCHIVES_ZIP/         <-- 14 Golden Master compressed archives (~10.16 MB)

2. Master Subsystem Documentation Catalog
=========================================

.. list-table:: Master Data Vault Documentation Index
   :widths: 10 20 35 35
   :header-rows: 1

   * - Subsystem
     - Vault Directory
     - Markdown Dossier (.md)
     - Sphinx reStructuredText (.rst)
   * - **01**
     - ``01_SENSOR_INTAKE``
     - :ref:`01_SENSOR_INTAKE_DOCS/01_SENSOR_INTAKE_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_intake_01`
   * - **02**
     - ``02_MISSION_READY``
     - :ref:`02_MISSION_READY_DOCS/02_MISSION_READY_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_ready_02`
   * - **03**
     - ``03_APOLLO_ARCHIVE``
     - :ref:`03_APOLLO_ARCHIVE_DOCS/03_APOLLO_ARCHIVE_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_apollo_03`
   * - **04**
     - ``04_SHUTTLE_DSO_ARCHIVE``
     - :ref:`04_SHUTTLE_DSO_DOCS/04_SHUTTLE_DSO_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_shuttle_04`
   * - **05**
     - ``05_ISS_EXPEDITIONS_ARCHIVE``
     - :ref:`05_ISS_EXPEDITIONS_DOCS/05_ISS_EXPEDITIONS_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_iss_05`
   * - **06**
     - ``06_ARTEMIS_II_ARCHIVE``
     - :ref:`06_ARTEMIS_II_DOCS/06_ARTEMIS_II_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_artemis_06`
   * - **07**
     - ``07_SPACE_RADIATION_ARCHIVE``
     - :ref:`07_SPACE_RADIATION_DOCS/07_SPACE_RADIATION_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_radiation_07`
   * - **08**
     - ``08_RAW_ARCHIVES_ZIP``
     - :ref:`08_RAW_ARCHIVES_ZIP_DOCS/08_RAW_ARCHIVES_ZIP_SPECIFICATION.md`
     - :ref:`astrovital_spec_data_zip_08`

3. Data Flow & Ingestion Engine Coupling
========================================

All 8 archival repositories feed directly into the certified 5-phase Ingestion Engine (``02_AI_CORE/01_src/ingestion_adapter.py``):

.. math::

   \begin{aligned}
   \text{Raw Vault Repositories} &\xrightarrow{\text{Phase 1: Discovery}} \text{ArchiveResolver \& SHA-256 Catalog} \\
   &\xrightarrow{\text{Phase 2: Parsing}} \text{ArchiveParser (Artemis, Shuttle, Apollo, ISS)} \\
   &\xrightarrow{\text{Phase 3: Harmonization}} \text{TelemetrySynchronizer (1.0 Hz Uniform Temporal Grid)} \\
   &\xrightarrow{\text{Phase 4: Synthesis}} \text{TensorDatasetBuilder (N } \times \text{ 12 Vector Matrix)} \\
   &\xrightarrow{\text{Phase 5: Certification}} \text{DataExporter (Parquet Tensor + SHA-256 Manifest)}
   \end{aligned}

4. Cryptographic Integrity & DO-178C DAL C Traceability
=======================================================

Every dataset within ``01_DATA_VAULT`` is locked by multi-layer cryptographic hashing:

1. **MD5 Historical Parity:** Individual files inside legacy archives match original NASA LSDA MD5 manifests.
2. **SHA-256 Golden Master Digests:** All 14 golden master ZIP bundles in ``08_RAW_ARCHIVES_ZIP/ZIP/`` are verified before unpacking.
3. **Immutable Output Manifest:** Final mission-ready tensors are accompanied by SHA-256 JSON manifests verifying zero nulls, zero unphysical values, and bit-level determinism.
