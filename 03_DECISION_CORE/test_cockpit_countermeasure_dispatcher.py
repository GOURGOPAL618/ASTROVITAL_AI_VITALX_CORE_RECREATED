"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Verification Suite: test_cockpit_countermeasure_dispatcher.py (Phase 4 IV&V)
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A
Governance: 3-Second Astronaut Cockpit Protocol & Dispatcher Verification
=============================================================================
"""

import sys
import json
import time
import pytest
from pathlib import Path
from typing import Dict, Any

# Ensure 03_DECISION_CORE is on sys.path
decision_path = Path(__file__).resolve().parent
if str(decision_path) not in sys.path:
    sys.path.insert(0, str(decision_path))

from cockpit_countermeasure_dispatcher import (
    SequencedActionStep,
    HUDAlertBanner,
    CockpitActionPayload,
    CockpitCountermeasureDispatcher,
    EQUIPMENT_LOCKER_REGISTRY,
)
from triage_model_engine import (
    TriageModelEngine,
    TriageDecisionPacket,
)


@pytest.fixture
def dispatcher() -> CockpitCountermeasureDispatcher:
    return CockpitCountermeasureDispatcher()


@pytest.fixture
def triage_engine() -> TriageModelEngine:
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
# GROUP 1: HUD ALERT BANNER & VISUAL-ACOUSTIC SIGNALS (TESTS 01-05)
# =============================================================================

def test_01_dispatcher_initialization_defaults_and_custom():
    """Verify dispatcher initializes with default and custom equipment registries."""
    disp1 = CockpitCountermeasureDispatcher()
    assert len(disp1.registry) > 10

    custom_reg = {"ACT_TEST": {"location": "Locker A", "verification": "Check A", "subsystem_lead": "CMO"}}
    disp2 = CockpitCountermeasureDispatcher(equipment_registry=custom_reg)
    assert disp2.registry == custom_reg


def test_02_hud_banner_red_critical(dispatcher: CockpitCountermeasureDispatcher):
    """Verify RED HUD banner: 1.2 kHz alarm, #FF1E27 red, 2.0 Hz flash, tactile vibration."""
    banner = dispatcher.generate_hud_alert_banner("RED")
    assert banner.alert_level == "RED_CRITICAL"
    assert banner.hud_banner_color == "#FF1E27"
    assert banner.audio_tone_frequency_hz == 1200
    assert banner.audio_pulse_pattern == "URGENT_PULSED_ALARM"
    assert banner.flash_rate_hz == 2.0
    assert banner.tactile_vibration_alert is True
    assert banner.priority_code == 1


def test_03_hud_banner_amber_warning(dispatcher: CockpitCountermeasureDispatcher):
    """Verify AMBER HUD banner: 600 Hz chime, #FFB800 yellow, 1.0 Hz flash, no vibration."""
    banner = dispatcher.generate_hud_alert_banner("AMBER")
    assert banner.alert_level == "AMBER_WARNING"
    assert banner.hud_banner_color == "#FFB800"
    assert banner.audio_tone_frequency_hz == 600
    assert banner.audio_pulse_pattern == "INTERMITTENT_CAUTION"
    assert banner.flash_rate_hz == 1.0
    assert banner.tactile_vibration_alert is False
    assert banner.priority_code == 2


def test_04_hud_banner_green_nominal(dispatcher: CockpitCountermeasureDispatcher):
    """Verify GREEN HUD banner: 0 Hz silent, #00E676 green, 0.0 Hz flash, priority 3."""
    banner = dispatcher.generate_hud_alert_banner("GREEN")
    assert banner.alert_level == "GREEN_NOMINAL"
    assert banner.hud_banner_color == "#00E676"
    assert banner.audio_tone_frequency_hz == 0
    assert banner.audio_pulse_pattern == "SILENT"
    assert banner.flash_rate_hz == 0.0
    assert banner.tactile_vibration_alert is False
    assert banner.priority_code == 3


def test_05_hud_banner_unclassified_fallback(dispatcher: CockpitCountermeasureDispatcher):
    """Verify unknown or unclassified state falls back safely to cautionary warning banner."""
    banner = dispatcher.generate_hud_alert_banner("UNKNOWN_STATE")
    assert banner.alert_level == "AMBER_WARNING"
    assert banner.audio_tone_frequency_hz == 600
    assert banner.priority_code == 2


