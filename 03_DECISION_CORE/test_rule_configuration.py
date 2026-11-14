"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Verification Suite: test_rule_configuration.py (Phase 1 IV&V)
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A
Governance: Deterministic Rule Matrix & Biophysical Parameters Verification
=============================================================================
"""

import os
import sys
import json
import time
import pytest
from pathlib import Path
from typing import Dict, Any

# Ensure 03_DECISION_CORE is on sys.path
decision_path = Path(__file__).resolve().parent
if str(decision_path) not in sys.path:
    sys.path.insert(0, str(decision_path))

from rule_schema_validator import (
    RuleCondition,
    CountermeasureAction,
    TriageRule,
    CephaladFluidShiftConfig,
    StrokeVolumeAtrophyConfig,
    HemodynamicBaselines,
    BiophysicalConstantsContract,
    DecisionConfigManager,
    load_default_decision_configuration,
    evaluate_operator,
    VALID_OPERATORS,
    VALID_TRIAGE_STATES,
    VALID_CONDITION_TYPES,
)


@pytest.fixture
def decision_dir() -> Path:
    return Path(__file__).resolve().parent


@pytest.fixture
def config_mgr() -> DecisionConfigManager:
    return load_default_decision_configuration()


@pytest.fixture
def nominal_telemetry() -> Dict[str, float]:
    """Nominal 12D telemetry plus derived biophysical metrics."""
    return {
        "heart_rate_bpm": 72.0,
        "systolic_bp_mmhg": 120.0,
        "diastolic_bp_mmhg": 80.0,
        "spo2_percent": 98.5,
        "core_temp_c": 37.0,
        "resp_rate_bpm": 14.0,
        "etco2_mmhg": 38.0,
        "icp_est_mmhg": 10.0,
        "cvp_mmhg": 5.0,
        "co2_cabin_ppm": 3800.0,
        "cabin_pressure_psi": 14.7,
        "ambient_temp_c": 22.0,
        # Derived biophysical metrics
        "map_mmhg": 93.33,
        "pulse_pressure_mmhg": 40.0,
        "shock_index": 0.60,
        "icp_gradient_index": 1.15,
        "stroke_volume_ml": 88.0,
        "sleep_debt_hours": 4.0,
    }


# =============================================================================
# GROUP 1: FILE EXISTENCE & INTEGRITY CHECKS (TESTS 01-05)
# =============================================================================

def test_01_configuration_files_exist(decision_dir: Path):
    """Verify that all three core JSON configuration files exist."""
    assert (decision_dir / "deterministic_triage_rules.json").is_file()
    assert (decision_dir / "biophysical_constants.json").is_file()
    assert (decision_dir / "sensor_filter_parameters.json").is_file()


def test_02_sha256_cryptographic_integrity(config_mgr: DecisionConfigManager):
    """Verify that SHA-256 hashes are computed for all configuration artifacts."""
    checksums = config_mgr.get_checksums()
    assert len(checksums) == 3
    for filename in ["deterministic_triage_rules.json", "biophysical_constants.json", "sensor_filter_parameters.json"]:
        assert filename in checksums
        assert len(checksums[filename]) == 64  # Valid SHA-256 hex string


def test_03_sensor_filter_canonical_channels(config_mgr: DecisionConfigManager):
    """Verify exact 12 canonical channels exist in sensor_filter_parameters."""
    channels = config_mgr.filter_parameters["canonical_channels"]
    assert len(channels) == 12
    expected = [
        "heart_rate_bpm", "systolic_bp_mmhg", "diastolic_bp_mmhg",
        "spo2_percent", "core_temp_c", "resp_rate_bpm",
        "etco2_mmhg", "icp_est_mmhg", "cvp_mmhg",
        "co2_cabin_ppm", "cabin_pressure_psi", "ambient_temp_c"
    ]
    assert channels == expected


def test_04_channel_specifications_validity(config_mgr: DecisionConfigManager):
    """Verify each channel has viable min, max, baseline, and gradient limits."""
    specs = config_mgr.filter_parameters["channel_specifications"]
    for ch, data in specs.items():
        assert data["viable_min"] < data["viable_max"], f"Channel {ch} invalid bounds"
        assert data["viable_min"] <= data["baseline_mean"] <= data["viable_max"]
        assert data["max_gradient_per_sec"] > 0


def test_05_signal_quality_parameters(config_mgr: DecisionConfigManager):
    """Verify signal quality bounds adhere to DO-178C standards."""
    sqp = config_mgr.filter_parameters["signal_quality_parameters"]
    assert sqp["nominal_sampling_rate_hz"] == 1.0
    assert sqp["min_sqi_acceptable"] == 0.70
    assert sqp["decoupling_variance_threshold"] == 1e-4


# =============================================================================
# GROUP 2: BIOPHYSICAL CONSTANTS CONSTRAINTS (TESTS 06-10)
# =============================================================================

def test_06_cephalad_fluid_shift_alpha_normalization(config_mgr: DecisionConfigManager):
    """Verify that cephalad fluid shift coefficients strictly sum to 1.0."""
    cfs = config_mgr.biophysical_constants.cephalad_shift
    total_alpha = cfs.alpha_1 + cfs.alpha_2 + cfs.alpha_3 + cfs.alpha_4
    assert abs(total_alpha - 1.0) < 1e-6
    assert cfs.green_upper_bound < cfs.amber_upper_bound
    assert cfs.amber_upper_bound == cfs.red_critical_threshold


def test_07_stroke_volume_atrophy_parameters(config_mgr: DecisionConfigManager):
    """Verify stroke volume decay parameters and minimum thresholds."""
    sva = config_mgr.biophysical_constants.stroke_volume
    assert sva.sv_0_ml > 0
    assert sva.kappa_atrophy > 0
    assert sva.beta_exercise >= 0
    assert sva.min_viable_sv_ml < sva.warning_threshold_sv_ml < sva.sv_0_ml


def test_08_hemodynamic_baselines_completeness(config_mgr: DecisionConfigManager):
    """Verify all hemodynamic baselines have plausible values."""
    base = config_mgr.biophysical_constants.baselines
    assert base.map_baseline_mmhg > 0
    assert base.heart_rate_baseline_bpm > 0
    assert base.systolic_bp_baseline_mmhg > base.diastolic_bp_baseline_mmhg
    assert base.spo2_baseline_percent > 90.0


def test_09_cerebral_perfusion_bounds(config_mgr: DecisionConfigManager):
    """Verify cerebral perfusion pressure safety limits."""
    bio = config_mgr.biophysical_constants
    assert bio.critical_floor_cpp_mmhg < bio.warning_min_cpp_mmhg < bio.nominal_min_cpp_mmhg


def test_10_shock_index_threshold_hierarchy(config_mgr: DecisionConfigManager):
    """Verify shock index progression: nominal < mild < decompensated < fatal."""
    bio = config_mgr.biophysical_constants
    assert bio.si_nominal_max < bio.si_mild_stress_max < bio.si_decompensated_critical < bio.si_severe_fatal


# =============================================================================
# GROUP 3: TRIAGE RULE MATRIX & OPERATOR RIGOR (TESTS 11-15)
# =============================================================================

def test_11_all_rule_ids_unique(config_mgr: DecisionConfigManager):
    """Verify no duplicate rule IDs exist in rule matrix."""
    rule_ids = [r.rule_id for r in config_mgr.rules]
    assert len(rule_ids) == len(set(rule_ids))
    assert len(rule_ids) >= 10


def test_12_operator_evaluation_logic():
    """Verify evaluate_operator behaves deterministically across all operators."""
    assert evaluate_operator(5.0, "<", 10.0) is True
    assert evaluate_operator(10.0, "<", 5.0) is False
    assert evaluate_operator(10.0, "<=", 10.0) is True
    assert evaluate_operator(15.0, ">", 10.0) is True
    assert evaluate_operator(10.0, ">=", 10.0) is True
    assert evaluate_operator(10.0, "==", 10.0) is True

    with pytest.raises(ValueError, match="Unrecognized comparison operator"):
        evaluate_operator(10.0, "!=", 10.0)


def test_13_rule_priority_sorting(config_mgr: DecisionConfigManager):
    """Verify rules are sorted by priority descending within each state."""
    for state in ["RED", "AMBER", "GREEN"]:
        rules = config_mgr.get_rules_for_state(state)
        priorities = [r.priority for r in rules]
        assert priorities == sorted(priorities, reverse=True)


def test_14_single_condition_evaluation():
    """Verify single threshold rule evaluation."""
    rule = TriageRule(
        rule_id="RULE_TEST_SINGLE",
        state="AMBER",
        priority=50,
        category="TEST",
        clinical_title="Test Single",
        description="Single threshold test",
        condition_type="SINGLE_THRESHOLD",
        conditions=[RuleCondition(channel="heart_rate_bpm", operator=">", threshold=100.0)],
        cockpit_audit_template="HR high {heart_rate_bpm}",
        actionable_countermeasures=[],
        evidence_rationale="N/A"
    )
    matched, audit = rule.evaluate({"heart_rate_bpm": 105.0})
    assert matched is True
    assert "HR high 105.0" in audit

    matched, _ = rule.evaluate({"heart_rate_bpm": 95.0})
    assert matched is False


def test_15_compound_and_evaluation():
    """Verify COMPOUND_AND requires all conditions to be satisfied."""
    rule = TriageRule(
        rule_id="RULE_TEST_AND",
        state="RED",
        priority=90,
        category="TEST",
        clinical_title="Test AND",
        description="Compound AND test",
        condition_type="COMPOUND_AND",
        conditions=[
            RuleCondition(channel="spo2_percent", operator="<", threshold=88.0),
            RuleCondition(channel="heart_rate_bpm", operator=">", threshold=120.0)
        ],
        cockpit_audit_template="Hypoxic Tachycardia: SpO2={spo2_percent}, HR={heart_rate_bpm}",
        actionable_countermeasures=[],
        evidence_rationale="N/A"
    )
    # Only one matches -> should be False
    assert rule.evaluate({"spo2_percent": 85.0, "heart_rate_bpm": 100.0})[0] is False
    assert rule.evaluate({"spo2_percent": 95.0, "heart_rate_bpm": 130.0})[0] is False
    # Both match -> should be True
    matched, audit = rule.evaluate({"spo2_percent": 85.0, "heart_rate_bpm": 130.0})
    assert matched is True
    assert "SpO2=85.0, HR=130.0" in audit


# =============================================================================
# GROUP 4: CLINICAL TRIAGE SCENARIOS (TESTS 16-24)
# =============================================================================

def test_16_compound_or_evaluation():
    """Verify COMPOUND_OR triggers if any condition is satisfied."""
    rule = TriageRule(
        rule_id="RULE_TEST_OR",
        state="RED",
        priority=90,
        category="TEST",
        clinical_title="Test OR",
        description="Compound OR test",
        condition_type="COMPOUND_OR",
        conditions=[
            RuleCondition(channel="systolic_bp_mmhg", operator=">=", threshold=165.0),
            RuleCondition(channel="map_mmhg", operator=">=", threshold=125.0)
        ],
        cockpit_audit_template="Hypertension",
        actionable_countermeasures=[],
        evidence_rationale="N/A"
    )
    assert rule.evaluate({"systolic_bp_mmhg": 170.0, "map_mmhg": 110.0})[0] is True
    assert rule.evaluate({"systolic_bp_mmhg": 150.0, "map_mmhg": 130.0})[0] is True
    assert rule.evaluate({"systolic_bp_mmhg": 140.0, "map_mmhg": 100.0})[0] is False


def test_17_missing_telemetry_channel_defensive_rejection():
    """Verify that rule evaluation safely reports deficit if channel missing."""
    rule = TriageRule(
        rule_id="RULE_TEST_MISSING",
        state="RED",
        priority=50,
        category="TEST",
        clinical_title="Missing",
        description="",
        condition_type="SINGLE_THRESHOLD",
        conditions=[RuleCondition(channel="missing_vital_channel", operator=">", threshold=10.0)],
        cockpit_audit_template="",
        actionable_countermeasures=[],
        evidence_rationale=""
    )
    matched, audit = rule.evaluate({"heart_rate_bpm": 75.0})
    assert matched is False
    assert "CHANNEL_DEFICIT" in audit


def test_18_red_hypoxia_tachycardia_trigger(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify critical hypoxia + tachycardia triggers RED and returns rebreather countermeasure."""
    telemetry = dict(nominal_telemetry)
    telemetry["spo2_percent"] = 85.0
    telemetry["heart_rate_bpm"] = 135.0

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "RED"
    assert rule.rule_id == "RULE_RED_001_SEVERE_HYPOXIA_TACHYCARDIA"
    assert "SpO2 85.0%" in audit
    assert len(countermeasures) > 0
    assert any("O2" in c.protocol for c in countermeasures)


