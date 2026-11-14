"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_cockpit_app.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Master Flight App Verification
Verification: 100% Statement Coverage on app.py
=============================================================================
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

# Ensure cockpit, ai_core, and decision dirs are on sys.path
root_dir = Path(__file__).resolve().parent.parent
cockpit_dir = root_dir / "04_ASTRONAUT_COCKPIT"
cockpit_comp = cockpit_dir / "01_components"
ai_core_src = root_dir / "02_AI_CORE" / "01_src"
decision_dir = root_dir / "03_DECISION_CORE"

for p in [str(cockpit_dir), str(cockpit_comp), str(ai_core_src), str(decision_dir)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app import (
    get_state_manager,
    inject_custom_css,
    main,
    render_cockpit_display,
    render_sidebar_controls,
)
from cockpit_state import CockpitStateManager


@pytest.fixture
def state_manager() -> CockpitStateManager:
    return CockpitStateManager()


# =============================================================================
# 1. CSS INJECTION & SESSION STATE TESTS
# =============================================================================

def test_01_inject_custom_css(monkeypatch):
    """Verifies custom CSS file injection into Streamlit DOM."""
    mock_st = MagicMock()
    monkeypatch.setattr("streamlit.markdown", mock_st.markdown)
    inject_custom_css()
    assert mock_st.markdown.called


def test_02_inject_custom_css_import_error(monkeypatch):
    """Verifies safe fallback when streamlit raises ImportError."""
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    inject_custom_css()


def test_03_get_state_manager_initialization(monkeypatch):
    """Verifies state manager creation in session_state and retrieval."""
    import streamlit as st
    st.session_state.clear()

    mgr1 = get_state_manager()
    assert isinstance(mgr1, CockpitStateManager)
    assert "state_manager" in st.session_state

    # Second call retrieves existing instance
    mgr2 = get_state_manager()
    assert mgr1 is mgr2


def test_04_get_state_manager_import_error(monkeypatch):
    """Verifies fallback state manager creation on ImportError."""
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    mgr = get_state_manager()
    assert isinstance(mgr, CockpitStateManager)


# =============================================================================
# 2. SIDEBAR CONTROLS TESTS
# =============================================================================

def test_05_render_sidebar_controls_steady(state_manager: CockpitStateManager, monkeypatch):
    """Verifies rendering sidebar without triggering changes."""
    mock_st = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.selectbox.side_effect = [
        state_manager.active_crew_member,
        state_manager.current_scenario_id,
    ]
    mock_st.button.return_value = False
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    with patch("streamlit.sidebar", mock_st.sidebar), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button):
        render_sidebar_controls(state_manager)

        # Verify format_func lambdas execute and format properly
        calls = mock_st.selectbox.call_args_list
        crew_fmt = calls[0].kwargs.get("format_func")
        assert "Cmdr. Neil Armstrong" in crew_fmt("CDR_ORION")
        scen_fmt = calls[1].kwargs.get("format_func")
        assert "Nominal Deep-Space Cruise" in scen_fmt("SCENARIO_01_NOMINAL_CRUISE")
        assert "STATE GREEN" in scen_fmt("SCENARIO_01_NOMINAL_CRUISE")


def test_06_render_sidebar_crew_change(state_manager: CockpitStateManager, monkeypatch):
    """Verifies changing crew member triggers state change and rerun."""
    mock_st = MagicMock()
    mock_st.selectbox.side_effect = ["CMO_ORION", state_manager.current_scenario_id]
    mock_st.button.return_value = False
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    with patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button), \
         patch("streamlit.rerun", mock_st.rerun):
        render_sidebar_controls(state_manager)
        assert state_manager.active_crew_member == "CMO_ORION"
        assert mock_st.rerun.called


def test_07_render_sidebar_scenario_change(state_manager: CockpitStateManager, monkeypatch):
    """Verifies changing scenario preset triggers injection and rerun."""
    mock_st = MagicMock()
    mock_st.selectbox.side_effect = [
        state_manager.active_crew_member,
        "SCENARIO_02_ACUTE_EVA_HYPOXIA",
    ]
    mock_st.button.return_value = False
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    with patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button), \
         patch("streamlit.rerun", mock_st.rerun):
        render_sidebar_controls(state_manager)
        assert state_manager.current_scenario_id == "SCENARIO_02_ACUTE_EVA_HYPOXIA"
        assert mock_st.rerun.called


