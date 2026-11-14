"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 02_AI_CORE / Airworthiness & Integrity Verification
Package: 02_AI_CORE/01_src/__init__.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Operational Pipeline
=============================================================================
"""

import sys
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))

from ingestion_adapter import (
    TelemetryArchiveRegistry,
    TelemetryVector12DBuilder,
    TelemetryTemporalSynchronizer,
)
from inno3_signal_stabilizer import (
    StabilizedFrameExporter,
    SignalQualityEvaluator,
    BaselineDriftCompensator,
    AdaptiveSignalStabilizer,
)
from sanity_gate import (
    PhysiologicalBound,
    PhysiologicalBoundaryEnforcer,
    PhysiologicalCouplingGuard,
    SensorDecouplingFallbackEngine,
    SanityGatedPacket,
    SanityGateExporter,
    NASA_STD_3001_PHYSIOLOGICAL_BOUNDS,
)
from inno6_biomarker_ranker import (
    SensitivityContractExporter,
    CompositeSensitivityRanker,
    EntropyWeightEngine,
    PhysiologicalDeviationScorer,
    BiomarkerSensitivityContract,
)
from pipeline_orchestrator import (
    AstroVitalPipelineOrchestrator,
    PipelineExecutionRecord,
    PipelineHealthSummary,
    CANONICAL_CHANNELS,
)

__all__ = [
    "TelemetryArchiveRegistry",
    "TelemetryVector12DBuilder",
    "TelemetryTemporalSynchronizer",
    "CANONICAL_CHANNELS",
    "StabilizedFrameExporter",
    "SignalQualityEvaluator",
    "BaselineDriftCompensator",
    "AdaptiveSignalStabilizer",
    "PhysiologicalBound",
    "PhysiologicalBoundaryEnforcer",
    "PhysiologicalCouplingGuard",
    "SensorDecouplingFallbackEngine",
    "SanityGatedPacket",
    "SanityGateExporter",
    "NASA_STD_3001_PHYSIOLOGICAL_BOUNDS",
    "SensitivityContractExporter",
    "CompositeSensitivityRanker",
    "EntropyWeightEngine",
    "PhysiologicalDeviationScorer",
    "BiomarkerSensitivityContract",
    "AstroVitalPipelineOrchestrator",
    "PipelineExecutionRecord",
    "PipelineHealthSummary",
]