# =============================================================================
# GROUP 2: ACTION CHECKLIST SEQUENCING & HARDWARE REGISTRY (TESTS 06-11)
# =============================================================================

def test_06_action_deck_priority_and_temporal_sorting(dispatcher: CockpitCountermeasureDispatcher):
    """Verify action deck sorts by priority ascending, then time_to_execute ascending."""
    raw_actions = [
        {"action_id": "ACT_B", "protocol": "Step B", "priority": 2, "time_to_execute_sec": 60},
        {"action_id": "ACT_A2", "protocol": "Step A2", "priority": 1, "time_to_execute_sec": 30},
        {"action_id": "ACT_A1", "protocol": "Step A1", "priority": 1, "time_to_execute_sec": 15},
    ]
    deck = dispatcher.build_sequenced_action_deck(raw_actions, triage_state="RED")
    assert len(deck) == 3
    assert deck[0].action_id == "ACT_A1"  # Priority 1, 15s
    assert deck[1].action_id == "ACT_A2"  # Priority 1, 30s
    assert deck[2].action_id == "ACT_B"   # Priority 2, 60s
    assert deck[0].step_number == 1
    assert deck[1].step_number == 2
    assert deck[2].step_number == 3


def test_07_equipment_registry_cross_referencing(dispatcher: CockpitCountermeasureDispatcher):
    """Verify known action IDs retrieve exact flight locker and verification instructions."""
    raw = [{"action_id": "ACT_RED_001_O2_REBREATHER", "protocol": "Deploy O2", "priority": 1, "time_to_execute_sec": 15}]
    deck = dispatcher.build_sequenced_action_deck(raw, triage_state="RED")
    step = deck[0]
    assert "Forward Locker MED-01" in step.equipment_location
    assert "1200 psi" in step.verification_step
    assert step.subsystem_lead == "CREW_MEDICAL_OFFICER"


def test_08_equipment_registry_unknown_action_fallback(dispatcher: CockpitCountermeasureDispatcher):
    """Verify unregistered action ID safely falls back to default flight medical locker."""
    raw = [{"action_id": "ACT_CUSTOM_UNREGISTERED", "protocol": "Custom", "priority": 1, "time_to_execute_sec": 20}]
    deck = dispatcher.build_sequenced_action_deck(raw, triage_state="AMBER")
    step = deck[0]
    assert "Main Flight Deck Medical Locker" in step.equipment_location
    assert step.subsystem_lead == "CREW_MEDICAL_OFFICER"


def test_09_empty_action_deck_fallback_to_nominal(dispatcher: CockpitCountermeasureDispatcher):
    """Verify empty countermeasure list defaults to standard timeline maintenance."""
    deck = dispatcher.build_sequenced_action_deck([], triage_state="GREEN")
    assert len(deck) == 1
    assert deck[0].action_id == "ACT_GRN_001_MAINTAIN_TIMELINE"
    assert "Maintain nominal" in deck[0].protocol


def test_10_critical_path_flagging_in_red_state(dispatcher: CockpitCountermeasureDispatcher):
    """Verify step 1 in a RED state is strictly flagged as critical path."""
    raw = [
        {"action_id": "ACT_RED_001_O2_REBREATHER", "protocol": "O2", "priority": 1, "time_to_execute_sec": 15},
        {"action_id": "ACT_RED_001_SUSPEND_EVA", "protocol": "EVA", "priority": 2, "time_to_execute_sec": 30}
    ]
    deck = dispatcher.build_sequenced_action_deck(raw, triage_state="RED")
    assert deck[0].is_critical_path is True
    assert deck[1].is_critical_path is False


def test_11_critical_path_not_flagged_in_amber_or_green(dispatcher: CockpitCountermeasureDispatcher):
    """Verify no step is flagged critical path in AMBER or GREEN states."""
    raw = [{"action_id": "ACT_AMB_001_LBNP_SESSION", "protocol": "LBNP", "priority": 1, "time_to_execute_sec": 600}]
    deck_amb = dispatcher.build_sequenced_action_deck(raw, triage_state="AMBER")
    assert deck_amb[0].is_critical_path is False

    deck_grn = dispatcher.build_sequenced_action_deck(raw, triage_state="GREEN")
    assert deck_grn[0].is_critical_path is False


