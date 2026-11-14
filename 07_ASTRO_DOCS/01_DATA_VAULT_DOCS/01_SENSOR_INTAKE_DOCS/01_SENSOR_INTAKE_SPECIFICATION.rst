.. _astrovital_spec_data_intake_01:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Sensor Intake Specification
-------------------------------------------------------
Real-Time Biomedical Sensor Stream Ingestion & Spooling Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-INTAKE-01
:Subsystem Location: ``01_DATA_VAULT/01_SENSOR_INTAKE/``
:Target Subsystem: ``02_AI_CORE/01_src/ingestion_adapter.py``
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001 Vol 1 & 2
:Transmission Protocol: CCSDS 133.0-B-2 / ZeroMQ PUB-SUB / Ring Buffer Spool
:Intake Buffer Capacity: 10,000 packets/channel (FIFO circular memory)
:Author & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Architectural Scope & Functional Objective
=============================================

The ``01_SENSOR_INTAKE`` subsystem serves as the high-throughput, fault-tolerant entry staging gate for raw astronaut biomedical, environmental, and kinematic telemetry streams. In operational deep-space flight (e.g., Artemis II, Lunar Gateway, Mars Transit), physiological signals originate from distributed body-worn sensors, Intra-Vehicular Activity (IVA) suits, Extravehicular Mobility Units (EMU), and spacecraft cabin environmental loggers.

The primary objective of ``01_SENSOR_INTAKE`` is to decouple raw network packet capture from downstream ingestion, resampling, and tensor assembly. By providing a hardened staging queue and memory-mapped ring buffer, it guarantees zero packet drops during transient CPU spikes or burst telemetry intervals.

.. code-block:: text

   +-----------------------------------------------------------------------------------+
   |                           DISTRIBUTED ASTRONAUT SENSORS                           |
   |  +--------------------+   +-----------------------+   +------------------------+  |
   |  | Smart Wearable PPG |   | 3-Lead ECG Biosensors |   | Continuous Arterial BP |  |
   |  +---------+----------+   +-----------+-----------+   +-----------+------------+  |
   |            |                          |                           |               |
   |            +--------------------------+---------------------------+               |
   |                                       | (Wireless / BLE 5.3 / USB-C Spool)        |
   |                                       v                                           |
   |                      +--------------------------------+                           |
   |                      | 01_DATA_VAULT/01_SENSOR_INTAKE |                           |
   |                      |  - Raw Spool Buffers (.jsonl)  |                           |
   |                      |  - Cyclic Staging Queue (.csv) |                           |
   |                      |  - Memory-Mapped FIFO Ring     |                           |
   |                      +----------------+---------------+                           |
   +---------------------------------------|-------------------------------------------+
                                           v
                    +---------------------------------------------+
                    | 02_AI_CORE: IngestionAdapter (Phases 1-5)   |
                    |  - Archive Discovery & SHA-256 Hashing      |
                    |  - Resampling (1.0 Hz Uniform Grid)         |
                    |  - Bounded Forward-Fill Imputation          |
                    |  - 12D Tensor Assembly & Parquet Export     |
                    +---------------------------------------------+

2. Ingested Stream Channels & Sensor Metadata
=============================================

Under DO-178C DAL C fault-containment guidelines, all inbound packet payloads are validated against strict structural constraints before being passed to ``ingestion_adapter.py``:

