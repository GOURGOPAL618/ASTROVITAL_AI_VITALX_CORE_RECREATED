"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT / 01_components
Package: __init__.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A HMI Systems
=============================================================================
"""

import sys
from pathlib import Path

_pkg_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_pkg_dir))

from cockpit_state import (
    CrewProfile,
    CREW_PROFILES,
    FlightScenarioPreset,
    FLIGHT_SCENARIO_PRESETS,
    TelemetryRingBuffer,
    CockpitStateManager,
)
from hud_status_banner import (
    HUDDisplayConfig,
    HUDStatusBannerRenderer,
)
from telemetry_stream_view import (
    TelemetryChannelMetadata,
    BiophysicalGaugeMetadata,
    CHANNEL_REGISTRY,
    BIOPHYSICAL_REGISTRY,
    TelemetryStreamRenderer,
)
from countermeasure_deck import (
    LockerSpec,
    LOCKER_DIRECTORY,
    CountermeasureDeckRenderer,
)
from audit_trace_terminal import AuditTraceTerminalRenderer
from cmo_override_console import CMOOverrideConsoleRenderer

__all__ = [
    "CrewProfile",
    "CREW_PROFILES",
    "FlightScenarioPreset",
    "FLIGHT_SCENARIO_PRESETS",
    "TelemetryRingBuffer",
    "CockpitStateManager",
    "HUDDisplayConfig",
    "HUDStatusBannerRenderer",
    "TelemetryChannelMetadata",
    "BiophysicalGaugeMetadata",
    "CHANNEL_REGISTRY",
    "BIOPHYSICAL_REGISTRY",
    "TelemetryStreamRenderer",
    "LockerSpec",
    "LOCKER_DIRECTORY",
    "CountermeasureDeckRenderer",
    "AuditTraceTerminalRenderer",
    "CMOOverrideConsoleRenderer",
]
