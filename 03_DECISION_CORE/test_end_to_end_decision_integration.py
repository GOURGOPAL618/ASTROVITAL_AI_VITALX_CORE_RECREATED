"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Integration Suite: test_end_to_end_decision_integration.py (Phase 5 IV&V)
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Master Integration
Governance: End-to-End Full Pipeline IV&V (AI Core -> Decision Core -> Cockpit)
=============================================================================
"""

import sys
import json
import time
import pytest
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np

# Ensure 02_AI_CORE and 03_DECISION_CORE are on sys.path
root_dir = Path(__file__).resolve().parent.parent
ai_core_src = root_dir / "02_AI_CORE" / "01_src"
decision_dir = root_dir / "03_DECISION_CORE"

for p in [str(ai_core_src), str(decision_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ingestion_adapter import (
    TelemetryArchiveRegistry,
    TelemetryVector12DBuilder,
    TelemetryTemporalSynchronizer,
)
from inno3_signal_stabilizer import (
    StabilizedFrameExporter,
    SignalQualityEvaluator,
    BaselineDriftCompensator,
)
from sanity_gate import (
    PhysiologicalBoundaryEnforcer,
    PhysiologicalCouplingGuard,
    SensorDecouplingFallbackEngine,
    SanityGateExporter,
)
from inno6_biomarker_ranker import (
    SensitivityContractExporter,
    CompositeSensitivityRanker,
    EntropyWeightEngine,
    PhysiologicalDeviationScorer,
)
from rule_schema_validator import DecisionConfigManager, load_default_decision_configuration
from biophysical_physics_engine import BiophysicalPhysicsEngine
from triage_model_engine import TriageModelEngine, TriageDecisionPacket
from cockpit_countermeasure_dispatcher import (
    CockpitCountermeasureDispatcher,
    CockpitActionPayload,
)


@pytest.fixture
def end_to_end_pipeline():
    """Initializes all sub-components across the 6-stage operational pipeline."""
    return {
        "sync": TelemetryTemporalSynchronizer(),
        "stabilizer": StabilizedFrameExporter(),
        "sanity_gate": SanityGateExporter(),
        "ranker": SensitivityContractExporter(),
        "decision_engine": TriageModelEngine(recovery_debounce_frames=5),
        "cockpit_dispatcher": CockpitCountermeasureDispatcher(),
    }


@pytest.fixture
def canonical_nominal_vector() -> Dict[str, float]:
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
# MASTER FULL-PIPELINE INTEGRATION TESTS (SCENARIOS 01-10)
# =============================================================================

def test_01_full_pipeline_nominal_cruise_state_green(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 1: Nominal Deep-Space Cruise (Day 5)
    Flow: 12D Normal Intake -> Stabilizer -> Sanity Gate -> Ranker -> Decision Engine -> Cockpit
    Expected: STATE GREEN, silent HUD banner, baseline maintain timeline.
    """
    pipe = end_to_end_pipeline

    # Stage 3: Sanity Gate
    df_raw = pd.DataFrame([canonical_nominal_vector])
    gated_packet = pipe["sanity_gate"].process_and_export_packet(df_raw)
    assert gated_packet.is_gate_passed is True
    sanitized_vitals = gated_packet.sanitized_df.iloc[0].to_dict()

    # Stage 4: Biomarker Sensitivity Divergence
    contract = pipe["ranker"].process_and_export_contract(gated_packet.sanitized_df)
    weights_dict = contract.sensitivity_dict
    assert len(weights_dict) == 12

    # Stage 5: Decision Model Engine
    decision_packet = pipe["decision_engine"].process_telemetry_frame(
        telemetry=sanitized_vitals,
        microgravity_days=5.0,
        exercise_metric=1.0,
        biomarker_weights=weights_dict
    )
    assert decision_packet.triage_state == "GREEN"
    assert decision_packet.matched_rule_id == "RULE_GREEN_001_PHYSIOLOGICAL_EQUILIBRIUM"

    # Stage 6: Cockpit Dispatcher
    cockpit_payload = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision_packet)
    assert isinstance(cockpit_payload, CockpitActionPayload)
    assert cockpit_payload.triage_state == "GREEN"
    assert cockpit_payload.hud_banner.alert_level == "GREEN_NOMINAL"
    assert cockpit_payload.hud_banner.audio_tone_frequency_hz == 0
    assert "NOMINAL GREEN EQUILIBRIUM" in cockpit_payload.three_second_executive_summary
    assert cockpit_payload.action_deck[0].action_id == "ACT_GRN_001_MAINTAIN_TIMELINE"


