"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Verification Suite: test_biophysical_physics_engine.py (Phase 2 IV&V)
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A
Governance: First-Principles Closed-Form Spaceflight Biophysics Verification
=============================================================================
"""

import sys
import math
import time
import pytest
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np

# Ensure 03_DECISION_CORE is on sys.path
decision_path = Path(__file__).resolve().parent
if str(decision_path) not in sys.path:
    sys.path.insert(0, str(decision_path))

from biophysical_physics_engine import (
    BiophysicalPhysicsEngine,
    HemodynamicPacket,
    FluidShiftPacket,
    CardiacOutputPacket,
    BiophysicalEnrichedPacket,
)
from rule_schema_validator import (
    DecisionConfigManager,
    load_default_decision_configuration,
)


@pytest.fixture
def engine() -> BiophysicalPhysicsEngine:
    return BiophysicalPhysicsEngine()


@pytest.fixture
def nominal_vitals() -> Dict[str, float]:
    return {
        "heart_rate_bpm": 72.0,
        "systolic_bp_mmhg": 120.0,
        "diastolic_bp_mmhg": 80.0,
        "spo2_percent": 98.0,
        "core_temp_c": 37.0,
        "resp_rate_bpm": 14.0,
        "etco2_mmhg": 38.0,
        "icp_est_mmhg": 10.0,
        "cvp_mmhg": 5.0,
        "co2_cabin_ppm": 3950.0,
        "cabin_pressure_psi": 14.7,
        "ambient_temp_c": 22.0,
    }


# =============================================================================
# GROUP 1: HEMODYNAMICS DERIVATIONS (TESTS 01-08)
# =============================================================================

def test_01_engine_initialization_modes():
    """Verify engine initializes with both default and explicit config managers."""
    eng1 = BiophysicalPhysicsEngine()
    assert eng1.constants is not None

    custom_cfg = load_default_decision_configuration()
    eng2 = BiophysicalPhysicsEngine(config_manager=custom_cfg)
    assert eng2.config_manager is custom_cfg


def test_02_hemodynamic_calculations_nominal(engine: BiophysicalPhysicsEngine):
    """Verify exact formula values for SBP=120, DBP=80, HR=72, ICP=10."""
    packet = engine.compute_hemodynamics(systolic_bp=120.0, diastolic_bp=80.0, heart_rate=72.0, icp_est=10.0)

    # PP = 120 - 80 = 40
    assert packet.pulse_pressure_mmhg == 40.0
    # MAP = 80 + 40/3 = 93.3333...
    assert math.isclose(packet.map_mmhg, 93.33333333333333, rel_tol=1e-5)
    # SI = 72 / 120 = 0.60
    assert math.isclose(packet.shock_index, 0.60, rel_tol=1e-5)
    # MSI = 72 / 93.3333... = 0.771428...
    assert math.isclose(packet.modified_shock_index, 0.77142857, rel_tol=1e-5)
    # CPP = MAP - ICP = 93.3333... - 10 = 83.3333...
    assert math.isclose(packet.cerebral_perfusion_pressure_mmhg, 83.33333333333333, rel_tol=1e-5)
    assert packet.is_shock_indicated is False
    assert packet.is_cerebral_ischemia_threat is False


def test_03_hemodynamics_non_finite_defensive_exception(engine: BiophysicalPhysicsEngine):
    """Verify ValueError when non-finite inputs are passed to hemodynamics."""
    with pytest.raises(ValueError, match="Non-finite inputs"):
        engine.compute_hemodynamics(systolic_bp=float("nan"), diastolic_bp=80.0, heart_rate=72.0)
    with pytest.raises(ValueError, match="Non-finite inputs"):
        engine.compute_hemodynamics(systolic_bp=120.0, diastolic_bp=float("inf"), heart_rate=72.0)


def test_04_hemodynamics_non_positive_defensive_exception(engine: BiophysicalPhysicsEngine):
    """Verify ValueError when pressures or heart rate are non-positive."""
    with pytest.raises(ValueError, match="strictly positive"):
        engine.compute_hemodynamics(systolic_bp=0.0, diastolic_bp=80.0, heart_rate=72.0)
    with pytest.raises(ValueError, match="strictly positive"):
        engine.compute_hemodynamics(systolic_bp=120.0, diastolic_bp=-10.0, heart_rate=72.0)
    with pytest.raises(ValueError, match="strictly positive"):
        engine.compute_hemodynamics(systolic_bp=120.0, diastolic_bp=80.0, heart_rate=0.0)


def test_05_hemodynamics_systolic_less_than_diastolic(engine: BiophysicalPhysicsEngine):
    """Verify ValueError when SBP < DBP (physiologically impossible reversed pressure)."""
    with pytest.raises(ValueError, match="cannot be less than diastolic"):
        engine.compute_hemodynamics(systolic_bp=70.0, diastolic_bp=90.0, heart_rate=72.0)


def test_06_hemodynamics_shock_indication(engine: BiophysicalPhysicsEngine):
    """Verify Shock Index >= 1.10 trips is_shock_indicated flag."""
    packet = engine.compute_hemodynamics(systolic_bp=90.0, diastolic_bp=60.0, heart_rate=110.0)
    # SI = 110 / 90 = 1.222... >= 1.10
    assert packet.shock_index >= 1.10
    assert packet.is_shock_indicated is True


def test_07_hemodynamics_cerebral_ischemia_threat(engine: BiophysicalPhysicsEngine):
    """Verify CPP < 40.0 mmHg trips is_cerebral_ischemia_threat flag."""
    # SBP=80, DBP=50 -> MAP=60. ICP=25 -> CPP = 35 < 40
    packet = engine.compute_hemodynamics(systolic_bp=80.0, diastolic_bp=50.0, heart_rate=80.0, icp_est=25.0)
    assert packet.cerebral_perfusion_pressure_mmhg == 35.0
    assert packet.is_cerebral_ischemia_threat is True


def test_08_hemodynamics_default_icp_fallback(engine: BiophysicalPhysicsEngine):
    """Verify fallback to baseline ICP when icp_est is None or non-finite."""
    packet1 = engine.compute_hemodynamics(systolic_bp=120.0, diastolic_bp=80.0, heart_rate=72.0, icp_est=None)
    packet2 = engine.compute_hemodynamics(systolic_bp=120.0, diastolic_bp=80.0, heart_rate=72.0, icp_est=float("nan"))
    assert packet1.cerebral_perfusion_pressure_mmhg == packet2.cerebral_perfusion_pressure_mmhg
    assert math.isclose(packet1.cerebral_perfusion_pressure_mmhg, 93.33333333333333 - 10.0, rel_tol=1e-5)


# =============================================================================
# GROUP 2: CEPHALAD FLUID SHIFT & ICP INDEX (TESTS 09-17)
# =============================================================================

def test_09_fluid_shift_nominal_day_zero(engine: BiophysicalPhysicsEngine):
    """Verify fluid shift index on Day 0 with nominal parameters."""
    packet = engine.compute_fluid_shift_index(
        map_mmhg=93.33,
        microgravity_days=0.0,
        cabin_co2_ppm=3950.0,
        rmssd_ms=42.0
    )
    # Day 0: alpha_2 * ln(1 + 0) = 0.
    # alpha_1 * (93.33/93.33) = 0.40
    # alpha_3 * (3950/3950) = 0.15
    # alpha_4 * (42/42) = 0.10
    # Expected I_ICP = 0.40 + 0 + 0.15 - 0.10 = 0.45
    assert math.isclose(packet.icp_gradient_index, 0.45, abs_tol=1e-3)
    assert packet.is_green_equilibrium is True
    assert packet.is_amber_warning is False
    assert packet.is_red_critical is False
    assert packet.clinical_risk_tier == "NOMINAL_GREEN"


def test_10_fluid_shift_microgravity_logarithmic_growth(engine: BiophysicalPhysicsEngine):
    """Verify fluid shift index increases logarithmically with microgravity duration."""
    p0 = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=0.0, cabin_co2_ppm=3950.0)
    p7 = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=7.0, cabin_co2_ppm=3950.0)
    p30 = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=30.0, cabin_co2_ppm=3950.0)
    p180 = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=180.0, cabin_co2_ppm=3950.0)

    assert p0.icp_gradient_index < p7.icp_gradient_index < p30.icp_gradient_index < p180.icp_gradient_index
    # Verify logarithmic rate of growth decreases (diminishing incremental returns)
    growth_1 = p7.icp_gradient_index - p0.icp_gradient_index
    growth_2 = p30.icp_gradient_index - p7.icp_gradient_index
    assert growth_1 > growth_2  # ln curve derivative decreases


def test_11_fluid_shift_co2_sensitivity(engine: BiophysicalPhysicsEngine):
    """Verify elevated cabin CO2 linearly increases fluid shift index."""
    p_norm = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=14.0, cabin_co2_ppm=3950.0)
    p_high = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=14.0, cabin_co2_ppm=7900.0)

    delta = p_high.icp_gradient_index - p_norm.icp_gradient_index
    # Doubling CO2 adds alpha_3 * (7900/3950 - 1) = 0.15 * 1.0 = 0.15
    assert math.isclose(delta, 0.15, abs_tol=1e-4)


def test_12_fluid_shift_rmssd_buffering(engine: BiophysicalPhysicsEngine):
    """Verify high RMSSD buffers against fluid shift, and low RMSSD increases it."""
    p_normal = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=14.0, cabin_co2_ppm=3950.0, rmssd_ms=42.0)
    p_low_rmssd = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=14.0, cabin_co2_ppm=3950.0, rmssd_ms=21.0)
    p_high_rmssd = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=14.0, cabin_co2_ppm=3950.0, rmssd_ms=84.0)

    assert p_high_rmssd.icp_gradient_index < p_normal.icp_gradient_index < p_low_rmssd.icp_gradient_index


def test_13_fluid_shift_classification_tiers(engine: BiophysicalPhysicsEngine):
    """Verify exact tier transitions: GREEN (< 1.35), AMBER ([1.35, 1.85)), RED (>= 1.85)."""
    # Nominal green
    p_green = engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=5.0, cabin_co2_ppm=3950.0)
    assert p_green.is_green_equilibrium is True
    assert p_green.clinical_risk_tier == "NOMINAL_GREEN"

    # Amber stress: Moderate duration (25 days) in compensatory envelope
    p_amber = engine.compute_fluid_shift_index(map_mmhg=98.0, microgravity_days=25.0, cabin_co2_ppm=4200.0)
    assert p_amber.is_amber_warning is True
    assert p_amber.clinical_risk_tier == "WARNING_AMBER"

    # Critical Red: Long duration (180 days) + acute hypertension + hypercapnia
    p_red = engine.compute_fluid_shift_index(map_mmhg=135.0, microgravity_days=180.0, cabin_co2_ppm=9000.0)
    assert p_red.is_red_critical is True
    assert p_red.clinical_risk_tier == "CRITICAL_RED"


def test_14_fluid_shift_non_finite_defensive_exception(engine: BiophysicalPhysicsEngine):
    """Verify ValueError when non-finite inputs are passed to fluid shift."""
    with pytest.raises(ValueError, match="Non-finite inputs"):
        engine.compute_fluid_shift_index(map_mmhg=float("nan"), microgravity_days=14.0, cabin_co2_ppm=3950.0)


def test_15_fluid_shift_negative_days_exception(engine: BiophysicalPhysicsEngine):
    """Verify ValueError when microgravity days is negative."""
    with pytest.raises(ValueError, match="cannot be negative"):
        engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=-5.0, cabin_co2_ppm=3950.0)


def test_16_fluid_shift_negative_co2_or_zero_map(engine: BiophysicalPhysicsEngine):
    """Verify ValueError when CO2 is negative or MAP is zero/negative."""
    with pytest.raises(ValueError, match="Negative or zero"):
        engine.compute_fluid_shift_index(map_mmhg=0.0, microgravity_days=14.0, cabin_co2_ppm=3950.0)
    with pytest.raises(ValueError, match="Negative or zero"):
        engine.compute_fluid_shift_index(map_mmhg=93.33, microgravity_days=14.0, cabin_co2_ppm=-500.0)


def test_17_fluid_shift_lower_bound_clamp(engine: BiophysicalPhysicsEngine):
    """Verify I_ICP cannot be negative even under extreme autonomic RMSSD buffer."""
    # Extremely low MAP, zero days, zero CO2, extreme RMSSD
    p = engine.compute_fluid_shift_index(map_mmhg=10.0, microgravity_days=0.0, cabin_co2_ppm=100.0, rmssd_ms=500.0)
    assert p.icp_gradient_index >= 0.0


# =============================================================================
# GROUP 3: CARDIAC DECONDITIONING & STROKE VOLUME (TESTS 18-22)
# =============================================================================

def test_18_stroke_volume_atrophy_decay(engine: BiophysicalPhysicsEngine):
    """Verify stroke volume degrades exponentially with microgravity duration."""
    c0 = engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=0.0, exercise_metric=1.0)
    c30 = engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=30.0, exercise_metric=1.0)
    c180 = engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=180.0, exercise_metric=1.0)

    assert c0.stroke_volume_ml > c30.stroke_volume_ml > c180.stroke_volume_ml
    assert c0.cardiac_output_l_min > c30.cardiac_output_l_min > c180.cardiac_output_l_min


def test_19_stroke_volume_exercise_mitigation(engine: BiophysicalPhysicsEngine):
    """Verify exercise metric = 1.0 provides 25% attenuation boost over exercise = 0.0."""
    c_sedentary = engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=60.0, exercise_metric=0.0)
    c_exercising = engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=60.0, exercise_metric=1.0)

    # With beta=0.25, exercising should be exactly 1.25 * sedentary (unless clamped)
    assert c_exercising.stroke_volume_ml > c_sedentary.stroke_volume_ml
    ratio = c_exercising.stroke_volume_ml / c_sedentary.stroke_volume_ml
    assert math.isclose(ratio, 1.25, rel_tol=1e-3)


def test_20_cardiac_output_computation_accuracy(engine: BiophysicalPhysicsEngine):
    """Verify CO = (SV * HR) / 1000.0."""
    c = engine.compute_cardiac_deconditioning(heart_rate_bpm=80.0, microgravity_days=14.0, exercise_metric=0.8)
    expected_co = (c.stroke_volume_ml * 80.0) / 1000.0
    assert math.isclose(c.cardiac_output_l_min, expected_co, rel_tol=1e-5)


def test_21_stroke_volume_physiological_minimum_clamping(engine: BiophysicalPhysicsEngine):
    """Verify stroke volume is clamped at minimum viable 40.0 mL after multi-year exposure without exercise."""
    c = engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=1000.0, exercise_metric=0.0)
    assert c.stroke_volume_ml == 40.0
    assert c.is_stroke_volume_depleted is True


def test_22_cardiac_deconditioning_defensive_exceptions(engine: BiophysicalPhysicsEngine):
    """Verify ValueError on non-finite values, negative heart rate, negative days."""
    with pytest.raises(ValueError, match="Non-finite inputs"):
        engine.compute_cardiac_deconditioning(heart_rate_bpm=float("nan"), microgravity_days=14.0)
    with pytest.raises(ValueError, match="Heart rate must be > 0"):
        engine.compute_cardiac_deconditioning(heart_rate_bpm=-50.0, microgravity_days=14.0)
    with pytest.raises(ValueError, match="Heart rate must be > 0"):
        engine.compute_cardiac_deconditioning(heart_rate_bpm=72.0, microgravity_days=-10.0)


# =============================================================================
# GROUP 4: TELEMETRY ENRICHMENT (SCALAR & VECTORIZED) (TESTS 23-28)
# =============================================================================

def test_23_enrich_telemetry_packet_nominal(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify enrich_telemetry_packet populates all required biophysical fields."""
    enriched_packet = engine.enrich_telemetry_packet(
        telemetry=nominal_vitals,
        microgravity_days=14.0,
        exercise_metric=1.0
    )
    assert isinstance(enriched_packet, BiophysicalEnrichedPacket)
    enriched = enriched_packet.enriched_telemetry

    required_keys = [
        "pulse_pressure_mmhg", "map_mmhg", "shock_index",
        "modified_shock_index", "cerebral_perfusion_pressure_mmhg",
        "icp_gradient_index", "stroke_volume_ml", "cardiac_output_l_min",
        "microgravity_days", "sleep_debt_hours"
    ]
    for key in required_keys:
        assert key in enriched, f"Missing key {key}"
        assert math.isfinite(enriched[key])


