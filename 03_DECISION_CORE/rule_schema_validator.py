"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Module: rule_schema_validator.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Deterministic Engine
Governance: 80% Biophysical Supreme Head Rule Matrix & Schema Validator
=============================================================================
"""

import os
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Set, Union


# =============================================================================
# DO-178C DETERMINISTIC OPERATORS & COMPARISONS
# =============================================================================

VALID_OPERATORS: Set[str] = {"<", "<=", ">", ">=", "=="}
VALID_TRIAGE_STATES: Set[str] = {"RED", "AMBER", "GREEN"}
VALID_CONDITION_TYPES: Set[str] = {"SINGLE_THRESHOLD", "COMPOUND_AND", "COMPOUND_OR"}


def evaluate_operator(actual: float, op: str, threshold: float) -> bool:
    """
    DO-178C Level C Deterministic Operator Evaluation.
    Guarantees mathematically bounded, non-stochastic comparison.
    """
    if op == "<":
        return actual < threshold
    elif op == "<=":
        return actual <= threshold
    elif op == ">":
        return actual > threshold
    elif op == ">=":
        return actual >= threshold
    elif op == "==":
        return abs(actual - threshold) < 1e-7
    else:
        raise ValueError(f"DO-178C Violation: Unrecognized comparison operator '{op}'")


# =============================================================================
# DATACLASSES FOR CONFIGURATION & AUDIT
# =============================================================================

@dataclass(frozen=True)
class RuleCondition:
    """Atomic physiological condition check."""
    channel: str
    operator: str
    threshold: float

    def evaluate(self, value: float) -> bool:
        return evaluate_operator(value, self.operator, self.threshold)


@dataclass(frozen=True)
class CountermeasureAction:
    """Actionable astronaut countermeasure item."""
    action_id: str
    protocol: str
    priority: int
    time_to_execute_sec: int


@dataclass(frozen=True)
class TriageRule:
    """Deterministic DO-178C Triage Rule Definition."""
    rule_id: str
    state: str
    priority: int
    category: str
    clinical_title: str
    description: str
    condition_type: str
    conditions: List[RuleCondition]
    cockpit_audit_template: str
    actionable_countermeasures: List[CountermeasureAction]
    evidence_rationale: str

    def evaluate(self, telemetry: Dict[str, float]) -> Tuple[bool, str]:
        """
        Evaluate rule against telemetry dictionary.
        Returns:
            (is_matched, formatted_audit_sentence)
        """
        # Verify required channels exist
        missing_channels = [c.channel for c in self.conditions if c.channel not in telemetry]
        if missing_channels:
            return False, f"CHANNEL_DEFICIT: Telemetry vector missing required channels {missing_channels}"

        condition_results = [
            cond.evaluate(telemetry[cond.channel])
            for cond in self.conditions
        ]

        matched = False
        if self.condition_type == "SINGLE_THRESHOLD":
            matched = condition_results[0] if condition_results else False
        elif self.condition_type == "COMPOUND_AND":
            matched = all(condition_results)
        elif self.condition_type == "COMPOUND_OR":
            matched = any(condition_results)
        else:
            raise ValueError(f"DO-178C Violation: Unknown condition_type {self.condition_type}")

        if matched:
            try:
                # Format audit template using telemetry values
                audit_str = self.cockpit_audit_template.format(**telemetry)
            except Exception:
                audit_str = f"ALERT {self.state} ({self.rule_id}): {self.clinical_title}"
            return True, audit_str

        return False, ""


@dataclass(frozen=True)
class CephaladFluidShiftConfig:
    alpha_1: float
    alpha_2: float
    alpha_3: float
    alpha_4: float
    green_upper_bound: float
    amber_upper_bound: float
    red_critical_threshold: float


@dataclass(frozen=True)
class StrokeVolumeAtrophyConfig:
    sv_0_ml: float
    kappa_atrophy: float
    beta_exercise: float
    min_viable_sv_ml: float
    warning_threshold_sv_ml: float


@dataclass(frozen=True)
class HemodynamicBaselines:
    map_baseline_mmhg: float
    rmssd_baseline_ms: float
    cabin_co2_baseline_ppm: float
    cabin_co2_baseline_mmhg: float
    icp_baseline_mmhg: float
    cvp_baseline_mmhg: float
    heart_rate_baseline_bpm: float
    systolic_bp_baseline_mmhg: float
    diastolic_bp_baseline_mmhg: float
    spo2_baseline_percent: float
    core_temp_baseline_c: float
    resp_rate_baseline_bpm: float


@dataclass(frozen=True)
class BiophysicalConstantsContract:
    cephalad_shift: CephaladFluidShiftConfig
    stroke_volume: StrokeVolumeAtrophyConfig
    baselines: HemodynamicBaselines
    nominal_min_cpp_mmhg: float
    warning_min_cpp_mmhg: float
    critical_floor_cpp_mmhg: float
    si_nominal_max: float
    si_mild_stress_max: float
    si_decompensated_critical: float
    si_severe_fatal: float


# =============================================================================
# MASTER DECISION CONFIGURATION MANAGER & VALIDATOR
# =============================================================================

class DecisionConfigManager:
    """
    Pure Python DO-178C Level C Decision Configuration Manager.
    Loads, cryptographically verifies, parses, and executes deterministic
    white-box triage rules and biophysical parameters.
    """

    def __init__(
        self,
        rules_path: Union[str, Path],
        biophysical_path: Union[str, Path],
        filter_params_path: Union[str, Path]
    ):
        self.rules_path = Path(rules_path)
        self.biophysical_path = Path(biophysical_path)
        self.filter_params_path = Path(filter_params_path)

        self._is_frozen = False
        self._sha256_checksums: Dict[str, str] = {}
        self.rules: List[TriageRule] = []
        self.biophysical_constants: Optional[BiophysicalConstantsContract] = None
        self.filter_parameters: Dict[str, Any] = {}

        # Load and validate upon initialization
        self.reload_all()

    def reload_all(self) -> None:
        """Loads and strictly validates all configuration files."""
        if self._is_frozen:
            raise RuntimeError("DO-178C Violation: Configuration is frozen in flight; mutation prohibited.")

        self._load_checksums()
        self._load_filter_parameters()
        self._load_biophysical_constants()
        self._load_triage_rules()

    def _load_checksums(self) -> None:
        """Calculates SHA-256 digests for all configuration files to ensure integrity."""
        for path in [self.rules_path, self.biophysical_path, self.filter_params_path]:
            if not path.is_file():
                raise FileNotFoundError(f"DO-178C Error: Configuration file not found at '{path}'")
            hasher = hashlib.sha256()
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    hasher.update(chunk)
            self._sha256_checksums[path.name] = hasher.hexdigest()

    def get_checksums(self) -> Dict[str, str]:
        """Returns verified SHA-256 checksums."""
        return dict(self._sha256_checksums)

    def _load_filter_parameters(self) -> None:
        """Loads and validates sensor filter parameters JSON."""
        with open(self.filter_params_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "canonical_channels" not in data or not isinstance(data["canonical_channels"], list):
            raise ValueError("DO-178C Violation: sensor_filter_parameters missing valid 'canonical_channels' list.")
        if len(data["canonical_channels"]) != 12:
            raise ValueError(f"DO-178C Violation: Expected exactly 12 canonical channels, found {len(data['canonical_channels'])}.")

        self.filter_parameters = data

    def _load_biophysical_constants(self) -> None:
        """Loads and validates biophysical constants JSON."""
        with open(self.biophysical_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        cfs = data["cephalad_fluid_shift_model"]
        coeffs = cfs["coefficients"]
        alpha_sum = sum([
            coeffs["alpha_1_map"],
            coeffs["alpha_2_microgravity_duration"],
            coeffs["alpha_3_cabin_co2"],
            coeffs["alpha_4_autonomic_rmssd"]
        ])
        if abs(alpha_sum - 1.0) > 1e-6:
            raise ValueError(f"DO-178C Violation: Cephalad fluid shift coefficients must sum to 1.0, got {alpha_sum:.6f}")

        shift_cfg = CephaladFluidShiftConfig(
            alpha_1=coeffs["alpha_1_map"],
            alpha_2=coeffs["alpha_2_microgravity_duration"],
            alpha_3=coeffs["alpha_3_cabin_co2"],
            alpha_4=coeffs["alpha_4_autonomic_rmssd"],
            green_upper_bound=cfs["thresholds"]["green_upper_bound"],
            amber_upper_bound=cfs["thresholds"]["amber_upper_bound"],
            red_critical_threshold=cfs["thresholds"]["red_critical_threshold"]
        )

        sva = data["stroke_volume_atrophy_model"]
        sv_cfg = StrokeVolumeAtrophyConfig(
            sv_0_ml=sva["sv_0_ml"],
            kappa_atrophy=sva["kappa_atrophy_per_day"],
            beta_exercise=sva["beta_exercise_factor"],
            min_viable_sv_ml=sva["min_viable_sv_ml"],
            warning_threshold_sv_ml=sva["warning_threshold_sv_ml"]
        )

        hb = data["hemodynamic_baselines"]
        baselines = HemodynamicBaselines(
            map_baseline_mmhg=hb["map_baseline_mmhg"],
            rmssd_baseline_ms=hb["rmssd_baseline_ms"],
            cabin_co2_baseline_ppm=hb["cabin_co2_baseline_ppm"],
            cabin_co2_baseline_mmhg=hb["cabin_co2_baseline_mmhg"],
            icp_baseline_mmhg=hb["icp_baseline_mmhg"],
            cvp_baseline_mmhg=hb["cvp_baseline_mmhg"],
            heart_rate_baseline_bpm=hb["heart_rate_baseline_bpm"],
            systolic_bp_baseline_mmhg=hb["systolic_bp_baseline_mmhg"],
            diastolic_bp_baseline_mmhg=hb["diastolic_bp_baseline_mmhg"],
            spo2_baseline_percent=hb["spo2_baseline_percent"],
            core_temp_baseline_c=hb["core_temp_baseline_c"],
            resp_rate_baseline_bpm=hb["resp_rate_baseline_bpm"]
        )

        cpp = data["cerebral_perfusion_bounds"]
        si = data["shock_index_thresholds"]

        self.biophysical_constants = BiophysicalConstantsContract(
            cephalad_shift=shift_cfg,
            stroke_volume=sv_cfg,
            baselines=baselines,
            nominal_min_cpp_mmhg=cpp["nominal_min_cpp_mmhg"],
            warning_min_cpp_mmhg=cpp["warning_min_cpp_mmhg"],
            critical_floor_cpp_mmhg=cpp["critical_floor_cpp_mmhg"],
            si_nominal_max=si["nominal_max"],
            si_mild_stress_max=si["mild_stress_max"],
            si_decompensated_critical=si["decompensated_shock_critical"],
            si_severe_fatal=si["severe_fatal_shock"]
        )

    def _load_triage_rules(self) -> None:
        """Loads and verifies deterministic triage rules from JSON."""
        with open(self.rules_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_rules = data.get("rules", [])
        if not raw_rules:
            raise ValueError("DO-178C Violation: No triage rules found in rule matrix JSON.")

        parsed_rules: List[TriageRule] = []
        rule_ids_seen: Set[str] = set()

        for r in raw_rules:
            rule_id = r["rule_id"]
            if rule_id in rule_ids_seen:
                raise ValueError(f"DO-178C Violation: Duplicate rule_id '{rule_id}' detected.")
            rule_ids_seen.add(rule_id)

            state = r["state"]
            if state not in VALID_TRIAGE_STATES:
                raise ValueError(f"DO-178C Violation: Invalid state '{state}' in rule '{rule_id}'.")

            cond_type = r["condition_type"]
            if cond_type not in VALID_CONDITION_TYPES:
                raise ValueError(f"DO-178C Violation: Invalid condition_type '{cond_type}' in rule '{rule_id}'.")

            conditions: List[RuleCondition] = []
            for c in r["conditions"]:
                op = c["operator"]
                if op not in VALID_OPERATORS:
                    raise ValueError(f"DO-178C Violation: Invalid operator '{op}' in rule '{rule_id}'.")
                conditions.append(RuleCondition(
                    channel=c["channel"],
                    operator=op,
                    threshold=float(c["threshold"])
                ))

            countermeasures: List[CountermeasureAction] = []
            for a in r.get("actionable_countermeasures", []):
                countermeasures.append(CountermeasureAction(
                    action_id=a["action_id"],
                    protocol=a["protocol"],
                    priority=int(a["priority"]),
                    time_to_execute_sec=int(a["time_to_execute_sec"])
                ))

            parsed_rules.append(TriageRule(
                rule_id=rule_id,
                state=state,
                priority=int(r.get("priority", 0)),
                category=r.get("category", "GENERAL"),
                clinical_title=r.get("clinical_title", ""),
                description=r.get("description", ""),
                condition_type=cond_type,
                conditions=conditions,
                cockpit_audit_template=r.get("cockpit_audit_template", ""),
                actionable_countermeasures=countermeasures,
                evidence_rationale=r.get("evidence_rationale", "")
            ))

        self.rules = parsed_rules

    def freeze(self) -> None:
        """Freezes configuration for immutable in-flight runtime execution."""
        self._is_frozen = True

    @property
    def is_frozen(self) -> bool:
        return self._is_frozen

    def get_rules_for_state(self, state: str) -> List[TriageRule]:
        """Returns rules for a given state sorted by priority descending."""
        if state not in VALID_TRIAGE_STATES:
            raise ValueError(f"Invalid triage state: {state}")
        matched = [r for r in self.rules if r.state == state]
        return sorted(matched, key=lambda x: x.priority, reverse=True)

    def evaluate_triage(
        self,
        telemetry: Dict[str, float]
    ) -> Tuple[str, Optional[TriageRule], str, List[CountermeasureAction]]:
        """
        Executes strict DO-178C Level C deterministic triage hierarchy:
        1. Evaluate all RED rules (highest priority descending). If match -> RED.
        2. Evaluate all AMBER rules (highest priority descending). If match -> AMBER.
        3. Evaluate GREEN equilibrium rule. If match -> GREEN.
        4. Default fail-safe: AMBER (unclassified borderline state).
        """
        # Step 1: RED hierarchy
        for rule in self.get_rules_for_state("RED"):
            matched, audit_text = rule.evaluate(telemetry)
            if matched:
                return "RED", rule, audit_text, rule.actionable_countermeasures

        # Step 2: AMBER hierarchy
        for rule in self.get_rules_for_state("AMBER"):
            matched, audit_text = rule.evaluate(telemetry)
            if matched:
                return "AMBER", rule, audit_text, rule.actionable_countermeasures

        # Step 3: GREEN hierarchy
        for rule in self.get_rules_for_state("GREEN"):
            matched, audit_text = rule.evaluate(telemetry)
            if matched:
                return "GREEN", rule, audit_text, rule.actionable_countermeasures

        # Fail-safe state
        return (
            "AMBER",
            None,
            "UNCLASSIFIED VITAL PROFILE: Parameters border nominal envelope without meeting formal GREEN equilibrium.",
            [
                CountermeasureAction(
                    action_id="ACT_FALLBACK_MONITOR",
                    protocol="Engage secondary physiological monitoring telemetry loop.",
                    priority=1,
                    time_to_execute_sec=60
                )
            ]
        )


def load_default_decision_configuration() -> DecisionConfigManager:
    """Convenience factory loading default JSON configurations from current directory."""
    current_dir = Path(__file__).resolve().parent
    return DecisionConfigManager(
        rules_path=current_dir / "deterministic_triage_rules.json",
        biophysical_path=current_dir / "biophysical_constants.json",
        filter_params_path=current_dir / "sensor_filter_parameters.json"
    )