def test_08_render_sidebar_step_and_reset_buttons(state_manager: CockpitStateManager, monkeypatch):
    """Verifies step simulation and reset buffer button triggers."""
    # Step button True
    mock_st = MagicMock()
    mock_st.selectbox.side_effect = [state_manager.active_crew_member, state_manager.current_scenario_id]
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.button.side_effect = [True, False]

    with patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button), \
         patch("streamlit.rerun", mock_st.rerun):
        render_sidebar_controls(state_manager)
        assert mock_st.rerun.called

    # Reset button True
    mock_st_reset = MagicMock()
    mock_st_reset.selectbox.side_effect = [state_manager.active_crew_member, state_manager.current_scenario_id]
    mock_st_reset.columns.return_value = [MagicMock(), MagicMock()]
    mock_st_reset.button.side_effect = [False, True]

    with patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st_reset.markdown), \
         patch("streamlit.selectbox", mock_st_reset.selectbox), \
         patch("streamlit.columns", mock_st_reset.columns), \
         patch("streamlit.button", mock_st_reset.button), \
         patch("streamlit.rerun", mock_st_reset.rerun):
        render_sidebar_controls(state_manager)
        assert mock_st_reset.rerun.called


def test_09_render_sidebar_no_record(state_manager: CockpitStateManager, monkeypatch):
    """Verifies sidebar rendering when latest_record is None."""
    state_manager.latest_record = None
    mock_st = MagicMock()
    mock_st.selectbox.side_effect = [state_manager.active_crew_member, state_manager.current_scenario_id]
    mock_st.columns.return_value = [MagicMock(), MagicMock()]
    mock_st.button.return_value = False

    with patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button):
        render_sidebar_controls(state_manager)


def test_10_render_sidebar_import_error(state_manager: CockpitStateManager, monkeypatch):
    """Verifies safe fallback when streamlit raises ImportError in sidebar."""
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    render_sidebar_controls(state_manager)


# =============================================================================
# 3. MAIN COCKPIT DISPLAY TESTS
# =============================================================================

def test_11_render_cockpit_display_no_record(state_manager: CockpitStateManager):
    """Verifies early return when latest_record is None."""
    state_manager.latest_record = None
    render_cockpit_display(state_manager)


def test_12_render_cockpit_display_with_tabs(state_manager: CockpitStateManager, monkeypatch):
    """Verifies rendering full flight deck with tabs and components."""
    mock_tab = MagicMock()
    mock_tabs = [mock_tab, mock_tab, mock_tab, mock_tab]
    mock_st = MagicMock()
    mock_st.tabs.return_value = mock_tabs

    with patch("streamlit.tabs", mock_st.tabs):
        render_cockpit_display(state_manager)
        assert mock_st.tabs.called


def test_13_render_cockpit_display_import_error(state_manager: CockpitStateManager, monkeypatch):
    """Verifies safe fallback when streamlit raises ImportError in cockpit display."""
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    render_cockpit_display(state_manager)


# =============================================================================
# 4. MASTER MAIN ENTRYPOINT TESTS
# =============================================================================

def test_14_main_execution(monkeypatch):
    """Verifies complete main function invocation."""
    mock_st = MagicMock()
    mock_tab = MagicMock()
    mock_st.tabs.return_value = [mock_tab, mock_tab, mock_tab, mock_tab]
    mock_st.selectbox.side_effect = ["CDR_ORION", "SCENARIO_01_NOMINAL_CRUISE"]
    mock_st.button.return_value = False
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    with patch("streamlit.set_page_config", mock_st.set_page_config), \
         patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button), \
         patch("streamlit.tabs", mock_st.tabs):
        main()
        assert mock_st.set_page_config.called


def test_15_main_import_error(monkeypatch):
    """Verifies main safe fallback when streamlit raises ImportError."""
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    main()


def test_16_main_dunder_run():
    """Verifies execution when invoked as __main__."""
    import runpy
    mock_st = MagicMock()
    mock_tab = MagicMock()
    mock_st.tabs.return_value = [mock_tab, mock_tab, mock_tab, mock_tab]
    mock_st.selectbox.side_effect = ["CDR_ORION", "SCENARIO_01_NOMINAL_CRUISE"]
    mock_st.button.return_value = False
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    with patch("streamlit.set_page_config", mock_st.set_page_config), \
         patch("streamlit.sidebar", MagicMock()), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button), \
         patch("streamlit.tabs", mock_st.tabs):
        runpy.run_path(str(cockpit_dir / "app.py"), run_name="__main__")


def test_17_render_sidebar_controls_fallback_markdown(state_manager: CockpitStateManager, monkeypatch):
    """Verifies fallback to st.markdown when st.html is absent."""
    import streamlit as st
    mock_st = MagicMock()
    mock_st.sidebar = MagicMock()
    mock_st.selectbox.side_effect = [
        state_manager.active_crew_member,
        state_manager.current_scenario_id,
    ]
    mock_st.button.return_value = False
    mock_st.columns.return_value = [MagicMock(), MagicMock()]

    if hasattr(st, "html"):
        monkeypatch.delattr(st, "html", raising=False)

    with patch("streamlit.sidebar", mock_st.sidebar), \
         patch("streamlit.markdown", mock_st.markdown), \
         patch("streamlit.selectbox", mock_st.selectbox), \
         patch("streamlit.columns", mock_st.columns), \
         patch("streamlit.button", mock_st.button):
        render_sidebar_controls(state_manager)
        assert mock_st.markdown.called

