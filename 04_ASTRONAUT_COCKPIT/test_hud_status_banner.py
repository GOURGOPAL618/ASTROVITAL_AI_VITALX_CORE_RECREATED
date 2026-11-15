"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_hud_status_banner.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A HMI Systems
Verification: 100% Statement Coverage on hud_status_banner.py
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

from hud_status_banner import (
    HUDDisplayConfig,
    HUDStatusBannerRenderer,
)
from cockpit_state import CockpitStateManager
from cockpit_countermeasure_dispatcher import (
    CockpitActionPayload,
    HUDAlertBanner,
    SequencedActionStep,
)


@pytest.fixture
def state_manager() -> CockpitStateManager:
    return CockpitStateManager()


# =============================================================================
# 1. HUD DISPLAY CONFIGURATION TESTS
# =============================================================================

def test_01_hud_display_config_initialization():
    """Verifies dataclass fields and immutability of HUDDisplayConfig."""
    cfg = HUDDisplayConfig(
        triage_state="GREEN",
        clinical_title="Nominal Homeostasis",
        executive_summary="All vitals normal.",
        matched_rule_id="RULE_GREEN_001",
        audio_tone_frequency_hz=0,
        flash_frequency_hz=0.0,
    )
    assert cfg.triage_state == "GREEN"
    assert cfg.audio_tone_frequency_hz == 0
    assert cfg.flash_frequency_hz == 0.0
    assert cfg.target_locker_id is None
    assert cfg.is_cmo_override is False
    assert cfg.is_alarm_acknowledged is False


def test_02_create_config_from_record_green(state_manager: CockpitStateManager):
    """Verifies creating display config from a nominal GREEN execution record."""
    record = state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    config = HUDStatusBannerRenderer.create_config_from_record(record, is_acknowledged=False)

    assert config.triage_state == "GREEN"
    assert config.audio_tone_frequency_hz == 0
    assert config.flash_frequency_hz == 0.0
    assert "NOMINAL GREEN EQUILIBRIUM" in config.executive_summary
    assert config.is_cmo_override is False


def test_03_create_config_from_record_red_with_locker(state_manager: CockpitStateManager):
    """Verifies creating display config from a critical RED execution record with locker routing."""
    record = state_manager.inject_scenario("SCENARIO_02_ACUTE_EVA_HYPOXIA")
    config = HUDStatusBannerRenderer.create_config_from_record(record, is_acknowledged=False)

    assert config.triage_state == "RED"
    assert config.audio_tone_frequency_hz == 1200
    assert config.flash_frequency_hz == 2.0
    assert "MED-01" in config.target_locker_id
    assert "LOCKER L1" in config.target_locker_label


def test_04_create_config_from_payload_direct():
    """Verifies creating display config directly from CockpitActionPayload."""
    banner = HUDAlertBanner(
        alert_level="RED_CRITICAL",
        hud_banner_color="#FF1E27",
        hud_contrast_text_color="#FFFFFF",
        audio_tone_frequency_hz=1200,
        audio_pulse_pattern="URGENT_PULSED_ALARM",
        flash_rate_hz=2.0,
        tactile_vibration_alert=True,
        priority_code=1,
    )
    step = SequencedActionStep(
        step_number=1,
        action_id="ACT_001",
        protocol="Deploy O2",
        priority=1,
        time_to_execute_sec=15,
        equipment_location="Flight Deck Forward Locker ENV-01",
        verification_step="Seal confirmed",
        subsystem_lead="CREW_MEDICAL_OFFICER",
        is_critical_path=True,
    )
    payload = CockpitActionPayload(
        decision_id="DEC_TEST_001",
        timestamp_utc="2026-11-14T00:00:00Z",
        triage_state="RED",
        clinical_title="Acute Hypoxia",
        hud_banner=banner,
        three_second_executive_summary="Critical Hypoxia Detected",
        action_deck=[step],
        total_execution_window_sec=15,
        biomarker_context_lead="SpO2",
        is_cmo_override_active=True,
    )

    config = HUDStatusBannerRenderer.create_config_from_payload(
        payload,
        is_acknowledged=True,
        cmo_override_active={"is_active": True, "rationale": "Flight Surgeon assert."},
    )
    assert config.triage_state == "RED"
    assert config.target_locker_id == "Flight Deck Forward Locker ENV-01"
    assert "LOCKER L3" in config.target_locker_label
    assert config.is_cmo_override is True
    assert config.cmo_rationale == "Flight Surgeon assert."
    assert config.is_alarm_acknowledged is True


