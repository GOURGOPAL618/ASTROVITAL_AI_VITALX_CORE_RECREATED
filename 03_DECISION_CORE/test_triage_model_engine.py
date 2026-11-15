"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Verification Suite: test_triage_model_engine.py (Phase 3 IV&V)
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A
Governance: Central Deterministic Triage Model Engine Verification
=============================================================================
"""

import sys
import json
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

from triage_model_engine import (
    TriageModelEngine,
    TriageDecisionPacket,
    CMOOverrideRecord,
)
from rule_schema_validator import (
    DecisionConfigManager,
    load_default_decision_configuration,
)
from biophysical_physics_engine import BiophysicalPhysicsEngine


@pytest.fixture
def engine() -> TriageModelEngine:
    return TriageModelEngine(recovery_debounce_frames=5)


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
# GROUP 1: INITIALIZATION & NOMINAL EXECUTION (TESTS 01-05)
# =============================================================================

def test_01_engine_initialization_defaults():
    """Verify engine initializes cleanly with defaults and custom parameters."""
    eng1 = TriageModelEngine()
    assert eng1.current_state == "GREEN"
    assert eng1.is_cmo_override_active is False
    assert eng1.recovery_debounce_frames == 5

    custom_cfg = load_default_decision_configuration()
    custom_phy = BiophysicalPhysicsEngine(config_manager=custom_cfg)
    eng2 = TriageModelEngine(config_manager=custom_cfg, physics_engine=custom_phy, recovery_debounce_frames=3)
    assert eng2.config_manager is custom_cfg
    assert eng2.physics_engine is custom_phy
    assert eng2.recovery_debounce_frames == 3


def test_02_process_nominal_telemetry_produces_green(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify nominal vitals yield STATE GREEN TriageDecisionPacket."""
    packet = engine.process_telemetry_frame(nominal_vitals, microgravity_days=5.0)

    assert isinstance(packet, TriageDecisionPacket)
    assert packet.triage_state == "GREEN"
    assert packet.matched_rule_id == "RULE_GREEN_001_PHYSIOLOGICAL_EQUILIBRIUM"
    assert "NOMINAL GREEN" in packet.clinical_audit_sentence
    assert packet.is_flight_certified is True
    assert packet.execution_latency_ms < 50.0
    assert packet.hemodynamics["pulse_pressure_mmhg"] == 40.0
    assert packet.fluid_shift["is_green_equilibrium"] is True
    assert len(packet.actionable_countermeasures) > 0


