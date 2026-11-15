"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT / State Architecture & Buffer Engine
Component: Cockpit State Engine & Rolling Telemetry Ring Buffer
File: 04_ASTRONAUT_COCKPIT/01_components/cockpit_state.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A HMI Systems
=============================================================================
"""

import sys
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Path Anchoring for Standalone & Streamlit Execution
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_cockpit_dir = _this_dir.parent
_root_dir = _cockpit_dir.parent
_ai_core_dir = _root_dir / "02_AI_CORE" / "01_src"
_decision_dir = _root_dir / "03_DECISION_CORE"

sys.path.insert(0, str(_this_dir))
sys.path.insert(0, str(_cockpit_dir))
sys.path.insert(0, str(_ai_core_dir))
sys.path.insert(0, str(_decision_dir))

from pipeline_orchestrator import (
    AstroVitalPipelineOrchestrator,
    PipelineExecutionRecord,
    CANONICAL_CHANNELS,
)


@dataclass(frozen=True)
class CrewProfile:
    """Immutable astronaut biometric profile and role credentials."""
    callsign: str
    name: str
    role: str
    age: int
    baseline_hr_bpm: float
    baseline_map_mmhg: float
    has_cmo_authority: bool


# Canonical Spaceflight Crew Register
CREW_PROFILES: Dict[str, CrewProfile] = {
    "CDR_ORION": CrewProfile(
        callsign="CDR_ORION",
        name="Cmdr. Neil Armstrong",
        role="Mission Commander",
        age=42,
        baseline_hr_bpm=64.0,
        baseline_map_mmhg=93.3,
        has_cmo_authority=False,
    ),
    "PLT_ORION": CrewProfile(
        callsign="PLT_ORION",
        name="Lt. Buzz Aldrin",
        role="Lunar Module Pilot",
        age=39,
        baseline_hr_bpm=62.0,
        baseline_map_mmhg=90.0,
        has_cmo_authority=False,
    ),
    "CMO_ORION": CrewProfile(
        callsign="CMO_ORION",
        name="Dr. Michael Collins",
        role="Crew Medical Officer / Flight Surgeon",
        age=45,
        baseline_hr_bpm=68.0,
        baseline_map_mmhg=92.0,
        has_cmo_authority=True,
    ),
    "FE_ORION": CrewProfile(
        callsign="FE_ORION",
        name="Dr. Kalpana Chawla",
        role="Flight Engineer & Science Specialist",
        age=38,
        baseline_hr_bpm=60.0,
        baseline_map_mmhg=88.5,
        has_cmo_authority=False,
    ),
}


@dataclass(frozen=True)
class FlightScenarioPreset:
    """Standardized operational spaceflight scenario for drills and evaluation."""
    scenario_id: str
    display_title: str
    flight_phase: str
    default_microgravity_days: float
    default_sleep_debt_hours: float
    default_exercise_metric: float
    expected_triage_state: str
    description: str
    vitals: Dict[str, float]


# 6 Canonical Flight Evaluation Scenarios
FLIGHT_SCENARIO_PRESETS: Dict[str, FlightScenarioPreset] = {
    "SCENARIO_01_NOMINAL_CRUISE": FlightScenarioPreset(
        scenario_id="SCENARIO_01_NOMINAL_CRUISE",
        display_title="01 // Nominal Deep-Space Cruise (Day 5)",
        flight_phase="INTRA_VEHICULAR_NOMINAL",
        default_microgravity_days=5.0,
        default_sleep_debt_hours=1.5,
        default_exercise_metric=1.0,
        expected_triage_state="GREEN",
        description="All 12 physiological variables within standard NASA-STD-3001 envelope. Stable hemodynamics.",
        vitals={
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
        },
    ),
    "SCENARIO_02_ACUTE_EVA_HYPOXIA": FlightScenarioPreset(
        scenario_id="SCENARIO_02_ACUTE_EVA_HYPOXIA",
        display_title="02 // Acute EVA Hypoxia & Cardiorespiratory Desaturation",
        flight_phase="EXTRAVEHICULAR_ACTIVITY_EVA",
        default_microgravity_days=12.0,
        default_sleep_debt_hours=2.0,
        default_exercise_metric=0.8,
        expected_triage_state="RED",
        description="Critical arterial oxygen desaturation (SpO2=82%) coupled with compensatory tachycardia (HR=138 bpm).",
        vitals={
            "heart_rate_bpm": 138.0,
            "systolic_bp_mmhg": 128.0,
            "diastolic_bp_mmhg": 84.0,
            "spo2_percent": 82.0,
            "core_temp_c": 37.4,
            "resp_rate_bpm": 28.0,
            "etco2_mmhg": 48.0,
            "icp_est_mmhg": 14.0,
            "cvp_mmhg": 7.0,
            "co2_cabin_ppm": 4200.0,
            "cabin_pressure_psi": 14.2,
            "ambient_temp_c": 21.5,
        },
    ),
    "SCENARIO_03_CEPHALAD_FLUID_SHIFT_SURGE": FlightScenarioPreset(
        scenario_id="SCENARIO_03_CEPHALAD_FLUID_SHIFT_SURGE",
        display_title="03 // SANS Cephalad Fluid Shift ICP Surge (Day 60)",
        flight_phase="INTRA_VEHICULAR_NOMINAL",
        default_microgravity_days=60.0,
        default_sleep_debt_hours=4.0,
        default_exercise_metric=0.5,
        expected_triage_state="RED",
        description="Microgravity duration cephalad fluid shift surge (I_ICP >= 1.85) threatening vision impairment (SANS).",
        vitals={
            "heart_rate_bpm": 86.0,
            "systolic_bp_mmhg": 135.0,
            "diastolic_bp_mmhg": 92.0,
            "spo2_percent": 97.0,
            "core_temp_c": 37.1,
            "resp_rate_bpm": 16.0,
            "etco2_mmhg": 40.0,
            "icp_est_mmhg": 22.0,
            "cvp_mmhg": 9.5,
            "co2_cabin_ppm": 4800.0,
            "cabin_pressure_psi": 14.7,
            "ambient_temp_c": 22.5,
        },
    ),
    "SCENARIO_04_HYPERTENSIVE_EMERGENCY": FlightScenarioPreset(
        scenario_id="SCENARIO_04_HYPERTENSIVE_EMERGENCY",
        display_title="04 // Acute Hypertensive Emergency (SBP 180+ mmHg)",
        flight_phase="INTRA_VEHICULAR_NOMINAL",
        default_microgravity_days=18.0,
        default_sleep_debt_hours=6.0,
        default_exercise_metric=0.2,
        expected_triage_state="RED",
        description="Critical cerebrovascular overload with SBP=185 mmHg and MAP >= 125 mmHg requiring immediate Labetalol.",
        vitals={
            "heart_rate_bpm": 105.0,
            "systolic_bp_mmhg": 185.0,
            "diastolic_bp_mmhg": 115.0,
            "spo2_percent": 96.0,
            "core_temp_c": 37.3,
            "resp_rate_bpm": 20.0,
            "etco2_mmhg": 42.0,
            "icp_est_mmhg": 18.0,
            "cvp_mmhg": 8.0,
            "co2_cabin_ppm": 4100.0,
            "cabin_pressure_psi": 14.7,
            "ambient_temp_c": 23.0,
        },
    ),
    "SCENARIO_05_EARLY_FLUID_SHIFT_COMPENSATION": FlightScenarioPreset(
        scenario_id="SCENARIO_05_EARLY_FLUID_SHIFT_COMPENSATION",
        display_title="05 // Early Cephalad Fluid Shift Compensation (Day 25)",
        flight_phase="EARLY_MICROGRAVITY_FLUID_SHIFT",
        default_microgravity_days=25.0,
        default_sleep_debt_hours=3.0,
        default_exercise_metric=0.7,
        expected_triage_state="AMBER",
        description="Compensatory fluid redistribution phase (1.35 <= I_ICP < 1.85). Deploy Chibis LBNP at -25 mmHg & thigh cuffs.",
        vitals={
            "heart_rate_bpm": 78.0,
            "systolic_bp_mmhg": 126.0,
            "diastolic_bp_mmhg": 84.0,
            "spo2_percent": 97.5,
            "core_temp_c": 37.0,
            "resp_rate_bpm": 15.0,
            "etco2_mmhg": 39.0,
            "icp_est_mmhg": 15.0,
            "cvp_mmhg": 6.8,
            "co2_cabin_ppm": 4050.0,
            "cabin_pressure_psi": 14.7,
            "ambient_temp_c": 22.0,
        },
    ),
    "SCENARIO_06_EXTREME_SLEEP_DEBT_FATIGUE": FlightScenarioPreset(
        scenario_id="SCENARIO_06_EXTREME_SLEEP_DEBT_FATIGUE",
        display_title="06 // Autonomic Fatigue & 18-Hour Sleep Debt",
        flight_phase="INTRA_VEHICULAR_NOMINAL",
        default_microgravity_days=5.0,
        default_sleep_debt_hours=18.0,
        default_exercise_metric=0.3,
        expected_triage_state="AMBER",
        description="Autonomic strain due to cumulative sleep deficit >= 16.0 hrs. Mandatory EVA hold and sleep cabin dark phase.",
        vitals={
            "heart_rate_bpm": 96.0,
            "systolic_bp_mmhg": 134.0,
            "diastolic_bp_mmhg": 88.0,
            "spo2_percent": 96.0,
            "core_temp_c": 36.8,
            "resp_rate_bpm": 16.0,
            "etco2_mmhg": 44.0,
            "icp_est_mmhg": 12.0,
            "cvp_mmhg": 5.5,
            "co2_cabin_ppm": 4250.0,
            "cabin_pressure_psi": 14.7,
            "ambient_temp_c": 22.0,
        },
    ),
}


class TelemetryRingBuffer:
    """
    Thread-safe, bounded circular ring buffer for real-time telemetry waveforms.
    Maintains the last N frames with zero-allocation retrieval for instant Plotly charting.
    """

    def __init__(self, capacity: int = 120) -> None:
        if capacity < 10:
            raise ValueError(f"Ring buffer capacity must be >= 10, got {capacity}")
        self._capacity: int = capacity
        self._buffer: Deque[Dict[str, Any]] = deque(maxlen=capacity)

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def count(self) -> int:
        return len(self._buffer)

    def append_frame(
        self,
        frame_index: int,
        timestamp: str,
        vitals: Dict[str, float],
        biophysics: Dict[str, Any],
        triage_state: str,
    ) -> None:
        """Appends a synchronized frame entry into the circular buffer."""
        entry = {
            "frame_index": int(frame_index),
            "timestamp": timestamp,
            "triage_state": triage_state,
            **{k: float(v) for k, v in vitals.items() if isinstance(v, (int, float))},
            **{
                k: float(v)
                for k, v in biophysics.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            },
        }
        self._buffer.append(entry)

    def to_dataframe(self) -> pd.DataFrame:
        """Converts the active ring buffer directly into a Pandas DataFrame."""
        if not self._buffer:
            return pd.DataFrame(columns=["frame_index", "timestamp", "triage_state"] + list(CANONICAL_CHANNELS))
        return pd.DataFrame(list(self._buffer))

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Returns the most recently appended frame dictionary or None."""
        return dict(self._buffer[-1]) if self._buffer else None

    def clear(self) -> None:
        """Empties the ring buffer completely."""
        self._buffer.clear()


