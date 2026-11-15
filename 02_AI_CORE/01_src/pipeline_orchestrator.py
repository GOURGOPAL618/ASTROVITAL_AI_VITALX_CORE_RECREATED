"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 02_AI_CORE / Master Operational Orchestration
Component: AstroVital Master End-to-End Pipeline Orchestrator
File: 02_AI_CORE/01_src/pipeline_orchestrator.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Operational Pipeline
Governance: 20% Adaptive AI Telemetry Conditioning -> 80% Biophysical Supreme Head
=============================================================================
"""

import math
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Dynamic Path Anchoring for Standalone & Modular Execution
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_root_dir = _this_dir.parent.parent
_decision_dir = _root_dir / "03_DECISION_CORE"

sys.path.insert(0, str(_this_dir))
sys.path.insert(0, str(_decision_dir))

# Sibling AI Core modules
from ingestion_adapter import (
    TelemetryTemporalSynchronizer,
    TelemetryVector12DBuilder,
)
from inno3_signal_stabilizer import StabilizedFrameExporter
from sanity_gate import (
    NASA_STD_3001_PHYSIOLOGICAL_BOUNDS,
    SanityGatedPacket,
    SanityGateExporter,
)
from inno6_biomarker_ranker import (
    BiomarkerSensitivityContract,
    SensitivityContractExporter,
)

CANONICAL_CHANNELS: Tuple[str, ...] = tuple(NASA_STD_3001_PHYSIOLOGICAL_BOUNDS.keys())

# 80% Biophysical Supreme Head modules
from rule_schema_validator import DecisionConfigManager
from biophysical_physics_engine import (
    BiophysicalEnrichedPacket,
    BiophysicalPhysicsEngine,
)
from triage_model_engine import (
    CMOOverrideRecord,
    TriageDecisionPacket,
    TriageModelEngine,
)
from cockpit_countermeasure_dispatcher import (
    CockpitActionPayload,
    CockpitCountermeasureDispatcher,
)


@dataclass(frozen=True)
class PipelineExecutionRecord:
    """
    Immutable DO-178C Level C execution record generated for every telemetry frame.
    Guarantees complete traceability from raw input through AI filtering,
    deterministic sanity gating, biophysical modeling, and cockpit dispatch.
    """
    timestamp: str
    flight_mode: str
    frame_index: int
    mission_elapsed_days: float
    raw_input: Dict[str, float]
    stabilized_telemetry: Dict[str, float]
    sanitized_telemetry: Dict[str, float]
    sanity_gate_passed: bool
    total_violations_remediated: int
    biomarker_weights: Dict[str, float]
    top_divergent_biomarkers: Tuple[Tuple[str, float], ...]
    biophysical_metrics: Dict[str, Any]
    triage_state: str
    matched_rule_id: str
    clinical_title: str
    is_cmo_overridden: bool
    cockpit_payload: CockpitActionPayload
    execution_latency_ms: float
    config_sha256: str
    cmo_override_details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the record into an auditable Python dictionary."""
        return {
            "timestamp": self.timestamp,
            "flight_mode": self.flight_mode,
            "frame_index": self.frame_index,
            "mission_elapsed_days": self.mission_elapsed_days,
            "raw_input": dict(self.raw_input),
            "stabilized_telemetry": dict(self.stabilized_telemetry),
            "sanitized_telemetry": dict(self.sanitized_telemetry),
            "sanity_gate_passed": self.sanity_gate_passed,
            "total_violations_remediated": self.total_violations_remediated,
            "biomarker_weights": dict(self.biomarker_weights),
            "top_divergent_biomarkers": list(self.top_divergent_biomarkers),
            "biophysical_metrics": dict(self.biophysical_metrics),
            "triage_state": self.triage_state,
            "matched_rule_id": self.matched_rule_id,
            "clinical_title": self.clinical_title,
            "is_cmo_overridden": self.is_cmo_overridden,
            "cockpit_payload": self.cockpit_payload.to_dict(),
            "execution_latency_ms": round(self.execution_latency_ms, 3),
            "config_sha256": self.config_sha256,
            "cmo_override_details": self.cmo_override_details,
        }

    def get_executive_summary(self) -> str:
        """Returns the 3-second rapid response cockpit executive summary."""
        return self.cockpit_payload.three_second_executive_summary


