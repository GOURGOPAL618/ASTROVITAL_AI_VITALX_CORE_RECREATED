"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_cockpit_state.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A HMI Systems
Verification: 100% Statement Coverage on cockpit_state.py
=============================================================================
"""

import sys
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd
import pytest

# Ensure cockpit, ai_core, and decision dirs are on sys.path
root_dir = Path(__file__).resolve().parent.parent
cockpit_dir = root_dir / "04_ASTRONAUT_COCKPIT"
cockpit_comp = cockpit_dir / "01_components"
ai_core_src = root_dir / "02_AI_CORE" / "01_src"
decision_dir = root_dir / "03_DECISION_CORE"

import importlib
for p in [str(cockpit_comp), str(cockpit_dir), str(ai_core_src), str(decision_dir)]:
    sys.path.insert(0, p)

importlib.import_module("01_components")

from cockpit_state import (
    CrewProfile,
    CREW_PROFILES,
    FlightScenarioPreset,
    FLIGHT_SCENARIO_PRESETS,
    TelemetryRingBuffer,
    CockpitStateManager,
)


# =============================================================================
# 1. CREW PROFILE & SCENARIO REGISTRY INTEGRITY
# =============================================================================

def test_01_crew_profiles_integrity():
    """Verifies the registered astronaut crew profiles and medical permissions."""
    assert len(CREW_PROFILES) == 4
    assert "CDR_ORION" in CREW_PROFILES
    assert "PLT_ORION" in CREW_PROFILES
    assert "CMO_ORION" in CREW_PROFILES
    assert "FE_ORION" in CREW_PROFILES

    cmo = CREW_PROFILES["CMO_ORION"]
    assert cmo.has_cmo_authority is True
    assert cmo.role == "Crew Medical Officer / Flight Surgeon"

    cdr = CREW_PROFILES["CDR_ORION"]
    assert cdr.has_cmo_authority is False


def test_02_flight_scenario_presets_integrity():
    """Verifies that all 6 spaceflight scenarios are properly formed."""
    assert len(FLIGHT_SCENARIO_PRESETS) == 6
    for sc_id, sc in FLIGHT_SCENARIO_PRESETS.items():
        assert sc.scenario_id == sc_id
        assert sc.expected_triage_state in ["GREEN", "AMBER", "RED"]
        assert len(sc.vitals) == 12
        assert sc.default_microgravity_days > 0


# =============================================================================
# 2. TELEMETRY RING BUFFER TESTS
# =============================================================================

def test_03_telemetry_ring_buffer_initialization():
    """Verifies ring buffer capacity constraints and defensive bounds."""
    buf = TelemetryRingBuffer(capacity=60)
    assert buf.capacity == 60
    assert buf.count == 0

    with pytest.raises(ValueError, match="capacity must be >= 10"):
        TelemetryRingBuffer(capacity=5)


def test_04_telemetry_ring_buffer_append_and_overflow():
    """Verifies FIFO sliding window behavior under continuous stream overflow."""
    buf = TelemetryRingBuffer(capacity=10)
    for i in range(1, 16):
        buf.append_frame(
            frame_index=i,
            timestamp=f"2026-11-14T19:00:{i:02d}Z",
            vitals={"heart_rate_bpm": 70.0 + i},
            biophysics={"map_mmhg": 90.0 + i},
            triage_state="GREEN"
        )

    assert buf.count == 10
    latest = buf.get_latest()
    assert latest is not None
    assert latest["frame_index"] == 15
    assert latest["heart_rate_bpm"] == 85.0


def test_05_telemetry_ring_buffer_to_dataframe():
    """Verifies fast conversion of buffer to Pandas DataFrame."""
    buf = TelemetryRingBuffer(capacity=20)
    df_empty = buf.to_dataframe()
    assert df_empty.empty
    assert "frame_index" in df_empty.columns

    buf.append_frame(
        frame_index=1,
        timestamp="2026-11-14T19:00:00Z",
        vitals={"heart_rate_bpm": 72.0, "spo2_percent": 98.0},
        biophysics={"map_mmhg": 93.3},
        triage_state="GREEN"
    )
    df_pop = buf.to_dataframe()
    assert len(df_pop) == 1
    assert df_pop.iloc[0]["heart_rate_bpm"] == 72.0


def test_06_telemetry_ring_buffer_clear():
    """Verifies complete buffer clearing."""
    buf = TelemetryRingBuffer(capacity=20)
    buf.append_frame(1, "t0", {"heart_rate_bpm": 70.0}, {}, "GREEN")
    assert buf.count == 1
    buf.clear()
    assert buf.count == 0
    assert buf.get_latest() is None


# =============================================================================
# 3. COCKPIT STATE MANAGER INITIALIZATION & CREW SELECTION
# =============================================================================

def test_07_cockpit_state_manager_initialization():
    """Verifies default startup state of CockpitStateManager."""
    mgr = CockpitStateManager()
    assert mgr.active_crew_member == "CDR_ORION"
    assert mgr.current_crew.name == "Cmdr. Neil Armstrong"
    assert mgr.current_scenario_id == "SCENARIO_01_NOMINAL_CRUISE"
    assert mgr.latest_record is not None
    assert mgr.latest_record.triage_state == "GREEN"
    assert mgr.telemetry_buffer.count >= 1


def test_08_set_crew_member_success_and_invalid():
    """Verifies switching crew members and defensive rejection of invalid callsigns."""
    mgr = CockpitStateManager()
    cmo = mgr.set_crew_member("CMO_ORION")
    assert cmo.callsign == "CMO_ORION"
    assert mgr.active_crew_member == "CMO_ORION"

    with pytest.raises(KeyError, match="Unknown astronaut callsign"):
        mgr.set_crew_member("UNKNOWN_CREW")


# =============================================================================
# 4. SCENARIO INJECTION & SIMULATION STEPPING
# =============================================================================

def test_09_inject_all_canonical_scenarios():
    """Verifies that all 6 certified scenarios inject and produce expected triage states."""
    mgr = CockpitStateManager()

    rec_01 = mgr.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    assert rec_01.triage_state == "GREEN"

    rec_02 = mgr.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")
    assert rec_02.triage_state == "RED"

    rec_03 = mgr.inject_scenario("SCENARIO_03_CEPHALAD_FLUID_SHIFT_SURGE")
    assert rec_03.triage_state == "RED"

    rec_04 = mgr.inject_scenario("SCENARIO_04_HYPERTENSIVE_EMERGENCY")
    assert rec_04.triage_state == "RED"

    rec_05 = mgr.inject_scenario("SCENARIO_05_EARLY_FLUID_SHIFT_COMPENSATION")
    assert rec_05.triage_state == "AMBER"

    rec_06 = mgr.inject_scenario("SCENARIO_06_EXTREME_SLEEP_DEBT_FATIGUE")
    assert rec_06.triage_state == "AMBER"

    with pytest.raises(KeyError, match="Unknown scenario ID"):
        mgr.inject_scenario("SCENARIO_NON_EXISTENT")


def test_10_step_simulation_nominal_and_noise():
    """Verifies stepping the simulation forward with and without sensor noise."""
    mgr = CockpitStateManager()
    initial_count = mgr.telemetry_buffer.count

    rec_step = mgr.step_simulation()
    assert mgr.telemetry_buffer.count == initial_count + 1
    assert rec_step.frame_index > 0

    # Step with custom vitals override
    override = dict(FLIGHT_SCENARIO_PRESETS["SCENARIO_01_NOMINAL_CRUISE"].vitals)
    override["heart_rate_bpm"] = 80.0
    rec_override = mgr.step_simulation(vitals_override=override)
    assert rec_override.sanitized_telemetry["heart_rate_bpm"] == 80.0

    # Step with noise perturbation
    rec_noise = mgr.step_simulation(noise_amplitude=2.0)
    assert rec_noise.triage_state in ["GREEN", "AMBER", "RED"]


# =============================================================================
# 5. CHECKLIST, CMO OVERRIDE & SUMMARY STATE TESTS
# =============================================================================

def test_11_toggle_checklist_item():
    """Verifies interactive toggle of actionable countermeasure checklist items."""
    mgr = CockpitStateManager()
    mgr.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")
    
    assert len(mgr.checklist_states) > 0
    action_key = list(mgr.checklist_states.keys())[0]

    mgr.toggle_checklist_item(action_key, True)
    assert mgr.checklist_states[action_key] is True

    mgr.toggle_checklist_item(action_key, False)
    assert mgr.checklist_states[action_key] is False


def test_12_apply_cmo_override_success_and_clear():
    """Verifies sovereign CMO manual command override and subsequent revocation."""
    mgr = CockpitStateManager()
    mgr.set_crew_member("CMO_ORION")

    override_record = mgr.apply_cmo_override(
        target_state="RED",
        clinical_rationale="Simulated cardiac arrhythmia during manual hatch ingress drill.",
        authorizing_cmo="CMO_ORION"
    )
    assert override_record["is_active"] is True
    assert override_record["target_state"] == "RED"
    assert mgr.latest_record is not None
    assert mgr.latest_record.triage_state == "RED"

    # Clear override
    mgr.clear_cmo_override()
    assert mgr.active_cmo_override is None
    assert mgr.latest_record.triage_state == "GREEN"


def test_13_apply_cmo_override_unauthorized_crew_raises_permission_error():
    """Verifies that non-physician astronauts cannot assert sovereign overrides."""
    mgr = CockpitStateManager()
    mgr.set_crew_member("CDR_ORION")  # Commander has no CMO authority

    with pytest.raises(PermissionError, match="does not have sovereign CMO command authority"):
        mgr.apply_cmo_override(
            target_state="RED",
            clinical_rationale="Unauthorized attempt.",
            authorizing_cmo="CDR_ORION"
        )


def test_14_reset_buffer():
    """Verifies buffer reset cleans history and re-seeds with current scenario."""
    mgr = CockpitStateManager()
    for _ in range(5):
        mgr.step_simulation()
    assert mgr.telemetry_buffer.count > 1

    mgr.reset_buffer()
    assert mgr.telemetry_buffer.count == 1
    assert mgr.latest_record is not None
    assert mgr.latest_record.triage_state == "GREEN"


def test_15_get_summary_state():
    """Verifies serializable summary state export."""
    mgr = CockpitStateManager()
    summary = mgr.get_summary_state()

    assert isinstance(summary, dict)
    assert summary["active_crew"] == "CDR_ORION"
    assert summary["current_scenario"] == "SCENARIO_01_NOMINAL_CRUISE"
    assert summary["latest_triage_state"] == "GREEN"
    assert summary["is_cmo_overridden"] is False
    assert "buffered_frames_count" in summary
    assert "total_checklist_count" in summary