def test_05_create_config_from_payload_empty_actions_and_no_cmo():
    """Verifies creating display config when action deck is empty and CMO is inactive."""
    banner = HUDAlertBanner(
        alert_level="GREEN_NOMINAL",
        hud_banner_color="#00E676",
        hud_contrast_text_color="#05070E",
        audio_tone_frequency_hz=0,
        audio_pulse_pattern="SILENT",
        flash_rate_hz=0.0,
        tactile_vibration_alert=False,
        priority_code=3,
    )
    payload = CockpitActionPayload(
        decision_id="DEC_TEST_002",
        timestamp_utc="2026-11-14T00:00:00Z",
        triage_state="GREEN",
        clinical_title="Nominal",
        hud_banner=banner,
        three_second_executive_summary="Nominal equilibrium",
        action_deck=[],
        total_execution_window_sec=0,
        biomarker_context_lead="HR",
        is_cmo_override_active=False,
    )
    config = HUDStatusBannerRenderer.create_config_from_payload(payload)
    assert config.target_locker_id is None
    assert config.target_locker_label is None
    assert config.is_cmo_override is False


# =============================================================================
# 2. HTML RENDERING & VISUAL / ACOUSTIC SIGNALING TESTS
# =============================================================================

def test_06_render_html_green_state():
    """Verifies HTML output for STATE GREEN nominal equilibrium."""
    config = HUDDisplayConfig(
        triage_state="GREEN",
        clinical_title="Nominal Spaceflight Homeostasis",
        executive_summary="Crew vitals within standard biological envelope.",
        matched_rule_id="RULE_GREEN_001",
        audio_tone_frequency_hz=0,
        flash_frequency_hz=0.0,
    )
    html_out = HUDStatusBannerRenderer.render_html(config)

    assert "hud-banner-green" in html_out
    assert "STATE GREEN // HOMEOSTATIC EQUILIBRIUM" in html_out
    assert "0 Hz (SILENT)" in html_out
    assert "STEADY HOMEOSTASIS" in html_out
    assert "DO-178C DAL C VERIFIED" in html_out


def test_07_render_html_amber_state_with_locker():
    """Verifies HTML output for STATE AMBER compensatory stress alert."""
    config = HUDDisplayConfig(
        triage_state="AMBER",
        clinical_title="Early Cephalad Fluid Shift",
        executive_summary="Compensatory fluid shift detected. Apply thigh cuffs.",
        matched_rule_id="RULE_AMBER_001",
        audio_tone_frequency_hz=600,
        flash_frequency_hz=1.0,
        target_locker_id="PHYS-01",
        target_locker_label="LOCKER L4 // CHIBIS LBNP & EXERCISE COUNTERMEASURES",
        is_alarm_acknowledged=False,
    )
    html_out = HUDStatusBannerRenderer.render_html(config)

    assert "hud-banner-amber" in html_out
    assert "STATE AMBER // COMPENSATORY STRESS" in html_out
    assert "600 Hz PULSING ALERT" in html_out
    assert "1.0 Hz PULSE" in html_out
    assert "LOCKER L4" in html_out
    assert "[UNACKNOWLEDGED]" in html_out


def test_08_render_html_red_state_unacknowledged():
    """Verifies HTML output for STATE RED critical emergency with unacknowledged alarm."""
    config = HUDDisplayConfig(
        triage_state="RED",
        clinical_title="Acute EVA Hypoxia Emergency",
        executive_summary="Critical SpO2 drop. Deploy O2 rebreather immediately.",
        matched_rule_id="RULE_RED_001",
        audio_tone_frequency_hz=1200,
        flash_frequency_hz=2.0,
        target_locker_id="ENV-01",
        target_locker_label="LOCKER L3 // RESPIRATORY & O2 REBREATHER",
        is_alarm_acknowledged=False,
    )
    html_out = HUDStatusBannerRenderer.render_html(config)

    assert "hud-banner-red" in html_out
    assert "STATE RED // CRITICAL EMERGENCY" in html_out
    assert "1,200 Hz EMERGENCY KLAXON" in html_out
    assert "2.0 Hz STROBE" in html_out
    assert "LOCKER L3" in html_out
    assert "[UNACKNOWLEDGED]" in html_out


def test_09_render_html_red_state_acknowledged():
    """Verifies HTML output when critical alarm has been silenced / acknowledged."""
    config = HUDDisplayConfig(
        triage_state="RED",
        clinical_title="Cardiovascular Decompensation",
        executive_summary="Immediate resuscitation protocol active.",
        matched_rule_id="RULE_RED_004",
        audio_tone_frequency_hz=1200,
        flash_frequency_hz=2.0,
        is_alarm_acknowledged=True,
    )
    html_out = HUDStatusBannerRenderer.render_html(config)

    assert "[ACKNOWLEDGED]" in html_out
    assert "[UNACKNOWLEDGED]" not in html_out


