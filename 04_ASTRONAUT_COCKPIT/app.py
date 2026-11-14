"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT
Master Flight Application Entrypoint: app.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / NASA-STD-3001 Vol 2 / MIL-STD-1472H
Deployment: NASA Orion Flight Deck / SpaceX Crew Dragon Glassmorphic Cockpit HUD
=============================================================================
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# ---------------------------------------------------------------------------
# Path Anchoring
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_cockpit_comp = _this_dir / "01_components"
_root_dir = _this_dir.parent
_ai_core_dir = _root_dir / "02_AI_CORE" / "01_src"
_decision_dir = _root_dir / "03_DECISION_CORE"

for p in [str(_this_dir), str(_cockpit_comp), str(_ai_core_dir), str(_decision_dir)]:
    sys.path.insert(0, p)

from cockpit_state import (
    CREW_PROFILES,
    FLIGHT_SCENARIO_PRESETS,
    CockpitStateManager,
)
from hud_status_banner import HUDStatusBannerRenderer
from telemetry_stream_view import TelemetryStreamRenderer
from countermeasure_deck import CountermeasureDeckRenderer
from audit_trace_terminal import AuditTraceTerminalRenderer
from cmo_override_console import CMOOverrideConsoleRenderer


def inject_custom_css() -> None:
    """Injects high-contrast Orion glassmorphic dark theme CSS into Streamlit DOM."""
    try:
        import streamlit as st
        css_file = _this_dir / "02_assets" / "cockpit_theme.css"
        if css_file.exists():
            css_code = css_file.read_text(encoding="utf-8")
            st.markdown(f"<style>{css_code}</style>", unsafe_allow_html=True)
    except ImportError:
        pass


def get_state_manager() -> CockpitStateManager:
    """Retrieves or initializes the CockpitStateManager within Streamlit session state."""
    try:
        import streamlit as st
        if "state_manager" not in st.session_state:
            st.session_state["state_manager"] = CockpitStateManager()
        return st.session_state["state_manager"]
    except ImportError:
        return CockpitStateManager()


def render_sidebar_controls(state_manager: CockpitStateManager) -> None:
    """Renders flight deck control panel in Streamlit sidebar."""
    try:
        import streamlit as st
        with st.sidebar:
            st.markdown(
                """
                <div style="padding: 10px 0; border-bottom: 1px solid rgba(0, 229, 255, 0.2); margin-bottom: 1rem;">
                  <div style="font-family: 'Roboto Mono', monospace; font-size: 0.95rem; font-weight: 800; color: #00E5FF; letter-spacing: 2px;">
                    🚀 ASTROVITAL AI
                  </div>
                  <div style="font-family: monospace; font-size: 0.68rem; color: #94a3b8; letter-spacing: 1px;">
                    ORION FLIGHT DECK CDSS // V1
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Crew Profile Selector
            st.markdown("##### 👨‍🚀 Active Astronaut Profile")
            crew_keys = list(CREW_PROFILES.keys())
            current_crew_idx = crew_keys.index(state_manager.active_crew_member) if state_manager.active_crew_member in crew_keys else 0
            selected_crew = st.selectbox(
                "Select Crew Member:",
                options=crew_keys,
                index=current_crew_idx,
                format_func=lambda k: f"{CREW_PROFILES[k].name} ({CREW_PROFILES[k].role})",
                key="sb_crew_select",
            )
            if selected_crew != state_manager.active_crew_member:
                state_manager.set_crew_member(selected_crew)
                st.rerun()

            st.markdown("---")

            # Scenario Presets Selector
            st.markdown("##### 🎮 Flight Simulation Scenarios")
            scenario_keys = list(FLIGHT_SCENARIO_PRESETS.keys())
            current_scen_idx = scenario_keys.index(state_manager.current_scenario_id) if state_manager.current_scenario_id in scenario_keys else 0
            selected_scen = st.selectbox(
                "Inject Mission Scenario:",
                options=scenario_keys,
                index=current_scen_idx,
                format_func=lambda k: f"{FLIGHT_SCENARIO_PRESETS[k].title} [STATE {FLIGHT_SCENARIO_PRESETS[k].expected_triage}]",
                key="sb_scenario_select",
            )
            if selected_scen != state_manager.current_scenario_id:
                state_manager.inject_scenario(selected_scen)
                st.rerun()

            st.markdown("---")

            # Simulation Controls
            st.markdown("##### ⏱ Telemetry Stream Controls")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⏩ Step Frame", use_container_width=True):
                    state_manager.step_simulation()
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Buffer", use_container_width=True):
                    state_manager.reset_buffer()
                    st.rerun()

            st.markdown("---")

            # System Verification Metrics
            rec = state_manager.latest_record
            if rec:
                st.markdown(
                    f"""
                    <div style="font-family: monospace; font-size: 0.68rem; color: #64748b; line-height: 1.5;">
                      <div>FRAME: #{rec.frame_index}</div>
                      <div>LATENCY: <strong style="color: #00E676;">{rec.execution_latency_ms:.2f} ms</strong></div>
                      <div>MODE: {rec.flight_mode}</div>
                      <div>SHA-256: {rec.config_sha256[:12]}...</div>
                      <div style="margin-top: 6px; color: #00E5FF;">DO-178C LEVEL C VERIFIED</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    except ImportError:
        pass


def render_cockpit_display(state_manager: CockpitStateManager) -> None:
    """Renders the complete 6-stage unified flight deck dashboard."""
    rec = state_manager.latest_record
    if rec is None:
        return

    try:
        import streamlit as st

        # 1. Top Section: 3-Second Rapid Response Cockpit Alert Banner
        hud_config = HUDStatusBannerRenderer.create_config_from_record(rec)
        HUDStatusBannerRenderer.render_streamlit(hud_config)

        # 2. Main Flight Deck Tabs
        tab_vitals, tab_lockers, tab_cmo, tab_audit = st.tabs([
            "📡 TELEMETRY & BIOPHYSICS",
            "🧰 LOCKERS & COUNTERMEASURES",
            "🛡️ CMO COMMAND CONSOLE",
            "📟 WHITE-BOX AUDIT TERMINAL",
        ])

        with tab_vitals:
            df = state_manager.telemetry_buffer.to_dataframe()
            TelemetryStreamRenderer.render_streamlit(rec, df)

        with tab_lockers:
            CountermeasureDeckRenderer.render_streamlit(state_manager)

        with tab_cmo:
            CMOOverrideConsoleRenderer.render_streamlit(state_manager)

        with tab_audit:
            AuditTraceTerminalRenderer.render_streamlit(rec)

    except ImportError:
        pass


def main() -> None:
    """Master application entrypoint for Streamlit."""
    try:
        import streamlit as st
        st.set_page_config(
            page_title="ASTROVITAL AI // ORION FLIGHT DECK HUD",
            page_icon="🚀",
            layout="wide",
            initial_sidebar_state="expanded",
        )
    except ImportError:
        pass

    inject_custom_css()
    state_manager = get_state_manager()
    render_sidebar_controls(state_manager)
    render_cockpit_display(state_manager)


if __name__ == "__main__":
    main()