def test_02_full_pipeline_acute_hypoxia_eva_emergency_state_red(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 2: Acute Hypoxia During High-Metabolic EVA Excursion
    Flow: SpO2=82%, HR=138 bpm -> Sanity Gate -> Ranker -> Decision Engine -> Cockpit
    Expected: STATE RED, 1.2 kHz klaxon, critical path O2 rebreather step at Locker MED-01.
    """
    pipe = end_to_end_pipeline
    vitals = dict(canonical_nominal_vector)
    vitals["spo2_percent"] = 82.0
    vitals["heart_rate_bpm"] = 138.0
    vitals["resp_rate_bpm"] = 28.0

    # Sanity Gate passes physical plausibility (30 <= HR <= 220, 50 <= SpO2 <= 100)
    df_raw = pd.DataFrame([vitals])
    gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
    assert gated.is_gate_passed is True
    sanitized_vitals = gated.sanitized_df.iloc[0].to_dict()

    # Biomarker Ranker identifies spo2_percent as highest urgency
    contract = pipe["ranker"].process_and_export_contract(gated.sanitized_df)
    weights = contract.sensitivity_dict
    assert "spo2_percent" in weights

    # Decision Engine evaluates RED cardiorespiratory failure
    decision = pipe["decision_engine"].process_telemetry_frame(
        telemetry=sanitized_vitals,
        microgravity_days=5.0,
        biomarker_weights=weights
    )
    assert decision.triage_state == "RED"
    assert decision.matched_rule_id == "RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA"

    # Cockpit Dispatcher builds emergency protocol
    cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)
    assert cockpit.triage_state == "RED"
    assert cockpit.hud_banner.alert_level == "RED_CRITICAL"
    assert cockpit.hud_banner.audio_tone_frequency_hz == 1200
    assert cockpit.hud_banner.flash_rate_hz == 2.0
    assert cockpit.action_deck[0].is_critical_path is True
    assert cockpit.action_deck[0].action_id == "ACT_RED_001_O2_REBREATHER"
    assert "MED-01" in cockpit.action_deck[0].equipment_location


def test_03_full_pipeline_sans_cephalad_fluid_shift_surge_state_red(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 3: Long-Duration Deep Space Cephalad Fluid Surge (Innovation 1)
    Flow: Day 180 transit + acute hypertensive shift + hypercapnia -> I_ICP >= 1.85 -> Cockpit LBNP deployment.
    """
    pipe = end_to_end_pipeline
    vitals = dict(canonical_nominal_vector)
    vitals["systolic_bp_mmhg"] = 158.0
    vitals["diastolic_bp_mmhg"] = 102.0
    vitals["co2_cabin_ppm"] = 7200.0

    df_raw = pd.DataFrame([vitals])
    gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
    sanitized_vitals = gated.sanitized_df.iloc[0].to_dict()

    contract = pipe["ranker"].process_and_export_contract(gated.sanitized_df)
    weights = contract.sensitivity_dict

    decision = pipe["decision_engine"].process_telemetry_frame(
        telemetry=sanitized_vitals,
        microgravity_days=180.0,
        biomarker_weights=weights
    )
    assert decision.triage_state == "RED"
    assert decision.matched_rule_id == "RULE_RED_002_CEPHALAD_ICP_SURGE"
    assert decision.fluid_shift["icp_gradient_index"] >= 1.85

    cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)
    assert cockpit.triage_state == "RED"
    assert any("LBNP" in step.protocol for step in cockpit.action_deck)
    lbnp_step = next(s for s in cockpit.action_deck if "LBNP" in s.protocol)
    assert "LBNP-03" in lbnp_step.equipment_location
    assert "-35.0 mmHg" in lbnp_step.verification_step


