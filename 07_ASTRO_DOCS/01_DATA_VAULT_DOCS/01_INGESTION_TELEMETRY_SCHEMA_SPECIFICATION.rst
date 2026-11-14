.. _astrovital_spec_data_12d:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — 12-Dimensional Telemetry Schema Specification
------------------------------------------------------------------------
Flight-Ready Telemetry Definition & Physical Boundary Constraints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-12D
:Subsystem Location: ``01_DATA_VAULT/`` & ``02_AI_CORE/01_src/ingestion_adapter.py``
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001
:Data Schema Vector: :math:`\mathbf{X}(t) \in \mathbb{R}^{12}` (:math:`N \times 12` float64 Tensor)
:Architect & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Scope & Aeronautical Flight Context
======================================

The standardized **12-Dimensional Telemetry Vector** :math:`\mathbf{X}(t) \in \mathbb{R}^{12}` is the fundamental data contract across the entire ASTROVITAL decision support architecture. Derived from multi-mission operational flight archives (Artemis II Orion multi-channel sensors, Space Shuttle DSO cardiovascular profiles, and Apollo 7 clinical monitoring), this schema harmonizes disparate sampling rates, analog sensor variations, and temporal gaps into a unified, cryptographically auditable time-series representation.

2. 12-Dimensional Feature Definition & Physical Bounds
======================================================

Under DO-178C Level C defensive engineering, every biological parameter is bounded by strict, non-negotiable physical envelopes:

.. math::

   \mathbf{X}(t) = \begin{bmatrix} x_1(t) & x_2(t) & \dots & x_{12}(t) \end{bmatrix}^T

.. list-table:: 12-Dimensional Flight Telemetry Features
   :widths: 10 25 35 15 15
   :header-rows: 1

   * - Index
     - Feature Name
     - Description & Clinical Significance
     - Unit
     - Valid Range
   * - **0**
     - ``heart_rate``
     - Cardiac chronotropic frequency; cardiovascular strain
     - :math:`\text{bpm}`
     - :math:`[30.0, 220.0]`
   * - **1**
     - ``blood_pressure_systolic``
     - Peak arterial pressure during left ventricular ejection (SBP)
     - :math:`\text{mmHg}`
     - :math:`[70.0, 240.0]`
   * - **2**
     - ``blood_pressure_diastolic``
     - Minimum arterial pressure during ventricular diastole (DBP)
     - :math:`\text{mmHg}`
     - :math:`[40.0, 140.0]`
   * - **3**
     - ``rmssd``
     - Root Mean Square of Successive RR interval Differences (vagal tone)
     - :math:`\text{ms}`
     - :math:`[5.0, 250.0]`
   * - **4**
     - ``spo2``
     - Functional arterial blood oxygen saturation (hypoxia indicator)
     - :math:`\%`
     - :math:`[50.0, 100.0]`
   * - **5**
     - ``core_temp``
     - Core body temperature (:math:`T_c`)
     - :math:`^\circ\text{C}`
     - :math:`[34.0, 42.0]`
   * - **6**
     - ``blood_glucose``
     - Circulating blood glucose concentration (metabolic fuel)
     - :math:`\text{mg/dL}`
     - :math:`[40.0, 400.0]`
   * - **7**
     - ``perfusion_index``
     - Ratio of pulsatile to non-pulsatile blood flow
     - :math:`\%`
     - :math:`[0.1, 20.0]`
   * - **8**
     - ``respiration_rate``
     - Respiratory ventilatory frequency
     - :math:`\text{br/min}`
     - :math:`[4.0, 50.0]`
   * - **9**
     - ``motion_artifact_index``
     - Triaxial IMU accelerometer-derived kinematic jerk
     - Normalized
     - :math:`[0.0, 1.0]`
   * - **10**
     - ``ecg_lead2_entropy``
     - Shannon spectral entropy of Lead II ECG
     - :math:`\text{bits}`
     - :math:`[0.0, 8.0]`
   * - **11**
     - ``galvanic_skin_response``
     - Sympathetic autonomic electrodermal conductance
     - :math:`\mu\text{S}`
     - :math:`[0.5, 30.0]`

3. Mathematical Invariants & Hemodynamic Constraints
====================================================

Pulse Pressure Constraint
-------------------------
.. math::

   \Delta P(t) = x_{\text{SBP}}(t) - x_{\text{DBP}}(t) \ge 15.0\text{ mmHg}

Mean Arterial Pressure (MAP)
----------------------------
.. math::

   \text{MAP}(t) = x_{\text{DBP}}(t) + \frac{1}{3} \cdot \left( x_{\text{SBP}}(t) - x_{\text{DBP}}(t) \right)
