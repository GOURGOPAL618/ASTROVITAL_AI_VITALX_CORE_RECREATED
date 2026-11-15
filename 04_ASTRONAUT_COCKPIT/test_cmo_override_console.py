"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_cmo_override_console.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Operational Command
Verification: 100% Statement Coverage on cmo_override_console.py
=============================================================================
"""

import sys
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

from cmo_override_console import CMOOverrideConsoleRenderer
from cockpit_state import CockpitStateManager


@pytest.fixture
def state_manager() -> CockpitStateManager:
    return CockpitStateManager()


# =============================================================================
# 1. AUTHORITY VERIFICATION & HTML CONSOLE TESTS
# =============================================================================

def test_01_check_crew_authority_branches():
    """Verifies sovereign CMO authority verification across profiles."""
    assert CMOOverrideConsoleRenderer.check_crew_authority("CMO_ORION") is True
    assert CMOOverrideConsoleRenderer.check_crew_authority("CDR_ORION") is False
    assert CMOOverrideConsoleRenderer.check_crew_authority("UNKNOWN_CREW") is False


def test_02_render_console_html_cmo_nominal():
    """Verifies rendering console when authorized CMO is logged with no active overrides."""
    html_out = CMOOverrideConsoleRenderer.render_console_html(
        active_crew_id="CMO_ORION",
        active_override=None,
    )
    assert "SOVEREIGN CLEARANCE GRANTED" in html_out
    assert "Dr. Michael Collins" in html_out
    assert "ZERO OVERRIDES ACTIVE" in html_out


def test_03_render_console_html_non_cmo_and_active_override():
    """Verifies rendering console for non-CMO astronaut with active override banner."""
    active_ovr = {
        "is_active": True,
        "target_state": "RED",
        "rationale": "Severe EVA suit pressure drop",
        "authorizing_officer": "DR. COLLINS (CMO)",
        "timestamp": "2026-11-14T00:00:00Z",
    }
    html_out = CMOOverrideConsoleRenderer.render_console_html(
        active_crew_id="CDR_ORION",
        active_override=active_ovr,
    )
    assert "COMMAND CLEARANCE DENIED" in html_out
    assert "SOVEREIGN CMO OVERRIDE ACTIVE // STATE RED" in html_out
    assert "Severe EVA suit pressure drop" in html_out


def test_04_render_console_html_unknown_profile():
    """Verifies console fallback when unknown crew ID is passed."""
    html_out = CMOOverrideConsoleRenderer.render_console_html(
        active_crew_id="ROBOTIC_ARM_AGENT",
        active_override=None,
    )
    assert "UNKNOWN CREW" in html_out
    assert "COMMAND CLEARANCE DENIED" in html_out


# =============================================================================
# 2. STREAMLIT INTERACTIVE OVERRIDE TESTS
# =============================================================================

def test_05_render_streamlit_non_cmo_warning(state_manager: CockpitStateManager):
    """Verifies warning banner when active crew lacks CMO authority."""
    state_manager.set_crew_member("CDR_ORION")
    mock_container = MagicMock()

    CMOOverrideConsoleRenderer.render_streamlit(state_manager, container=mock_container)
    assert mock_container.warning.called


def test_06_render_streamlit_cmo_assert_blank_rationale(state_manager: CockpitStateManager):
    """Verifies error prompt when CMO attempts to assert override without mandatory rationale."""
    state_manager.set_crew_member("CMO_ORION")
    mock_container = MagicMock()
    mock_container.columns.return_value = [mock_container, mock_container]
    mock_container.selectbox.return_value = "RED"
    mock_container.text_input.return_value = "   "  # Blank rationale
    mock_container.button.return_value = True

    CMOOverrideConsoleRenderer.render_streamlit(state_manager, container=mock_container)
    assert mock_container.error.called


def test_07_render_streamlit_cmo_assert_success(state_manager: CockpitStateManager):
    """Verifies successful override assertion by authorized CMO."""
    state_manager.set_crew_member("CMO_ORION")
    mock_container = MagicMock()
    mock_container.columns.return_value = [mock_container, mock_container]
    mock_container.selectbox.return_value = "RED"
    mock_container.text_input.return_value = "Suspected severe barotrauma"
    mock_container.button.side_effect = [True, False]

    CMOOverrideConsoleRenderer.render_streamlit(state_manager, container=mock_container)
    assert state_manager.active_cmo_override is not None
    assert state_manager.active_cmo_override["target_state"] == "RED"
    assert mock_container.success.called
    assert mock_container.rerun.called


def test_08_render_streamlit_cmo_revoke_override(state_manager: CockpitStateManager):
    """Verifies revoking active override and restoring autonomous deterministic triage."""
    state_manager.set_crew_member("CMO_ORION")
    state_manager.apply_cmo_override("RED", "Initial trauma rationale")
    assert state_manager.active_cmo_override is not None

    mock_container = MagicMock()
    mock_container.columns.return_value = [mock_container, mock_container]
    mock_container.selectbox.return_value = "GREEN"
    mock_container.text_input.return_value = ""
    # First button (assert) = False, second button (revoke) = True
    mock_container.button.side_effect = [False, True]

    CMOOverrideConsoleRenderer.render_streamlit(state_manager, container=mock_container)
    assert state_manager.active_cmo_override is None
    assert mock_container.info.called
    assert mock_container.rerun.called


def test_09_render_streamlit_import_error(state_manager: CockpitStateManager, monkeypatch):
    """Verifies headless execution fallback when streamlit raises ImportError."""
    state_manager.set_crew_member("CMO_ORION")

    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Simulated missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    CMOOverrideConsoleRenderer.render_streamlit(state_manager)