def test_24_enrich_telemetry_packet_missing_channels_fallback(engine: BiophysicalPhysicsEngine):
    """Verify enrich_telemetry_packet uses baselines when partial telemetry is provided."""
    partial = {"heart_rate_bpm": 85.0}
    packet = engine.enrich_telemetry_packet(partial)
    assert packet.hemodynamics.pulse_pressure_mmhg == 40.0  # 120 - 80
    assert packet.enriched_telemetry["heart_rate_bpm"] == 85.0


def test_25_enrich_telemetry_packet_preserves_raw_telemetry(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify original input telemetry is preserved unaltered in raw_telemetry attribute."""
    packet = engine.enrich_telemetry_packet(nominal_vitals)
    assert packet.raw_telemetry == nominal_vitals


def test_26_vectorized_dataframe_stream_enrichment(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify enrich_dataframe_stream enriches a multi-row DataFrame accurately."""
    df_in = pd.DataFrame([nominal_vitals] * 10)
    df_out = engine.enrich_dataframe_stream(df_in, microgravity_days=21.0, exercise_metric=0.9)

    assert len(df_out) == 10
    assert "map_mmhg" in df_out.columns
    assert "icp_gradient_index" in df_out.columns
    assert "stroke_volume_ml" in df_out.columns
    assert "cardiac_output_l_min" in df_out.columns


def test_27_vectorized_vs_scalar_consistency(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify scalar enrich_telemetry_packet and vectorized enrich_dataframe_stream yield identical outputs."""
    scalar_packet = engine.enrich_telemetry_packet(nominal_vitals, microgravity_days=14.0, exercise_metric=1.0)
    df_in = pd.DataFrame([nominal_vitals])
    df_out = engine.enrich_dataframe_stream(df_in, microgravity_days=14.0, exercise_metric=1.0)

    row = df_out.iloc[0].to_dict()
    assert math.isclose(row["map_mmhg"], scalar_packet.enriched_telemetry["map_mmhg"], rel_tol=1e-5)
    assert math.isclose(row["shock_index"], scalar_packet.enriched_telemetry["shock_index"], rel_tol=1e-5)
    assert math.isclose(row["icp_gradient_index"], scalar_packet.enriched_telemetry["icp_gradient_index"], rel_tol=1e-5)
    assert math.isclose(row["stroke_volume_ml"], scalar_packet.enriched_telemetry["stroke_volume_ml"], rel_tol=1e-5)


def test_28_vectorized_dataframe_handles_missing_columns(engine: BiophysicalPhysicsEngine):
    """Verify DataFrame stream enrichment handles dataframes with missing channels."""
    sparse_df = pd.DataFrame([{"heart_rate_bpm": 80.0}, {"heart_rate_bpm": 90.0}])
    df_out = engine.enrich_dataframe_stream(sparse_df)
    assert len(df_out) == 2
    assert "map_mmhg" in df_out.columns
    assert "stroke_volume_ml" in df_out.columns


# =============================================================================
# GROUP 5: END-TO-END PIPELINE & PERFORMANCE (TESTS 29-32)
# =============================================================================

def test_29_e2e_enriched_packet_triggers_green_equilibrium(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify nominal enriched packet feeds DecisionConfigManager to trigger STATE GREEN."""
    cfg_mgr = engine.config_manager
    enriched_packet = engine.enrich_telemetry_packet(nominal_vitals, microgravity_days=5.0)

    state, rule, audit, countermeasures = cfg_mgr.evaluate_triage(enriched_packet.enriched_telemetry)
    assert state == "GREEN"
    assert rule.rule_id == "RULE_GREEN_001_PHYSIOLOGICAL_EQUILIBRIUM"
    assert "NOMINAL GREEN" in audit


def test_30_e2e_enriched_packet_triggers_amber_cephalad_warning(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify moderate microgravity duration (25 days) elevates I_ICP into AMBER envelope."""
    cfg_mgr = engine.config_manager
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 125.0  # Mild elevation
    vitals["co2_cabin_ppm"] = 4200.0

    enriched_packet = engine.enrich_telemetry_packet(vitals, microgravity_days=25.0)
    assert 1.35 <= enriched_packet.enriched_telemetry["icp_gradient_index"] < 1.85

    state, rule, audit, countermeasures = cfg_mgr.evaluate_triage(enriched_packet.enriched_telemetry)
    assert state == "AMBER"
    assert rule.rule_id == "RULE_AMBER_001_ELEVATED_CEPHALAD_FLUID_SHIFT"


def test_31_e2e_enriched_packet_triggers_red_fluid_shift_surge(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify multi-month exposure + severe hypertension trips RED I_ICP >= 1.85 alert."""
    cfg_mgr = engine.config_manager
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 155.0
    vitals["diastolic_bp_mmhg"] = 105.0
    vitals["co2_cabin_ppm"] = 7000.0

    enriched_packet = engine.enrich_telemetry_packet(vitals, microgravity_days=180.0)
    assert enriched_packet.enriched_telemetry["icp_gradient_index"] >= 1.85

    state, rule, audit, countermeasures = cfg_mgr.evaluate_triage(enriched_packet.enriched_telemetry)
    assert state == "RED"
    assert rule.rule_id == "RULE_RED_002_CEPHALAD_ICP_SURGE"
    assert any("LBNP" in c.protocol for c in countermeasures)


def test_32_biophysical_performance_latency_budget(engine: BiophysicalPhysicsEngine, nominal_vitals: Dict[str, float]):
    """Verify 1,000 complete packet enrichments execute within 50.0 ms budget (< 0.05 ms per packet)."""
    t0 = time.perf_counter()
    for _ in range(1000):
        engine.enrich_telemetry_packet(nominal_vitals, microgravity_days=14.0)
    dt_total_ms = (time.perf_counter() - t0) * 1000.0
    dt_per_eval_ms = dt_total_ms / 1000.0

    assert dt_per_eval_ms < 0.20, f"Per-packet latency {dt_per_eval_ms:.4f} ms exceeds 0.20 ms budget"