def test_03_packet_serialization_dict_and_json(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify to_dict and to_json serialize completely without schema violations."""
    packet = engine.process_telemetry_frame(nominal_vitals)
    d = packet.to_dict()
    assert isinstance(d, dict)
    assert d["triage_state"] == "GREEN"
    assert "decision_id" in d

    json_str = packet.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["decision_id"] == packet.decision_id
    assert parsed["triage_state"] == "GREEN"


def test_04_biomarker_urgency_attribution_propagation(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify Stage 4 biomarker weights propagate directly into decision packet."""
    weights = {"heart_rate_bpm": 0.35, "spo2_percent": 0.45, "co2_cabin_ppm": 0.20}
    packet = engine.process_telemetry_frame(nominal_vitals, biomarker_weights=weights)
    assert packet.biomarker_urgency_attribution == weights


def test_05_decision_id_uniqueness_and_counter(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify decision IDs increment sequentially with unique cryptographic suffixes."""
    p1 = engine.process_telemetry_frame(nominal_vitals)
    p2 = engine.process_telemetry_frame(nominal_vitals)
    assert p1.decision_id != p2.decision_id
    assert "DEC-0000001" in p1.decision_id
    assert "DEC-0000002" in p2.decision_id


# =============================================================================
# GROUP 2: CRITICAL RED TRIAGE DISPATCH (TESTS 06-10)
# =============================================================================

def test_06_red_hypoxia_tachycardia_instant_dispatch(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify SpO2 < 88% and HR > 125 bpm immediately trips STATE RED."""
    vitals = dict(nominal_vitals)
    vitals["spo2_percent"] = 84.0
    vitals["heart_rate_bpm"] = 132.0

    packet = engine.process_telemetry_frame(vitals)
    assert packet.triage_state == "RED"
    assert packet.matched_rule_id == "RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA"
    assert "CRITICAL RED ALERT" in packet.clinical_audit_sentence
    assert any("rebreather" in c["protocol"].lower() or "o2" in c["protocol"].lower() for c in packet.actionable_countermeasures)
    assert engine.current_state == "RED"


def test_07_red_cephalad_fluid_shift_surge_dispatch(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify I_ICP >= 1.85 trips STATE RED with LBNP protocol."""
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 155.0
    vitals["diastolic_bp_mmhg"] = 100.0
    vitals["co2_cabin_ppm"] = 7500.0

    packet = engine.process_telemetry_frame(vitals, microgravity_days=180.0)
    assert packet.triage_state == "RED"
    assert packet.matched_rule_id == "RULE_RED_002_CEPHALAD_ICP_SURGE"
    assert any("lbnp" in c["protocol"].lower() for c in packet.actionable_countermeasures)


def test_08_red_hypertensive_crisis_dispatch(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify SBP >= 165 trips STATE RED hypertensive crisis."""
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 172.0

    packet = engine.process_telemetry_frame(vitals)
    assert packet.triage_state == "RED"
    assert packet.matched_rule_id == "RULE_RED_003_HYPERTENSIVE_CRISIS"
    assert "Acute Hypertensive Emergency" in packet.clinical_title


def test_09_red_hemodynamic_shock_collapse(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify Shock Index >= 1.10 and SBP <= 90 trips STATE RED."""
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 85.0
    vitals["heart_rate_bpm"] = 115.0  # SI = 115 / 85 = 1.35 >= 1.10

    packet = engine.process_telemetry_frame(vitals)
    assert packet.triage_state == "RED"
    assert packet.matched_rule_id == "RULE_RED_004_SEVERE_SHOCK_HEMODYNAMIC_COLLAPSE"
    assert packet.hemodynamics["is_shock_indicated"] is True


def test_10_red_cabin_decompression_dispatch(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify cabin pressure <= 10.5 psi trips STATE RED decompression alert."""
    vitals = dict(nominal_vitals)
    vitals["cabin_pressure_psi"] = 9.5

    packet = engine.process_telemetry_frame(vitals)
    assert packet.triage_state == "RED"
    assert packet.matched_rule_id == "RULE_RED_005_RAPID_CABIN_DECOMPRESSION"
    assert any("ocss" in c["protocol"].lower() or "suit" in c["protocol"].lower() for c in packet.actionable_countermeasures)


# =============================================================================
# GROUP 3: WARNING AMBER TRIAGE DISPATCH (TESTS 11-15)
# =============================================================================

def test_11_amber_elevated_cephalad_fluid_shift(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify I_ICP in [1.35, 1.85) trips STATE AMBER."""
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 125.0
    vitals["co2_cabin_ppm"] = 4200.0

    packet = engine.process_telemetry_frame(vitals, microgravity_days=25.0)
    assert packet.triage_state == "AMBER"
    assert packet.matched_rule_id == "RULE_AMBER_001_ELEVATED_CEPHALAD_FLUID_SHIFT"
    assert engine.current_state == "AMBER"


def test_12_amber_hypercapnic_cabin_co2(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify cabin CO2 >= 5000 ppm trips STATE AMBER scrubber canister alert."""
    vitals = dict(nominal_vitals)
    vitals["co2_cabin_ppm"] = 5200.0

    packet = engine.process_telemetry_frame(vitals, microgravity_days=2.0)
    assert packet.triage_state == "AMBER"
    assert packet.matched_rule_id == "RULE_AMBER_002_HYPERCAPNIC_CABIN_AIR"


def test_13_amber_stroke_volume_deconditioning(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify Stroke Volume <= 65 mL (due to microgravity duration without exercise) trips AMBER."""
    vitals = dict(nominal_vitals)
    # 120 days microgravity with zero exercise metric
    packet = engine.process_telemetry_frame(vitals, microgravity_days=120.0, exercise_metric=0.0)
    assert packet.cardiac_output["is_stroke_volume_depleted"] is True


def test_14_amber_mild_hypoxia_desaturation(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify SpO2 in [88%, 92%] trips STATE AMBER deep-breathing alert."""
    vitals = dict(nominal_vitals)
    vitals["spo2_percent"] = 91.0
    vitals["heart_rate_bpm"] = 80.0  # Non-tachycardic

    packet = engine.process_telemetry_frame(vitals, microgravity_days=1.0)
    assert packet.triage_state == "AMBER"
    assert packet.matched_rule_id == "RULE_AMBER_004_MILD_HYPOXIA_DESATURATION"


def test_15_amber_cumulative_sleep_debt(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify sleep debt >= 16.0 hours trips STATE AMBER fatigue alert."""
    vitals = dict(nominal_vitals)
    vitals["sleep_debt_hours"] = 17.5

    packet = engine.process_telemetry_frame(vitals, microgravity_days=2.0)
    assert packet.triage_state == "AMBER"
    assert packet.matched_rule_id == "RULE_AMBER_005_EXTREME_SLEEP_DEBT_FATIGUE"


# =============================================================================
# GROUP 4: STATE MACHINE TRANSITION & HYSTERESIS DEBOUNCE (TESTS 16-20)
# =============================================================================

def test_16_instant_transition_green_to_red(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify green to red transition trips instantly on frame 1 with zero debounce delay."""
    # Frame 1: Nominal
    p1 = engine.process_telemetry_frame(nominal_vitals)
    assert p1.triage_state == "GREEN"

    # Frame 2: Sudden severe hypoxia
    vitals_red = dict(nominal_vitals)
    vitals_red["spo2_percent"] = 82.0
    vitals_red["heart_rate_bpm"] = 135.0

    p2 = engine.process_telemetry_frame(vitals_red)
    assert p2.triage_state == "RED"
    assert engine.current_state == "RED"


def test_17_hysteresis_recovery_from_red_to_green_requires_debounce(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify returning from RED to GREEN requires 5 consecutive nominal frames."""
    # Step 1: Trip to RED
    vitals_red = dict(nominal_vitals)
    vitals_red["spo2_percent"] = 82.0
    vitals_red["heart_rate_bpm"] = 135.0
    p_red = engine.process_telemetry_frame(vitals_red)
    assert p_red.triage_state == "RED"

    # Step 2: Feed nominal vitals for 4 frames (should HOLD RED due to hysteresis)
    for frame_idx in range(1, 5):
        p_held = engine.process_telemetry_frame(nominal_vitals)
        assert p_held.triage_state == "RED", f"Frame {frame_idx} should have held RED"
        assert "STABILIZING HYSTERESIS" in p_held.clinical_audit_sentence

    # Step 3: Frame 5 of nominal vitals satisfies debounce threshold -> transitions to GREEN
    p_cleared = engine.process_telemetry_frame(nominal_vitals)
    assert p_cleared.triage_state == "GREEN"
    assert engine.current_state == "GREEN"


def test_18_hysteresis_recovery_interrupted_by_new_red_event(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify that an intermittent RED violation resets the hysteresis debounce counter."""
    # Trip RED
    vitals_red = dict(nominal_vitals)
    vitals_red["spo2_percent"] = 82.0
    vitals_red["heart_rate_bpm"] = 135.0
    engine.process_telemetry_frame(vitals_red)

    # 3 frames of nominal recovery
    for _ in range(3):
        p = engine.process_telemetry_frame(nominal_vitals)
        assert p.triage_state == "RED"

    # Frame 4: Another RED event
    p_re_trip = engine.process_telemetry_frame(vitals_red)
    assert p_re_trip.triage_state == "RED"
    assert engine._consecutive_nominal_frames == 0


def test_19_hysteresis_recovery_from_amber_to_green(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify returning from AMBER to GREEN requires 5 debounce frames."""
    # Trip AMBER
    vitals_amber = dict(nominal_vitals)
    vitals_amber["co2_cabin_ppm"] = 5500.0
    p_amb = engine.process_telemetry_frame(vitals_amber, microgravity_days=2.0)
    assert p_amb.triage_state == "AMBER"

    # 4 frames of nominal -> held in AMBER
    for frame_idx in range(1, 5):
        p_held = engine.process_telemetry_frame(nominal_vitals, microgravity_days=2.0)
        assert p_held.triage_state == "AMBER"

    # Frame 5 -> cleared to GREEN
    p_green = engine.process_telemetry_frame(nominal_vitals, microgravity_days=2.0)
    assert p_green.triage_state == "GREEN"


def test_20_hysteresis_recovery_from_red_to_amber_debounce(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify de-escalating from RED to AMBER obeys debounce frames."""
    # Trip RED
    vitals_red = dict(nominal_vitals)
    vitals_red["spo2_percent"] = 82.0
    vitals_red["heart_rate_bpm"] = 135.0
    engine.process_telemetry_frame(vitals_red)

    # Mild condition (AMBER only)
    vitals_amber = dict(nominal_vitals)
    vitals_amber["co2_cabin_ppm"] = 5200.0

    # Frames 1-4 should hold RED
    for _ in range(4):
        p_held = engine.process_telemetry_frame(vitals_amber, microgravity_days=2.0)
        assert p_held.triage_state == "RED"

    # Frame 5 transitions to AMBER
    p_amb = engine.process_telemetry_frame(vitals_amber, microgravity_days=2.0)
    assert p_amb.triage_state == "AMBER"


# =============================================================================
# GROUP 5: CREW MEDICAL OFFICER (CMO) OVERRIDE PROTOCOL (TESTS 21-26)
# =============================================================================

def test_21_cmo_override_forces_amber_state(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify CMO override forces state to AMBER even during nominal telemetry."""
    engine.apply_cmo_override(
        override_state="AMBER",
        rationale="Astronaut reported unilateral retro-orbital headache and blurred vision.",
        authorizing_officer="CMO_DR_HANSEN"
    )
    assert engine.is_cmo_override_active is True

    packet = engine.process_telemetry_frame(nominal_vitals)
    assert packet.triage_state == "AMBER"
    assert "CMO MANUAL OVERRIDE ACTIVE" in packet.clinical_audit_sentence
    assert "CMO_DR_HANSEN" in packet.clinical_audit_sentence
    assert packet.cmo_override["is_active"] is True


def test_22_cmo_override_forces_red_state(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify CMO override can elevate nominal crew member directly to RED."""
    engine.apply_cmo_override(
        override_state="RED",
        rationale="Suspected subacute cabin toxic leak; initiating precautionary crew emergency.",
        authorizing_officer="FLIGHT_SURGEON_HOUSTON"
    )
    packet = engine.process_telemetry_frame(nominal_vitals)
    assert packet.triage_state == "RED"
    assert packet.cmo_override["authorizing_officer"] == "FLIGHT_SURGEON_HOUSTON"


def test_23_cmo_override_clearing_restores_autonomous_control(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify clearing CMO override immediately restores autonomous engine logic."""
    engine.apply_cmo_override("RED", "Test override", "CMO_TEST")
    p1 = engine.process_telemetry_frame(nominal_vitals)
    assert p1.triage_state == "RED"

    engine.clear_cmo_override()
    assert engine.is_cmo_override_active is False

    # Reset state to clear hysteresis
    engine.reset_state_machine()
    p2 = engine.process_telemetry_frame(nominal_vitals)
    assert p2.triage_state == "GREEN"
    assert p2.cmo_override["is_active"] is False


def test_24_cmo_override_defensive_invalid_state(engine: TriageModelEngine):
    """Verify ValueError when attempting override with invalid state string."""
    with pytest.raises(ValueError, match="Invalid CMO override state"):
        engine.apply_cmo_override("YELLOW", "Rationale", "CMO_DR")


def test_25_cmo_override_defensive_empty_rationale_or_officer(engine: TriageModelEngine):
    """Verify ValueError when rationale or authorizing officer are empty strings."""
    with pytest.raises(ValueError, match="requires formal clinical rationale"):
        engine.apply_cmo_override("RED", "", "CMO_DR")
    with pytest.raises(ValueError, match="requires verified authorizing officer"):
        engine.apply_cmo_override("RED", "Valid rationale", "   ")


def test_26_state_machine_reset_behavior(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify reset_state_machine clears state history, debounce, and CMO overrides."""
    engine.apply_cmo_override("AMBER", "Test", "OFFICER")
    vitals_red = dict(nominal_vitals)
    vitals_red["spo2_percent"] = 80.0
    vitals_red["heart_rate_bpm"] = 130.0
    engine.process_telemetry_frame(vitals_red)

    engine.reset_state_machine()
    assert engine.current_state == "GREEN"
    assert engine.is_cmo_override_active is False
    assert engine._consecutive_nominal_frames == 0


# =============================================================================
# GROUP 6: STREAM CONTINUITY & LATENCY PERFORMANCE (TESTS 27-30)
# =============================================================================

def test_27_process_telemetry_stream_multi_frame(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify continuous streaming multi-frame processing with dynamic state changes."""
    # Create 15-frame scenario: 5 Nominal -> 3 Red -> 7 Nominal (testing full trip and hysteresis recovery)
    rows = []
    # 5 Nominal
    for _ in range(5):
        rows.append(dict(nominal_vitals))
    # 3 Red (acute hypoxia)
    for _ in range(3):
        r = dict(nominal_vitals)
        r["spo2_percent"] = 82.0
        r["heart_rate_bpm"] = 135.0
        rows.append(r)
    # 7 Nominal (recovery)
    for _ in range(7):
        rows.append(dict(nominal_vitals))

    df_stream = pd.DataFrame(rows)
    packets = engine.process_telemetry_stream(df_stream, microgravity_days=5.0)

    assert len(packets) == 15
    states = [p.triage_state for p in packets]

    # Frames 0-4 should be GREEN
    assert states[:5] == ["GREEN"] * 5
    # Frames 5-7 should be RED
    assert states[5:8] == ["RED"] * 3
    # Frames 8-11 should HOLD RED (hysteresis recovery debounce frames 1-4)
    assert states[8:12] == ["RED"] * 4
    # Frame 12 is 5th recovery frame -> transitions to GREEN!
    assert states[12] == "GREEN"
    # Frames 13-14 remain GREEN
    assert states[13:] == ["GREEN"] * 2


def test_28_deterministic_reproducibility(nominal_vitals: Dict[str, float]):
    """Verify that two independent engine runs produce mathematically identical packets."""
    eng1 = TriageModelEngine(recovery_debounce_frames=3)
    eng2 = TriageModelEngine(recovery_debounce_frames=3)

    p1 = eng1.process_telemetry_frame(nominal_vitals, microgravity_days=10.0)
    p2 = eng2.process_telemetry_frame(nominal_vitals, microgravity_days=10.0)

    assert p1.triage_state == p2.triage_state
    assert p1.matched_rule_id == p2.matched_rule_id
    assert p1.hemodynamics == p2.hemodynamics
    assert p1.fluid_shift == p2.fluid_shift
    assert p1.cardiac_output == p2.cardiac_output


def test_29_execution_latency_budget(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify 100 consecutive frames process with average latency < 5.0 ms (budget: 50 ms)."""
    t0 = time.perf_counter()
    for _ in range(100):
        engine.process_telemetry_frame(nominal_vitals, microgravity_days=14.0)
    dt_total_ms = (time.perf_counter() - t0) * 1000.0
    dt_per_frame_ms = dt_total_ms / 100.0

    assert dt_per_frame_ms < 5.0, f"Per-frame latency {dt_per_frame_ms:.4f} ms exceeds 5.0 ms threshold"


def test_30_unclassified_fallback_when_rule_none(engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify unclassified borderline fallback sets correct fallback rule ID and clinical title."""
    vitals = dict(nominal_vitals)
    # Slightly sub-nominal SpO2 (94.0%) which fails GREEN (requires >= 95.0) but does not trip AMBER (<= 92.0)
    vitals["spo2_percent"] = 94.0

    packet = engine.process_telemetry_frame(vitals, microgravity_days=1.0)
    assert packet.triage_state == "AMBER"
    assert "UNCLASSIFIED" in packet.clinical_audit_sentence