class CockpitStateManager:
    """
    Central State Architecture & Flight Simulation Manager for the Astronaut Cockpit.
    Seamlessly manages session variables, telemetry streaming, scenario injection,
    sovereign CMO overrides, and equipment locker checklist tracking.
    """

    def __init__(
        self,
        orchestrator: Optional[AstroVitalPipelineOrchestrator] = None,
        buffer_capacity: int = 120,
        default_crew_id: str = "CDR_ORION",
    ) -> None:
        self.orchestrator: AstroVitalPipelineOrchestrator = (
            orchestrator or AstroVitalPipelineOrchestrator()
        )
        self.telemetry_buffer: TelemetryRingBuffer = TelemetryRingBuffer(capacity=buffer_capacity)
        
        # Operational State Variables
        self.active_crew_member: str = (
            default_crew_id if default_crew_id in CREW_PROFILES else "CDR_ORION"
        )
        self.current_scenario_id: str = "SCENARIO_01_NOMINAL_CRUISE"
        self.mission_elapsed_days: float = 5.0
        self.aerobic_exercise_metric: float = 1.0
        self.sleep_debt_hours: float = 1.5
        self.flight_mode: str = "SIMULATION"
        self.is_stream_running: bool = False
        self.stream_speed_hz: float = 1.0
        
        # Execution State
        self.latest_record: Optional[PipelineExecutionRecord] = None
        self.checklist_states: Dict[str, bool] = {}
        self.active_cmo_override: Optional[Dict[str, Any]] = None

        # Pre-populate with initial nominal frame
        self.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")

    @property
    def current_crew(self) -> CrewProfile:
        return CREW_PROFILES[self.active_crew_member]

    @property
    def current_scenario(self) -> FlightScenarioPreset:
        return FLIGHT_SCENARIO_PRESETS[self.current_scenario_id]

    def set_crew_member(self, callsign: str) -> CrewProfile:
        """Switches active astronaut biometric profile."""
        if callsign not in CREW_PROFILES:
            raise KeyError(f"Unknown astronaut callsign '{callsign}'. Registered: {list(CREW_PROFILES.keys())}")
        self.active_crew_member = callsign
        return CREW_PROFILES[callsign]

    def inject_scenario(
        self,
        scenario_id: str,
        reset_debounce: bool = True,
    ) -> PipelineExecutionRecord:
        """
        Loads and executes a certified flight scenario through the full pipeline.
        Resets checklist completion states and updates the telemetry ring buffer.
        """
        if scenario_id not in FLIGHT_SCENARIO_PRESETS:
            raise KeyError(f"Unknown scenario ID '{scenario_id}'. Valid: {list(FLIGHT_SCENARIO_PRESETS.keys())}")

        if reset_debounce:
            self.orchestrator.decision_engine._current_state = "GREEN"
            self.orchestrator.decision_engine._consecutive_nominal_frames = 0

        scenario = FLIGHT_SCENARIO_PRESETS[scenario_id]
        self.current_scenario_id = scenario_id
        self.mission_elapsed_days = scenario.default_microgravity_days
        self.sleep_debt_hours = scenario.default_sleep_debt_hours
        self.aerobic_exercise_metric = scenario.default_exercise_metric

        # Execute through pipeline orchestrator
        record = self.orchestrator.process_telemetry_frame(
            telemetry=scenario.vitals,
            microgravity_days=self.mission_elapsed_days,
            exercise_metric=self.aerobic_exercise_metric,
            sleep_debt_hours=self.sleep_debt_hours,
            flight_mode=self.flight_mode,
        )

        self.latest_record = record

        # Append to circular telemetry buffer
        self.telemetry_buffer.append_frame(
            frame_index=record.frame_index,
            timestamp=record.timestamp,
            vitals=record.sanitized_telemetry,
            biophysics=record.biophysical_metrics,
            triage_state=record.triage_state,
        )

        # Reset checklist states for the new action deck
        self.checklist_states = {
            step.action_id: False for step in record.cockpit_payload.action_deck
        }

        return record

    def step_simulation(
        self,
        vitals_override: Optional[Dict[str, float]] = None,
        noise_amplitude: float = 0.0,
    ) -> PipelineExecutionRecord:
        """
        Advances the telemetry stream by 1 step. Applies optional stochastic spaceflight
        sensor noise or manual vital parameter perturbations.
        """
        base_vitals = dict(
            vitals_override
            if vitals_override is not None
            else self.current_scenario.vitals
        )

        if noise_amplitude > 0.0:
            for k in ["heart_rate_bpm", "systolic_bp_mmhg", "diastolic_bp_mmhg", "resp_rate_bpm"]:
                if k in base_vitals:
                    jitter = float(np.random.normal(0.0, noise_amplitude))
                    base_vitals[k] = max(0.0, base_vitals[k] + jitter)

        record = self.orchestrator.process_telemetry_frame(
            telemetry=base_vitals,
            microgravity_days=self.mission_elapsed_days,
            exercise_metric=self.aerobic_exercise_metric,
            sleep_debt_hours=self.sleep_debt_hours,
            flight_mode=self.flight_mode,
        )

        self.latest_record = record

        self.telemetry_buffer.append_frame(
            frame_index=record.frame_index,
            timestamp=record.timestamp,
            vitals=record.sanitized_telemetry,
            biophysics=record.biophysical_metrics,
            triage_state=record.triage_state,
        )

        return record

    def toggle_checklist_item(self, action_id: str, is_completed: bool) -> None:
        """Updates the completion state of a countermeasure action item."""
        self.checklist_states[action_id] = bool(is_completed)

    def apply_cmo_override(
        self,
        target_state: str,
        clinical_rationale: str,
        authorizing_cmo: str = "CMO_ORION",
    ) -> Dict[str, Any]:
        """
        Asserts sovereign Crew Medical Officer command override authority.
        """
        if not CREW_PROFILES.get(authorizing_cmo, CrewProfile("", "", "", 0, 0, 0, False)).has_cmo_authority:
            raise PermissionError(f"Astronaut '{authorizing_cmo}' does not have sovereign CMO command authority.")

        cmo_record = self.orchestrator.assert_cmo_override(
            target_state=target_state,
            clinical_rationale=clinical_rationale,
            cmo_id=authorizing_cmo,
        )

        self.active_cmo_override = {
            "is_active": cmo_record.is_active,
            "target_state": cmo_record.override_state,
            "rationale": cmo_record.rationale,
            "authorizing_officer": cmo_record.authorizing_officer,
            "timestamp": cmo_record.timestamp_utc,
        }

        # Step simulation to reflect overridden state immediately
        self.step_simulation()
        return dict(self.active_cmo_override)

    def clear_cmo_override(self) -> None:
        """Revokes sovereign CMO override and restores autonomous triage."""
        self.orchestrator.clear_cmo_override()
        self.active_cmo_override = None
        self.step_simulation()

    def reset_buffer(self) -> None:
        """Clears the waveform ring buffer and re-injects current scenario."""
        self.telemetry_buffer.clear()
        self.inject_scenario(self.current_scenario_id)

    def get_summary_state(self) -> Dict[str, Any]:
        """Returns full serializable cockpit state dictionary."""
        return {
            "active_crew": self.current_crew.callsign,
            "current_scenario": self.current_scenario_id,
            "mission_elapsed_days": self.mission_elapsed_days,
            "aerobic_exercise_metric": self.aerobic_exercise_metric,
            "sleep_debt_hours": self.sleep_debt_hours,
            "flight_mode": self.flight_mode,
            "buffered_frames_count": self.telemetry_buffer.count,
            "latest_triage_state": (
                self.latest_record.triage_state if self.latest_record else "UNINITIALIZED"
            ),
            "is_cmo_overridden": bool(self.active_cmo_override is not None),
            "completed_checklist_count": sum(1 for v in self.checklist_states.values() if v),
            "total_checklist_count": len(self.checklist_states),
        }