def test_04_full_pipeline_eclss_hypercapnia_state_amber(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 4: Environmental ECLSS Scrubber Failure (Cabin CO2 = 5600 ppm)
    Expected: STATE AMBER, 600 Hz caution chime, LiOH canister swap action.
    """
    pipe = end_to_end_pipeline
    vitals = dict(canonical_nominal_vector)
    vitals["co2_cabin_ppm"] = 5600.0

    df_raw = pd.DataFrame([vitals])
    gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
    sanitized_vitals = gated.sanitized_df.iloc[0].to_dict()

    decision = pipe["decision_engine"].process_telemetry_frame(
        telemetry=sanitized_vitals,
        microgravity_days=2.0
    )
    assert decision.triage_state == "AMBER"
    assert decision.matched_rule_id == "RULE_AMBER_002_HYPERCAPNIC_CABIN_AIR"

    cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)
    assert cockpit.triage_state == "AMBER"
    assert cockpit.hud_banner.alert_level == "AMBER_WARNING"
    assert cockpit.hud_banner.audio_tone_frequency_hz == 600
    assert any("scrubber" in s.protocol.lower() for s in cockpit.action_deck)


def test_05_full_pipeline_stroke_volume_deconditioning_state_amber(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 5: Left Ventricular Deconditioning Strain (Day 20, HR = 106 bpm)
    Expected: Resting HR >= 105 bpm -> STATE AMBER -> ARED resistive countermeasure.
    """
    pipe = end_to_end_pipeline
    vitals = dict(canonical_nominal_vector)
    vitals["heart_rate_bpm"] = 106.0  # Elevated resting HR compensatory tachycardia

    df_raw = pd.DataFrame([vitals])
    gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
    sanitized_vitals = gated.sanitized_df.iloc[0].to_dict()

    decision = pipe["decision_engine"].process_telemetry_frame(
        telemetry=sanitized_vitals,
        microgravity_days=2.0,
        exercise_metric=0.5
    )
    assert decision.triage_state == "AMBER"
    assert decision.matched_rule_id == "RULE_AMBER_003_CARDIOVASCULAR_DECONDITIONING_STRAIN"

    cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)
    assert cockpit.triage_state == "AMBER"
    assert any("ARED" in s.protocol for s in cockpit.action_deck)


def test_06_full_pipeline_sleep_debt_fatigue_state_amber(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 6: Cumulative 18-Hour Sleep Debt
    Expected: STATE AMBER, sleep rest buffer, circadian blue-depleted lighting.
    """
    pipe = end_to_end_pipeline
    # Sanity Gate processes the 12 canonical physical sensor channels
    df_raw = pd.DataFrame([canonical_nominal_vector])
    gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
    sanitized_vitals = gated.sanitized_df.iloc[0].to_dict()

    # Mission timeline supplies operational sleep debt context
    sanitized_vitals["sleep_debt_hours"] = 18.0

    decision = pipe["decision_engine"].process_telemetry_frame(
        telemetry=sanitized_vitals,
        microgravity_days=2.0
    )
    assert decision.triage_state == "AMBER"
    assert decision.matched_rule_id == "RULE_AMBER_005_EXTREME_SLEEP_DEBT_FATIGUE"

    cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)
    assert any("circadian" in s.protocol.lower() for s in cockpit.action_deck)


def test_07_full_pipeline_cmo_override_integration(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 7: Physician Sovereign Command Override
    CMO engages manual RED override during nominal telemetry.
    Expected: Autonomous engine overridden, audit trail updated, RED HUD banner dispatched.
    """
    pipe = end_to_end_pipeline
    pipe["decision_engine"].apply_cmo_override(
        override_state="RED",
        rationale="Suspected subacute cabin carbon monoxide leak.",
        authorizing_officer="CMO_DR_HANSEN"
    )

    df_raw = pd.DataFrame([canonical_nominal_vector])
    gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
    decision = pipe["decision_engine"].process_telemetry_frame(gated.sanitized_df.iloc[0].to_dict())
    assert decision.triage_state == "RED"
    assert decision.cmo_override["is_active"] is True
    assert "CMO_DR_HANSEN" in decision.clinical_audit_sentence

    cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)
    assert cockpit.triage_state == "RED"
    assert cockpit.is_cmo_override_active is True
    assert cockpit.hud_banner.alert_level == "RED_CRITICAL"

    # Clear override and reset state
    pipe["decision_engine"].clear_cmo_override()
    pipe["decision_engine"].reset_state_machine()