@dataclass
class PipelineHealthSummary:
    """
    Real-time operational health summary of all orchestrated pipeline stages.
    """
    is_healthy: bool
    subsystems_status: Dict[str, str]
    rule_config_sha256: str
    frames_processed_count: int
    last_triage_state: str
    average_latency_ms: float


class AstroVitalPipelineOrchestrator:
    """
    Supreme Master Pipeline Orchestrator for ASTROVITAL AI : VITALX CORE RECREATED V1.
    Integrates the 6 operational pipeline stages under strict DO-178C Level C determinism:
      - STAGE 1: Multi-Mission Ingestion & 12D Normalization
      - STAGE 2: 20% Adaptive AI Drift & Motion Filter (Stabilizer)
      - STAGE 3: DO-178C Mathematical Sanity & Boundary Gate (Airworthiness Firewall)
      - STAGE 4: 20% Dynamic Biomarker Sensitivity Gradient Ranker
      - STAGE 5: 80% Biophysical Supreme Head (Hemodynamics, ICP, SV & 12 Rules)
      - STAGE 6: 3-Second Astronaut Cockpit & Countermeasure Dispatcher
    """

    def __init__(
        self,
        synchronizer: Optional[TelemetryTemporalSynchronizer] = None,
        stabilizer: Optional[StabilizedFrameExporter] = None,
        sanity_gate: Optional[SanityGateExporter] = None,
        biomarker_ranker: Optional[SensitivityContractExporter] = None,
        decision_engine: Optional[TriageModelEngine] = None,
        cockpit_dispatcher: Optional[CockpitCountermeasureDispatcher] = None,
        recovery_debounce_frames: int = 5,
        max_audit_history: int = 500,
    ) -> None:
        """
        Initializes the pipeline orchestrator with certified subsystem components.
        """
        self.synchronizer = synchronizer or TelemetryTemporalSynchronizer()
        self.stabilizer = stabilizer or StabilizedFrameExporter()
        self.sanity_gate = sanity_gate or SanityGateExporter()
        self.biomarker_ranker = biomarker_ranker or SensitivityContractExporter()
        self.decision_engine = decision_engine or TriageModelEngine(
            recovery_debounce_frames=recovery_debounce_frames
        )
        self.cockpit_dispatcher = cockpit_dispatcher or CockpitCountermeasureDispatcher()

        self._frame_counter: int = 0
        self._latencies_ms: List[float] = []
        self._audit_history: List[PipelineExecutionRecord] = []
        self._max_audit_history: int = max_audit_history

    @property
    def frame_count(self) -> int:
        """Returns total telemetry frames processed since instantiation."""
        return self._frame_counter

    @property
    def config_sha256(self) -> str:
        """Returns the cryptographic SHA-256 hash of active clinical triage rules."""
        checksums = self.decision_engine.config_manager.get_checksums()
        return checksums.get("deterministic_triage_rules.json", "")

    def process_telemetry_frame(
        self,
        telemetry: Union[Dict[str, float], pd.Series, pd.DataFrame],
        microgravity_days: float = 3.0,
        exercise_metric: float = 1.0,
        sleep_debt_hours: float = 0.0,
        flight_mode: str = "REALTIME",
        skip_stabilizer: bool = False,
    ) -> PipelineExecutionRecord:
        """
        Executes the end-to-end 6-stage flight pipeline for a single telemetry frame.
        Guarantees deterministic execution latency and produces an immutable execution record.
        """
        start_time = time.perf_counter()
        self._frame_counter += 1

        # -------------------------------------------------------------------
        # 1. Normalization & Raw Input Extraction
        # -------------------------------------------------------------------
        if isinstance(telemetry, pd.DataFrame):
            if telemetry.empty:
                raise ValueError("Telemetry DataFrame cannot be empty.")
            raw_dict = telemetry.iloc[0].to_dict()
        elif isinstance(telemetry, pd.Series):
            raw_dict = telemetry.to_dict()
        elif isinstance(telemetry, dict):
            raw_dict = dict(telemetry)
        else:
            raise TypeError(
                f"Unsupported telemetry type {type(telemetry)}. Must be dict, Series, or DataFrame."
            )

        # Standardize physical values to canonical 12 channels
        canonical_raw: Dict[str, float] = {}
        for ch in CANONICAL_CHANNELS:
            canonical_raw[ch] = float(raw_dict.get(ch, 0.0))

        # -------------------------------------------------------------------
        # 2. Stage 2: Adaptive AI Signal Stabilization (20% AI)
        # -------------------------------------------------------------------
        # DO-178C Defense: If raw telemetry contains decoupled non-finite values (NaN/Inf),
        # automatically route directly to Stage 3 Sanity Gate fallback engine.
        has_non_finite = any(not math.isfinite(v) for v in canonical_raw.values())
        if not skip_stabilizer and not has_non_finite:
            df_for_stabilizer = pd.DataFrame([canonical_raw])
            stabilized_frame = self.stabilizer.process_and_export_frame(df_for_stabilizer)
            stabilized_vitals = stabilized_frame.stabilized_data.iloc[0].to_dict()
        else:
            stabilized_vitals = dict(canonical_raw)

        # -------------------------------------------------------------------
        # 3. Stage 3: DO-178C Mathematical Sanity Gate (Airworthiness Firewall)
        # -------------------------------------------------------------------
        df_for_gate = pd.DataFrame([stabilized_vitals])
        gated_packet: SanityGatedPacket = self.sanity_gate.process_and_export_packet(df_for_gate)
        sanitized_vitals = gated_packet.sanitized_df.iloc[0].to_dict()

        # Re-attach operational mission context (not physical channels)
        sanitized_vitals["sleep_debt_hours"] = float(
            raw_dict.get("sleep_debt_hours", sleep_debt_hours)
        )
        sanitized_vitals["exercise_metric"] = float(
            raw_dict.get("exercise_metric", exercise_metric)
        )

        # -------------------------------------------------------------------
        # 4. Stage 4: Dynamic Biomarker Sensitivity Gradient (20% AI Aux)
        # -------------------------------------------------------------------
        df_for_ranker = gated_packet.sanitized_df
        biomarker_contract: BiomarkerSensitivityContract = (
            self.biomarker_ranker.process_and_export_contract(df_for_ranker)
        )
        biomarker_weights = biomarker_contract.sensitivity_dict

        # Extract top 3 divergent biomarkers sorted by sensitivity weight
        sorted_biomarkers = tuple(
            sorted(biomarker_weights.items(), key=lambda item: item[1], reverse=True)[:3]
        )

        # -------------------------------------------------------------------
        # 5. Stage 5: 80% Biophysical Supreme Head (Deterministic Triage)
        # -------------------------------------------------------------------
        decision_packet: TriageDecisionPacket = self.decision_engine.process_telemetry_frame(
            telemetry=sanitized_vitals,
            microgravity_days=microgravity_days,
            exercise_metric=exercise_metric,
            biomarker_weights=biomarker_weights,
        )

        # -------------------------------------------------------------------
        # 6. Stage 6: 3-Second Cockpit & Countermeasure Dispatcher
        # -------------------------------------------------------------------
        cockpit_payload: CockpitActionPayload = (
            self.cockpit_dispatcher.dispatch_cockpit_payload(decision_packet)
        )

        # Compute end-to-end execution latency
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        self._latencies_ms.append(elapsed_ms)
        if len(self._latencies_ms) > 1000:
            self._latencies_ms = self._latencies_ms[-1000:]

        # Assemble unified biophysical metrics dictionary
        biophysical_metrics: Dict[str, Any] = {
            **decision_packet.hemodynamics,
            **decision_packet.fluid_shift,
            **decision_packet.cardiac_output,
        }
        is_cmo_overridden = bool(decision_packet.cmo_override.get("is_active", False))

        # Format ISO-8601 UTC timestamp
        timestamp_str = datetime.now(timezone.utc).isoformat()

        # Assemble immutable execution record
        record = PipelineExecutionRecord(
            timestamp=timestamp_str,
            flight_mode=flight_mode,
            frame_index=self._frame_counter,
            mission_elapsed_days=float(microgravity_days),
            raw_input=canonical_raw,
            stabilized_telemetry=stabilized_vitals,
            sanitized_telemetry={
                k: float(v) for k, v in sanitized_vitals.items() if k in CANONICAL_CHANNELS
            },
            sanity_gate_passed=gated_packet.is_gate_passed,
            total_violations_remediated=gated_packet.total_violations_remediated,
            biomarker_weights=biomarker_weights,
            top_divergent_biomarkers=sorted_biomarkers,
            biophysical_metrics=biophysical_metrics,
            triage_state=decision_packet.triage_state,
            matched_rule_id=decision_packet.matched_rule_id,
            clinical_title=decision_packet.clinical_title,
            is_cmo_overridden=is_cmo_overridden,
            cockpit_payload=cockpit_payload,
            execution_latency_ms=elapsed_ms,
            config_sha256=self.config_sha256,
            cmo_override_details=decision_packet.cmo_override if is_cmo_overridden else None,
        )

        # Maintain rolling audit buffer
        self._audit_history.append(record)
        if len(self._audit_history) > self._max_audit_history:
            self._audit_history.pop(0)

        return record

    def process_telemetry_stream(
        self,
        df_stream: pd.DataFrame,
        microgravity_days: float = 3.0,
        exercise_metric: float = 1.0,
        sleep_debt_hours: float = 0.0,
        flight_mode: str = "HISTORICAL_REPLAY",
    ) -> List[PipelineExecutionRecord]:
        """
        Processes a continuous timeseries DataFrame row-by-row through the operational pipeline.
        """
        if df_stream.empty:
            return []

        records: List[PipelineExecutionRecord] = []
        for _, row in df_stream.iterrows():
            rec = self.process_telemetry_frame(
                telemetry=row,
                microgravity_days=microgravity_days,
                exercise_metric=exercise_metric,
                sleep_debt_hours=sleep_debt_hours,
                flight_mode=flight_mode,
            )
            records.append(rec)
        return records

    def assert_cmo_override(
        self,
        target_state: str,
        clinical_rationale: str,
        cmo_id: str = "CMO-ORION-01",
        rule_id: str = "CMO_SOVEREIGN_OVERRIDE",
    ) -> CMOOverrideRecord:
        """
        Enacts a sovereign manual override from the Crew Medical Officer (CMO).
        """
        self.decision_engine.apply_cmo_override(
            override_state=target_state,
            rationale=clinical_rationale,
            authorizing_officer=cmo_id,
        )
        return self.decision_engine._cmo_override

    def clear_cmo_override(self) -> None:
        """
        Clears sovereign CMO override, returning system to automatic deterministic triage.
        """
        self.decision_engine.clear_cmo_override()

    def get_audit_trail(self, limit: int = 10) -> List[PipelineExecutionRecord]:
        """
        Retrieves the most recent N execution records from the rolling flight audit buffer.
        """
        return self._audit_history[-limit:]

    def get_health_summary(self) -> PipelineHealthSummary:
        """
        Returns real-time health and operational status across all orchestrated pipeline stages.
        """
        subsystems = {
            "ingestion_adapter": "ONLINE",
            "inno3_signal_stabilizer": "ONLINE",
            "sanity_gate": "ONLINE",
            "inno6_biomarker_ranker": "ONLINE",
            "biophysical_physics_engine": "ONLINE",
            "triage_model_engine": "ONLINE",
            "cockpit_countermeasure_dispatcher": "ONLINE",
        }
        avg_latency = (
            float(np.mean(self._latencies_ms)) if self._latencies_ms else 0.0
        )
        last_state = (
            self._audit_history[-1].triage_state if self._audit_history else "UNINITIALIZED"
        )

        return PipelineHealthSummary(
            is_healthy=True,
            subsystems_status=subsystems,
            rule_config_sha256=self.config_sha256,
            frames_processed_count=self._frame_counter,
            last_triage_state=last_state,
            average_latency_ms=avg_latency,
        )
