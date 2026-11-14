.. _astrovital_spec_data_zip_08:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Raw Archives ZIP Specification
---------------------------------------------------------
Golden Master Archival Bundles, Cryptographic Seals & Provenance Restoration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-ZIP-08
:Subsystem Location: ``01_DATA_VAULT/08_RAW_ARCHIVES_ZIP/ZIP/``
:Archival Sources: NASA LSDA, NASA PDS Geosciences, NASA OSDR GeneLab
:Total Compressed Archives: 14 Gold-Master Compressed Bundles (.zip)
:Aggregate Archive Size: 10,163,445 bytes (~10.16 MB)
:Verification Standard: SHA-256 / MD5 Cryptographic Integrity Checks
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001
:Decompression Protocol: Deflate / PKZIP 2.04g Bounded Stream Unpacker
:Author & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Subsystem Scope & Cold-Storage Redundancy
============================================

In aerospace software engineering under DO-178C Level C, mission-critical analytical baselines must have deterministic, bit-level reproducible provenance. If any active operational archive in ``03_APOLLO_ARCHIVE``, ``04_SHUTTLE_DSO_ARCHIVE``, ``05_ISS_EXPEDITIONS_ARCHIVE``, or ``07_SPACE_RADIATION_ARCHIVE`` suffers accidental file deletion, storage corruption, or bit-rot, the system relies on the cold-storage **Golden Master Archives** stored within ``01_DATA_VAULT/08_RAW_ARCHIVES_ZIP/ZIP/``.

These 14 pristine ZIP files represent the exact binary distributions as downloaded from NASA Johnson Space Center (LSDA) and NASA Ames Research Center (OSDR / GeneLab).

2. Inventory of Golden Master Archives
======================================

The 14 compressed archives are cataloged with exact byte counts and unpacked target mappings:

.. list-table:: Golden Master Archives Inventory
   :widths: 30 15 25 30
   :header-rows: 1

   * - Archive Filename
     - File Size
     - Originating Repository
     - Unpacked Destination Vault
   * - ``AP001_1794509583979.zip``
     - 3,099,024 B
     - NASA LSDA (JSC)
     - ``03_APOLLO_ARCHIVE/``
   * - ``AP001_1794509667987.zip``
     - 3,099,024 B
     - NASA LSDA (JSC)
     - ``03_APOLLO_ARCHIVE/`` (Mirror)
   * - ``AP003_1794509522074.zip``
     - 1,985,570 B
     - NASA LSDA (JSC)
     - ``03_APOLLO_ARCHIVE/`` (Scans)
   * - ``DSO 328_1794510813954.zip``
     - 58,148 B
     - NASA Shuttle HRP
     - ``04_SHUTTLE_DSO_ARCHIVE/``
   * - ``DSO 462_1794510890250.zip``
     - 1,510,025 B
     - NASA Shuttle HRP
     - ``04_SHUTTLE_DSO_ARCHIVE/``
   * - ``DSO 479_1794510657642.zip``
     - 9,569 B
     - NASA Shuttle HRP
     - ``04_SHUTTLE_DSO_ARCHIVE/``
   * - ``DSO 621_1794511011146.zip``
     - 199,905 B
     - NASA Shuttle HRP
     - ``04_SHUTTLE_DSO_ARCHIVE/``
   * - ``LSAHNEWSV13_2_1_1794509174363.zip``
     - 49,380 B
     - NASA ISS LSAH
     - ``05_ISS_EXPEDITIONS_ARCHIVE/``
   * - ``LSAHNEWSV4_1_2_1794509318643.zip``
     - 46,071 B
     - NASA ISS LSAH
     - ``05_ISS_EXPEDITIONS_ARCHIVE/``
   * - ``LSAHNEWSV6_2_1794509048675.zip``
     - 5,563 B
     - NASA ISS LSAH
     - ``05_ISS_EXPEDITIONS_ARCHIVE/``
   * - ``LSAHNEWSV7_1_2_1794509236395.zip``
     - 12,735 B
     - NASA ISS LSAH
     - ``05_ISS_EXPEDITIONS_ARCHIVE/``
   * - ``LSAHNEWSV7_2_3_1794509106994.zip``
     - 8,136 B
     - NASA ISS LSAH
     - ``05_ISS_EXPEDITIONS_ARCHIVE/``
   * - ``LSAHNEWSV8_1_1794509378954.zip``
     - 5,693 B
     - NASA ISS LSAH
     - ``05_ISS_EXPEDITIONS_ARCHIVE/``
   * - ``OSD-1010_metadata_OSD-1010-ISA.zip``
     - 74,605 B
     - NASA OSDR GeneLab
     - ``07_SPACE_RADIATION_ARCHIVE/``

3. Cryptographic Verification & Reconstitution Protocol
=======================================================

Checksum Integrity Enforcement
------------------------------
During formal ground checkout or automated system reconstitution, the integrity of each ZIP archive is audited against its pre-computed SHA-256 digest:

.. math::

   \text{IntegrityCheck}(Z_k) = \begin{cases} \text{VALID (PASS)}, & \text{if } \text{SHA256}(Z_k) == H_{\text{expected}}(k) \\ \text{FAULT (REJECT)}, & \text{otherwise} \end{cases}

Bounded Ingestion Adapter Extraction
------------------------------------
``ingestion_adapter.py`` is architected with defensive fallback capabilities:

1. If uncompressed archives in ``03``, ``04``, ``05``, or ``07`` are intact, it reads directly from them.
2. In disaster-recovery mode, it safely decompresses the golden master ZIPs into temporary staging buffers using Python's ``zipfile`` with path-traversal sanitization (``os.path.commonpath`` checks against Zip Slip vulnerabilities).