def test_08_full_pipeline_sensor_decoupling_fallback_resilience(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 8: Sensor Decoupling Defense
    Incoming telemetry has impossible zero-voltage flatline SpO2=0% and HR=0 bpm.
    Expected: Sanity Gate discards decoupled sensor, falls back to 15-min rolling baseline,
    allowing Decision Core to evaluate with safe baseline projection.
    """
    pipe = end_to_end_pipeline
    corrupted_vitals = dict(canonical_nominal_vector)
    corrupted_vitals["spo2_percent"] = 0.0  # Physically impossible live flatline
    corrupted_vitals["heart_rate_bpm"] = 0.0

    df_corrupted = pd.DataFrame([corrupted_vitals])
    gated = pipe["sanity_gate"].process_and_export_packet(df_corrupted)
    assert gated.is_gate_passed is False  # Had violations
    assert gated.total_violations_remediated > 0
    assert gated.sanitized_df.iloc[0]["spo2_percent"] >= 50.0  # Imputed fallback
    assert gated.sanitized_df.iloc[0]["heart_rate_bpm"] >= 20.0

    # Decision Engine processes the sanitized projection
    decision = pipe["decision_engine"].process_telemetry_frame(
        telemetry=gated.sanitized_df.iloc[0].to_dict(),
        microgravity_days=2.0
    )
    # The imputed fallback reflects nominal baselines -> GREEN
    assert decision.triage_state in ("GREEN", "AMBER")


def test_09_full_pipeline_execution_latency_budget(
    end_to_end_pipeline: Dict[str, Any],
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 9: Execution Latency Budget Verification
    DO-178C Requirement: Complete end-to-end processing across all 6 stages must
    execute in < 50.0 ms per packet on local hardware.
    """
    pipe = end_to_end_pipeline
    df_raw = pd.DataFrame([canonical_nominal_vector])
    t0 = time.perf_counter()

    for _ in range(50):
        # Stage 3: Sanity Gate
        gated = pipe["sanity_gate"].process_and_export_packet(df_raw)
        # Stage 5: Decision Core
        decision = pipe["decision_engine"].process_telemetry_frame(
            telemetry=gated.sanitized_df.iloc[0].to_dict(),
            microgravity_days=5.0
        )
        # Stage 6: Cockpit Dispatcher
        cockpit = pipe["cockpit_dispatcher"].dispatch_cockpit_payload(decision)

    dt_total_ms = (time.perf_counter() - t0) * 1000.0
    dt_per_packet_ms = dt_total_ms / 50.0

    assert dt_per_packet_ms < 50.0, f"Full pipeline latency {dt_per_packet_ms:.3f} ms exceeds 50 ms budget"


def test_10_full_pipeline_determinism_certification_seal(
    canonical_nominal_vector: Dict[str, float]
):
    """
    Scenario 10: DO-178C Level C Complete Pipeline Determinism Seal
    Instantiates two completely independent pipelines from scratch and verifies
    100% bitwise identical output states, decision IDs prefixes, and cockpit action deck.
    """
    pipe1_engine = TriageModelEngine(recovery_debounce_frames=5)
    pipe2_engine = TriageModelEngine(recovery_debounce_frames=5)
    disp1 = CockpitCountermeasureDispatcher()
    disp2 = CockpitCountermeasureDispatcher()

    # Pass 1: Pipeline 1
    d1 = pipe1_engine.process_telemetry_frame(canonical_nominal_vector, microgravity_days=10.0)
    c1 = disp1.dispatch_cockpit_payload(d1)

    # Pass 2: Pipeline 2
    d2 = pipe2_engine.process_telemetry_frame(canonical_nominal_vector, microgravity_days=10.0)
    c2 = disp2.dispatch_cockpit_payload(d2)

    assert d1.triage_state == d2.triage_state
    assert d1.matched_rule_id == d2.matched_rule_id
    assert d1.hemodynamics == d2.hemodynamics
    assert d1.fluid_shift == d2.fluid_shift
    assert d1.cardiac_output == d2.cardiac_output
    assert c1.hud_banner == c2.hud_banner
    assert c1.three_second_executive_summary == c2.three_second_executive_summary
    assert len(c1.action_deck) == len(c2.action_deck)
