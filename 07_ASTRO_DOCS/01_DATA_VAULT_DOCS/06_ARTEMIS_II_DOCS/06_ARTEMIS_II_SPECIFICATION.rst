.. _astrovital_spec_data_artemis_06:

=======================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
=======================================================
Subsystem 01: Data Vault — Artemis II Mission Archive Specification
-------------------------------------------------------------------
Orion Crew Cabin Environmental Telemetry, PDS4 Metadata & Thermal Coupling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Designator: ASTROVITAL-SPEC-DATA-ARTEMIS-06
:Subsystem Location: ``01_DATA_VAULT/06_ARTEMIS_II_ARCHIVE/``
:Archival Source: NASA Planetary Data System (PDS Geosciences / WUSTL)
:Flight Mission: Artemis II (Crewed Lunar Flyby, Orion Spacecraft)
:Crew Capacity: 4 Astronauts (Wiseman, Glover, Koch, Hansen)
:Telemetry Loggers: Onset HOBO Data Loggers (#1104 & #1105)
:Primary Formats: CSV Time-Series, PDS4 Collection Inventory, User Guide PDF (7.3 MB)
:Primary Channels: Temperature (deg C), Relative Humidity (RH %), Dew Point (deg C)
:Certification Standard: DO-178C Level C (DAL C) / NASA-STD-3001
:Author & Lead: Gourgopal Mohapatra (Team VitalX Core)
:Date of Ratification: November 14, 2026

.. contents:: Table of Contents
   :depth: 3
   :local:

1. Subsystem Scope & Deep Space Operational Flight Context
==========================================================

Artemis II is NASA's first crewed mission beyond low Earth orbit since Apollo 17, sending four astronauts around the Moon aboard the Orion spacecraft. In the deep space cislunar and trans-lunar injection environment, spacecraft thermal control and cabin environmental conditions directly couple with crew thermoregulation, metabolic rate, insensible water loss, and thermal stress.

The ``06_ARTEMIS_II_ARCHIVE`` supplies high-resolution (:math:`1.0\text{ Hz}` to :math:`0.1\text{ Hz}`) ambient environmental time-series recorded by Onset HOBO multi-channel dataloggers placed inside the Orion crew cabin. ASTROVITAL leverages this data to:

- Compute ambient-to-core thermal gradients :math:`\Delta T = T_{\text{core}} - T_{\text{cabin}}`.
- Model insensible sweat rate and hydration requirements under varying Relative Humidity (:math:`\text{RH}`).
- Drive environmental compensation in ``inno3_signal_stabilizer`` and ``sanity_gate``.

2. Directory Tree & Data Artifacts
==================================

.. code-block:: text

   01_DATA_VAULT/06_ARTEMIS_II_ARCHIVE/
   │
   ├── art002_086-162546_111-205046_hobo1104_raw_v01.csv (1,702,078 bytes)
   │   └── Orion Cabin Logger #1104 (Continuous Temp, RH, Dew Point)
   │
   ├── art002_086-162926_111-203826_hobo1105_raw_v01.csv (1,697,492 bytes)
   │   └── Orion Cabin Logger #1105 (Redundant Cabin Thermal Profile)
   │
   ├── collection_data_orion_environment_inventory.csv (204 bytes)
   │   └── NASA PDS4 Collection Inventory Mapping
   │
   └── pds-geosciences.wustl.edu_artemis2_..._artemis2_data_user_guide.pdf (7,304,535 bytes)
       └── Official NASA PDS Artemis II Data User Guide & Instrument Handbook

3. Data Schema & Physical Channel Attributes
============================================

Both HOBO loggers record synchronized environmental parameters:

.. list-table:: Orion Environmental Channels and Safety Envelopes
   :widths: 15 15 25 15 20 20
   :header-rows: 1

   * - Column Header
     - Data Type
     - Physical Domain
     - Unit
     - Nominal Range
     - Survival Range
   * - ``#``
     - ``Integer``
     - Sequence Index
     - Counter
     - :math:`1 \dots N`
     - Unbounded
   * - ``Date-Time (CDT)``
     - ``String``
     - Timestamp
     - ``MM/DD/YY``
     - Mission Elapsed Time
     - Valid UTC
   * - ``Temperature , deg C``
     - ``Float64``
     - Cabin Dry-Bulb Temp
     - :math:`^\circ\text{C}`
     - :math:`[18.0, 24.0]^\circ\text{C}`
     - :math:`[10.0, 35.0]^\circ\text{C}`
   * - ``RH , %``
     - ``Float64``
     - Relative Humidity
     - :math:`\%`
     - :math:`[30.0, 60.0]\%`
     - :math:`[20.0, 75.0]\%`
   * - ``Dew Point , deg C``
     - ``Float64``
     - Dew Point Saturation
     - :math:`^\circ\text{C}`
     - :math:`[4.0, 15.0]^\circ\text{C}`
     - :math:`[0.0, 25.0]^\circ\text{C}`

4. Biophysical Environmental Coupling Formulations
==================================================

Magnus-Tetens Vapor Pressure & Dew Point Validation
---------------------------------------------------
The dew point :math:`T_{\text{dp}}` recorded in the HOBO loggers satisfies the Magnus-Tetens thermodynamic relation:

.. math::

   \gamma(T, \text{RH}) = \frac{a \cdot T}{b + T} + \ln\left( \frac{\text{RH}}{100} \right)

.. math::

   T_{\text{dp}} = \frac{b \cdot \gamma(T, \text{RH})}{a - \gamma(T, \text{RH})}

where standard empirical constants are :math:`a = 17.27` and :math:`b = 237.7^\circ\text{C}`.

Astronaut Latent Heat Loss & Thermoregulation
---------------------------------------------
Ambient cabin temperature :math:`T_{\text{cabin}}` and relative humidity directly regulate human heat dissipation:

.. math::

   \dot{Q}_{\text{total}} = \dot{Q}_{\text{rad}} + \dot{Q}_{\text{conv}} + \dot{Q}_{\text{evap}}

.. math::

   \dot{Q}_{\text{conv}} = h_c \cdot A_{\text{body}} \cdot (T_{\text{skin}} - T_{\text{cabin}})

.. math::

   \dot{Q}_{\text{evap}} = \dot{m}_{\text{sweat}} \cdot \lambda_{\text{vap}} \cdot \left( 1 - \frac{\text{RH}}{100} \right)

When cabin :math:`\text{RH} > 70\%` or :math:`T_{\text{cabin}} > 27^\circ\text{C}`, evaporative cooling drops by :math:`> 40\%`, elevating crew core temperature :math:`T_{\text{core}}` and triggering heart rate tachycardia (:math:`+10 - 25\text{ bpm}`).

5. Ingestion Adapter Extraction Pipeline (Phase 2)
==================================================

In ``02_AI_CORE/01_src/ingestion_adapter.py``, the ``ArchiveParser`` extracts Artemis II telemetry via ``_parse_artemis_orion_hobo()``:

.. code-block:: python

   # Extraction Pipeline:
   1. Discover 'art002_*_hobo*.csv' in '06_ARTEMIS_II_ARCHIVE'.
   2. Parse 'Date-Time (CDT)' with strict datetime parsing.
   3. Extract 'Temperature , deg C', 'RH , %', and 'Dew Point , deg C'.
   4. Impute missing Dew Point via Magnus formula if absent.
   5. Project onto 12-dimensional telemetry space as environmental covariate.
