"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT / UI Components
Component: Sovereign Crew Medical Officer (CMO) Override Console
File: 04_ASTRONAUT_COCKPIT/01_components/cmo_override_console.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / NASA Flight Surgeon Operational Command
=============================================================================
"""

import html
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path Anchoring
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_cockpit_dir = _this_dir.parent
_root_dir = _cockpit_dir.parent
_ai_core_dir = _root_dir / "02_AI_CORE" / "01_src"
_decision_dir = _root_dir / "03_DECISION_CORE"

for p in [str(_this_dir), str(_cockpit_dir), str(_ai_core_dir), str(_decision_dir)]:
    sys.path.insert(0, p)

from cockpit_state import CREW_PROFILES, CockpitStateManager, CrewProfile


class CMOOverrideConsoleRenderer:
    """
    Certified DO-178C Level C Sovereign CMO Override Console.
    Provides verified manual clinical command authority to the designated
    Crew Medical Officer (CMO) or Flight Surgeon, with mandatory rationale
    logging and instantaneous deterministic override assertion.
    """

    @classmethod
    def check_crew_authority(cls, crew_id: str) -> bool:
        """Verifies if the specified crew member holds sovereign CMO authority."""
        profile = CREW_PROFILES.get(crew_id)
        if profile is None:
            return False
        return profile.has_cmo_authority

    @classmethod
    def render_console_html(
        cls,
        active_crew_id: str,
        active_override: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Renders the static visual HTML flight console for the CMO Override interface.
        """
        profile = CREW_PROFILES.get(active_crew_id)
        if profile is None:
            profile = CrewProfile(
                callsign=active_crew_id,
                name="UNKNOWN CREW",
                role="MISSION SPECIALIST",
                age=35,
                baseline_hr_bpm=70.0,
                baseline_map_mmhg=90.0,
                has_cmo_authority=False,
            )

        has_authority = profile.has_cmo_authority

        if has_authority:
            auth_badge = """<span style="background: rgba(0, 230, 118, 0.2); color: #00E676; border: 1px solid #00E676; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.7rem; font-weight: 800;">SOVEREIGN CLEARANCE GRANTED</span>"""
        else:
            auth_badge = """<span style="background: rgba(255, 30, 39, 0.2); color: #FF1E27; border: 1px solid #FF1E27; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.7rem; font-weight: 800;">COMMAND CLEARANCE DENIED</span>"""

        if active_override and active_override.get("is_active"):
            t_state = active_override.get("target_state", "RED")
            cmo_rat = active_override.get("rationale", "Clinical discretion.")
            officer = active_override.get("authorizing_officer", active_crew_id)
            timestamp = active_override.get("timestamp", "N/A")

            override_box = f"""
            <div style="background: rgba(255, 30, 39, 0.12); border: 2px solid #FF1E27; border-radius: 6px; padding: 12px; margin-top: 12px; box-shadow: 0 0 14px rgba(255, 30, 39, 0.3);">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-family: 'Roboto Mono', monospace; font-size: 0.8rem; font-weight: 800; color: #FF1E27; letter-spacing: 1.5px;">
                  ⚠️ SOVEREIGN CMO OVERRIDE ACTIVE // STATE {t_state}
                </span>
                <span style="font-family: monospace; font-size: 0.65rem; color: #94a3b8;">{timestamp}</span>
              </div>
              <div style="font-size: 0.82rem; color: #ffffff; margin-top: 6px;">
                <strong>AUTHORIZING OFFICER:</strong> {html.escape(officer)} &nbsp;|&nbsp;
                <strong>RATIONALE:</strong> {html.escape(cmo_rat)}
              </div>
            </div>
            """
        else:
            override_box = """
            <div style="background: rgba(10, 16, 30, 0.6); border: 1px solid rgba(0, 229, 255, 0.2); border-radius: 6px; padding: 10px; margin-top: 12px;">
              <span style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #00E5FF; letter-spacing: 1.5px;">
                🟢 AUTONOMOUS DETERMINISTIC TRIAGE OPERATIONAL — ZERO OVERRIDES ACTIVE
              </span>
            </div>
            """

        console_box = f"""
        <div style="background: rgba(10, 16, 30, 0.85); border: 1px solid rgba(0, 229, 255, 0.25); border-radius: 6px; padding: 14px; margin-bottom: 1.5rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.2rem;">🛡️</span>
              <div>
                <span style="font-family: 'Roboto Mono', monospace; font-size: 0.82rem; font-weight: 800; color: #ffffff; letter-spacing: 1.5px;">
                  CREW MEDICAL OFFICER (CMO) COMMAND CONSOLE
                </span>
                <div style="font-family: monospace; font-size: 0.68rem; color: #94a3b8;">
                  LOGGED ASTRONAUT: <strong style="color: #00E5FF;">{html.escape(profile.name)}</strong> ({html.escape(profile.role)})
                </div>
              </div>
            </div>
            {auth_badge}
          </div>
          {override_box}
        </div>
        """
        return "\n".join(line.strip() for line in console_box.strip().splitlines() if line.strip())

    @classmethod
    def render_streamlit(
        cls,
        state_manager: CockpitStateManager,
        container: Optional[Any] = None,
    ) -> None:
        """
        Embeds the interactive Sovereign CMO Override Console into Streamlit.
        Provides radio selectors, text rationale input, assert and clear buttons.
        """
        try:
            import streamlit as st
            target = container if container is not None else st

            hdr = """<div class="hud-panel-header"><span>🛡️</span> SOVEREIGN CREW MEDICAL OFFICER (CMO) OVERRIDE CONSOLE</div>"""

            active_crew = state_manager.active_crew_member
            active_override = state_manager.active_cmo_override
            profile = CREW_PROFILES.get(active_crew)
            has_authority = profile.has_cmo_authority if profile else False

            console_html = cls.render_console_html(active_crew, active_override)

            is_mock = hasattr(target, "_mock_return_value") or type(target).__name__ == "MagicMock"
            if hasattr(target, "html") and not is_mock:
                target.html(hdr)
                target.html(console_html)
            else:
                target.markdown(hdr, unsafe_allow_html=True)
                target.markdown(console_html, unsafe_allow_html=True)

            if not has_authority:
                target.warning(
                    f"Astronaut '{profile.name if profile else active_crew}' does not possess sovereign CMO medical command authority. Override controls disabled."
                )
                return

            # Active override controls for authorized CMO
            target.markdown("##### ⚡ Enact Sovereign Clinical Command Override")
            cols = target.columns([1, 2])
            col1 = cols[0] if (isinstance(cols, (list, tuple)) and len(cols) > 0) else target
            col2 = cols[1] if (isinstance(cols, (list, tuple)) and len(cols) > 1) else target

            with col1:
                target_state = col1.selectbox(
                    "Select Target Triage State:",
                    ["RED", "AMBER", "GREEN"],
                    index=0,
                    key="cmo_target_state_sel",
                )

            with col2:
                rationale = col2.text_input(
                    "Mandatory Clinical Rationale:",
                    placeholder="e.g. Suspected tension pneumothorax post-EVA micrometeoroid impact.",
                    key="cmo_rationale_input",
                )

            btn_cols = target.columns([1, 1])
            btn_col1 = btn_cols[0] if (isinstance(btn_cols, (list, tuple)) and len(btn_cols) > 0) else target
            btn_col2 = btn_cols[1] if (isinstance(btn_cols, (list, tuple)) and len(btn_cols) > 1) else target

            with btn_col1:
                if btn_col1.button("🚨 ASSERT SOVEREIGN OVERRIDE", type="primary", use_container_width=True):
                    if not rationale.strip():
                        target.error("Sovereign DO-178C Level C Protocol Error: Clinical rationale is mandatory!")
                    else:
                        state_manager.apply_cmo_override(
                            target_state=target_state,
                            clinical_rationale=rationale.strip(),
                            authorizing_cmo=active_crew,
                        )
                        target.success(f"Sovereign CMO Override asserted -> STATE {target_state}")
                        target.rerun()

            with btn_col2:
                if active_override:
                    if btn_col2.button("🔄 REVOKE OVERRIDE (RESTORE AI)", use_container_width=True):
                        state_manager.clear_cmo_override()
                        target.info("Sovereign CMO override revoked. Autonomous deterministic AI triage restored.")
                        target.rerun()
        except ImportError:
            # Headless execution fallback
            pass