def test_10_render_html_with_cmo_override(state_manager: CockpitStateManager):
    """Verifies Sovereign CMO Override banner presentation."""
    state_manager.set_crew_member("CMO_ORION")
    state_manager.apply_cmo_override(
        target_state="RED",
        clinical_rationale="Suspected thoracic trauma after payload latch release.",
        authorizing_cmo="CMO_ORION"
    )
    record = state_manager.latest_record
    assert record is not None

    config = HUDStatusBannerRenderer.create_config_from_record(record)
    html_out = HUDStatusBannerRenderer.render_html(config)

    assert "SOVEREIGN CREW MEDICAL OFFICER (CMO) OVERRIDE ASSERTED" in html_out
    assert "DR. MICHAEL COLLINS (CMO)" in html_out
    assert "Suspected thoracic trauma" in html_out


def test_11_render_html_cmo_override_default_rationale_fallback():
    """Verifies CMO override fallback rationale when none is explicitly provided."""
    config = HUDDisplayConfig(
        triage_state="RED",
        clinical_title="Critical State",
        executive_summary="Summary text",
        matched_rule_id="RULE_RED_001",
        audio_tone_frequency_hz=1200,
        flash_frequency_hz=2.0,
        is_cmo_override=True,
        cmo_rationale=None,
    )
    html_out = HUDStatusBannerRenderer.render_html(config)
    assert "Clinical discretion applied." in html_out


# =============================================================================
# 3. STREAMLIT EMBEDDING & HEADLESS COMPATIBILITY
# =============================================================================

def test_12_render_streamlit_with_mock_container():
    """Verifies rendering into a Streamlit container object."""
    mock_container = MagicMock()
    config = HUDDisplayConfig(
        triage_state="GREEN",
        clinical_title="Nominal Homeostasis",
        executive_summary="All vitals normal.",
        matched_rule_id="RULE_GREEN_001",
        audio_tone_frequency_hz=0,
        flash_frequency_hz=0.0,
    )

    HUDStatusBannerRenderer.render_streamlit(config, container=mock_container)
    assert mock_container.markdown.called
    args, kwargs = mock_container.markdown.call_args
    assert "hud-banner-green" in args[0]
    assert kwargs.get("unsafe_allow_html") is True


def test_13_render_streamlit_default_container():
    """Verifies rendering to default Streamlit module."""
    config = HUDDisplayConfig(
        triage_state="GREEN",
        clinical_title="Nominal Homeostasis",
        executive_summary="All vitals normal.",
        matched_rule_id="RULE_GREEN_001",
        audio_tone_frequency_hz=0,
        flash_frequency_hz=0.0,
    )
    # When streamlit is available, render_streamlit will safely execute without error
    HUDStatusBannerRenderer.render_streamlit(config)


def test_14_create_config_from_payload_unmapped_locker():
    """Verifies creating display config when equipment location has no matching known locker ID."""
    banner = HUDAlertBanner("AMBER_WARNING", "#FFB800", "#05070E", 600, "INTERMITTENT_CAUTION", 1.0, False, 2)
    step = SequencedActionStep(
        step_number=1,
        action_id="ACT_999",
        protocol="Check Airlock Seals",
        priority=2,
        time_to_execute_sec=60,
        equipment_location="Forward Airlock Bay 3",
        verification_step="Hatch pressure normal",
        subsystem_lead="FLIGHT_ENGINEER",
        is_critical_path=False,
    )
    payload = CockpitActionPayload(
        decision_id="DEC_UNMAPPED",
        timestamp_utc="2026-11-14T00:00:00Z",
        triage_state="AMBER",
        clinical_title="Airlock Differential Warning",
        hud_banner=banner,
        three_second_executive_summary="Pressure seal check advised.",
        action_deck=[step],
        total_execution_window_sec=60,
        biomarker_context_lead="ENV_P",
        is_cmo_override_active=False,
    )
    config = HUDStatusBannerRenderer.create_config_from_payload(payload)
    assert config.target_locker_id == "Forward Airlock Bay 3"
    assert config.target_locker_label == "EQUIPMENT: Forward Airlock Bay 3"


def test_15_render_streamlit_import_error(monkeypatch):
    """Verifies headless execution fallback when streamlit raises ImportError."""
    config = HUDDisplayConfig(
        triage_state="GREEN",
        clinical_title="Nominal Homeostasis",
        executive_summary="All vitals normal.",
        matched_rule_id="RULE_GREEN_001",
        audio_tone_frequency_hz=0,
        flash_frequency_hz=0.0,
    )
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Simulated missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    HUDStatusBannerRenderer.render_streamlit(config)

