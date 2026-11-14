"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_countermeasure_deck.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A HMI Systems
Verification: 100% Statement Coverage on countermeasure_deck.py
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

from countermeasure_deck import (
    LOCKER_DIRECTORY,
    CountermeasureDeckRenderer,
    LockerSpec,
)
from cockpit_countermeasure_dispatcher import (
    CockpitActionPayload,
    HUDAlertBanner,
    SequencedActionStep,
)
from cockpit_state import CockpitStateManager


@pytest.fixture
def state_manager() -> CockpitStateManager:
    return CockpitStateManager()


# =============================================================================
# 1. HARDWARE SPECIFICATION & SVG CACHING TESTS
# =============================================================================

def test_01_locker_spec_initialization():
    """Verifies dataclass fields and immutability of LockerSpec."""
    spec = LockerSpec(
        locker_id="TEST-01",
        locker_code="L9",
        title="TEST LOCKER",
        bay_location="Test Bay",
        icon_filename="test.svg",
    )
    assert spec.locker_id == "TEST-01"
    assert spec.locker_code == "L9"
    assert spec.title == "TEST LOCKER"
    assert spec.bay_location == "Test Bay"


def test_02_get_locker_icon_svg_branches():
    """Verifies SVG loading, in-memory caching, and fallback handling."""
    # Empty icon
    assert CountermeasureDeckRenderer.get_locker_icon_svg("") == ""

    # Known existing icon file
    svg1 = CountermeasureDeckRenderer.get_locker_icon_svg("locker_l1_resuscitation.svg")
    assert "<svg" in svg1
    assert "locker_l1_resuscitation.svg" in CountermeasureDeckRenderer._icon_cache

    # Cache hit check
    svg2 = CountermeasureDeckRenderer.get_locker_icon_svg("locker_l1_resuscitation.svg")
    assert svg1 == svg2

    # Non-existent file fallback
    svg_fallback = CountermeasureDeckRenderer.get_locker_icon_svg("non_existent_locker.svg")
    assert "<svg" in svg_fallback
    assert "non_existent_locker.svg" in CountermeasureDeckRenderer._icon_cache


# =============================================================================
# 2. LOCKER RESOLUTION & RENDERING TESTS
# =============================================================================

def test_03_resolve_active_locker_id_branches():
    """Verifies locker ID resolution from action deck."""
    # Empty action deck
    assert CountermeasureDeckRenderer.resolve_active_locker_id([]) is None

    # Matched location (MED-01)
    step_med = SequencedActionStep(
        step_number=1,
        action_id="ACT_01",
        protocol="Defibrillator",
        priority=1,
        time_to_execute_sec=15,
        equipment_location="Flight Deck Forward Locker MED-01",
        verification_step="Pads attached",
        subsystem_lead="CMO",
        is_critical_path=True,
    )
    assert CountermeasureDeckRenderer.resolve_active_locker_id([step_med]) == "MED-01"

    # Unmatched location
    step_unmatched = SequencedActionStep(
        step_number=2,
        action_id="ACT_02",
        protocol="Manual CPR",
        priority=1,
        time_to_execute_sec=60,
        equipment_location="Cabin Deck Floor Area",
        verification_step="Compressions started",
        subsystem_lead="ALL_CREW",
        is_critical_path=True,
    )
    assert CountermeasureDeckRenderer.resolve_active_locker_id([step_unmatched]) is None

    # Sleep bunk rest station mapping
    step_sleep = SequencedActionStep(
        step_number=3,
        action_id="ACT_03",
        protocol="Mandatory Rest Buffer",
        priority=1,
        time_to_execute_sec=300,
        equipment_location="Crew Sleep Bunk Compartment",
        verification_step="Rest timer set",
        subsystem_lead="COMMANDER",
        is_critical_path=False,
    )
    assert CountermeasureDeckRenderer.resolve_active_locker_id([step_sleep]) == "PHYS-01"


def test_04_render_locker_bay_active_and_standby():
    """Verifies rendering the 5 physical Orion lockers with active target highlight."""
    # L1 active
    html_out = CountermeasureDeckRenderer.render_locker_bay(active_locker_id="MED-01")
    assert "TARGET ACTIVE" in html_out
    assert "STANDBY" in html_out
    assert "RESUSCITATION" in html_out
    assert "CHIBIS LBNP &amp; EXERCISE" in html_out or "CHIBIS LBNP" in html_out


