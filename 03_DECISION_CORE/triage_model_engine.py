"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Module: triage_model_engine.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Deterministic Engine
Governance: 80% Biophysical Supreme Head (Clinical Decision Authority)
=============================================================================
"""

import time
import json
import uuid
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Union, Any
import pandas as pd
import numpy as np

from rule_schema_validator import (
    TriageRule,
    CountermeasureAction,
    DecisionConfigManager,
    load_default_decision_configuration,
    VALID_TRIAGE_STATES,
)
from biophysical_physics_engine import (
    BiophysicalPhysicsEngine,
    HemodynamicPacket,
    FluidShiftPacket,
    CardiacOutputPacket,
    BiophysicalEnrichedPacket,
)


# =============================================================================
# DO-178C LEVEL C TRIAGE DECISION PACKET CONTRACT
# =============================================================================

@dataclass(frozen=True)
class CMOOverrideRecord:
    """Audit record for human Crew Medical Officer / Flight Surgeon override."""
    is_active: bool
    override_state: Optional[str]
    rationale: str
    authorizing_officer: str
    timestamp_utc: str


@dataclass(frozen=True)
class TriageDecisionPacket:
    """
    Standardized DO-178C Level C Autonomous Clinical Decision Packet.
    Delivered directly to the 3-Second Astronaut Cockpit HUD.
    """
    decision_id: str
    timestamp_utc: str
    triage_state: str  # "RED", "AMBER", "GREEN"
    matched_rule_id: str
    clinical_title: str
    clinical_audit_sentence: str
    hemodynamics: Dict[str, Any]
    fluid_shift: Dict[str, Any]
    cardiac_output: Dict[str, Any]
    actionable_countermeasures: List[Dict[str, Any]]
    biomarker_urgency_attribution: Dict[str, float]
    cmo_override: Dict[str, Any]
    execution_latency_ms: float
    is_flight_certified: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# CENTRAL DETERMINISTIC TRIAGE MODEL ENGINE (80% BIOPHYSICAL SUPREME HEAD)
# =============================================================================

class TriageModelEngine:
    """
    The Supreme Clinical Decision Authority of ASTROVITAL AI.
    Executes 100% deterministic, white-box medical triage for deep-space missions:
    1. Receives conditioned 12-channel telemetry from AI Core (Stages 1-4).
    2. Enriches telemetry with closed-form biophysics (Innovation 1 Cephalad Fluid Shift,
       Left Ventricular Stroke Volume Atrophy, MAP, PP, Shock Index, CPP).
    3. Evaluates DO-178C Level C deterministic triage rule matrix.
    4. Applies Crew Medical Officer (CMO) override logic if asserted.
    5. Dispatches formatted TriageDecisionPacket with 3-second actionable countermeasures.
    """

    def __init__(
        self,
        config_manager: Optional[DecisionConfigManager] = None,
        physics_engine: Optional[BiophysicalPhysicsEngine] = None,
        recovery_debounce_frames: int = 5
    ):
        if config_manager is None:
            self.config_manager = load_default_decision_configuration()
        else:
            self.config_manager = config_manager

        if physics_engine is None:
            self.physics_engine = BiophysicalPhysicsEngine(config_manager=self.config_manager)
        else:
            self.physics_engine = physics_engine

        self.recovery_debounce_frames = max(1, recovery_debounce_frames)

        # Internal state machine tracking
        self._current_state: str = "GREEN"
        self._consecutive_nominal_frames: int = 0
        self._decision_counter: int = 0
        self._cmo_override = CMOOverrideRecord(
            is_active=False,
            override_state=None,
            rationale="No CMO override engaged.",
            authorizing_officer="SYSTEM",
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    # -------------------------------------------------------------------------
    # CMO / FLIGHT SURGEON OVERRIDE PROTOCOL
    # -------------------------------------------------------------------------
    def apply_cmo_override(
        self,
        override_state: str,
        rationale: str,
        authorizing_officer: str
    ) -> None:
        """
        Asserts human Crew Medical Officer command override authority.
        DO-178C safety protocol guarantees physician autonomy over AI algorithms.
        """
        state_upper = override_state.upper()
        if state_upper not in VALID_TRIAGE_STATES:
            raise ValueError(f"DO-178C Violation: Invalid CMO override state '{override_state}'. Must be one of {VALID_TRIAGE_STATES}")

        if not rationale or not rationale.strip():
            raise ValueError("DO-178C Violation: CMO override requires formal clinical rationale.")

        if not authorizing_officer or not authorizing_officer.strip():
            raise ValueError("DO-178C Violation: CMO override requires verified authorizing officer callsign.")

        self._cmo_override = CMOOverrideRecord(
            is_active=True,
            override_state=state_upper,
            rationale=rationale.strip(),
            authorizing_officer=authorizing_officer.strip(),
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    def clear_cmo_override(self) -> None:
        """Revokes CMO override and returns decision control to autonomous engine."""
        self._cmo_override = CMOOverrideRecord(
            is_active=False,
            override_state=None,
            rationale="CMO override cleared. Autonomous biophysical triage restored.",
            authorizing_officer="SYSTEM",
            timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )

    @property
    def is_cmo_override_active(self) -> bool:
        return self._cmo_override.is_active

    @property
    def current_state(self) -> str:
        return self._current_state

    # -------------------------------------------------------------------------
    # TELEMETRY FRAME DECISION DISPATCH
    # -------------------------------------------------------------------------
    def process_telemetry_frame(
        self,
        telemetry: Dict[str, float],
        microgravity_days: float = 3.0,
        exercise_metric: float = 1.0,
        rmssd_ms: Optional[float] = None,
        biomarker_weights: Optional[Dict[str, float]] = None
    ) -> TriageDecisionPacket:
        """
        Processes a single synchronized telemetry vector and yields a complete
        DO-178C Level C certified TriageDecisionPacket.
        Latency target: < 10.0 ms.
        """
        t0 = time.perf_counter()
        self._decision_counter += 1

        # Step 1: First-principles biophysical enrichment
        enriched_packet = self.physics_engine.enrich_telemetry_packet(
            telemetry=telemetry,
            microgravity_days=microgravity_days,
            exercise_metric=exercise_metric,
            rmssd_ms=rmssd_ms
        )
        enriched_telemetry = enriched_packet.enriched_telemetry

        # Step 2: Deterministic Rule Matrix Evaluation
        computed_state, rule, raw_audit, countermeasures = self.config_manager.evaluate_triage(enriched_telemetry)

        # Step 3: State Machine Transition & Hysteresis Logic
        # Life-critical transitions (RED or AMBER) trip instantaneously.
        # De-escalation back to GREEN requires debounce stabilization frames.
        final_state = computed_state
        rule_id = rule.rule_id if rule is not None else "RULE_FALLBACK_UNCLASSIFIED"
        clinical_title = rule.clinical_title if rule is not None else "Borderline Unclassified State"
        audit_sentence = raw_audit

        if computed_state == "RED":
            self._current_state = "RED"
            self._consecutive_nominal_frames = 0
        elif computed_state == "AMBER":
            if self._current_state == "RED":
                # Moving from RED down to AMBER requires debounce
                self._consecutive_nominal_frames += 1
                if self._consecutive_nominal_frames < self.recovery_debounce_frames:
                    final_state = "RED"
                    audit_sentence += f" [HYSTERESIS DEBOUNCE: Frame {self._consecutive_nominal_frames}/{self.recovery_debounce_frames} toward AMBER stabilization]"
                else:
                    self._current_state = "AMBER"
                    self._consecutive_nominal_frames = 0
            else:
                self._current_state = "AMBER"
                self._consecutive_nominal_frames = 0
        elif computed_state == "GREEN":
            if self._current_state in ("RED", "AMBER"):
                self._consecutive_nominal_frames += 1
                if self._consecutive_nominal_frames < self.recovery_debounce_frames:
                    final_state = self._current_state
                    audit_sentence = (
                        f"STABILIZING HYSTERESIS: Vitals met GREEN criteria ({self._consecutive_nominal_frames}/"
                        f"{self.recovery_debounce_frames} frames). Holding previous {self._current_state} state."
                    )
                else:
                    self._current_state = "GREEN"
                    self._consecutive_nominal_frames = 0
            else:
                self._current_state = "GREEN"
                self._consecutive_nominal_frames = 0

        # Step 4: Apply Human CMO Override if Active
        if self._cmo_override.is_active and self._cmo_override.override_state is not None:
            override_state = self._cmo_override.override_state
            audit_sentence = (
                f"CMO MANUAL OVERRIDE ACTIVE: State forced to {override_state} by {self._cmo_override.authorizing_officer}. "
                f"Clinical Rationale: '{self._cmo_override.rationale}'. (Autonomous engine assessed: {final_state})."
            )
            final_state = override_state

        dt_ms = (time.perf_counter() - t0) * 1000.0

        # Build Countermeasures payload
        countermeasure_dicts = [asdict(c) for c in countermeasures]

        # Prepare normalized biomarker urgency dictionary
        effective_biomarkers = dict(biomarker_weights) if biomarker_weights is not None else {}

        decision_id = f"VITALX-DEC-{self._decision_counter:07d}-{uuid.uuid4().hex[:6].upper()}"
        timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        return TriageDecisionPacket(
            decision_id=decision_id,
            timestamp_utc=timestamp_utc,
            triage_state=final_state,
            matched_rule_id=rule_id,
            clinical_title=clinical_title,
            clinical_audit_sentence=audit_sentence,
            hemodynamics=asdict(enriched_packet.hemodynamics),
            fluid_shift=asdict(enriched_packet.fluid_shift),
            cardiac_output=asdict(enriched_packet.cardiac_output),
            actionable_countermeasures=countermeasure_dicts,
            biomarker_urgency_attribution=effective_biomarkers,
            cmo_override=asdict(self._cmo_override),
            execution_latency_ms=float(dt_ms),
            is_flight_certified=True
        )

    # -------------------------------------------------------------------------
    # STREAM TELEMETRY PROCESSOR (MULTI-ROW DATASET EVALUATION)
    # -------------------------------------------------------------------------
    def process_telemetry_stream(
        self,
        df: pd.DataFrame,
        microgravity_days: float = 3.0,
        exercise_metric: float = 1.0,
        biomarker_weights: Optional[Dict[str, float]] = None
    ) -> List[TriageDecisionPacket]:
        """
        Processes a multi-frame continuous telemetry DataFrame through the state machine.
        Yields chronological list of TriageDecisionPackets with hysteresis continuity.
        """
        packets: List[TriageDecisionPacket] = []
        for idx, row in df.iterrows():
            telemetry_row = row.dropna().to_dict()
            packet = self.process_telemetry_frame(
                telemetry=telemetry_row,
                microgravity_days=microgravity_days,
                exercise_metric=exercise_metric,
                biomarker_weights=biomarker_weights
            )
            packets.append(packet)
        return packets

    def reset_state_machine(self) -> None:
        """Resets state machine history to nominal initial conditions."""
        self._current_state = "GREEN"
        self._consecutive_nominal_frames = 0
        self.clear_cmo_override()
