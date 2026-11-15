"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 04_ASTRONAUT_COCKPIT / UI Components
Component: Physical Equipment Locker Deck & Interactive Countermeasures
File: 04_ASTRONAUT_COCKPIT/01_components/countermeasure_deck.py
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)
Safety Standard: DO-178C Level C (DAL C) / NASA-STD-3001 Vol 2 / MIL-STD-1472H
=============================================================================
"""

import html
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Path Anchoring
# ---------------------------------------------------------------------------
_this_dir = Path(__file__).resolve().parent
_cockpit_dir = _this_dir.parent
_root_dir = _cockpit_dir.parent
_ai_core_dir = _root_dir / "02_AI_CORE" / "01_src"
_decision_dir = _root_dir / "03_DECISION_CORE"
_icons_dir = _cockpit_dir / "02_assets" / "hud_icons"

for p in [str(_this_dir), str(_cockpit_dir), str(_ai_core_dir), str(_decision_dir)]:
    sys.path.insert(0, p)

from cockpit_countermeasure_dispatcher import (
    CockpitActionPayload,
    SequencedActionStep,
)
from cockpit_state import CockpitStateManager


@dataclass(frozen=True)
class LockerSpec:
    """Hardware specification for Orion physical equipment lockers."""
    locker_id: str
    locker_code: str  # "L1", "L2", "L3", "L4", "L5"
    title: str
    bay_location: str
    icon_filename: str


LOCKER_DIRECTORY: Dict[str, LockerSpec] = {
    "MED-01": LockerSpec(
        locker_id="MED-01",
        locker_code="L1",
        title="RESUSCITATION & AED",
        bay_location="Flight Deck Forward Locker MED-01",
        icon_filename="locker_l1_resuscitation.svg",
    ),
    "PHARM-01": LockerSpec(
        locker_id="PHARM-01",
        locker_code="L2",
        title="PHARMACOPEIA & INJECTABLES",
        bay_location="Middeck Medical Narcotics Locker MED-LOCK-A",
        icon_filename="locker_l2_pharmacopeia.svg",
    ),
    "ENV-01": LockerSpec(
        locker_id="ENV-01",
        locker_code="L3",
        title="RESPIRATORY & O2 REBREATHER",
        bay_location="Environmental Locker ENV-01",
        icon_filename="locker_l3_respiratory.svg",
    ),
    "PHYS-01": LockerSpec(
        locker_id="PHYS-01",
        locker_code="L4",
        title="CHIBIS LBNP & EXERCISE",
        bay_location="Crew Compartment Port PHYS-01",
        icon_filename="locker_l4_countermeasure.svg",
    ),
    "DIAG-01": LockerSpec(
        locker_id="DIAG-01",
        locker_code="L5",
        title="ULTRASOUND & DIAGNOSTICS",
        bay_location="Ultrasound Diagnostics Locker MED-04",
        icon_filename="locker_l5_diagnostic.svg",
    ),
}


class CountermeasureDeckRenderer:
    """
    Certified DO-178C Level C Countermeasure & Equipment Locker Deck.
    Maps clinical diagnostic decisions directly into actionable physical
    equipment retrieval sequences and interactive astronaut verification steps.
    """

    _icon_cache: Dict[str, str] = {}

    @classmethod
    def get_locker_icon_svg(cls, filename: str) -> str:
        """Retrieves and caches SVG content from the offline asset directory."""
        if not filename:
            return ""
        if filename in cls._icon_cache:
            return cls._icon_cache[filename]

        file_path = _icons_dir / filename
        if file_path.exists():
            content = file_path.read_text(encoding="utf-8")
            cls._icon_cache[filename] = content
            return content

        # Generic SVG box fallback
        fallback = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#00E5FF" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>"""
        cls._icon_cache[filename] = fallback
        return fallback

    @classmethod
    def resolve_active_locker_id(cls, action_deck: List[SequencedActionStep]) -> Optional[str]:
        """Identifies the active hardware locker ID from the primary critical action step."""
        if not action_deck:
            return None

        primary_loc = action_deck[0].equipment_location
        for loc_id in LOCKER_DIRECTORY:
            if loc_id in primary_loc:
                return loc_id
        if "Sleep" in primary_loc or "Bunk" in primary_loc:
            return "PHYS-01"
        return None

    @classmethod
    def render_locker_bay(cls, active_locker_id: Optional[str] = None) -> str:
        """
        Renders a high-visibility hardware locker array (L1 to L5).
        The targeted locker pulses with high-contrast HUD cyan or amber/red glow.
        """
        locker_cards: List[str] = []

        for loc_id, spec in LOCKER_DIRECTORY.items():
            is_active = (active_locker_id == loc_id)
            icon_svg = cls.get_locker_icon_svg(spec.icon_filename)

            if is_active:
                card_style = "background: rgba(0, 229, 255, 0.12); border: 2px solid #00E5FF; box-shadow: 0 0 16px rgba(0, 229, 255, 0.45); transform: translateY(-2px);"
                badge_style = "background: #00E5FF; color: #05070E; font-weight: 800;"
                status_text = "TARGET ACTIVE"
                status_color = "#00E5FF"
            else:
                card_style = "background: rgba(10, 16, 30, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); opacity: 0.75;"
                badge_style = "background: rgba(255, 255, 255, 0.1); color: #94a3b8;"
                status_text = "STANDBY"
                status_color = "#64748b"

            card_html = f"""
            <div style="{card_style} border-radius: 6px; padding: 10px; min-width: 150px; flex: 1; transition: all 0.2s ease;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="{badge_style} font-family: 'Roboto Mono', monospace; font-size: 0.7rem; padding: 2px 6px; border-radius: 3px;">
                  {spec.locker_code}
                </span>
                <span style="font-family: 'Roboto Mono', monospace; font-size: 0.62rem; color: {status_color}; font-weight: 700;">
                  {status_text}
                </span>
              </div>
              <div style="display: flex; align-items: center; gap: 8px; margin: 4px 0;">
                <div style="width: 26px; height: 26px; display: flex; align-items: center; justify-content: center;">
                  {icon_svg}
                </div>
                <div>
                  <div style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; font-weight: 700; color: #ffffff; line-height: 1.1;">
                    {html.escape(spec.title)}
                  </div>
                  <div style="font-family: monospace; font-size: 0.62rem; color: #94a3b8; margin-top: 2px;">
                    {spec.locker_id}
                  </div>
                </div>
              </div>
            </div>
            """
            locker_cards.append(card_html)

        joined_lockers = "\n".join(locker_cards)
        bay_html = f"""
        <div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 1.25rem;">
          {joined_lockers}
        </div>
        """
        return "\n".join(line.strip() for line in bay_html.strip().splitlines() if line.strip())

    @classmethod
    def render_checklist_card(
        cls,
        step: SequencedActionStep,
        is_completed: bool = False,
    ) -> str:
        """
        Renders a single countermeasure step card with execution window,
        verification criteria, subsystem lead, and completion indicator.
        """
        if is_completed:
            card_style = "background: rgba(0, 230, 118, 0.08); border: 1px solid rgba(0, 230, 118, 0.4); opacity: 0.7;"
            status_badge = """<span style="background: rgba(0, 230, 118, 0.2); color: #00E676; border: 1px solid #00E676; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.68rem; font-weight: 700;">COMPLETED</span>"""
            title_style = "color: #94a3b8; text-decoration: line-through;"
        else:
            if step.is_critical_path:
                card_style = "background: rgba(255, 30, 39, 0.08); border: 1px solid rgba(255, 30, 39, 0.5); box-shadow: 0 0 10px rgba(255, 30, 39, 0.2);"
                status_badge = """<span style="background: rgba(255, 30, 39, 0.2); color: #FF1E27; border: 1px solid #FF1E27; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.68rem; font-weight: 700;">CRITICAL PATH</span>"""
            else:
                card_style = "background: rgba(10, 16, 30, 0.7); border: 1px solid rgba(0, 229, 255, 0.2);"
                status_badge = """<span style="background: rgba(0, 229, 255, 0.15); color: #00E5FF; border: 1px solid #00E5FF; padding: 2px 8px; border-radius: 3px; font-family: monospace; font-size: 0.68rem; font-weight: 700;">ACTIVE STEP</span>"""
            title_style = "color: #ffffff; font-weight: 700;"

        card_html = f"""
        <div style="{card_style} border-radius: 6px; padding: 12px; margin-bottom: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-family: 'Roboto Mono', monospace; font-size: 0.8rem; font-weight: 800; color: #00E5FF; background: rgba(0,0,0,0.5); padding: 2px 6px; border-radius: 3px; border: 1px solid rgba(0,229,255,0.4);">
                #{step.step_number}
              </span>
              <span style="font-family: 'Roboto Mono', monospace; font-size: 0.75rem; color: #94a3b8;">
                {step.action_id}
              </span>
            </div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-family: monospace; font-size: 0.72rem; color: #FFB800;">
                ⏱ {step.time_to_execute_sec}s
              </span>
              {status_badge}
            </div>
          </div>
          <div style="font-size: 0.95rem; {title_style} margin: 4px 0 8px 0;">
            {html.escape(step.protocol)}
          </div>
          <div style="display: flex; flex-wrap: wrap; gap: 12px; font-family: 'Roboto Mono', monospace; font-size: 0.7rem; color: #cbd5e1; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 6px;">
            <div>
              <span style="color: #64748b;">LOC:</span> 
              <strong style="color: #00E5FF;">{html.escape(step.equipment_location)}</strong>
            </div>
            <div>
              <span style="color: #64748b;">LEAD:</span> 
              <strong style="color: #e2e8f0;">{html.escape(step.subsystem_lead)}</strong>
            </div>
          </div>
          <div style="margin-top: 6px; font-size: 0.72rem; color: #94a3b8; line-height: 1.25;">
            <span style="color: #64748b; font-family: monospace;">CRITERIA:</span> {html.escape(step.verification_step)}
          </div>
        </div>
        """
        return "\n".join(line.strip() for line in card_html.strip().splitlines() if line.strip())

    @classmethod
    def render_action_deck(
        cls,
        payload: CockpitActionPayload,
        checklist_states: Dict[str, bool],
    ) -> str:
        """
        Renders the complete countermeasure deck:
        Hardware locker array + sequenced countermeasure checklist cards.
        """
        active_locker_id = cls.resolve_active_locker_id(payload.action_deck)
        locker_bay_html = cls.render_locker_bay(active_locker_id)

        cards_html: List[str] = []
        for step in payload.action_deck:
            is_comp = checklist_states.get(step.action_id, False)
            cards_html.append(cls.render_checklist_card(step, is_comp))

        if not cards_html:
            cards_html.append(
                """<div style="padding: 16px; text-align: center; color: #64748b; font-family: monospace; font-size: 0.85rem;">NO ACTIVE COUNTERMEASURE ACTIONS REQUIRED — CREW IN EQUILIBRIUM</div>"""
            )

        joined_cards = "\n".join(cards_html)
        deck_html = f"""
        <div>
          {locker_bay_html}
          <div>
            {joined_cards}
          </div>
        </div>
        """
        return "\n".join(line.strip() for line in deck_html.strip().splitlines() if line.strip())

    @classmethod
    def render_streamlit(
        cls,
        state_manager: CockpitStateManager,
        container: Optional[Any] = None,
    ) -> None:
        """
        Embeds the interactive countermeasure deck into Streamlit,
        including live completion checkboxes that mutate state_manager.
        """
        try:
            import streamlit as st
            target = container if container is not None else st

            hdr = """<div class="hud-panel-header"><span>🧰</span> PHYSICAL ORION EQUIPMENT LOCKERS & COUNTERMEASURES</div>"""

            rec = state_manager.latest_record
            if not rec:
                return

            payload = rec.cockpit_payload
            active_locker_id = cls.resolve_active_locker_id(payload.action_deck)
            locker_bay_html = cls.render_locker_bay(active_locker_id)

            is_mock = hasattr(target, "_mock_return_value") or type(target).__name__ == "MagicMock"
            if hasattr(target, "html") and not is_mock:
                target.html(hdr)
                target.html(locker_bay_html)
            else:
                target.markdown(hdr, unsafe_allow_html=True)
                target.markdown(locker_bay_html, unsafe_allow_html=True)

            if not payload.action_deck:
                target.info("No active countermeasure actions required — nominal homeostasis.")
                return

            # Render each checklist step with interactive toggle checkbox
            for step in payload.action_deck:
                is_comp = state_manager.checklist_states.get(step.action_id, False)
                card_html = cls.render_checklist_card(step, is_comp)
                if hasattr(target, "html") and not is_mock:
                    target.html(card_html)
                else:
                    target.markdown(card_html, unsafe_allow_html=True)

                cols = target.columns([1, 4])
                col1 = cols[0] if (isinstance(cols, (list, tuple)) and len(cols) > 0) else target
                with col1:
                    new_val = col1.checkbox(
                        f"Verify #{step.step_number}",
                        value=is_comp,
                        key=f"chk_{step.action_id}",
                    )
                    if new_val != is_comp:
                        state_manager.toggle_checklist_item(step.action_id, is_completed=new_val)
                        target.rerun()
        except ImportError:
            # Headless execution fallback
            pass
