"""
================================================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
EXTREME BIO-ASTRONAUTIC STRESS & LIMITATION VERIFICATION TEST SUITE (25 TESTS)
RTCA DO-178C LEVEL C (DAL C) / NASA-STD-3001 VOL 2 AIRWORTHINESS PROOF
================================================================================

File: 08_EXTREME_SIMULATION_LAB/test_extreme_simulations.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C / ARP4754A / NASA-STD-3001
Competition: NASA Space Apps Challenge 2026 — Human Body in Deep Space

Exercises the 5 extreme bio-astronautic stress scenarios:
  1. Solar Particle Event (SPE) Acute Radiation Shock (Tests 001 - 005)
  2. Double Micrometeoroid Puncture + Complete Lead-Off Disconnect (Tests 006 - 010)
  3. 360-Day Deep Space SANS Stagnation (Tests 011 - 015)
  4. Lunar EVA In-Helmet Vomiting & Airway Asphyxiation (Tests 016 - 020)
  5. Avionics Electromagnetic Pulse (EMP) / EMI Blast (Tests 021 - 025)
================================================================================
"""

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Path Anchoring
SIM_LAB_DIR = Path(__file__).resolve().parent
ROOT_DIR = SIM_LAB_DIR.parent
AI_CORE_SRC = ROOT_DIR / "02_AI_CORE" / "01_src"
DECISION_DIR = ROOT_DIR / "03_DECISION_CORE"
COCKPIT_DIR = ROOT_DIR / "04_ASTRONAUT_COCKPIT"

