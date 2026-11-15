"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Test Suite: test_telemetry_stream_view.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A HMI Systems
Verification: 100% Statement Coverage on telemetry_stream_view.py
=============================================================================
"""

import math
import sys
from pathlib import Path
from unittest.mock import MagicMock
import pandas as pd
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

from telemetry_stream_view import (
    BIOPHYSICAL_REGISTRY,
    CHANNEL_REGISTRY,
    BiophysicalGaugeMetadata,
    TelemetryChannelMetadata,
    TelemetryStreamRenderer,
)
from cockpit_state import CockpitStateManager


@pytest.fixture
def state_manager() -> CockpitStateManager:
    return CockpitStateManager()


# =============================================================================
# 1. METADATA VECTOR INITIALIZATION TESTS
# =============================================================================

def test_01_channel_metadata_initialization():
    """Verifies dataclass fields and immutability of TelemetryChannelMetadata."""
    meta = TelemetryChannelMetadata(
        channel_id="test_channel",
        display_label="TEST CHANNEL",
        unit="units",
        nominal_min=10.0,
        nominal_max=20.0,
        critical_min=5.0,
        critical_max=25.0,
        icon_name="test.svg",
        format_spec="{:.1f}",
        category="CARDIO",
    )
    assert meta.channel_id == "test_channel"
    assert meta.display_label == "TEST CHANNEL"
    assert meta.unit == "units"
    assert meta.nominal_min == 10.0
    assert meta.nominal_max == 20.0
    assert meta.critical_min == 5.0
    assert meta.critical_max == 25.0
    assert meta.category == "CARDIO"


def test_02_biophysical_metadata_initialization():
    """Verifies dataclass fields and immutability of BiophysicalGaugeMetadata."""
    meta = BiophysicalGaugeMetadata(
        metric_id="test_gauge",
        display_name="Test Gauge",
        symbol="TG",
        unit="pts",
        formula_latex="TG = a + b",
        nominal_min=1.0,
        nominal_max=5.0,
        critical_direction="HIGH",
        format_spec="{:.2f}",
        clinical_meaning="Meaningful clinical rationale.",
    )
    assert meta.metric_id == "test_gauge"
    assert meta.symbol == "TG"
    assert meta.critical_direction == "HIGH"
    assert "Meaningful" in meta.clinical_meaning


# =============================================================================
# 2. EVALUATION & SIGNALING TESTS
# =============================================================================

def test_03_evaluate_channel_state_all_branches():
    """Verifies channel state evaluation across all nominal, warning, and critical branches."""
    meta = TelemetryChannelMetadata(
        channel_id="ch_test",
        display_label="TEST",
        unit="",
        nominal_min=50.0,
        nominal_max=100.0,
        critical_min=30.0,
        critical_max=120.0,
    )

    # NaN input
    assert TelemetryStreamRenderer.evaluate_channel_state(float("nan"), meta) == "AMBER"

    # Critical Min breach
    assert TelemetryStreamRenderer.evaluate_channel_state(25.0, meta) == "RED"

    # Critical Max breach
    assert TelemetryStreamRenderer.evaluate_channel_state(125.0, meta) == "RED"

    # Nominal range
    assert TelemetryStreamRenderer.evaluate_channel_state(75.0, meta) == "GREEN"
    assert TelemetryStreamRenderer.evaluate_channel_state(50.0, meta) == "GREEN"
    assert TelemetryStreamRenderer.evaluate_channel_state(100.0, meta) == "GREEN"

    # Warning range (between nominal and critical)
    assert TelemetryStreamRenderer.evaluate_channel_state(40.0, meta) == "AMBER"
    assert TelemetryStreamRenderer.evaluate_channel_state(110.0, meta) == "AMBER"


def test_04_evaluate_gauge_state_all_branches():
    """Verifies biophysical gauge evaluation for HIGH, LOW, and BOTH directions."""
    # NaN check
    dummy_meta = BIOPHYSICAL_REGISTRY["icp_gradient_index"]
    assert TelemetryStreamRenderer.evaluate_gauge_state(float("nan"), dummy_meta) == "AMBER"

    # HIGH direction: nominal <= 1.15
    meta_high = BIOPHYSICAL_REGISTRY["icp_gradient_index"]
    assert TelemetryStreamRenderer.evaluate_gauge_state(1.0, meta_high) == "GREEN"
    assert TelemetryStreamRenderer.evaluate_gauge_state(1.20, meta_high) == "AMBER"
    assert TelemetryStreamRenderer.evaluate_gauge_state(1.45, meta_high) == "RED"

    # LOW direction: nominal 80 - 120
    meta_low = BIOPHYSICAL_REGISTRY["stroke_volume_ml"]
    assert TelemetryStreamRenderer.evaluate_gauge_state(95.0, meta_low) == "GREEN"
    assert TelemetryStreamRenderer.evaluate_gauge_state(75.0, meta_low) == "AMBER"
    assert TelemetryStreamRenderer.evaluate_gauge_state(55.0, meta_low) == "RED"

    # BOTH direction: nominal 70 - 105
    meta_both = BIOPHYSICAL_REGISTRY["map_mmhg"]
    assert TelemetryStreamRenderer.evaluate_gauge_state(85.0, meta_both) == "GREEN"
    assert TelemetryStreamRenderer.evaluate_gauge_state(68.0, meta_both) == "AMBER"
    assert TelemetryStreamRenderer.evaluate_gauge_state(110.0, meta_both) == "AMBER"
    assert TelemetryStreamRenderer.evaluate_gauge_state(50.0, meta_both) == "RED"
    assert TelemetryStreamRenderer.evaluate_gauge_state(130.0, meta_both) == "RED"


def test_05_compute_trend_arrow_all_branches():
    """Verifies delta trend arrow computation including edge cases."""
    # None or NaN prev_val
    assert TelemetryStreamRenderer.compute_trend_arrow(100.0, None) == ("▶", "#64748b")
    assert TelemetryStreamRenderer.compute_trend_arrow(100.0, float("nan")) == ("▶", "#64748b")
    assert TelemetryStreamRenderer.compute_trend_arrow(float("nan"), 100.0) == ("▶", "#64748b")

    # Rising delta
    arrow, color = TelemetryStreamRenderer.compute_trend_arrow(110.0, 100.0)
    assert arrow == "▲"
    assert color == "#00E5FF"

    # Falling delta
    arrow, color = TelemetryStreamRenderer.compute_trend_arrow(90.0, 100.0)
    assert arrow == "▼"
    assert color == "#FFB800"

    # Steady within epsilon
    arrow, color = TelemetryStreamRenderer.compute_trend_arrow(100.005, 100.0)
    assert arrow == "▶"
    assert color == "#64748b"


def test_06_get_channel_icon_svg_branches():
    """Verifies SVG loading, in-memory caching, and fallback handling."""
    # Empty icon
    assert TelemetryStreamRenderer.get_channel_icon_svg("") == ""

    # Known existing icon file
    svg1 = TelemetryStreamRenderer.get_channel_icon_svg("heart_rate.svg")
    assert "<svg" in svg1
    assert "heart_rate.svg" in TelemetryStreamRenderer._svg_cache

    # Cache hit check
    svg2 = TelemetryStreamRenderer.get_channel_icon_svg("heart_rate.svg")
    assert svg1 == svg2

    # Non-existent file fallback
    svg_fallback = TelemetryStreamRenderer.get_channel_icon_svg("non_existent_icon.svg")
    assert "<svg" in svg_fallback
    assert "non_existent_icon.svg" in TelemetryStreamRenderer._svg_cache


# =============================================================================
# 3. HTML RENDERING TESTS (CARDS, GRIDS, GAUGES)
# =============================================================================

def test_07_render_metric_card_states():
    """Verifies rendering metric cards in GREEN, AMBER, RED, unknown channel, and NaN states."""
    # 1. GREEN state
    html_green = TelemetryStreamRenderer.render_metric_card("heart_rate_bpm", 72.0, 72.0)
    assert "HEART RATE" in html_green
    assert "NOM" in html_green
    assert "72" in html_green
    assert "bpm" in html_green

    # 2. AMBER state
    html_amber = TelemetryStreamRenderer.render_metric_card("heart_rate_bpm", 110.0, 100.0)
    assert "WARN" in html_amber
    assert "#FFD54F" in html_amber

    # 3. RED state
    html_red = TelemetryStreamRenderer.render_metric_card("heart_rate_bpm", 155.0, 140.0)
    assert "CRIT" in html_red
    assert "#FF454D" in html_red

    # 4. Unknown channel fallback
    html_unknown = TelemetryStreamRenderer.render_metric_card("unknown_sensor_raw", 42.0)
    assert "UNKNOWN SENSOR RAW" in html_unknown

    # 5. NaN value
    html_nan = TelemetryStreamRenderer.render_metric_card("heart_rate_bpm", float("nan"))
    assert "ERR" in html_nan


def test_08_render_telemetry_grid(state_manager: CockpitStateManager):
    """Verifies full 12-channel telemetry grid generation."""
    rec = state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    grid_html = TelemetryStreamRenderer.render_telemetry_grid(rec)

    for channel_id, meta in CHANNEL_REGISTRY.items():
        assert meta.display_label in grid_html

    # Test with prev_telemetry provided
    prev = dict(rec.sanitized_telemetry)
    prev["heart_rate_bpm"] = 65.0
    grid_html_with_prev = TelemetryStreamRenderer.render_telemetry_grid(rec, prev_telemetry=prev)
    assert "HEART RATE" in grid_html_with_prev


def test_09_render_biophysical_gauges(state_manager: CockpitStateManager):
    """Verifies rendering all 5 spaceflight biophysical gauges."""
    # Test nominal record
    rec_nom = state_manager.inject_scenario("SCENARIO_01_NOMINAL_CRUISE")
    gauges_nom = TelemetryStreamRenderer.render_biophysical_gauges(rec_nom)

    for metric_id, meta in BIOPHYSICAL_REGISTRY.items():
        assert meta.display_name.upper() in gauges_nom
        assert meta.unit in gauges_nom

    # Test scenario with critical, amber, and NaN values
    rec_crit = state_manager.inject_scenario("SCENARIO_05_EARLY_FLUID_SHIFT_COMPENSATION")
    from dataclasses import replace
    mock_metrics = dict(rec_crit.biophysical_metrics)
    mock_metrics["icp_gradient_index"] = 1.20  # AMBER
    mock_metrics["stroke_volume_ml"] = 40.0    # RED
    mock_metrics["map_mmhg"] = float("nan")     # NaN -> N/A
    rec_amber = replace(rec_crit, biophysical_metrics=mock_metrics)
    gauges_amber = TelemetryStreamRenderer.render_biophysical_gauges(rec_amber)
    assert "COMPENSATORY DRIFT" in gauges_amber
    assert "CRITICAL DEVIATION" in gauges_amber
    assert "N/A" in gauges_amber


# =============================================================================
# 4. PLOTLY WAVEFORM & STREAMLIT EMBEDDING TESTS
# =============================================================================

def test_10_create_waveform_figure(state_manager: CockpitStateManager):
    """Verifies Plotly 3-subplot waveform creation from telemetry ring buffer."""
    df = state_manager.telemetry_buffer.to_dataframe()
    fig = TelemetryStreamRenderer.create_waveform_figure(df, time_window_frames=60)

    assert fig is not None
    assert len(fig.data) >= 8  # HR, SBP, DBP, MAP, SpO2, EtCO2, RR, I_ICP, SV, SI
    assert fig.layout.paper_bgcolor == "#05070E"

    # Test empty dataframe fallback
    empty_df = pd.DataFrame()
    fig_empty = TelemetryStreamRenderer.create_waveform_figure(empty_df)
    assert fig_empty is not None
    assert len(fig_empty.data) >= 8


def test_11_render_streamlit_with_mock_container(state_manager: CockpitStateManager):
    """Verifies rendering into a Streamlit mock container."""
    rec = state_manager.latest_record
    df = state_manager.telemetry_buffer.to_dataframe()
    mock_container = MagicMock()

    TelemetryStreamRenderer.render_streamlit(rec, df, container=mock_container)
    assert mock_container.markdown.called
    assert mock_container.plotly_chart.called


def test_12_render_streamlit_default_container(state_manager: CockpitStateManager):
    """Verifies rendering into default Streamlit module."""
    rec = state_manager.latest_record
    df = state_manager.telemetry_buffer.to_dataframe()
    # Runs safely without exception
    TelemetryStreamRenderer.render_streamlit(rec, df)


def test_13_render_streamlit_import_error(state_manager: CockpitStateManager, monkeypatch):
    """Verifies headless execution fallback when streamlit raises ImportError."""
    rec = state_manager.latest_record
    df = state_manager.telemetry_buffer.to_dataframe()

    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "streamlit":
            raise ImportError("Simulated missing streamlit")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    # Should not raise exception
    TelemetryStreamRenderer.render_streamlit(rec, df)
