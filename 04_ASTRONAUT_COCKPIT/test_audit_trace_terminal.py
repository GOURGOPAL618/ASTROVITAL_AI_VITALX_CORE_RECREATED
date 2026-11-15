"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_audit_trace_terminal.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Safety Audit Trail
Verification: 100% Statement Coverage on audit_trace_terminal.py
=============================================================================
"""

import json
import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Ensure cockpit, ai_core, and decision dirs are on sys.path
root_dir = Path(__file__).resolve().parent.parent
cockpit_dir = root_dir / "04_ASTRONAUT_COCKPIT"
cockpit_comp = cockpit_dir / "01_components"
ai_core_src = root_dir / "02_AI_CORE" / "01_src"
decision_dir = root_dir / "03_DECISION_CORE"

for p in [str(cockpit_comp), str(cockpit_dir), str(ai_core_src), str(decision_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from audit_trace_terminal import AuditTraceTerminalRenderer
from cockpit_state import CockpitStateManager


@pytest.fixture
def state_manager() -> CockpitStateManager:
    return CockpitStateManager()


# =============================================================================
# 1. JSON & ASCII AUDIT TRACE FORMATTING TESTS
# =============================================================================

def test_01_format_json_trace(state_manager: CockpitStateManager):
    """Verifies complete serialization into audited JSON format."""
    rec = state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    json_str = AuditTraceTerminalRenderer.format_json_trace(rec)

    parsed = json.loads(json_str)
    assert parsed["triage_state"] == "GREEN"
    assert parsed["frame_index"] == rec.frame_index
    assert "raw_input" in parsed
    assert "sanitized_telemetry" in parsed
    assert "biophysical_metrics" in parsed


def test_02_format_ascii_trace_nominal(state_manager: CockpitStateManager):
    """Verifies ASCII trace formatting for nominal cruise execution."""
    rec = state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    ascii_out = AuditTraceTerminalRenderer.format_ascii_trace(rec)

    assert "ASTROVITAL AI : DO-178C DAL C WHITE-BOX DETERMINISTIC AUDIT TRACE" in ascii_out
    assert "STAGE 1 & 2: SENSOR INTAKE & KALMAN STABILIZATION" in ascii_out
    assert "STAGE 3: DETERMINISTIC BIOLOGICAL SANITY GATE" in ascii_out
    assert "SANITY GATE STATUS : PASSED (NOMINAL)" in ascii_out
    assert "STAGE 4: BIOPHYSICAL SPACEFLIGHT PHYSICS & HEMODYNAMICS" in ascii_out
    assert "STAGE 5: DETERMINISTIC TRIAGE RULE MATCHING" in ascii_out
    assert "AUTONOMOUS DETERMINISTIC" in ascii_out


def test_03_format_ascii_trace_violations_and_cmo(state_manager: CockpitStateManager):
    """Verifies ASCII trace formatting when sanity gate remediates violations and CMO override is active."""
    rec = state_manager.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")
    # Mutate to simulate sanity violation remediations and CMO override details
    cmo_dict = {
        "authorizing_officer": "DR. COLLINS (CMO)",
        "rationale": "Severe hypoxia decompensation post airlock repress.",
    }
    rec_mod = replace(
        rec,
        sanity_gate_passed=False,
        total_violations_remediated=3,
        is_cmo_overridden=True,
        cmo_override_details=cmo_dict,
    )

    ascii_out = AuditTraceTerminalRenderer.format_ascii_trace(rec_mod)
    assert "REMEDIATED (VIOLATIONS DETECTED)" in ascii_out
    assert "3 parameter violations" in ascii_out
    assert "ASSERTED [MANUAL OVERRIDE]" in ascii_out
    assert "DR. COLLINS (CMO)" in ascii_out
    assert "Severe hypoxia decompensation" in ascii_out


# =============================================================================
# 2. HTML TERMINAL BOX RENDERING TESTS
# =============================================================================

def test_04_render_html_green_amber_red_states(state_manager: CockpitStateManager):
    """Verifies CRT terminal box rendering across GREEN, AMBER, and RED triage states."""
    # 1. GREEN state
    rec_green = state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    html_green = AuditTraceTerminalRenderer.render_html(rec_green)
    assert "#00E5FF" in html_green
    assert "ORION WHITE-BOX AUDIT TERMINAL" in html_green

    # 2. AMBER state
    rec_amber = state_manager.inject_scenario("SCENARIO_05_EARLY_FLUID_SHIFT_COMPENSATION")
    html_amber = AuditTraceTerminalRenderer.render_html(rec_amber)
    assert "#FFB800" in html_amber

    # 3. RED state
    rec_red = state_manager.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")
    html_red = AuditTraceTerminalRenderer.render_html(rec_red)
    assert "#FF1E27" in html_red


# =============================================================================
# 3. STREAMLIT EMBEDDING & EXPORT TESTS
# =============================================================================

def test_05_render_streamlit_with_mock_container(state_manager: CockpitStateManager):
    """Verifies Streamlit audit terminal embedding with JSON packet download."""
    rec = state_manager.latest_record
    mock_container = MagicMock()

    AuditTraceTerminalRenderer.render_streamlit(rec, container=mock_container)
    assert mock_container.markdown.called
    assert mock_container.expander.called


def test_06_render_streamlit_import_error(state_manager: CockpitStateManager, monkeypatch):
    """Verifies headless execution fallback when streamlit raises ImportError."""
    rec = state_manager.latest_record

    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Simulated missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    AuditTraceTerminalRenderer.render_streamlit(rec)