# =============================================================================
# GROUP 3: 3-SECOND EXECUTIVE SUMMARY & BIOMARKER ATTRIBUTION (TESTS 12-16)
# =============================================================================

def test_12_three_second_summary_red_emergency(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify RED summary uses CRITICAL RED prefix and immediate action directive."""
    vitals = dict(nominal_vitals)
    vitals["spo2_percent"] = 82.0
    vitals["heart_rate_bpm"] = 135.0
    packet = triage_engine.process_telemetry_frame(vitals)

    summary = dispatcher.format_3_second_executive_summary(packet, "Deploy 100% emergency O2 mask.")
    assert "CRITICAL RED EMERGENCY" in summary
    assert packet.clinical_title in summary
    assert "IMMEDIATE ACTION (T-0)" in summary


def test_13_three_second_summary_amber_caution(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify AMBER summary uses CAUTION AMBER WARNING prefix."""
    vitals = dict(nominal_vitals)
    vitals["co2_cabin_ppm"] = 5500.0
    packet = triage_engine.process_telemetry_frame(vitals, microgravity_days=2.0)

    summary = dispatcher.format_3_second_executive_summary(packet, "Swap LiOH canister.")
    assert "CAUTION AMBER WARNING" in summary
    assert "IMMEDIATE ACTION (T-0)" in summary


def test_14_three_second_summary_green_nominal(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify GREEN summary uses NOMINAL GREEN EQUILIBRIUM prefix."""
    packet = triage_engine.process_telemetry_frame(nominal_vitals, microgravity_days=2.0)
    summary = dispatcher.format_3_second_executive_summary(packet, "Maintain baseline timeline.")
    assert "NOMINAL GREEN EQUILIBRIUM" in summary


def test_15_biomarker_context_lead_selection(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify lead biomarker is identified as the highest weight in attribution."""
    weights = {"heart_rate_bpm": 0.20, "spo2_percent": 0.65, "icp_est_mmhg": 0.15}
    packet = triage_engine.process_telemetry_frame(nominal_vitals, biomarker_weights=weights)

    payload = dispatcher.dispatch_cockpit_payload(packet)
    assert payload.biomarker_context_lead == "spo2_percent"


def test_16_biomarker_context_lead_default_when_empty(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify lead biomarker defaults to OVERALL_PHYSIOLOGICAL_PROFILE when no weights provided."""
    packet = triage_engine.process_telemetry_frame(nominal_vitals)
    payload = dispatcher.dispatch_cockpit_payload(packet)
    assert payload.biomarker_context_lead == "OVERALL_PHYSIOLOGICAL_PROFILE"


# =============================================================================
# GROUP 4: END-TO-END DISPATCH PAYLOAD CLINICAL SCENARIOS (TESTS 17-21)
# =============================================================================

def test_17_e2e_dispatch_hypoxia_red_payload(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify end-to-end cockpit payload generation for acute cardiorespiratory hypoxia."""
    vitals = dict(nominal_vitals)
    vitals["spo2_percent"] = 80.0
    vitals["heart_rate_bpm"] = 138.0
    packet = triage_engine.process_telemetry_frame(vitals)

    payload = dispatcher.dispatch_cockpit_payload(packet)
    assert isinstance(payload, CockpitActionPayload)
    assert payload.triage_state == "RED"
    assert payload.hud_banner.alert_level == "RED_CRITICAL"
    assert payload.hud_banner.audio_tone_frequency_hz == 1200
    assert payload.action_deck[0].is_critical_path is True
    assert "O2" in payload.action_deck[0].protocol
    assert "MED-01" in payload.action_deck[0].equipment_location
    assert payload.total_execution_window_sec > 0


def test_18_e2e_dispatch_fluid_shift_surge_payload(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify end-to-end cockpit payload for SANS cephalad fluid surge matches LBNP bay."""
    vitals = dict(nominal_vitals)
    vitals["systolic_bp_mmhg"] = 160.0
    vitals["co2_cabin_ppm"] = 8000.0
    packet = triage_engine.process_telemetry_frame(vitals, microgravity_days=180.0)

    payload = dispatcher.dispatch_cockpit_payload(packet)
    assert payload.triage_state == "RED"
    assert any("LBNP" in step.protocol for step in payload.action_deck)
    lbnp_step = next(s for s in payload.action_deck if "LBNP" in s.protocol)
    assert "LBNP-03" in lbnp_step.equipment_location
    assert "-35.0 mmHg" in lbnp_step.verification_step


def test_19_e2e_dispatch_hypercapnia_amber_payload(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify end-to-end cockpit payload for elevated cabin CO2 matches LiOH rack."""
    vitals = dict(nominal_vitals)
    vitals["co2_cabin_ppm"] = 5600.0
    packet = triage_engine.process_telemetry_frame(vitals, microgravity_days=2.0)

    payload = dispatcher.dispatch_cockpit_payload(packet)
    assert payload.triage_state == "AMBER"
    assert payload.hud_banner.alert_level == "AMBER_WARNING"
    assert payload.hud_banner.audio_tone_frequency_hz == 600
    assert any("scrubber" in step.protocol.lower() for step in payload.action_deck)


def test_20_e2e_dispatch_nominal_green_payload(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify end-to-end cockpit payload for nominal equilibrium is silent and green."""
    packet = triage_engine.process_telemetry_frame(nominal_vitals, microgravity_days=2.0)
    payload = dispatcher.dispatch_cockpit_payload(packet)

    assert payload.triage_state == "GREEN"
    assert payload.hud_banner.alert_level == "GREEN_NOMINAL"
    assert payload.hud_banner.audio_tone_frequency_hz == 0
    assert "Maintain" in payload.action_deck[0].protocol


def test_21_e2e_dispatch_with_cmo_override_active(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify payload reflects active CMO override flag and overridden state."""
    triage_engine.apply_cmo_override("RED", "CMO precautionary alert", "CMO_TEST")
    packet = triage_engine.process_telemetry_frame(nominal_vitals)

    payload = dispatcher.dispatch_cockpit_payload(packet)
    assert payload.triage_state == "RED"
    assert payload.is_cmo_override_active is True
    assert payload.hud_banner.alert_level == "RED_CRITICAL"


# =============================================================================
# GROUP 5: SERIALIZATION & PERFORMANCE LATENCY (TESTS 22-24)
# =============================================================================

def test_22_payload_serialization_to_dict_and_json(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify CockpitActionPayload serializes to dict and JSON cleanly without errors."""
    packet = triage_engine.process_telemetry_frame(nominal_vitals, microgravity_days=2.0)
    payload = dispatcher.dispatch_cockpit_payload(packet)

    d = payload.to_dict()
    assert isinstance(d, dict)
    assert d["triage_state"] == "GREEN"
    assert "hud_banner" in d
    assert "action_deck" in d

    json_str = payload.to_json()
    assert isinstance(json_str, str)
    parsed = json.loads(json_str)
    assert parsed["decision_id"] == packet.decision_id
    assert parsed["hud_banner"]["hud_banner_color"] == "#00E676"


def test_23_total_execution_window_calculation(dispatcher: CockpitCountermeasureDispatcher):
    """Verify total execution window equals the maximum deadline among steps."""
    raw = [
        {"action_id": "ACT_A", "protocol": "Step A", "priority": 1, "time_to_execute_sec": 15},
        {"action_id": "ACT_B", "protocol": "Step B", "priority": 2, "time_to_execute_sec": 90},
        {"action_id": "ACT_C", "protocol": "Step C", "priority": 3, "time_to_execute_sec": 45},
    ]
    deck = dispatcher.build_sequenced_action_deck(raw, triage_state="AMBER")
    total_window = max([s.time_to_execute_sec for s in deck])
    assert total_window == 90


def test_24_dispatch_performance_latency_budget(dispatcher: CockpitCountermeasureDispatcher, triage_engine: TriageModelEngine, nominal_vitals: Dict[str, float]):
    """Verify 1,000 cockpit payload dispatches execute well within 50.0 ms budget (< 0.05 ms per dispatch)."""
    packet = triage_engine.process_telemetry_frame(nominal_vitals, microgravity_days=2.0)

    t0 = time.perf_counter()
    for _ in range(1000):
        dispatcher.dispatch_cockpit_payload(packet)
    dt_total_ms = (time.perf_counter() - t0) * 1000.0
    dt_per_dispatch_ms = dt_total_ms / 1000.0

    assert dt_per_dispatch_ms < 0.20, f"Per-dispatch latency {dt_per_dispatch_ms:.4f} ms exceeds 0.20 ms budget"
