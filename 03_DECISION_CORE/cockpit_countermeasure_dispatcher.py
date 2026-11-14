"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Module: cockpit_countermeasure_dispatcher.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Deterministic Engine
Governance: 3-Second Astronaut Cockpit Protocol & Countermeasure Dispatcher
=============================================================================
"""

import json
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional, Tuple, Any, Union

from triage_model_engine import TriageDecisionPacket


# =============================================================================
# HARDWARE LOCKER & EQUIPMENT LOCATION REGISTRY
# =============================================================================

EQUIPMENT_LOCKER_REGISTRY: Dict[str, Dict[str, str]] = {
    "ACT_RED_001_O2_REBREATHER": {
        "location": "Flight Deck Forward Locker MED-01",
        "verification": "Confirm O2 pressure gauge > 1200 psi and mask seal green indicator illuminated.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_RED_001_SUSPEND_EVA": {
        "location": "Orion Avionics Console / Suit Umbilical Panel",
        "verification": "Confirm EVA comm circuit state transitioned to ABORT / STANDBY.",
        "subsystem_lead": "COMMANDER"
    },
    "ACT_RED_001_CMO_NOTIFICATION": {
        "location": "Cabin Master Audio Warning Intercom",
        "verification": "Verify audible klaxon acknowledged on CMO wearable display.",
        "subsystem_lead": "MISSION_CONTROLLER"
    },
    "ACT_RED_002_LBNP_DEPLOY": {
        "location": "Mid-Deck Lower Storage Bay LBNP-03",
        "verification": "Seal waist seal; verify vacuum pump pressure reads -35.0 mmHg on digital manometer.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_RED_002_CO2_SCRUBBING": {
        "location": "ECLSS Service Bay 2 (Lithium Hydroxide Rack)",
        "verification": "Verify secondary amine scrubber flow rate > 18.5 CFM on ECLSS telemetry.",
        "subsystem_lead": "FLIGHT_ENGINEER"
    },
    "ACT_RED_002_FUNDOSCOPIC_AUDIT": {
        "location": "Ultrasound Diagnostics Locker MED-04",
        "verification": "Confirm ONSD scan imagery recording to mission medical hard-drive.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_RED_003_REST_STATION": {
        "location": "Sleep Compartment / Crew Rest Tether Station 1",
        "verification": "Secure 4-point restraint tether; darken cabin lighting to 10% baseline.",
        "subsystem_lead": "COMMANDER"
    },
    "ACT_RED_003_PHARMA_READY": {
        "location": "Medical Narcotics & Cardiovascular Locker MED-LOCK-A",
        "verification": "Dual-verify drug label, ampoule integrity, and dosage with CMO checklist.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_RED_004_INFUSION_PROTOCOL": {
        "location": "Emergency Resuscitation Kit MED-02",
        "verification": "Prime IV tubing; verify zero air bubbles and gravity-independent pressure infuser at 150 mmHg.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_RED_004_G_SUIT_INFLATE": {
        "location": "Lower Extremity Pressure Garment Storage",
        "verification": "Verify thigh and abdominal bladders inflated to 50 mmHg counter-pressure.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_RED_005_DON_ORION_SUIT": {
        "location": "Suit Lockers SL-1 through SL-4",
        "verification": "Confirm neck ring lock, helmet visor closed, and positive suit differential pressure > 3.5 psid.",
        "subsystem_lead": "ALL_CREW"
    },
    "ACT_RED_005_SEAL_HATCHES": {
        "location": "Forward and Aft Bulkhead Pressure Hatches",
        "verification": "Check hatch equalize valve closed; confirm dual mechanical latch dogs fully engaged.",
        "subsystem_lead": "MISSION_SPECIALIST"
    },
    "ACT_RED_006_THERMAL_GARMENT": {
        "location": "LCVG Heat Exchanger Quick-Disconnect Panel",
        "verification": "Check water loop flow rate = 1.5 LPM and inlet temperature adjusted per protocol.",
        "subsystem_lead": "FLIGHT_ENGINEER"
    },
    "ACT_AMB_001_LBNP_SESSION": {
        "location": "Mid-Deck Lower Storage Bay LBNP-03",
        "verification": "Verify 30-minute timer started; pressure calibrated to -25.0 mmHg.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    },
    "ACT_AMB_001_POSTURE_REST": {
        "location": "Active Workstation / Crew Quarters",
        "verification": "Confirm astronaut posture elevated > 15 degrees relative to fluid gradient axis.",
        "subsystem_lead": "CREW_MEMBER"
    },
    "ACT_AMB_002_SWAP_CANISTER": {
        "location": "ECLSS Access Hatch 1",
        "verification": "Slide spent LiOH canister into hazmat stowage; lock fresh canister into Loop B.",
        "subsystem_lead": "FLIGHT_ENGINEER"
    },
    "ACT_AMB_002_VENTILATION_BOOST": {
        "location": "Environmental Control System Avionics Switch Panel",
        "verification": "Set cabin diffuser fan bank to HIGH (120 CFM); confirm air velocity > 0.15 m/s.",
        "subsystem_lead": "FLIGHT_ENGINEER"
    },
    "ACT_AMB_003_ARED_RESISTANCE": {
        "location": "Advanced Resistive Exercise Device (ARED) Platform",
        "verification": "Calibrate piston load cells to 250 lbs; record cadence on flight tablet.",
        "subsystem_lead": "CREW_MEMBER"
    },
    "ACT_AMB_003_ORAL_HYDRATION": {
        "location": "Galley Hydration Dispenser Bay",
        "verification": "Reconstitute Astro-Hydrate formulation with 500 mL ambient potable water; consume in 15 mins.",
        "subsystem_lead": "CREW_MEMBER"
    },
    "ACT_AMB_004_DEEP_BREATHE": {
        "location": "Personal Crew Medical Pouch MED-PERSONAL",
        "verification": "Complete 10 cycles of incentive spirometry to 2500 mL lung volume.",
        "subsystem_lead": "CREW_MEMBER"
    },
    "ACT_AMB_004_CABIN_O2_CHECK": {
        "location": "Orion Life Support Display Display-03",
        "verification": "Verify cabin oxygen fraction is within nominal 20.8% - 21.4% band.",
        "subsystem_lead": "FLIGHT_ENGINEER"
    },
    "ACT_AMB_005_MANDATORY_REST": {
        "location": "Crew Sleep Bunk Compartment",
        "verification": "Notify Houston Flight Surgeon; engage 2-hour sleep timer and ear protection.",
        "subsystem_lead": "COMMANDER"
    },
    "ACT_AMB_005_CIRCADIAN_LIGHTING": {
        "location": "Cabin Lighting Automation Controller",
        "verification": "Confirm solid-state LED fixtures switch to 2200K warm circadian spectrum.",
        "subsystem_lead": "COMMANDER"
    },
    "ACT_GRN_001_MAINTAIN_TIMELINE": {
        "location": "Flight Plan Timeline Console",
        "verification": "Log nominal physiological status check; proceed with scheduled mission tasks.",
        "subsystem_lead": "ALL_CREW"
    },
    "ACT_FALLBACK_MONITOR": {
        "location": "Biomedical Sensor Telemetry Panel",
        "verification": "Inspect biosensor electrode contacts and verify telemetry stream continuity.",
        "subsystem_lead": "CREW_MEDICAL_OFFICER"
    }
}


# =============================================================================
# COCKPIT ACTION & HUD CONTRACT DATACLASSES
# =============================================================================

@dataclass(frozen=True)
class SequencedActionStep:
    """A prioritized, actionable countermeasure step with physical flight location."""
    step_number: int
    action_id: str
    protocol: str
    priority: int
    time_to_execute_sec: int
    equipment_location: str
    verification_step: str
    subsystem_lead: str
    is_critical_path: bool


@dataclass(frozen=True)
class HUDAlertBanner:
    """High-visibility 3-Second visual and acoustic cockpit alert configuration."""
    alert_level: str  # "RED_CRITICAL", "AMBER_WARNING", "GREEN_NOMINAL"
    hud_banner_color: str  # Hex color string: Red="#FF1E27", Amber="#FFB800", Green="#00E676"
    hud_contrast_text_color: str
    audio_tone_frequency_hz: int
    audio_pulse_pattern: str  # "URGENT_PULSED_ALARM", "INTERMITTENT_CAUTION", "SILENT"
    flash_rate_hz: float
    tactile_vibration_alert: bool
    priority_code: int


@dataclass(frozen=True)
class CockpitActionPayload:
    """Complete 3-Second Astronaut HUD Dispatch Payload."""
    decision_id: str
    timestamp_utc: str
    triage_state: str
    clinical_title: str
    hud_banner: HUDAlertBanner
    three_second_executive_summary: str
    action_deck: List[SequencedActionStep]
    total_execution_window_sec: int
    biomarker_context_lead: str
    is_cmo_override_active: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


# =============================================================================
# COCKPIT COUNTERMEASURE DISPATCHER ENGINE
# =============================================================================

class CockpitCountermeasureDispatcher:
    """
    DO-178C Level C Cockpit Protocol & Countermeasure Dispatcher.
    Transforms raw TriageDecisionPackets into life-critical, unambiguous
    flight deck action sequences under the strict 3-Second Astronaut Rule:
    1. Generates instant visual, acoustic, and tactile alert configurations.
    2. Sequences actionable countermeasures sorted by priority and execution deadline.
    3. Links each action to physical Orion hardware lockers and verification steps.
    4. Synthesizes a high-contrast 3-Second Executive Summary for non-physician crew.
    """

    def __init__(self, equipment_registry: Optional[Dict[str, Dict[str, str]]] = None):
        if equipment_registry is None:
            self.registry = EQUIPMENT_LOCKER_REGISTRY
        else:
            self.registry = equipment_registry

    # -------------------------------------------------------------------------
    # 1. HUD VISUAL & ACOUSTIC ALERT CONFIGURATION
    # -------------------------------------------------------------------------
    def generate_hud_alert_banner(self, triage_state: str) -> HUDAlertBanner:
        """
        Synthesizes visual and audio alert parameters based on triage severity.
        Standards conform to NASA Human Integration Design Handbook (HIDH).
        """
        state_upper = triage_state.upper()

        if state_upper == "RED":
            return HUDAlertBanner(
                alert_level="RED_CRITICAL",
                hud_banner_color="#FF1E27",  # NASA High-Visibility Red
                hud_contrast_text_color="#FFFFFF",
                audio_tone_frequency_hz=1200,  # 1.2 kHz Urgent Alarm Klaxon
                audio_pulse_pattern="URGENT_PULSED_ALARM",
                flash_rate_hz=2.0,  # 2 Hz Flashing Alert
                tactile_vibration_alert=True,
                priority_code=1
            )
        elif state_upper == "AMBER":
            return HUDAlertBanner(
                alert_level="AMBER_WARNING",
                hud_banner_color="#FFB800",  # NASA Amber Warning Yellow
                hud_contrast_text_color="#000000",
                audio_tone_frequency_hz=600,   # 600 Hz Caution Chime
                audio_pulse_pattern="INTERMITTENT_CAUTION",
                flash_rate_hz=1.0,  # 1 Hz Pulsing
                tactile_vibration_alert=False,
                priority_code=2
            )
        elif state_upper == "GREEN":
            return HUDAlertBanner(
                alert_level="GREEN_NOMINAL",
                hud_banner_color="#00E676",  # NASA Nominal Green
                hud_contrast_text_color="#000000",
                audio_tone_frequency_hz=0,     # Silent
                audio_pulse_pattern="SILENT",
                flash_rate_hz=0.0,
                tactile_vibration_alert=False,
                priority_code=3
            )
        else:
            # Fallback cautionary alert
            return HUDAlertBanner(
                alert_level="AMBER_WARNING",
                hud_banner_color="#FF9100",
                hud_contrast_text_color="#000000",
                audio_tone_frequency_hz=600,
                audio_pulse_pattern="INTERMITTENT_CAUTION",
                flash_rate_hz=1.0,
                tactile_vibration_alert=False,
                priority_code=2
            )

    # -------------------------------------------------------------------------
    # 2. STEP-BY-STEP ACTION CHECKLIST SEQUENCING
    # -------------------------------------------------------------------------
    def build_sequenced_action_deck(
        self,
        raw_countermeasures: List[Dict[str, Any]],
        triage_state: str
    ) -> List[SequencedActionStep]:
        """
        Sequences and cross-references countermeasure items with the spacecraft
        equipment locker registry, sorting by execution urgency.
        """
        if not raw_countermeasures:
            # Provide standard baseline action if none provided
            raw_countermeasures = [{
                "action_id": "ACT_GRN_001_MAINTAIN_TIMELINE",
                "protocol": "Maintain nominal flight timeline and standard monitoring.",
                "priority": 1,
                "time_to_execute_sec": 0
            }]

        # Sort by priority ascending (1 is highest), then time_to_execute_sec ascending
        sorted_raw = sorted(
            raw_countermeasures,
            key=lambda x: (x.get("priority", 99), x.get("time_to_execute_sec", 999))
        )

        action_steps: List[SequencedActionStep] = []
        is_red = triage_state.upper() == "RED"

        for idx, item in enumerate(sorted_raw, start=1):
            act_id = item.get("action_id", "ACT_UNKNOWN")
            protocol = item.get("protocol", "Execute medical protocol.")
            priority = item.get("priority", 1)
            exec_sec = item.get("time_to_execute_sec", 60)

            # Retrieve equipment locker metadata
            meta = self.registry.get(act_id, {
                "location": "Main Flight Deck Medical Locker",
                "verification": "Confirm protocol completion on cockpit terminal.",
                "subsystem_lead": "CREW_MEDICAL_OFFICER"
            })

            # Critical path flag (first priority item in RED state is critical path)
            is_critical = bool(is_red and idx == 1)

            step = SequencedActionStep(
                step_number=idx,
                action_id=act_id,
                protocol=protocol,
                priority=priority,
                time_to_execute_sec=exec_sec,
                equipment_location=meta["location"],
                verification_step=meta["verification"],
                subsystem_lead=meta["subsystem_lead"],
                is_critical_path=is_critical
            )
            action_steps.append(step)

        return action_steps

    # -------------------------------------------------------------------------
    # 3. 3-SECOND EXECUTIVE SUMMARY SYNTHESIS
    # -------------------------------------------------------------------------
    def format_3_second_executive_summary(
        self,
        packet: TriageDecisionPacket,
        top_action_protocol: str
    ) -> str:
        """
        Generates an ultra-crisp, high-contrast natural language sentence
        designed for astronaut comprehension under 3 seconds:
        [STATE LEVEL]: [PRIMARY PHYSIOLOGICAL PROBLEM] -> ACTION: [IMMEDIATE PHYSICAL TASK]
        """
        state = packet.triage_state.upper()

        if state == "RED":
            prefix = "CRITICAL RED EMERGENCY"
        elif state == "AMBER":
            prefix = "CAUTION AMBER WARNING"
        else:
            prefix = "NOMINAL GREEN EQUILIBRIUM"

        summary = f"{prefix}: {packet.clinical_title} | IMMEDIATE ACTION (T-0): {top_action_protocol}"
        return summary

    # -------------------------------------------------------------------------
    # 4. MASTER DISPATCH METHOD
    # -------------------------------------------------------------------------
    def dispatch_cockpit_payload(
        self,
        packet: TriageDecisionPacket
    ) -> CockpitActionPayload:
        """
        Master factory producing the flight-ready CockpitActionPayload from
        a TriageDecisionPacket.
        """
        hud_banner = self.generate_hud_alert_banner(packet.triage_state)
        action_deck = self.build_sequenced_action_deck(
            raw_countermeasures=packet.actionable_countermeasures,
            triage_state=packet.triage_state
        )

        top_protocol = action_deck[0].protocol if action_deck else "Maintain baseline timeline."
        exec_summary = self.format_3_second_executive_summary(packet, top_protocol)

        total_exec_window = max([step.time_to_execute_sec for step in action_deck]) if action_deck else 0

        # Identify lead biomarker from Stage 4 urgency attribution if available
        lead_biomarker = "OVERALL_PHYSIOLOGICAL_PROFILE"
        if packet.biomarker_urgency_attribution:
            sorted_biomarkers = sorted(
                packet.biomarker_urgency_attribution.items(),
                key=lambda x: x[1],
                reverse=True
            )
            if sorted_biomarkers:
                lead_biomarker = sorted_biomarkers[0][0]

        return CockpitActionPayload(
            decision_id=packet.decision_id,
            timestamp_utc=packet.timestamp_utc,
            triage_state=packet.triage_state,
            clinical_title=packet.clinical_title,
            hud_banner=hud_banner,
            three_second_executive_summary=exec_summary,
            action_deck=action_deck,
            total_execution_window_sec=total_exec_window,
            biomarker_context_lead=lead_biomarker,
            is_cmo_override_active=packet.cmo_override.get("is_active", False)
        )