def test_19_red_cephalad_fluid_shift_surge(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify I_ICP >= 1.85 triggers RED and returns LBNP deployment countermeasure."""
    telemetry = dict(nominal_telemetry)
    telemetry["icp_gradient_index"] = 1.92

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "RED"
    assert rule.rule_id == "RULE_RED_002_CEPHALAD_ICP_SURGE"
    assert "I_ICP reached 1.92" in audit
    assert any("LBNP" in c.protocol for c in countermeasures)


def test_20_red_hypertensive_crisis_trigger(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify SBP >= 165 triggers RED hypertensive emergency."""
    telemetry = dict(nominal_telemetry)
    telemetry["systolic_bp_mmhg"] = 175.0

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "RED"
    assert rule.rule_id == "RULE_RED_003_HYPERTENSIVE_CRISIS"
    assert "175.0" in audit


def test_21_red_cabin_decompression_trigger(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify cabin pressure <= 10.5 psi triggers RED rapid decompression alert."""
    telemetry = dict(nominal_telemetry)
    telemetry["cabin_pressure_psi"] = 9.8

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "RED"
    assert rule.rule_id == "RULE_RED_005_RAPID_CABIN_DECOMPRESSION"
    assert any("OCSS" in c.protocol or "suit" in c.protocol for c in countermeasures)


def test_22_amber_elevated_cephalad_shift(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify I_ICP in [1.35, 1.85) triggers AMBER warning."""
    telemetry = dict(nominal_telemetry)
    telemetry["icp_gradient_index"] = 1.55

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "AMBER"
    assert rule.rule_id == "RULE_AMBER_001_ELEVATED_CEPHALAD_FLUID_SHIFT"
    assert "1.55" in audit


def test_23_amber_cabin_co2_hypercapnia(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify elevated cabin CO2 (>= 5000 ppm) triggers AMBER scrubber alert."""
    telemetry = dict(nominal_telemetry)
    telemetry["co2_cabin_ppm"] = 5500.0

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "AMBER"
    assert rule.rule_id == "RULE_AMBER_002_HYPERCAPNIC_CABIN_AIR"
    assert "5500" in audit
    assert any("scrubber" in c.protocol for c in countermeasures)


def test_24_amber_stroke_volume_deconditioning(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify stroke volume <= 65.0 mL triggers AMBER ARED countermeasure."""
    telemetry = dict(nominal_telemetry)
    telemetry["stroke_volume_ml"] = 62.0

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "AMBER"
    assert rule.rule_id == "RULE_AMBER_003_CARDIOVASCULAR_DECONDITIONING_STRAIN"
    assert any("ARED" in c.protocol for c in countermeasures)


# =============================================================================
# GROUP 5: GREEN EQUILIBRIUM & ARCHITECTURAL RIGOR (TESTS 25-31)
# =============================================================================

def test_25_amber_sleep_debt_fatigue(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify sleep debt >= 16.0 hours triggers AMBER rest countermeasure."""
    telemetry = dict(nominal_telemetry)
    telemetry["sleep_debt_hours"] = 18.5

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "AMBER"
    assert rule.rule_id == "RULE_AMBER_005_EXTREME_SLEEP_DEBT_FATIGUE"
    assert any("sleep" in c.protocol for c in countermeasures)


def test_26_green_nominal_equilibrium(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify all nominal parameters cleanly produce GREEN equilibrium state."""
    state, rule, audit, countermeasures = config_mgr.evaluate_triage(nominal_telemetry)
    assert state == "GREEN"
    assert rule.rule_id == "RULE_GREEN_001_PHYSIOLOGICAL_EQUILIBRIUM"
    assert "NOMINAL GREEN" in audit
    assert any("Maintain" in c.protocol for c in countermeasures)


def test_27_unclassified_fallback_to_amber(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify telemetry falling between bounds defaults safely to AMBER fallback."""
    telemetry = dict(nominal_telemetry)
    # Slightly sub-nominal SpO2 (94.0%) which fails GREEN (requires >= 95.0) but does not trip AMBER (<= 92.0)
    telemetry["spo2_percent"] = 94.0

    state, rule, audit, countermeasures = config_mgr.evaluate_triage(telemetry)
    assert state == "AMBER"
    assert "UNCLASSIFIED VITAL PROFILE" in audit
    assert len(countermeasures) > 0


def test_28_configuration_immutability_freeze(config_mgr: DecisionConfigManager):
    """Verify that freeze() prevents reloading or mutation during in-flight operations."""
    assert config_mgr.is_frozen is False
    config_mgr.freeze()
    assert config_mgr.is_frozen is True

    with pytest.raises(RuntimeError, match="Configuration is frozen in flight"):
        config_mgr.reload_all()


def test_29_missing_file_defensive_exception(decision_dir: Path):
    """Verify FileNotFoundError if configuration path does not exist."""
    with pytest.raises(FileNotFoundError):
        DecisionConfigManager(
            rules_path=decision_dir / "non_existent_rules.json",
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_30_duplicate_rule_id_defense(tmp_path: Path, decision_dir: Path):
    """Verify ValueError is raised if duplicate rule IDs are supplied."""
    bad_rules = {
        "rules": [
            {
                "rule_id": "RULE_DUP",
                "state": "RED",
                "condition_type": "SINGLE_THRESHOLD",
                "conditions": [{"channel": "heart_rate_bpm", "operator": ">", "threshold": 100.0}]
            },
            {
                "rule_id": "RULE_DUP",
                "state": "AMBER",
                "condition_type": "SINGLE_THRESHOLD",
                "conditions": [{"channel": "spo2_percent", "operator": "<", "threshold": 90.0}]
            }
        ]
    }
    dup_file = tmp_path / "dup_rules.json"
    with open(dup_file, "w") as f:
        json.dump(bad_rules, f)

    with pytest.raises(ValueError, match="Duplicate rule_id"):
        DecisionConfigManager(
            rules_path=dup_file,
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_31_triage_evaluation_latency_budget(config_mgr: DecisionConfigManager, nominal_telemetry: Dict[str, float]):
    """Verify complete triage evaluation executes well within 10.0 ms budget."""
    t0 = time.perf_counter()
    for _ in range(100):
        config_mgr.evaluate_triage(nominal_telemetry)
    dt_per_eval_ms = ((time.perf_counter() - t0) / 100.0) * 1000.0

    assert dt_per_eval_ms < 10.0, f"Evaluation latency {dt_per_eval_ms:.3f} ms exceeds 10 ms budget"


# =============================================================================
# GROUP 6: DO-178C LEVEL C 100% STATEMENT COVERAGE DEFENSIVE TESTS (TESTS 32-41)
# =============================================================================

def test_32_rule_evaluation_unknown_condition_type():
    """Verify ValueError when rule has unknown condition_type."""
    rule = TriageRule(
        rule_id="RULE_UNKNOWN_TYPE",
        state="AMBER",
        priority=10,
        category="TEST",
        clinical_title="Unknown Type",
        description="",
        condition_type="UNKNOWN_CONDITION_TYPE",
        conditions=[RuleCondition(channel="heart_rate_bpm", operator=">", threshold=100.0)],
        cockpit_audit_template="",
        actionable_countermeasures=[],
        evidence_rationale=""
    )
    with pytest.raises(ValueError, match="Unknown condition_type"):
        rule.evaluate({"heart_rate_bpm": 120.0})


def test_33_rule_audit_template_formatting_exception():
    """Verify fallback audit text when cockpit template formatting raises Exception."""
    rule = TriageRule(
        rule_id="RULE_BAD_TEMPLATE",
        state="AMBER",
        priority=10,
        category="TEST",
        clinical_title="Bad Template Title",
        description="",
        condition_type="SINGLE_THRESHOLD",
        conditions=[RuleCondition(channel="heart_rate_bpm", operator=">", threshold=100.0)],
        cockpit_audit_template="This will fail: {non_existent_field:.2f}",
        actionable_countermeasures=[],
        evidence_rationale=""
    )
    matched, audit = rule.evaluate({"heart_rate_bpm": 120.0})
    assert matched is True
    assert "ALERT AMBER (RULE_BAD_TEMPLATE): Bad Template Title" in audit


def test_34_filter_params_missing_canonical_channels(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when canonical_channels key is missing or not a list."""
    bad_filter = {"no_channels": []}
    f_path = tmp_path / "bad_filter1.json"
    with open(f_path, "w") as f:
        json.dump(bad_filter, f)

    with pytest.raises(ValueError, match="missing valid 'canonical_channels'"):
        DecisionConfigManager(
            rules_path=decision_dir / "deterministic_triage_rules.json",
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=f_path
        )


def test_35_filter_params_wrong_canonical_channel_count(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when canonical_channels count != 12."""
    bad_filter = {"canonical_channels": ["heart_rate_bpm", "spo2_percent"]}
    f_path = tmp_path / "bad_filter2.json"
    with open(f_path, "w") as f:
        json.dump(bad_filter, f)

    with pytest.raises(ValueError, match="Expected exactly 12 canonical channels"):
        DecisionConfigManager(
            rules_path=decision_dir / "deterministic_triage_rules.json",
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=f_path
        )


def test_36_biophysical_constants_non_normalized_alphas(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when cephalad shift coefficients do not sum to 1.0."""
    with open(decision_dir / "biophysical_constants.json", "r") as f:
        data = json.load(f)
    data["cephalad_fluid_shift_model"]["coefficients"]["alpha_1_map"] = 0.99  # sum > 1.0
    b_path = tmp_path / "bad_bio.json"
    with open(b_path, "w") as f:
        json.dump(data, f)

    with pytest.raises(ValueError, match="coefficients must sum to 1.0"):
        DecisionConfigManager(
            rules_path=decision_dir / "deterministic_triage_rules.json",
            biophysical_path=b_path,
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_37_empty_rules_matrix_defense(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when rule matrix contains an empty rules list."""
    bad_rules = {"rules": []}
    r_path = tmp_path / "empty_rules.json"
    with open(r_path, "w") as f:
        json.dump(bad_rules, f)

    with pytest.raises(ValueError, match="No triage rules found"):
        DecisionConfigManager(
            rules_path=r_path,
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_38_invalid_rule_state_defense(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when a rule defines an invalid triage state."""
    bad_rules = {
        "rules": [
            {
                "rule_id": "RULE_INVALID_STATE",
                "state": "PURPLE",
                "condition_type": "SINGLE_THRESHOLD",
                "conditions": [{"channel": "heart_rate_bpm", "operator": ">", "threshold": 100.0}]
            }
        ]
    }
    r_path = tmp_path / "invalid_state.json"
    with open(r_path, "w") as f:
        json.dump(bad_rules, f)

    with pytest.raises(ValueError, match="Invalid state 'PURPLE'"):
        DecisionConfigManager(
            rules_path=r_path,
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_39_invalid_rule_condition_type_defense(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when a rule defines an invalid condition_type in JSON."""
    bad_rules = {
        "rules": [
            {
                "rule_id": "RULE_INVALID_COND_TYPE",
                "state": "RED",
                "condition_type": "FUZZY_LOGIC",
                "conditions": [{"channel": "heart_rate_bpm", "operator": ">", "threshold": 100.0}]
            }
        ]
    }
    r_path = tmp_path / "invalid_cond.json"
    with open(r_path, "w") as f:
        json.dump(bad_rules, f)

    with pytest.raises(ValueError, match="Invalid condition_type 'FUZZY_LOGIC'"):
        DecisionConfigManager(
            rules_path=r_path,
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_40_invalid_rule_operator_defense(tmp_path: Path, decision_dir: Path):
    """Verify ValueError when a rule condition defines an invalid operator in JSON."""
    bad_rules = {
        "rules": [
            {
                "rule_id": "RULE_INVALID_OP",
                "state": "RED",
                "condition_type": "SINGLE_THRESHOLD",
                "conditions": [{"channel": "heart_rate_bpm", "operator": "~=", "threshold": 100.0}]
            }
        ]
    }
    r_path = tmp_path / "invalid_op.json"
    with open(r_path, "w") as f:
        json.dump(bad_rules, f)

    with pytest.raises(ValueError, match="Invalid operator '~='"):
        DecisionConfigManager(
            rules_path=r_path,
            biophysical_path=decision_dir / "biophysical_constants.json",
            filter_params_path=decision_dir / "sensor_filter_parameters.json"
        )


def test_41_get_rules_for_state_invalid_state(config_mgr: DecisionConfigManager):
    """Verify ValueError when requesting rules for invalid triage state."""
    with pytest.raises(ValueError, match="Invalid triage state"):
        config_mgr.get_rules_for_state("BLUE")

