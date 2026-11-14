"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 02_AI_CORE / Master Operational Orchestration
Test Suite: test_pipeline_orchestrator.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Master Integration
Verification: 100% Statement Coverage on pipeline_orchestrator.py
=============================================================================
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import pytest

# Ensure source and decision dirs are on sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
ai_core_src = root_dir / "02_AI_CORE" / "01_src"
decision_dir = root_dir / "03_DECISION_CORE"

for p in [str(ai_core_src), str(decision_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from pipeline_orchestrator import (
    AstroVitalPipelineOrchestrator,
    PipelineExecutionRecord,
    PipelineHealthSummary,
    CANONICAL_CHANNELS,
)
from ingestion_adapter import (
    TelemetryTemporalSynchronizer,
    TelemetryVector12DBuilder,
)
from inno3_signal_stabilizer import StabilizedFrameExporter
from sanity_gate import SanityGateExporter
from inno6_biomarker_ranker import SensitivityContractExporter
from triage_model_engine import TriageModelEngine
from cockpit_countermeasure_dispatcher import (
    CockpitCountermeasureDispatcher,
    CockpitActionPayload,
)


@pytest.fixture
def canonical_nominal_dict() -> Dict[str, float]:
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


@pytest.fixture
def orchestrator() -> AstroVitalPipelineOrchestrator:
    return AstroVitalPipelineOrchestrator(recovery_debounce_frames=5)


# =============================================================================
# INITIALIZATION & ARCHITECTURAL TESTS
# =============================================================================

def test_01_orchestrator_initialization_defaults(orchestrator: AstroVitalPipelineOrchestrator):
    """Verifies default initialization of the supreme pipeline orchestrator."""
    assert orchestrator.frame_count == 0
    assert len(orchestrator.config_sha256) == 64
    assert isinstance(orchestrator.synchronizer, TelemetryTemporalSynchronizer)
    assert isinstance(orchestrator.stabilizer, StabilizedFrameExporter)
    assert isinstance(orchestrator.sanity_gate, SanityGateExporter)
    assert isinstance(orchestrator.biomarker_ranker, SensitivityContractExporter)
    assert isinstance(orchestrator.decision_engine, TriageModelEngine)
    assert isinstance(orchestrator.cockpit_dispatcher, CockpitCountermeasureDispatcher)


def test_02_orchestrator_initialization_custom_components():
    """Verifies dependency injection with custom pre-configured subsystems."""
    sync = TelemetryTemporalSynchronizer()
    stab = StabilizedFrameExporter()
    gate = SanityGateExporter()
    rank = SensitivityContractExporter()
    engine = TriageModelEngine(recovery_debounce_frames=3)
    disp = CockpitCountermeasureDispatcher()

    custom_orch = AstroVitalPipelineOrchestrator(
        synchronizer=sync,
        stabilizer=stab,
        sanity_gate=gate,
        biomarker_ranker=rank,
        decision_engine=engine,
        cockpit_dispatcher=disp,
        recovery_debounce_frames=3,
        max_audit_history=50,
    )
    assert custom_orch._max_audit_history == 50
    assert custom_orch.decision_engine.recovery_debounce_frames == 3


# =============================================================================
# TELEMETRY INPUT TYPE & VALIDATION TESTS
# =============================================================================

def test_03_process_frame_from_dict_nominal_green(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Nominal cruise frame intake as Python dictionary."""
    record = orchestrator.process_telemetry_frame(
        telemetry=canonical_nominal_dict,
        microgravity_days=3.0,
        exercise_metric=1.0,
        flight_mode="REALTIME"
    )

    assert isinstance(record, PipelineExecutionRecord)
    assert record.frame_index == 1
    assert record.flight_mode == "REALTIME"
    assert record.triage_state == "GREEN"
    assert record.sanity_gate_passed is True
    assert record.total_violations_remediated == 0
    assert record.cockpit_payload.hud_banner.alert_level == "GREEN_NOMINAL"
    assert record.cockpit_payload.hud_banner.audio_tone_frequency_hz == 0
    assert record.execution_latency_ms >= 0.0
    assert len(record.top_divergent_biomarkers) > 0


def test_04_process_frame_from_series(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Intake as Pandas Series."""
    series = pd.Series(canonical_nominal_dict)
    record = orchestrator.process_telemetry_frame(series, microgravity_days=4.0)

    assert record.frame_index == 1
    assert record.triage_state == "GREEN"
    assert isinstance(record.get_executive_summary(), str)
    assert "NOMINAL GREEN EQUILIBRIUM" in record.get_executive_summary()


def test_05_process_frame_from_dataframe(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Intake as single-row Pandas DataFrame."""
    df = pd.DataFrame([canonical_nominal_dict])
    record = orchestrator.process_telemetry_frame(df, microgravity_days=2.0)

    assert record.frame_index == 1
    assert record.triage_state == "GREEN"


def test_06_process_frame_empty_dataframe_raises_value_error(
    orchestrator: AstroVitalPipelineOrchestrator
):
    """Verifies that an empty DataFrame raises ValueError defensively."""
    with pytest.raises(ValueError, match="Telemetry DataFrame cannot be empty"):
        orchestrator.process_telemetry_frame(pd.DataFrame())


def test_07_process_frame_invalid_type_raises_type_error(
    orchestrator: AstroVitalPipelineOrchestrator
):
    """Verifies that unsupported telemetry types raise TypeError defensively."""
    with pytest.raises(TypeError, match="Unsupported telemetry type"):
        orchestrator.process_telemetry_frame([1, 2, 3])  # type: ignore


def test_08_process_frame_skip_stabilizer(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies telemetry processing with skip_stabilizer=True."""
    record = orchestrator.process_telemetry_frame(
        canonical_nominal_dict,
        skip_stabilizer=True
    )
    assert record.stabilized_telemetry["heart_rate_bpm"] == canonical_nominal_dict["heart_rate_bpm"]
    assert record.triage_state == "GREEN"


# =============================================================================
# CLINICAL EMERGENCY & TRIAGE ESCALATION TESTS
# =============================================================================

def test_09_process_frame_acute_asystole_state_red(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Severe Hemodynamic Shock / Cardiovascular Collapse (HR=110, SBP=85, SI >= 1.1)."""
    vitals = dict(canonical_nominal_dict)
    vitals["heart_rate_bpm"] = 110.0
    vitals["systolic_bp_mmhg"] = 85.0
    vitals["diastolic_bp_mmhg"] = 55.0

    record = orchestrator.process_telemetry_frame(vitals)
    assert record.triage_state == "RED"
    assert record.matched_rule_id == "RULE_RED_004_SEVERE_SHOCK_HEMODYNAMIC_COLLAPSE"
    assert record.cockpit_payload.hud_banner.audio_tone_frequency_hz == 1200


def test_10_process_frame_hypoxia_emergency_state_red(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Severe Hypoxemia / Cabin Depressurization (SpO2=84%, HR=135)."""
    vitals = dict(canonical_nominal_dict)
    vitals["spo2_percent"] = 84.0
    vitals["heart_rate_bpm"] = 135.0
    vitals["resp_rate_bpm"] = 30.0

    record = orchestrator.process_telemetry_frame(vitals)
    assert record.triage_state == "RED"
    assert record.matched_rule_id == "RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA"
    assert record.cockpit_payload.hud_banner.alert_level == "RED_CRITICAL"


def test_11_process_frame_hypertensive_emergency_state_red(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Acute Hypertensive Crisis (SBP=175 mmHg, MAP >= 125 mmHg)."""
    vitals = dict(canonical_nominal_dict)
    vitals["systolic_bp_mmhg"] = 175.0
    vitals["diastolic_bp_mmhg"] = 115.0

    record = orchestrator.process_telemetry_frame(vitals)
    assert record.triage_state == "RED"
    assert record.matched_rule_id == "RULE_RED_003_HYPERTENSIVE_CRISIS"


def test_12_process_frame_cephalad_fluid_shift_surge_state_red(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Cephalad Fluid Shift ICP Surge in Long-Duration Flight (Day 60)."""
    record = orchestrator.process_telemetry_frame(
        canonical_nominal_dict,
        microgravity_days=60.0
    )
    assert record.triage_state == "RED"
    assert record.matched_rule_id == "RULE_RED_002_CEPHALAD_ICP_SURGE"
    assert record.biophysical_metrics["icp_gradient_index"] >= 1.85


def test_13_process_frame_early_cephalad_shift_state_amber(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Early Cephalad Fluid Shift Compensation (Day 25, 1.35 <= I_ICP < 1.85)."""
    record = orchestrator.process_telemetry_frame(
        canonical_nominal_dict,
        microgravity_days=25.0
    )
    assert record.triage_state == "AMBER"
    assert record.matched_rule_id == "RULE_AMBER_001_ELEVATED_CEPHALAD_FLUID_SHIFT"
    assert record.cockpit_payload.hud_banner.audio_tone_frequency_hz == 600


def test_14_process_frame_sleep_debt_autonomic_fatigue_state_amber(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Scenario: Severe Sleep Debt and Autonomic Stress (sleep_debt_hours >= 16.0)."""
    vitals = dict(canonical_nominal_dict)
    vitals["sleep_debt_hours"] = 18.0

    record = orchestrator.process_telemetry_frame(
        vitals,
        microgravity_days=3.0,
        sleep_debt_hours=18.0
    )
    assert record.triage_state == "AMBER"
    assert record.matched_rule_id == "RULE_AMBER_005_EXTREME_SLEEP_DEBT_FATIGUE"


def test_15_process_frame_with_partial_channels_defaults_missing(
    orchestrator: AstroVitalPipelineOrchestrator
):
    """Verifies that missing channels are filled defensively with 0.0 without crash."""
    partial = {"heart_rate_bpm": 75.0, "systolic_bp_mmhg": 118.0}
    record = orchestrator.process_telemetry_frame(partial)
    assert isinstance(record, PipelineExecutionRecord)
    assert record.raw_input["heart_rate_bpm"] == 75.0
    assert record.raw_input["spo2_percent"] == 0.0


# =============================================================================
# STREAMING & CONTINUOUS DATASET INTAKE TESTS
# =============================================================================

def test_16_process_stream_empty_dataframe(orchestrator: AstroVitalPipelineOrchestrator):
    """Verifies streaming over an empty DataFrame yields empty list."""
    records = orchestrator.process_telemetry_stream(pd.DataFrame())
    assert records == []


def test_17_process_stream_multi_frame_timeseries(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies streaming row-by-row over a multi-frame continuous timeseries."""
    df_stream = pd.DataFrame([canonical_nominal_dict] * 5)
    records = orchestrator.process_telemetry_stream(
        df_stream,
        microgravity_days=3.0,
        flight_mode="HISTORICAL_REPLAY"
    )
    assert len(records) == 5
    assert orchestrator.frame_count == 5
    assert records[-1].flight_mode == "HISTORICAL_REPLAY"


# =============================================================================
# SOVEREIGN CREW MEDICAL OFFICER (CMO) OVERRIDE TESTS
# =============================================================================

def test_18_sovereign_cmo_override_assert_and_clear(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies sovereign CMO manual override assertion, persistence, and clear."""
    # Assert manual override to RED
    cmo_record = orchestrator.assert_cmo_override(
        target_state="RED",
        clinical_rationale="Astronaut sustained blunt chest trauma during EVA hatch operations.",
        cmo_id="CMO-ORION-01",
        rule_id="RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA"
    )
    assert cmo_record.is_active is True
    assert cmo_record.override_state == "RED"

    # Next nominal vitals must report RED due to active sovereign override
    record_overridden = orchestrator.process_telemetry_frame(canonical_nominal_dict)
    assert record_overridden.triage_state == "RED"
    assert record_overridden.is_cmo_overridden is True

    # Clear override
    orchestrator.clear_cmo_override()

    # Subsequent nominal vitals must revert to automatic GREEN
    record_normal = orchestrator.process_telemetry_frame(canonical_nominal_dict)
    assert record_normal.triage_state == "GREEN"
    assert record_normal.is_cmo_overridden is False


# =============================================================================
# AUDIT TRAIL, HEALTH SUMMARY & BUFFER TESTS
# =============================================================================

def test_19_audit_trail_history_and_limit(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies audit trail retrieval with bounded limit."""
    for _ in range(5):
        orchestrator.process_telemetry_frame(canonical_nominal_dict)

    trail_3 = orchestrator.get_audit_trail(limit=3)
    assert len(trail_3) == 3
    assert trail_3[-1].frame_index == 5


def test_20_health_summary_metrics(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies operational health summary generation."""
    # Initially no frames processed
    initial_health = orchestrator.get_health_summary()
    assert initial_health.is_healthy is True
    assert initial_health.frames_processed_count == 0
    assert initial_health.last_triage_state == "UNINITIALIZED"

    # Process frame and re-evaluate
    orchestrator.process_telemetry_frame(canonical_nominal_dict)
    health = orchestrator.get_health_summary()
    assert health.frames_processed_count == 1
    assert health.last_triage_state == "GREEN"
    assert health.average_latency_ms >= 0.0
    assert health.subsystems_status["sanity_gate"] == "ONLINE"
    assert health.subsystems_status["cockpit_countermeasure_dispatcher"] == "ONLINE"


def test_21_pipeline_record_serialization_and_helpers(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies to_dict serialization of PipelineExecutionRecord."""
    record = orchestrator.process_telemetry_frame(canonical_nominal_dict)
    data = record.to_dict()

    assert isinstance(data, dict)
    assert data["triage_state"] == "GREEN"
    assert data["frame_index"] == 1
    assert "cockpit_payload" in data
    assert "biophysical_metrics" in data
    assert "execution_latency_ms" in data


def test_22_audit_history_buffer_cap(canonical_nominal_dict: Dict[str, float]):
    """Verifies audit history buffer stays capped at max_audit_history."""
    small_orch = AstroVitalPipelineOrchestrator(max_audit_history=3)
    for _ in range(7):
        small_orch.process_telemetry_frame(canonical_nominal_dict)

    assert len(small_orch._audit_history) == 3
    assert small_orch._audit_history[-1].frame_index == 7


def test_23_latencies_buffer_cap(
    orchestrator: AstroVitalPipelineOrchestrator,
    canonical_nominal_dict: Dict[str, float]
):
    """Verifies latency tracking list stays capped at 1000 items."""
    orchestrator._latencies_ms = [10.0] * 1005
    orchestrator.process_telemetry_frame(canonical_nominal_dict)
    assert len(orchestrator._latencies_ms) == 1000