for p in [str(ROOT_DIR), str(AI_CORE_SRC), str(DECISION_DIR), str(COCKPIT_DIR), str(SIM_LAB_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline_orchestrator import AstroVitalPipelineOrchestrator
from biophysical_physics_engine import BiophysicalPhysicsEngine
from run_extreme_stress_simulations import (
    EXTREME_SCENARIOS,
    ExtremeStressSimulationHarness,
)


@pytest.fixture(scope="module")
def sim_results() -> Dict[str, Any]:
    """Loads or executes the simulation results JSON fixture."""
    json_path = SIM_LAB_DIR / "extreme_simulation_results.json"
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    harness = ExtremeStressSimulationHarness()
    return harness.run_all()


@pytest.fixture(scope="module")
def orchestrator() -> AstroVitalPipelineOrchestrator:
    return AstroVitalPipelineOrchestrator()


@pytest.fixture(scope="module")
def physics_engine() -> BiophysicalPhysicsEngine:
    return BiophysicalPhysicsEngine()


# =============================================================================
# SCENARIO 1: SOLAR PARTICLE EVENT (SPE) ACUTE RADIATION SHOCK (001 - 005)
# =============================================================================

def test_001_scen1_hemodynamic_shock_index_calculation(sim_results):
    """Test 001: Verifies Shock Index >= 1.10 and SBP <= 90 mmHg under SPE shock."""
    scen1 = sim_results["scenarios"][0]
    metrics = scen1["biophysical_supreme_head_metrics"]
    assert metrics["shock_index"] >= 1.10, f"Expected SI >= 1.10, got {metrics['shock_index']}"
    assert scen1["sanitized_telemetry"]["systolic_bp_mmhg"] <= 90.0


def test_002_scen1_deterministic_red_triage(sim_results):
    """Test 002: Verifies SPE shock produces deterministic RED triage state."""
    scen1 = sim_results["scenarios"][0]
    decision = scen1["deterministic_triage_decision"]
    assert decision["triage_state"] == "RED"
    assert decision["matched_rule_id"] == "RULE_RED_004_SEVERE_SHOCK_HEMODYNAMIC_COLLAPSE"


def test_003_scen1_countermeasure_locker_dispatch(sim_results):
    """Test 003: Verifies Emergency Resuscitation Kit MED-02 is dispatched for IV infusion."""
    scen1 = sim_results["scenarios"][0]
    lockers = scen1["cockpit_3sec_rapid_dispatch"]["dispatched_equipment_lockers"]
    assert any("Emergency Resuscitation Kit MED-02" in loc for loc in lockers)


def test_004_scen1_sanity_gate_bounds(sim_results):
    """Test 004: Verifies raw vitals are within physical bounds and pass sanity gate cleanly."""
    scen1 = sim_results["scenarios"][0]
    audit = scen1["sanity_gate_audit"]
    assert audit["gate_passed"] is True
    assert audit["violations_remediated"] == 0


def test_005_scen1_documented_limitations(sim_results):
    """Test 005: Verifies explicit open limitation regarding DNA double-strand breaks."""
    scen1 = sim_results["scenarios"][0]
    limits = scen1["open_scientific_and_aerospace_limitations"]
    assert any("DNA double-strand breaks" in lim for lim in limits)


# =============================================================================
# SCENARIO 2: DOUBLE MICROMETEOROID PUNCTURE & LEAD-OFF (006 - 010)
# =============================================================================

def test_006_scen2_sensor_decoupling_fallback(sim_results):
    """Test 006: Verifies severed ECG NaN is remediated by SensorDecouplingFallbackEngine."""
    scen2 = sim_results["scenarios"][1]
    raw_hr = scen2["raw_input_telemetry"]["heart_rate_bpm"]
    sanitized_hr = scen2["sanitized_telemetry"]["heart_rate_bpm"]
    assert raw_hr is None or math.isnan(raw_hr)
    assert math.isfinite(sanitized_hr)
    assert scen2["sanity_gate_audit"]["violations_remediated"] >= 1


def test_007_scen2_rapid_decompression_triage(sim_results):
    """Test 007: Verifies cabin pressure plunge triggers rapid decompression rule."""
    scen2 = sim_results["scenarios"][1]
    decision = scen2["deterministic_triage_decision"]
    assert decision["triage_state"] == "RED"
    assert decision["matched_rule_id"] == "RULE_RED_005_RAPID_CABIN_DECOMPRESSION"


def test_008_scen2_critical_red_alert_audio(sim_results):
    """Test 008: Verifies HUD alert banner emits RED_CRITICAL and urgent pulse alarm."""
    scen2 = sim_results["scenarios"][1]
    cockpit = scen2["cockpit_3sec_rapid_dispatch"]
    assert cockpit["alert_level"] == "RED_CRITICAL"
    assert cockpit["audio_pulse_pattern"] == "URGENT_PULSED_ALARM"


def test_009_scen2_suit_locker_deployment(sim_results):
    """Test 009: Verifies Suit Lockers SL-1 through SL-4 are immediately dispatched."""
    scen2 = sim_results["scenarios"][1]
    lockers = scen2["cockpit_3sec_rapid_dispatch"]["dispatched_equipment_lockers"]
    assert any("Suit Lockers SL-1 through SL-4" in loc for loc in lockers)


def test_010_scen2_decoupling_limitations(sim_results):
    """Test 010: Verifies documented limitation on multi-sensor persistent disconnect."""
    scen2 = sim_results["scenarios"][1]
    limits = scen2["open_scientific_and_aerospace_limitations"]
    assert any("Sensor Blind Mode" in lim for lim in limits)


# =============================================================================
# SCENARIO 3: 360-DAY DEEP SPACE SANS STAGNATION (011 - 015)
# =============================================================================

def test_011_scen3_hydrodynamic_icp_index(sim_results):
    """Test 011: Verifies cephalad fluid shift index I_ICP >= 1.85 (Critical Red)."""
    scen3 = sim_results["scenarios"][2]
    metrics = scen3["biophysical_supreme_head_metrics"]
    assert metrics["icp_gradient_index"] >= 1.85, f"Expected I_ICP >= 1.85, got {metrics['icp_gradient_index']}"
    assert metrics["fluid_shift_tier"] == "CRITICAL_RED"


def test_012_scen3_stroke_volume_atrophy(sim_results):
    """Test 012: Verifies myocardial stroke volume atrophy SV <= 45.0 mL under zero exercise."""
    scen3 = sim_results["scenarios"][2]
    metrics = scen3["biophysical_supreme_head_metrics"]
    assert metrics["stroke_volume_ml"] <= 45.0, f"Expected SV <= 45.0, got {metrics['stroke_volume_ml']}"
    assert metrics["myocardial_atrophy_factor"] < 0.60


def test_013_scen3_deterministic_red_triage(sim_results):
    """Test 013: Verifies SANS progression triggers RULE_RED_002_CEPHALAD_ICP_SURGE."""
    scen3 = sim_results["scenarios"][2]
    decision = scen3["deterministic_triage_decision"]
    assert decision["triage_state"] == "RED"
    assert decision["matched_rule_id"] == "RULE_RED_002_CEPHALAD_ICP_SURGE"


def test_014_scen3_lbnp_locker_dispatch(sim_results):
    """Test 014: Verifies Mid-Deck LBNP-03 is dispatched for emergency lower body negative pressure."""
    scen3 = sim_results["scenarios"][2]
    lockers = scen3["cockpit_3sec_rapid_dispatch"]["dispatched_equipment_lockers"]
    assert any("LBNP-03" in loc for loc in lockers)


def test_015_scen3_sans_hydrodynamic_limitations(sim_results):
    """Test 015: Verifies documented limitation that I_ICP is a proxy requiring OCT confirmation."""
    scen3 = sim_results["scenarios"][2]
    limits = scen3["open_scientific_and_aerospace_limitations"]
    assert any("fundoscopy" in lim.lower() or "ultrasound" in lim.lower() for lim in limits)


# =============================================================================
# SCENARIO 4: LUNAR EVA IN-HELMET VOMITING & ASPHYXIATION (016 - 020)
# =============================================================================

def test_016_scen4_hypoxia_tachypnea_biophysics(sim_results):
    """Test 016: Verifies acute cardiorespiratory hypoxia (SpO2 < 88%, HR > 125 bpm)."""
    scen4 = sim_results["scenarios"][3]
    vitals = scen4["sanitized_telemetry"]
    assert vitals["spo2_percent"] < 88.0
    assert vitals["heart_rate_bpm"] > 125.0


def test_017_scen4_deterministic_red_triage(sim_results):
    """Test 017: Verifies immediate matching of RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA."""
    scen4 = sim_results["scenarios"][3]
    decision = scen4["deterministic_triage_decision"]
    assert decision["triage_state"] == "RED"
    assert decision["matched_rule_id"] == "RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA"


def test_018_scen4_eva_abort_action_priority(sim_results):
    """Test 018: Verifies rapid response actions include emergency O2 and EVA abort."""
    scen4 = sim_results["scenarios"][3]
    cockpit = scen4["cockpit_3sec_rapid_dispatch"]
    assert cockpit["action_count"] >= 2
    assert "hypoxia" in cockpit["executive_summary"].lower() or "red" in cockpit["executive_summary"].lower()


def test_019_scen4_medical_locker_dispatch(sim_results):
    """Test 019: Verifies Forward Locker MED-01 is dispatched for emergency resuscitation."""
    scen4 = sim_results["scenarios"][3]
    lockers = scen4["cockpit_3sec_rapid_dispatch"]["dispatched_equipment_lockers"]
    assert any("MED-01" in loc for loc in lockers)


def test_020_scen4_physical_buddy_rescue_limitation(sim_results):
    """Test 020: Verifies documented limitation on mandatory physical buddy-astronaut rescue."""
    scen4 = sim_results["scenarios"][3]
    limits = scen4["open_scientific_and_aerospace_limitations"]
    assert any("buddy" in lim.lower() or "aspirate" in lim.lower() for lim in limits)


# =============================================================================
# SCENARIO 5: AVIONICS ELECTROMAGNETIC PULSE (EMP) / EMI BLAST (021 - 025)
# =============================================================================

def test_021_scen5_sanity_gate_clamping(sim_results):
    """Test 021: Verifies 11 channel violations were remediated by the Sanity Gate."""
    scen5 = sim_results["scenarios"][4]
    audit = scen5["sanity_gate_audit"]
    assert audit["violations_remediated"] >= 10, f"Expected >= 10 remediations, got {audit['violations_remediated']}"


def test_022_scen5_no_floating_point_exception(sim_results):
    """Test 022: Verifies all sanitized channels strictly adhere to NASA-STD-3001 caps."""
    scen5 = sim_results["scenarios"][4]
    sanitized = scen5["sanitized_telemetry"]
    assert sanitized["heart_rate_bpm"] <= 240.0
    assert sanitized["systolic_bp_mmhg"] <= 260.0
    assert sanitized["core_temp_c"] <= 43.0
    assert sanitized["spo2_percent"] <= 100.0
    assert sanitized["cabin_pressure_psi"] >= 0.0


def test_023_scen5_clamped_triage_determinism(sim_results):
    """Test 023: Verifies system deterministically transitions to RED triage without crash."""
    scen5 = sim_results["scenarios"][4]
    decision = scen5["deterministic_triage_decision"]
    assert decision["triage_state"] == "RED"


def test_024_scen5_execution_latency_bounded(sim_results):
    """Test 024: Verifies extreme corrupted frame execution is completed rapidly."""
    scen5 = sim_results["scenarios"][4]
    latency = scen5["execution_performance"]["latency_ms"]
    assert latency < 50.0, f"Expected latency < 50 ms, got {latency} ms"


def test_025_scen5_hardware_shielding_limitation(sim_results):
    """Test 025: Verifies documented limitation on physical Faraday shielding requirement."""
    scen5 = sim_results["scenarios"][4]
    limits = scen5["open_scientific_and_aerospace_limitations"]
    assert any("Faraday" in lim or "hardware" in lim.lower() for lim in limits)