.. list-table:: Ingested Telemetry Channels and Physical Constraints
   :widths: 10 20 25 15 15 15
   :header-rows: 1

   * - Stream ID
     - Channel Parameter
     - Transducer / Instrument Source
     - Physical Domain
     - Sampling Rate (:math:`f_s`)
     - NASA-STD-3001 Range
   * - **STR-01**
     - ``heart_rate``
     - Optical PPG / 3-Lead ECG chest harness
     - Cardiovascular
     - :math:`1.0 - 250.0\text{ Hz}`
     - :math:`[30.0, 220.0]\text{ bpm}`
   * - **STR-02**
     - ``blood_pressure_sys``
     - Continuous arterial cuff plethysmography
     - Hemodynamic
     - :math:`1.0 - 50.0\text{ Hz}`
     - :math:`[70.0, 240.0]\text{ mmHg}`
   * - **STR-03**
     - ``blood_pressure_dia``
     - Continuous finger plethysmography
     - Hemodynamic
     - :math:`1.0 - 50.0\text{ Hz}`
     - :math:`[40.0, 140.0]\text{ mmHg}`
   * - **STR-04**
     - ``rmssd``
     - R-R interval peak detector algorithm
     - Autonomic
     - :math:`1.0\text{ Hz}` derived
     - :math:`[5.0, 250.0]\text{ ms}`
   * - **STR-05**
     - ``spo2``
     - Dual-wavelength reflective pulse oximeter
     - Pulmonary
     - :math:`1.0 - 25.0\text{ Hz}`
     - :math:`[50.0, 100.0]\%`
   * - **STR-06**
     - ``core_temp``
     - Ingestible radio telemetry pill / Tympanic IR
     - Thermoregulation
     - :math:`0.1 - 1.0\text{ Hz}`
     - :math:`[34.0, 42.0]^\circ\text{C}`
   * - **STR-07**
     - ``blood_glucose``
     - Subcutaneous continuous glucose monitor
     - Metabolic
     - :math:`0.016\text{ Hz}` (1/min)
     - :math:`[40.0, 400.0]\text{ mg/dL}`
   * - **STR-08**
     - ``perfusion_index``
     - Pulse oximetry pulsatile/non-pulsatile ratio
     - Vascular
     - :math:`1.0 - 10.0\text{ Hz}`
     - :math:`[0.1, 20.0]\%`
   * - **STR-09**
     - ``respiration_rate``
     - Transthoracic bioimpedance band
     - Respiratory
     - :math:`0.2 - 25.0\text{ Hz}`
     - :math:`[4.0, 50.0]\text{ br/min}`
   * - **STR-10**
     - ``motion_artifact_idx``
     - 6-Axis IMU (triaxial accel + gyro)
     - Biomechanical
     - :math:`50.0 - 200.0\text{ Hz}`
     - :math:`[0.0, 1.0]\text{ norm}`
   * - **STR-11**
     - ``ecg_lead2_entropy``
     - Shannon entropy over 250-point window
     - Electrophysiological
     - :math:`1.0\text{ Hz}` derived
     - :math:`[0.0, 8.0]\text{ bits}`
   * - **STR-12**
     - ``galvanic_skin_resp``
     - Dual-electrode epidermal conductance
     - Autonomic Sympathetic
     - :math:`1.0 - 20.0\text{ Hz}`
     - :math:`[0.5, 30.0]\ \mu\text{S}`

3. Mathematical Formulation of Packet Jitter & Buffer Ingestion
===============================================================

Packet Arrival Dynamics & Jitter Model
--------------------------------------
Let packet arrival time for sample :math:`k` across sensor channel :math:`i` be:

.. math::

   t_{i, k} = t_0 + k \cdot \Delta t_i + \delta_{i, k}

where:
- :math:`\Delta t_i = 1 / f_{s, i}` is the nominal inter-sample period.
- :math:`\delta_{i, k} \sim \mathcal{N}(0, \sigma_{\delta}^2)` represents transmission latency jitter over vehicle avionics buses.

FIFO Ring Buffer Overrun Protection
------------------------------------
To prevent buffer overflow during burst telemetry, the intake spool implements a bounded circular buffer of depth :math:`M_{\max} = 10,000`:

.. math::

   \text{Occupancy}(t) = \int_0^t \left( \lambda_{\text{in}}(\tau) - \mu_{\text{drain}}(\tau) \right) d\tau

The system triggers an asynchronous intake drain when :math:`\text{Occupancy}(t) \ge 0.80 \times M_{\max}`, guaranteeing that zero raw packets are dropped prior to the ``ingestion_adapter.py`` ingestion cycle.

4. Ingestion Adapter Coupling & Verification Traceability
=========================================================

1. **Ingestion Interface:** Inbound data dumped into ``01_DATA_VAULT/01_SENSOR_INTAKE`` is spooled as ``.csv`` or ``.jsonl`` packets conforming to ISO-8601 UTC timestamps.
2. **Phase 1 Parsing:** ``ingestion_adapter.py`` automatically discovers, checksums, and catalogs the spool files.
3. **Phase 3 Harmonization:** Transmitted records are projected onto a synchronized :math:`1.0\text{ Hz}` regular grid using ``TelemetrySynchronizer``.
4. **DO-178C DAL C Traceability:** Traced directly to High-Level Requirement ``HLR-BIO-001`` (Continuous Ingestion & Telemetry Sanitization) and Low-Level Requirements ``REQ-INGEST-01`` through ``REQ-INGEST-05``.