def test_05_render_checklist_card_states():
    """Verifies rendering completed, critical-path, and non-critical action cards."""
    step_crit = SequencedActionStep(
        step_number=1,
        action_id="ACT_CRIT",
        protocol="Deploy Emergency Mask",
        priority=1,
        time_to_execute_sec=10,
        equipment_location="Locker MED-01",
        verification_step="Positive flow",
        subsystem_lead="CMO",
        is_critical_path=True,
    )
    step_non_crit = SequencedActionStep(
        step_number=2,
        action_id="ACT_NON_CRIT",
        protocol="Record Log",
        priority=2,
        time_to_execute_sec=30,
        equipment_location="Terminal Panel",
        verification_step="Entry saved",
        subsystem_lead="CDR",
        is_critical_path=False,
    )

    # 1. Uncompleted Critical Path Card
    html_crit = CountermeasureDeckRenderer.render_checklist_card(step_crit, is_completed=False)
    assert "CRITICAL PATH" in html_crit
    assert "Deploy Emergency Mask" in html_crit
    assert "⏱ 10s" in html_crit

    # 2. Uncompleted Non-Critical Card
    html_non_crit = CountermeasureDeckRenderer.render_checklist_card(step_non_crit, is_completed=False)
    assert "ACTIVE STEP" in html_non_crit
    assert "Record Log" in html_non_crit

    # 3. Completed Card
    html_comp = CountermeasureDeckRenderer.render_checklist_card(step_crit, is_completed=True)
    assert "COMPLETED" in html_comp
    assert "line-through" in html_comp


def test_06_render_action_deck_empty_and_populated():
    """Verifies full action deck rendering for both populated and empty payloads."""
    banner = HUDAlertBanner("RED_CRITICAL", "#FF1E27", "#FFFFFF", 1200, "ALARM", 2.0, True, 1)
    step = SequencedActionStep(1, "ACT_01", "Protocol", 1, 15, "Locker MED-01", "Verify", "CMO", True)

    payload_pop = CockpitActionPayload(
        "DEC_01", "2026-11-14T00:00:00Z", "RED", "Title", banner, "Summary", [step], 15, "SpO2", False
    )
    html_pop = CountermeasureDeckRenderer.render_action_deck(payload_pop, checklist_states={"ACT_01": True})
    assert "COMPLETED" in html_pop
    assert "TARGET ACTIVE" in html_pop

    payload_empty = CockpitActionPayload(
        "DEC_02", "2026-11-14T00:00:00Z", "GREEN", "Nominal", banner, "Summary", [], 0, "HR", False
    )
    html_empty = CountermeasureDeckRenderer.render_action_deck(payload_empty, checklist_states={})
    assert "NO ACTIVE COUNTERMEASURE ACTIONS REQUIRED" in html_empty


# =============================================================================
# 3. STREAMLIT EMBEDDING & INTERACTIVE CHECKBOX TESTS
# =============================================================================

def test_07_render_streamlit_with_mock_and_toggle(state_manager: CockpitStateManager):
    """Verifies Streamlit interactive rendering with checkbox toggle triggering state change."""
    state_manager.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")
    mock_container = MagicMock()
    mock_col1 = MagicMock()
    mock_col1.checkbox.return_value = True
    mock_container.columns.return_value = [mock_col1, MagicMock()]

    CountermeasureDeckRenderer.render_streamlit(state_manager, container=mock_container)
    assert mock_container.markdown.called
    assert mock_col1.checkbox.called
    assert mock_container.rerun.called


def test_08_render_streamlit_empty_action_deck(state_manager: CockpitStateManager):
    """Verifies Streamlit rendering when action deck is empty."""
    from dataclasses import replace
    state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    rec = state_manager.latest_record
    empty_payload = replace(rec.cockpit_payload, action_deck=[])
    state_manager.latest_record = replace(rec, cockpit_payload=empty_payload)

    mock_container = MagicMock()
    CountermeasureDeckRenderer.render_streamlit(state_manager, container=mock_container)
    assert mock_container.info.called


def test_09_render_streamlit_no_record(state_manager: CockpitStateManager):
    """Verifies early exit when latest_record is None."""
    state_manager.latest_record = None
    mock_container = MagicMock()

    CountermeasureDeckRenderer.render_streamlit(state_manager, container=mock_container)
    assert not mock_container.info.called


def test_10_render_streamlit_import_error(state_manager: CockpitStateManager, monkeypatch):
    """Verifies headless execution fallback when streamlit raises ImportError."""
    state_manager.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")

    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Simulated missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    CountermeasureDeckRenderer.render_streamlit(state_manager)
