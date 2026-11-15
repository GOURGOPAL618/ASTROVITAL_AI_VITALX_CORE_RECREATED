# ASTROVITAL AI : VITALX CORE (RECREATED V1)
## SUBSYSTEM 01: DATA VAULT — ARTEMIS II MISSION ARCHIVE SPECIFICATION
### ORION CREW CABIN ENVIRONMENTAL TELEMETRY, PDS4 METADATA & THERMAL COUPLING

---

```
================================================================================
 SPECIFICATION DESIGNATOR: ASTROVITAL-SPEC-DATA-ARTEMIS-06
 SUBSYSTEM LOCATION: 01_DATA_VAULT/06_ARTEMIS_II_ARCHIVE/
 ARCHIVAL SOURCE: NASA Planetary Data System (PDS Geosciences / WUSTL)
 FLIGHT MISSION: Artemis II (Crewed Lunar Flyby, Orion Spacecraft)
 CREW CAPACITY: 4 Astronauts (Wiseman, Glover, Koch, Hansen)
 TELEMETRY LOGGERS: Onset HOBO Data Loggers (#1104 & #1105)
 PRIMARY FORMATS: CSV Time-Series, PDS4 Collection Inventory, User Guide PDF (7.3 MB)
 PRIMARY CHANNELS: Temperature (deg C), Relative Humidity (RH %), Dew Point (deg C)
 CERTIFICATION STANDARD: DO-178C LEVEL C (DAL C) / NASA-STD-3001
 AUTHOR & LEAD: TEAM VITALX CORE
 DATE OF RATIFICATION: NOVEMBER 14, 2026
================================================================================
```

---

## 1. Subsystem Scope & Deep Space Operational Flight Context

Artemis II is NASA's first crewed mission beyond low Earth orbit since Apollo 17, sending four astronauts around the Moon aboard the Orion spacecraft. In the deep space cislunar and trans-lunar injection environment, spacecraft thermal control and cabin environmental conditions directly couple with crew thermoregulation, metabolic rate, insensible water loss, and thermal stress.

The `06_ARTEMIS_II_ARCHIVE` supplies high-resolution ($1.0\text{ Hz}$ to $0.1\text{ Hz}$) ambient environmental time-series recorded by Onset HOBO multi-channel dataloggers placed inside the Orion crew cabin. ASTROVITAL leverages this data to:
- Compute ambient-to-core thermal gradients $\Delta T = T_{\text{core}} - T_{\text{cabin}}$.
- Model insensible sweat rate and hydration requirements under varying Relative Humidity ($\text{RH}$).
- Drive environmental compensation in `inno3_signal_stabilizer` and `sanity_gate`.

---

## 2. Directory Tree & Data Artifacts

```
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
```

---

## 3. Data Schema & Physical Channel Attributes

Both HOBO loggers record synchronized environmental parameters:

| Column Header | Data Type | Physical Domain | Engineering Unit | NASA-STD-3001 Nominal Range | Survival Limit Range |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `#` | `Integer` | Monotonic Sequence Index | Counter | $1 \dots N$ | Unbounded |
| `Date-Time (CDT)` | `String` | Central Daylight Time Timestamp | `MM/DD/YY HH:MM:SS` | Mission Elapsed Time | Valid UTC Range |
| `Temperature , deg C`| `Float64` | Cabin Ambient Dry-Bulb Temp | $^\circ\text{C}$ | $[18.0, 24.0]^\circ\text{C}$ | $[10.0, 35.0]^\circ\text{C}$ |
| `RH , %` | `Float64` | Relative Humidity | $\%$ | $[30.0, 60.0]\%$ | $[20.0, 75.0]\%$ |
| `Dew Point , deg C` | `Float64` | Saturation Dew Point Temperature | $^\circ\text{C}$ | $[4.0, 15.0]^\circ\text{C}$ | $[0.0, 25.0]^\circ\text{C}$ |

---

## 4. Biophysical Environmental Coupling Formulations

### 4.1 Magnus-Tetens Vapor Pressure & Dew Point Validation
The dew point $T_{\text{dp}}$ recorded in the HOBO loggers satisfies the Magnus-Tetens thermodynamic relation:

$$\gamma(T, \text{RH}) = \frac{a \cdot T}{b + T} + \ln\left( \frac{\text{RH}}{100} \right)$$

$$T_{\text{dp}} = \frac{b \cdot \gamma(T, \text{RH})}{a - \gamma(T, \text{RH})}$$

where standard empirical constants are $a = 17.27$ and $b = 237.7^\circ\text{C}$.

### 4.2 Astronaut Latent Heat Loss & Thermoregulation
Ambient cabin temperature $T_{\text{cabin}}$ and relative humidity directly regulate human heat dissipation:

$$\dot{Q}_{\text{total}} = \dot{Q}_{\text{rad}} + \dot{Q}_{\text{conv}} + \dot{Q}_{\text{evap}}$$

$$\dot{Q}_{\text{conv}} = h_c \cdot A_{\text{body}} \cdot (T_{\text{skin}} - T_{\text{cabin}})$$

$$\dot{Q}_{\text{evap}} = \dot{m}_{\text{sweat}} \cdot \lambda_{\text{vap}} \cdot \left( 1 - \frac{\text{RH}}{100} \right)$$

When cabin $\text{RH} > 70\%$ or $T_{\text{cabin}} > 27^\circ\text{C}$, evaporative cooling drops by $> 40\%$, elevating crew core temperature $T_{\text{core}}$ and triggering heart rate tachycardia ($+10 - 25\text{ bpm}$).

---

## 5. Ingestion Adapter Extraction Pipeline (Phase 2)

In `02_AI_CORE/01_src/ingestion_adapter.py`, the `ArchiveParser` extracts Artemis II telemetry via `_parse_artemis_orion_hobo()`:

```python
# Extraction Pipeline:
1. Discover 'art002_*_hobo*.csv' in '06_ARTEMIS_II_ARCHIVE'.
2. Parse 'Date-Time (CDT)' with strict datetime parsing.
3. Extract 'Temperature , deg C', 'RH , %', and 'Dew Point , deg C'.
4. Impute missing Dew Point via Magnus formula if absent.
5. Project onto 12-dimensional telemetry space as environmental covariate.
```
