.. _astrovital_spec_data_ready_02:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Mission-Ready Data Specification
------------------------------------------------------------
Synchronized, Imputed, & Cryptographically Certified Flight Tensors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-READY-02
:Subsystem Location: ``01_DATA_VAULT/02_MISSION_READY/``
:Generating Producer: ``02_AI_CORE/01_src/ingestion_adapter.py`` (Phase 5 DataExporter)
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001
:Serialization Format: Apache Parquet (Snappy Compressed) & HDF5 / NumPy .npz
:Cryptographic Side-Car: SHA-256 JSON Digest Manifest
:Tensor Dimensionality: :math:`N \times 12` IEEE 754 Float64 Matrix
:Author & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Subsystem Scope & Mission Role
=================================

The ``02_MISSION_READY`` vault directory stores the fully calibrated, temporally aligned, imputed, and flight-certified biomedical data products output by the ASTROVITAL Ingestion Pipeline. Downstream analytical components—including:

- ``inno3_signal_stabilizer.py`` (Innovation 3: Adaptive Motion Canceller & Wavelet Denoising)
- ``sanity_gate.py`` (DO-178C Level C Mathematical Sanity Gate :math:`\mathbf{\Omega}_{\text{bio}}`)
- ``inno6_biomarker_ranker.py`` (Innovation 6: Multi-Criteria Dynamic Biomarker Sensitivity Ranker)
- ``03_DECISION_CORE`` (80% Biophysical Supreme Head: Fluid Shift & Cardiac Deconditioning Engines)

read exclusively from ``02_MISSION_READY`` or memory-mapped equivalents. Raw or unvalidated sensor inputs are strictly prohibited from entering downstream decision networks.

2. Standardized Mission-Ready File Format & Artifact Schema
===========================================================

When ``DataExporter.export_dataset()`` in ``ingestion_adapter.py`` executes, it generates a pair of coupled artifacts:

.. code-block:: text

   01_DATA_VAULT/02_MISSION_READY/
   │
   ├── mission_ready_vitalx_telemetry.parquet      <-- Columnar Time-Series Tensor
   └── mission_ready_vitalx_telemetry.sha256.json  <-- Cryptographic Integrity Sidecar

Schema Definition Table
-----------------------
The Parquet file schema contains 13 strongly-typed columns (1 ISO-8601 Timestamp + 12 Normalized Physiological Dimensions):

.. list-table:: Parquet File Schema and Physiological Dimensions
   :widths: 20 20 10 20 15 15
   :header-rows: 1

   * - Column Name
     - Arrow / Parquet Type
     - Nullable
     - Mathematical Domain
     - Physical Unit
     - Calibration Scale
   * - ``timestamp``
     - ``TIMESTAMP('us', 'UTC')``
     - **NO**
     - Monotonic
     - :math:`\mu\text{s}` since Unix Epoch
     - :math:`dt = 1.0\text{ s}`
   * - ``heart_rate``
     - ``FLOAT64``
     - **NO**
     - :math:`[30.0, 220.0]`
     - :math:`\text{bpm}`
     - Unscaled
   * - ``blood_pressure_systolic``
     - ``FLOAT64``
     - **NO**
     - :math:`[70.0, 240.0]`
     - :math:`\text{mmHg}`
     - Unscaled
   * - ``blood_pressure_diastolic``
     - ``FLOAT64``
     - **NO**
     - :math:`[40.0, 140.0]`
     - :math:`\text{mmHg}`
     - Unscaled
   * - ``rmssd``
     - ``FLOAT64``
     - **NO**
     - :math:`[5.0, 250.0]`
     - :math:`\text{ms}`
     - Unscaled
   * - ``spo2``
     - ``FLOAT64``
     - **NO**
     - :math:`[50.0, 100.0]`
     - :math:`\%`
     - Unscaled
   * - ``core_temp``
     - ``FLOAT64``
     - **NO**
     - :math:`[34.0, 42.0]`
     - :math:`^\circ\text{C}`
     - Unscaled
   * - ``blood_glucose``
     - ``FLOAT64``
     - **NO**
     - :math:`[40.0, 400.0]`
     - :math:`\text{mg/dL}`
     - Unscaled
   * - ``perfusion_index``
     - ``FLOAT64``
     - **NO**
     - :math:`[0.1, 20.0]`
     - :math:`\%`
     - Unscaled
   * - ``respiration_rate``
     - ``FLOAT64``
     - **NO**
     - :math:`[4.0, 50.0]`
     - :math:`\text{br/min}`
     - Unscaled
   * - ``motion_artifact_index``
     - ``FLOAT64``
     - **NO**
     - :math:`[0.0, 1.0]`
     - Normalized
     - Unscaled
   * - ``ecg_lead2_entropy``
     - ``FLOAT64``
     - **NO**
     - :math:`[0.0, 8.0]`
     - :math:`\text{bits}`
     - Unscaled
   * - ``galvanic_skin_response``
     - ``FLOAT64``
     - **NO**
     - :math:`[0.5, 30.0]`
     - :math:`\mu\text{S}`
     - Unscaled

3. Cryptographic Sidecar Verification Manifest
==============================================

To guarantee airworthiness and chain-of-custody verification under DO-178C DAL C, every mission-ready file is accompanied by a SHA-256 metadata digest:

.. code-block:: json

   {
     "system": "ASTROVITAL_AI_VITALX_CORE",
     "artifact_type": "MISSION_READY_TELEMETRY_TENSOR",
     "specification": "ASTROVITAL-SPEC-DATA-READY-02",
     "generated_at_utc": "2026-11-14T11:35:47.129384Z",
     "total_records": 18450,
     "sampling_frequency_hz": 1.0,
     "temporal_span": {
       "start_utc": "2026-11-14T00:00:00Z",
       "end_utc": "2026-11-14T05:07:30Z"
     },
     "sha256_checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
     "validation_status": "PASSED_ZERO_NULLS_DO178C_LEVEL_C",
     "compiler_signature": "Python 3.12.0 / PyArrow 15.0.0"
   }

4. Mathematical Guarantees & Non-Zero Invariants
================================================

Prior to export into ``02_MISSION_READY``, ``TensorDatasetBuilder`` verifies three mathematical invariants across the entire tensor :math:`\mathbf{X} \in \mathbb{R}^{N \times 12}`:

Invariant 1: Completeness & Finite Support
------------------------------------------
.. math::

   \forall i \in \{1, \dots, N\}, \forall j \in \{1, \dots, 12\}, \quad x_{i, j} \in \mathbb{R} \setminus \{\text{NaN}, \pm\infty\}

No ``NaN``, ``Inf``, or ``None`` values are permitted.

Invariant 2: Physical Boundedness
---------------------------------
.. math::

   \forall i, j, \quad \text{Bound}_{\min}(j) \le x_{i, j} \le \text{Bound}_{\max}(j)

Every parameter is strictly contained within its physiological envelope.

Invariant 3: Hemodynamic Plausibility
-------------------------------------
.. math::

   \forall i \in \{1, \dots, N\}, \quad x_{i, \text{SBP}} - x_{i, \text{DBP}} \ge 15.0\text{ mmHg}

Ensures positive, physiologically valid pulse pressure across every recorded heartbeat.
