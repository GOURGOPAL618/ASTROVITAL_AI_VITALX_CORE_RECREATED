"""
ASTROVITAL AI: VITALX CORE RECREATED V1
Test Suite: DO-178C Level C Verification for sanity_gate.py
Phase 1 Verification Tests (Physiological Boundary Enforcer)
File: 02_AI_CORE/02_tests/test_sanity_gate.py
"""

import sys
from pathlib import Path

# Permanent DO-178C path resolution: Add 02_AI_CORE/01_src directly to sys.path
SRC_DIR = Path(__file__).resolve().parent.parent / "01_src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import numpy as np
import pandas as pd
import pytest

from sanity_gate import (
    PhysiologicalBound,
    NASA_STD_3001_PHYSIOLOGICAL_BOUNDS,
    BoundaryAuditResult,
    PhysiologicalBoundaryEnforcer,
    GradientLimit,
    NASA_MAX_PHYSIOLOGICAL_GRADIENTS,
    GradientAuditResult,
    PhysiologicalGradientLimiter,
    CouplingViolation,
    CouplingAuditResult,
    PhysiologicalCouplingGuard,
    FallbackPolicy,
    APOLLO_ISS_MISSION_BASELINES,
    FallbackActionLog,
    SensorDecouplingFallbackEngine,
    SanityGatedPacket,
    SanityGateExporter,
)


class TestPhase1PhysiologicalBoundaryEnforcer:
    """
    DO-178C Level C Requirements-Based Test Suite for Phase 1.
    Tests boundary constants, custom envelopes, scalar audit, array auditing,
    violation classification, clamping, and batch DataFrame verification.
    """

    # --- Test 01: Default instantiation with standard bounds ---
    def test_01_default_instantiation(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        assert len(enforcer.bounds) == len(NASA_STD_3001_PHYSIOLOGICAL_BOUNDS)
        assert "heart_rate_bpm" in enforcer.bounds
        assert "spo2_percent" in enforcer.bounds

    # --- Test 02: Custom bounds instantiation ---
    def test_02_custom_bounds_instantiation(self):
        custom = {
            "hr": PhysiologicalBound("hr", 30.0, 200.0, 60.0, 100.0, "bpm")
        }
        enforcer = PhysiologicalBoundaryEnforcer(custom_bounds=custom)
        assert len(enforcer.bounds) == 1
        assert "hr" in enforcer.bounds

    # --- Test 03: Reject empty custom bounds dictionary ---
    def test_03_reject_empty_bounds(self):
        with pytest.raises(ValueError, match="Boundary dictionary cannot be empty"):
            PhysiologicalBoundaryEnforcer(custom_bounds={})

    # --- Test 04: Channel bound lookup and alias resolution ---
    def test_04_get_channel_bound_resolution(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        # Direct key
        b1 = enforcer.get_channel_bound("heart_rate_bpm")
        assert b1.min_viable == 20.0
        assert b1.max_viable == 240.0

        # Substring / alias resolution
        b2 = enforcer.get_channel_bound("spo2")
        assert b2.channel_name == "spo2_percent"

        # Case-insensitivity and whitespace stripping
        b3 = enforcer.get_channel_bound("  HEART_RATE_BPM  ")
        assert b3.channel_name == "heart_rate_bpm"

    # --- Test 05: Reject invalid or unregistered channel names ---
    def test_05_reject_invalid_channel_name_lookup(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        with pytest.raises(ValueError, match="channel_name must be a non-empty string"):
            enforcer.get_channel_bound("")
        with pytest.raises(ValueError, match="channel_name must be a non-empty string"):
            enforcer.get_channel_bound(None)
        with pytest.raises(KeyError, match="No physiological bounds registered"):
            enforcer.get_channel_bound("non_existent_biomarker_xyz")

    # --- Test 06: Scalar value audit within normal bounds ---
    def test_06_audit_value_normal(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        res = enforcer.audit_value("heart_rate_bpm", 72.0)
        assert isinstance(res, BoundaryAuditResult)
        assert res.is_within_viable_bounds is True
        assert res.is_within_normal_bounds is True
        assert res.clamped_value == 72.0
        assert res.violation_code is None

    # --- Test 07: Scalar value audit viable but outside normal (e.g. astronaut exercise) ---
    def test_07_audit_value_viable_abnormal(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        # 140 bpm during CEVIS exercise (viable, but not normal resting range [50, 100])
        res = enforcer.audit_value("heart_rate_bpm", 140.0)
        assert res.is_within_viable_bounds is True
        assert res.is_within_normal_bounds is False
        assert res.clamped_value == 140.0
        assert res.violation_code is None

    # --- Test 08: Scalar value audit non-viable low (e.g. HR < 20) ---
    def test_08_audit_value_non_viable_low(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        res = enforcer.audit_value("heart_rate_bpm", 10.0)
        assert res.is_within_viable_bounds is False
        assert res.is_within_normal_bounds is False
        assert res.violation_code == "NON_VIABLE_LOW"
        assert res.clamped_value == 20.0  # Clamped to min_viable

    # --- Test 09: Scalar value audit non-viable high (e.g. SpO2 > 100% or HR > 240) ---
    def test_09_audit_value_non_viable_high(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        res = enforcer.audit_value("spo2_percent", 105.0)
        assert res.is_within_viable_bounds is False
        assert res.violation_code == "NON_VIABLE_HIGH"
        assert res.clamped_value == 100.0  # Clamped to max_viable

    # --- Test 10: Reject non-finite values in scalar audit ---
    def test_10_reject_non_finite_scalar_value(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        with pytest.raises(ValueError, match="must be a finite float"):
            enforcer.audit_value("heart_rate_bpm", np.nan)
        with pytest.raises(ValueError, match="must be a finite float"):
            enforcer.audit_value("heart_rate_bpm", np.inf)

    # --- Test 11: Array audit with valid 1D array ---
    def test_11_audit_channel_array_valid(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        hr_arr = np.array([60.0, 72.0, 85.0, 90.0, 78.0])
        clamped, audits, all_viable = enforcer.audit_channel_array("heart_rate_bpm", hr_arr)
        assert all_viable is True
        assert np.array_equal(clamped, hr_arr)
        assert len(audits) == 5

    # --- Test 12: Array audit with out-of-boundary values requiring clamping ---
    def test_12_audit_channel_array_clamping(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        # Extreme values: 5.0 (below 20.0), 300.0 (above 240.0)
        hr_arr = np.array([5.0, 70.0, 300.0])
        clamped, audits, all_viable = enforcer.audit_channel_array("heart_rate_bpm", hr_arr)
        assert all_viable is False
        assert clamped[0] == 20.0
        assert clamped[1] == 70.0
        assert clamped[2] == 240.0
        assert audits[0].violation_code == "NON_VIABLE_LOW"
        assert audits[2].violation_code == "NON_VIABLE_HIGH"

    # --- Test 13: Array audit supporting list and pandas Series ---
    def test_13_audit_channel_array_input_types(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        # List
        clamped_list, audits_list, viable1 = enforcer.audit_channel_array("spo2_percent", [98.0, 99.0])
        assert isinstance(clamped_list, np.ndarray)

        # Series
        s = pd.Series([97.0, 98.0, 96.0])
        clamped_s, audits_s, viable2 = enforcer.audit_channel_array("spo2_percent", s)
        assert len(clamped_s) == len(s)

    # --- Test 14: Reject invalid types and empty arrays in audit_channel_array ---
    def test_14_reject_invalid_array_inputs(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        with pytest.raises(TypeError, match="Unsupported signal type"):
            enforcer.audit_channel_array("hr", "invalid_string")
        with pytest.raises(ValueError, match="must be a non-empty 1D array"):
            enforcer.audit_channel_array("hr", np.array([]))
        with pytest.raises(ValueError, match="must be a non-empty 1D array"):
            enforcer.audit_channel_array("hr", np.ones((5, 2)))

    # --- Test 15: Reject NaN and Inf in audit_channel_array ---
    def test_15_reject_nan_inf_in_channel_array(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        with pytest.raises(ValueError, match="contains non-finite values"):
            enforcer.audit_channel_array("hr", np.array([70.0, np.nan, 72.0]))
        with pytest.raises(ValueError, match="contains non-finite values"):
            enforcer.audit_channel_array("hr", np.array([70.0, np.inf, 72.0]))

    # --- Test 16: Telemetry frame audit with auto numeric columns ---
    def test_16_audit_telemetry_frame_auto(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=5, freq="min"),
            "heart_rate_bpm": [70.0, 75.0, 80.0, 72.0, 71.0],
            "spo2_percent": [98.0, 97.0, 99.0, 98.0, 98.0],
        })
        out_df, audits, frame_viable = enforcer.audit_telemetry_frame(df)
        assert isinstance(out_df, pd.DataFrame)
        assert "heart_rate_bpm" in audits
        assert "spo2_percent" in audits
        assert "timestamp" not in audits
        assert frame_viable is True

    # --- Test 17: Telemetry frame audit with explicit columns ---
    def test_17_audit_telemetry_frame_explicit(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 72.0, 74.0],
            "ambient_temp_c": [22.0, 22.5, 22.1],
            "unrelated": [1, 2, 3],
        })
        out_df, audits, frame_viable = enforcer.audit_telemetry_frame(
            df,
            target_columns=["heart_rate_bpm", "ambient_temp_c"],
        )
        assert "heart_rate_bpm" in audits
        assert "ambient_temp_c" in audits
        assert "unrelated" not in audits

    # --- Test 18: Telemetry frame with violations flags frame_viable as False ---
    def test_18_audit_telemetry_frame_with_violations(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 500.0, 72.0],  # 500 bpm is non-viable
            "spo2_percent": [98.0, 97.0, 98.0],
        })
        out_df, audits, frame_viable = enforcer.audit_telemetry_frame(df)
        assert frame_viable is False
        assert out_df["heart_rate_bpm"].iloc[1] == 240.0  # Clamped to max_viable

    # --- Test 19: Error handling in audit_telemetry_frame ---
    def test_19_audit_telemetry_frame_exceptions(self):
        enforcer = PhysiologicalBoundaryEnforcer()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            enforcer.audit_telemetry_frame("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            enforcer.audit_telemetry_frame(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            enforcer.audit_telemetry_frame(text_df)

        valid_df = pd.DataFrame({"heart_rate_bpm": [70.0, 72.0]})
        with pytest.raises(KeyError, match="Target column 'missing' not present"):
            enforcer.audit_telemetry_frame(valid_df, target_columns=["missing"])


class TestPhase2PhysiologicalGradientLimiter:
    """
    DO-178C Level C Verification for Phase 2 PhysiologicalGradientLimiter.
    Tests rate-of-change derivatives dV/dt, slew-rate clamping, sudden step-jump
    suppression, sampling rate adaptation, and DataFrame batch auditing.
    """

    # --- Test 20: Default instantiation ---
    def test_20_default_instantiation(self):
        limiter = PhysiologicalGradientLimiter()
        assert limiter.sampling_rate_hz == 1.0
        assert limiter.time_delta_sec == 1.0
        assert len(limiter.gradients) == len(NASA_MAX_PHYSIOLOGICAL_GRADIENTS)
        assert "heart_rate_bpm" in limiter.gradients

    # --- Test 21: Custom sampling rate and custom gradients ---
    def test_21_custom_instantiation(self):
        custom = {"hr": GradientLimit("hr", 10.0, "bpm/sec")}
        limiter = PhysiologicalGradientLimiter(sampling_rate_hz=5.0, custom_gradients=custom)
        assert limiter.sampling_rate_hz == 5.0
        assert limiter.time_delta_sec == 0.2
        assert len(limiter.gradients) == 1

    # --- Test 22: Reject invalid initialization parameters ---
    def test_22_reject_invalid_parameters(self):
        with pytest.raises(ValueError, match="sampling_rate_hz must be strictly positive"):
            PhysiologicalGradientLimiter(sampling_rate_hz=0.0)
        with pytest.raises(ValueError, match="sampling_rate_hz must be strictly positive"):
            PhysiologicalGradientLimiter(sampling_rate_hz=-1.0)
        with pytest.raises(ValueError, match="Gradient limits dictionary cannot be empty"):
            PhysiologicalGradientLimiter(custom_gradients={})

    # --- Test 23: Gradient limit key resolution and aliases ---
    def test_23_gradient_limit_lookup(self):
        limiter = PhysiologicalGradientLimiter()
        # Direct key
        g1 = limiter.get_gradient_limit("heart_rate_bpm")
        assert g1.max_delta_per_sec == 5.0

        # Substring / alias resolution
        g2 = limiter.get_gradient_limit("spo2")
        assert g2.channel_name == "spo2_percent"

        # Case-insensitivity
        g3 = limiter.get_gradient_limit("  CORE_TEMP_C  ")
        assert g3.channel_name == "core_temp_c"

    # --- Test 24: Reject invalid channel lookup in gradient limiter ---
    def test_24_reject_invalid_lookup(self):
        limiter = PhysiologicalGradientLimiter()
        with pytest.raises(ValueError, match="channel_name must be a non-empty string"):
            limiter.get_gradient_limit("")
        with pytest.raises(ValueError, match="channel_name must be a non-empty string"):
            limiter.get_gradient_limit(None)
        with pytest.raises(KeyError, match="No gradient limits registered"):
            limiter.get_gradient_limit("unregistered_channel_xyz")

    # --- Test 25: Permissible physiological gradient passes through unchanged ---
    def test_25_permissible_gradient(self):
        limiter = PhysiologicalGradientLimiter(sampling_rate_hz=1.0)
        # Normal physiological heart rate acceleration: +2 bpm/sec (limit is 5 bpm/sec)
        hr_series = [70.0, 72.0, 74.0, 76.0, 77.0]
        limited, audits, all_valid = limiter.audit_channel_gradient("heart_rate_bpm", hr_series)
        assert all_valid is True
        np.testing.assert_allclose(limited, hr_series)
        assert len(audits) == 4
        assert all(a.is_gradient_permissible for a in audits)

    # --- Test 26: Slew-rate clamping on impossible sudden step jump ---
    def test_26_slew_rate_clamping_on_step_jump(self):
        limiter = PhysiologicalGradientLimiter(sampling_rate_hz=1.0)
        # Sudden non-physiological step: 70 bpm to 150 bpm in 1 second (delta = +80, limit = 5.0)
        hr_jump = [70.0, 150.0]
        limited, audits, all_valid = limiter.audit_channel_gradient("heart_rate_bpm", hr_jump)
        assert all_valid is False
        assert limited[0] == 70.0
        assert limited[1] == 75.0  # Clamped to 70 + 5.0 max slew rate
        assert audits[0].is_gradient_permissible is False
        assert audits[0].delta_observed == 80.0
        assert audits[0].gradient_per_sec == 80.0
        assert audits[0].filtered_value == 75.0

    # --- Test 27: Downward spike slew-rate clamping ---
    def test_27_downward_spike_clamping(self):
        limiter = PhysiologicalGradientLimiter(sampling_rate_hz=1.0)
        # Sudden drop: 120 mmHg SBP to 40 mmHg in 1 second (delta = -80, max negative is -6.0)
        sbp_drop = [120.0, 40.0]
        limited, audits, all_valid = limiter.audit_channel_gradient("systolic_bp_mmhg", sbp_drop)
        assert all_valid is False
        assert limited[1] == 114.0  # Clamped to 120.0 - 6.0

    # --- Test 28: Support list, ndarray, and pandas Series in gradient audit ---
    def test_28_gradient_audit_input_types(self):
        limiter = PhysiologicalGradientLimiter()
        # ndarray
        arr = np.array([98.0, 97.0, 96.0])
        lim_arr, audits1, valid1 = limiter.audit_channel_gradient("spo2_percent", arr)
        assert isinstance(lim_arr, np.ndarray)

        # Series
        s = pd.Series([36.5, 36.55, 36.60])
        lim_s, audits2, valid2 = limiter.audit_channel_gradient("core_temp_c", s)
        assert len(lim_s) == len(s)

    # --- Test 29: Reject invalid types, empty arrays, and NaN/Inf in gradient audit ---
    def test_29_reject_invalid_gradient_inputs(self):
        limiter = PhysiologicalGradientLimiter()
        with pytest.raises(TypeError, match="Unsupported signal type"):
            limiter.audit_channel_gradient("hr", "invalid_string")
        with pytest.raises(ValueError, match="must be a non-empty 1D array"):
            limiter.audit_channel_gradient("hr", np.array([]))
        with pytest.raises(ValueError, match="must be a non-empty 1D array"):
            limiter.audit_channel_gradient("hr", np.ones((5, 2)))
        with pytest.raises(ValueError, match="contains non-finite values"):
            limiter.audit_channel_gradient("hr", np.array([70.0, np.nan, 72.0]))
        with pytest.raises(ValueError, match="contains non-finite values"):
            limiter.audit_channel_gradient("hr", np.array([70.0, np.inf, 72.0]))

    # --- Test 30: DataFrame gradient audit with auto columns ---
    def test_30_audit_telemetry_frame_auto(self):
        limiter = PhysiologicalGradientLimiter()
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=5, freq="min"),
            "heart_rate_bpm": [70.0, 72.0, 74.0, 76.0, 78.0],
            "spo2_percent": [98.0, 98.0, 97.5, 97.0, 97.5],
        })
        out_df, audits, frame_valid = limiter.audit_telemetry_frame(df)
        assert isinstance(out_df, pd.DataFrame)
        assert "heart_rate_bpm" in audits
        assert "spo2_percent" in audits
        assert "timestamp" not in audits
        assert frame_valid is True

    # --- Test 31: DataFrame gradient audit with step spike flags frame_valid False ---
    def test_31_audit_telemetry_frame_with_spikes(self):
        limiter = PhysiologicalGradientLimiter()
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 180.0, 185.0],  # 70 to 180 is illegal jump
            "spo2_percent": [98.0, 98.0, 98.0],
        })
        out_df, audits, frame_valid = limiter.audit_telemetry_frame(df)
        assert frame_valid is False
        assert out_df["heart_rate_bpm"].iloc[1] == 75.0  # Clamped

    # --- Test 32: Error handling in audit_telemetry_frame ---
    def test_32_audit_telemetry_frame_exceptions(self):
        limiter = PhysiologicalGradientLimiter()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            limiter.audit_telemetry_frame("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            limiter.audit_telemetry_frame(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            limiter.audit_telemetry_frame(text_df)

        valid_df = pd.DataFrame({"heart_rate_bpm": [70.0, 72.0]})
        with pytest.raises(KeyError, match="Target column 'missing' not present"):
            limiter.audit_telemetry_frame(valid_df, target_columns=["missing"])


class TestPhase3PhysiologicalCouplingGuard:
    """
    DO-178C Level C Verification for Phase 3 PhysiologicalCouplingGuard.
    Tests hemodynamic coupling (SBP vs DBP pulse pressure), cardiorespiratory
    discordance detection, vector audits, and DataFrame consistency auditing.
    """

    # --- Test 33: Default instantiation ---
    def test_33_default_instantiation(self):
        guard = PhysiologicalCouplingGuard()
        assert guard.min_pp == 15.0

    # --- Test 34: Custom min pulse pressure and invalid rejection ---
    def test_34_custom_instantiation(self):
        guard = PhysiologicalCouplingGuard(min_pulse_pressure_mmhg=20.0)
        assert guard.min_pp == 20.0
        with pytest.raises(ValueError, match="min_pulse_pressure_mmhg must be strictly positive"):
            PhysiologicalCouplingGuard(min_pulse_pressure_mmhg=0.0)
        with pytest.raises(ValueError, match="min_pulse_pressure_mmhg must be strictly positive"):
            PhysiologicalCouplingGuard(min_pulse_pressure_mmhg=-5.0)

    # --- Test 35: Valid hemodynamic coupling (e.g. SBP 120, DBP 80 -> PP 40 >= 15) ---
    def test_35_valid_hemodynamic_coupling(self):
        guard = PhysiologicalCouplingGuard()
        sbp, dbp, viols, is_coupled = guard.audit_hemodynamic_coupling(120.0, 80.0)
        assert is_coupled is True
        assert len(viols) == 0
        assert sbp == 120.0
        assert dbp == 80.0

    # --- Test 36: Pulse pressure deficit (SBP <= DBP, physically impossible) ---
    def test_36_sbp_less_than_dbp_inversion(self):
        guard = PhysiologicalCouplingGuard(min_pulse_pressure_mmhg=15.0)
        # SBP 80, DBP 90 (impossible inverted pressures)
        sbp, dbp, viols, is_coupled = guard.audit_hemodynamic_coupling(80.0, 90.0)
        assert is_coupled is False
        assert len(viols) == 1
        assert viols[0].rule_name == "PULSE_PRESSURE_DEFICIT"
        assert sbp == 105.0  # dbp + min_pp (90 + 15)

    # --- Test 37: Narrow pulse pressure (< 15 mmHg, e.g. 100/90) ---
    def test_37_narrow_pulse_pressure_expansion(self):
        guard = PhysiologicalCouplingGuard(min_pulse_pressure_mmhg=15.0)
        # SBP 100, DBP 90 (PP = 10 < 15)
        sbp, dbp, viols, is_coupled = guard.audit_hemodynamic_coupling(100.0, 90.0)
        assert is_coupled is False
        assert len(viols) == 1
        # Mean pressure is 95. SBP should become 95 + 7.5 = 102.5, DBP = 95 - 7.5 = 87.5
        assert sbp == 102.5
        assert dbp == 87.5

    # --- Test 38: Reject non-finite values in hemodynamic coupling ---
    def test_38_reject_non_finite_hemodynamic(self):
        guard = PhysiologicalCouplingGuard()
        with pytest.raises(ValueError, match="must be finite numbers"):
            guard.audit_hemodynamic_coupling(np.nan, 80.0)
        with pytest.raises(ValueError, match="must be finite numbers"):
            guard.audit_hemodynamic_coupling(120.0, np.inf)

    # --- Test 39: Valid cardiorespiratory coupling ---
    def test_39_valid_cardiorespiratory_coupling(self):
        guard = PhysiologicalCouplingGuard()
        hr, rr, viols, is_coupled = guard.audit_cardiorespiratory_coupling(75.0, 16.0)
        assert is_coupled is True
        assert len(viols) == 0

    # --- Test 40: Cardiorespiratory discordance (HR < 25 while RR > 8) ---
    def test_40_cardiac_arrest_respiratory_discordance(self):
        guard = PhysiologicalCouplingGuard()
        # Flatline HR (10 bpm) with spontaneous breathing (18 bpm)
        hr, rr, viols, is_coupled = guard.audit_cardiorespiratory_coupling(10.0, 18.0)
        assert is_coupled is False
        assert len(viols) == 1
        assert viols[0].rule_name == "CARDIAC_ARREST_RESPIRATORY_DISCORDANCE"

    # --- Test 41: Reject non-finite values in cardiorespiratory coupling ---
    def test_41_reject_non_finite_cardiorespiratory(self):
        guard = PhysiologicalCouplingGuard()
        with pytest.raises(ValueError, match="must be finite numbers"):
            guard.audit_cardiorespiratory_coupling(np.nan, 16.0)
        with pytest.raises(ValueError, match="must be finite numbers"):
            guard.audit_cardiorespiratory_coupling(70.0, np.nan)

    # --- Test 42: Telemetry vector audit (Dictionary) ---
    def test_42_audit_telemetry_vector(self):
        guard = PhysiologicalCouplingGuard()
        vec = {
            "heart_rate_bpm": 72.0,
            "resp_rate_bpm": 15.0,
            "systolic_bp_mmhg": 80.0,
            "diastolic_bp_mmhg": 90.0,  # Inverted!
            "spo2_percent": 98.0,
        }
        res = guard.audit_telemetry_vector(vec)
        assert isinstance(res, CouplingAuditResult)
        assert res.is_physiologically_coupled is False
        assert len(res.violations) == 1
        # Fixed hemodynamic pressure
        assert res.sanitized_values["systolic_bp_mmhg"] == 105.0

    # --- Test 43: Reject empty or invalid dictionary in audit_telemetry_vector ---
    def test_43_reject_invalid_dict_telemetry_vector(self):
        guard = PhysiologicalCouplingGuard()
        with pytest.raises(ValueError, match="must be a non-empty dictionary"):
            guard.audit_telemetry_vector({})
        with pytest.raises(ValueError, match="must be a non-empty dictionary"):
            guard.audit_telemetry_vector("invalid_string")

    # --- Test 44: DataFrame frame audit with coupling enforcement ---
    def test_44_audit_telemetry_frame(self):
        guard = PhysiologicalCouplingGuard()
        df = pd.DataFrame({
            "systolic_bp_mmhg": [120.0, 80.0, 115.0],
            "diastolic_bp_mmhg": [80.0, 90.0, 75.0],  # Row 1 is inverted
            "heart_rate_bpm": [70.0, 72.0, 75.0],
            "resp_rate_bpm": [14.0, 15.0, 16.0],
        })
        out_df, audits, all_coupled = guard.audit_telemetry_frame(df)
        assert isinstance(out_df, pd.DataFrame)
        assert all_coupled is False
        assert len(audits) == 3
        # Row 1 SBP should be adjusted
        assert out_df.loc[1, "systolic_bp_mmhg"] == 105.0

    # --- Test 45: Error handling in audit_telemetry_frame ---
    def test_45_audit_telemetry_frame_exceptions(self):
        guard = PhysiologicalCouplingGuard()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            guard.audit_telemetry_frame("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            guard.audit_telemetry_frame(pd.DataFrame())


class TestPhase4SensorDecouplingFallbackEngine:
    """
    DO-178C Level C Verification for Phase 4 SensorDecouplingFallbackEngine.
    Tests bounded last-known-valid hold, transition to mission baseline,
    validity mask enforcement, auto NaN/Inf substitution, and DataFrame batch processing.
    """

    # --- Test 46: Default instantiation ---
    def test_46_default_instantiation(self):
        engine = SensorDecouplingFallbackEngine()
        assert engine.sampling_rate_hz == 1.0
        assert engine.time_delta_sec == 1.0
        assert len(engine.policies) == len(APOLLO_ISS_MISSION_BASELINES)
        assert "heart_rate_bpm" in engine.policies

    # --- Test 47: Custom instantiation ---
    def test_47_custom_instantiation(self):
        custom = {"hr": FallbackPolicy("hr", "HOLD_LAST_VALID", 60.0, 75.0)}
        engine = SensorDecouplingFallbackEngine(sampling_rate_hz=2.0, policies=custom)
        assert engine.sampling_rate_hz == 2.0
        assert engine.time_delta_sec == 0.5
        assert len(engine.policies) == 1

    # --- Test 48: Reject invalid initialization parameters ---
    def test_48_reject_invalid_parameters(self):
        with pytest.raises(ValueError, match="sampling_rate_hz must be strictly positive"):
            SensorDecouplingFallbackEngine(sampling_rate_hz=0.0)
        with pytest.raises(ValueError, match="sampling_rate_hz must be strictly positive"):
            SensorDecouplingFallbackEngine(sampling_rate_hz=-2.0)
        with pytest.raises(ValueError, match="Fallback policies dictionary cannot be empty"):
            SensorDecouplingFallbackEngine(policies={})

    # --- Test 49: Policy lookup and alias resolution ---
    def test_49_policy_lookup(self):
        engine = SensorDecouplingFallbackEngine()
        # Direct
        p1 = engine.get_policy("heart_rate_bpm")
        assert p1.calibrated_baseline_value == 72.0
        # Substring / alias
        p2 = engine.get_policy("spo2")
        assert p2.channel_name == "spo2_percent"
        # Case insensitive
        p3 = engine.get_policy("  ICP_EST_MMHG  ")
        assert p3.channel_name == "icp_est_mmhg"

    # --- Test 50: Reject invalid policy lookup ---
    def test_50_reject_invalid_policy_lookup(self):
        engine = SensorDecouplingFallbackEngine()
        with pytest.raises(ValueError, match="channel_name must be a non-empty string"):
            engine.get_policy("")
        with pytest.raises(ValueError, match="channel_name must be a non-empty string"):
            engine.get_policy(None)
        with pytest.raises(KeyError, match="No fallback policy registered"):
            engine.get_policy("unknown_channel_xyz")

    # --- Test 51: Valid signal without dropouts requires zero fallbacks ---
    def test_51_valid_signal_zero_fallbacks(self):
        engine = SensorDecouplingFallbackEngine()
        sig = [70.0, 72.0, 74.0, 73.0, 75.0]
        sanitized, logs, f_count = engine.apply_fallback_channel("heart_rate_bpm", sig)
        assert f_count == 0
        assert len(logs) == 0
        np.testing.assert_allclose(sanitized, sig)

    # --- Test 52: Short dropout within max_hold_duration uses HOLD_LAST_VALID ---
    def test_52_short_dropout_hold_last_valid(self):
        # 1 Hz sampling, max_hold 180s.
        engine = SensorDecouplingFallbackEngine(sampling_rate_hz=1.0)
        # Dropouts (NaN) at index 2 and 3
        sig = np.array([72.0, 75.0, np.nan, np.nan, 78.0])
        sanitized, logs, f_count = engine.apply_fallback_channel("heart_rate_bpm", sig)
        assert f_count == 2
        assert len(logs) == 2
        # Index 2 and 3 should hold the last valid value (75.0)
        assert sanitized[2] == 75.0
        assert sanitized[3] == 75.0
        assert logs[0].policy_applied == "HOLD_LAST_VALID"
        assert logs[1].policy_applied == "HOLD_LAST_VALID"

    # --- Test 53: Extended dropout exceeding max_hold transitions to MISSION_BASELINE ---
    def test_53_extended_dropout_mission_baseline(self):
        # Policy with small max_hold_duration (2.0 seconds = 2 samples at 1 Hz)
        custom_policy = {
            "hr": FallbackPolicy("hr", "HOLD_LAST_VALID", 2.0, 72.0)
        }
        engine = SensorDecouplingFallbackEngine(sampling_rate_hz=1.0, policies=custom_policy)
        # 1 valid sample followed by 4 consecutive dropouts
        sig = np.array([80.0, np.nan, np.nan, np.nan, np.nan])
        sanitized, logs, f_count = engine.apply_fallback_channel("hr", sig)
        assert f_count == 4
        # Dropouts 1 and 2 (duration 1.0s and 2.0s <= 2.0s) hold 80.0
        assert sanitized[1] == 80.0
        assert logs[0].policy_applied == "HOLD_LAST_VALID"
        assert sanitized[2] == 80.0
        assert logs[1].policy_applied == "HOLD_LAST_VALID"
        # Dropout 3 and 4 (duration 3.0s and 4.0s > 2.0s) fall back to calibrated baseline 72.0
        assert sanitized[3] == 72.0
        assert logs[2].policy_applied == "MISSION_BASELINE"
        assert sanitized[4] == 72.0
        assert logs[3].policy_applied == "MISSION_BASELINE"

    # --- Test 54: Dropout starting at sample 0 (no prior valid) uses MISSION_BASELINE ---
    def test_54_lead_off_at_start(self):
        engine = SensorDecouplingFallbackEngine()
        sig = np.array([np.nan, np.nan, 75.0])
        sanitized, logs, f_count = engine.apply_fallback_channel("heart_rate_bpm", sig)
        assert f_count == 2
        # Sample 0 and 1 have no last valid, so they fall back to 72.0
        assert sanitized[0] == 72.0
        assert sanitized[1] == 72.0
        assert logs[0].policy_applied == "MISSION_BASELINE"

    # --- Test 55: Explicit boolean validity mask support ---
    def test_55_explicit_validity_mask(self):
        engine = SensorDecouplingFallbackEngine()
        sig = [70.0, 80.0, 90.0]
        # Mark index 1 as corrupted via mask
        mask = [True, False, True]
        sanitized, logs, f_count = engine.apply_fallback_channel(
            "heart_rate_bpm",
            sig,
            validity_mask=mask,
        )
        assert f_count == 1
        assert sanitized[1] == 70.0  # Held from sample 0

    # --- Test 56: Support list, ndarray, Series and reject invalid inputs ---
    def test_56_fallback_input_types_and_rejections(self):
        engine = SensorDecouplingFallbackEngine()
        # Series
        s = pd.Series([98.0, 97.0])
        san, logs, fc = engine.apply_fallback_channel("spo2_percent", s)
        assert len(san) == 2

        with pytest.raises(TypeError, match="Unsupported signal type"):
            engine.apply_fallback_channel("heart_rate_bpm", "invalid")
        with pytest.raises(ValueError, match="must be a non-empty 1D array"):
            engine.apply_fallback_channel("heart_rate_bpm", np.array([]))
        with pytest.raises(ValueError, match="must be a non-empty 1D array"):
            engine.apply_fallback_channel("heart_rate_bpm", np.ones((3, 3)))
        with pytest.raises(ValueError, match="validity_mask shape"):
            engine.apply_fallback_channel("heart_rate_bpm", np.ones(5), validity_mask=np.ones(3))

    # --- Test 57: DataFrame fallback with auto numeric columns ---
    def test_57_apply_fallback_frame_auto(self):
        engine = SensorDecouplingFallbackEngine()
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=5, freq="min"),
            "heart_rate_bpm": [70.0, 72.0, np.nan, 74.0, 75.0],
            "spo2_percent": [98.0, np.nan, 97.0, 98.0, 99.0],
        })
        out_df, logs, total_fc = engine.apply_fallback_frame(df)
        assert isinstance(out_df, pd.DataFrame)
        assert total_fc == 2
        assert "heart_rate_bpm" in logs
        assert "spo2_percent" in logs
        assert "timestamp" not in logs
        # Check no NaNs remaining
        assert not out_df.isna().any().any()

    # --- Test 58: DataFrame fallback with validity_df mask ---
    def test_58_apply_fallback_frame_with_validity_df(self):
        engine = SensorDecouplingFallbackEngine()
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 200.0, 72.0],  # 200 is marked invalid in mask
        })
        val_df = pd.DataFrame({
            "heart_rate_bpm": [True, False, True],
        })
        out_df, logs, total_fc = engine.apply_fallback_frame(df, validity_df=val_df)
        assert total_fc == 1
        assert out_df["heart_rate_bpm"].iloc[1] == 70.0  # Held

    # --- Test 59: Error handling in apply_fallback_frame ---
    def test_59_apply_fallback_frame_exceptions(self):
        engine = SensorDecouplingFallbackEngine()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            engine.apply_fallback_frame("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            engine.apply_fallback_frame(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            engine.apply_fallback_frame(text_df)

        valid_df = pd.DataFrame({"heart_rate_bpm": [70.0, 72.0]})
        with pytest.raises(KeyError, match="Target column 'missing' not present"):
            engine.apply_fallback_frame(valid_df, target_columns=["missing"])


class TestPhase5SanityGateExporter:
    """
    DO-178C Level C Verification for Phase 5 SanityGateExporter.
    Tests end-to-end 4-stage sequential sanity gating, clean flight telemetry pass,
    multi-violation remediation, audit manifest generation, and contract validation.
    """

    # --- Test 60: Default instantiation ---
    def test_60_default_instantiation(self):
        exporter = SanityGateExporter()
        assert isinstance(exporter.fallback_engine, SensorDecouplingFallbackEngine)
        assert isinstance(exporter.boundary_enforcer, PhysiologicalBoundaryEnforcer)
        assert isinstance(exporter.gradient_limiter, PhysiologicalGradientLimiter)
        assert isinstance(exporter.coupling_guard, PhysiologicalCouplingGuard)

    # --- Test 61: Custom subcomponents instantiation ---
    def test_61_custom_instantiation(self):
        fe = SensorDecouplingFallbackEngine(sampling_rate_hz=2.0)
        be = PhysiologicalBoundaryEnforcer()
        gl = PhysiologicalGradientLimiter(sampling_rate_hz=2.0)
        cg = PhysiologicalCouplingGuard(min_pulse_pressure_mmhg=20.0)

        exporter = SanityGateExporter(
            fallback_engine=fe,
            boundary_enforcer=be,
            gradient_limiter=gl,
            coupling_guard=cg,
        )
        assert exporter.fallback_engine == fe
        assert exporter.boundary_enforcer == be
        assert exporter.gradient_limiter == gl
        assert exporter.coupling_guard == cg

    # --- Test 62: Clean nominal flight telemetry produces clean gate pass ---
    def test_62_clean_telemetry_clean_pass(self):
        exporter = SanityGateExporter()
        n = 5
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=n, freq="min"),
            "heart_rate_bpm": [70.0, 72.0, 73.0, 72.0, 71.0],
            "systolic_bp_mmhg": [118.0, 120.0, 119.0, 121.0, 120.0],
            "diastolic_bp_mmhg": [78.0, 80.0, 79.0, 80.0, 79.0],
            "spo2_percent": [98.0, 98.0, 97.0, 98.0, 98.0],
            "resp_rate_bpm": [14.0, 15.0, 14.0, 15.0, 14.0],
        })

        packet = exporter.process_and_export_packet(df)
        assert isinstance(packet, SanityGatedPacket)
        assert packet.is_gate_passed is True
        assert packet.total_violations_remediated == 0
        assert packet.boundary_violations_count == 0
        assert packet.gradient_violations_count == 0
        assert packet.coupling_violations_count == 0
        assert packet.fallback_substitutions_count == 0
        assert packet.sanitized_tensor.shape == (5, 5)
        assert packet.audit_manifest["is_clean_pass"] is True

    # --- Test 63: Corrupted telemetry with all 4 stages of violations remediated ---
    def test_63_corrupted_telemetry_remediation(self):
        exporter = SanityGateExporter()
        # Telemetry exhibiting:
        # 1. Row 0: Inverted/Narrow BP (SBP 90, DBP 85 -> PP 5 < 15) -> Coupling Guard fixes
        # 2. Row 1: Extreme SBP (500 mmHg) -> Boundary Enforcer clamps to 260
        # 3. Row 2: Sudden step jump in HR (70 to 150) -> Gradient Limiter clamps slew rate
        # 4. Row 3: NaN in heart_rate_bpm -> Fallback Engine triggers
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 71.0, 150.0, np.nan],
            "systolic_bp_mmhg": [90.0, 500.0, 120.0, 120.0],
            "diastolic_bp_mmhg": [85.0, 80.0, 80.0, 80.0],
            "resp_rate_bpm": [14.0, 14.0, 14.0, 14.0],
        })

        packet = exporter.process_and_export_packet(df)
        assert packet.is_gate_passed is False
        assert packet.total_violations_remediated > 0
        assert packet.fallback_substitutions_count >= 1
        assert packet.boundary_violations_count >= 1
        assert packet.gradient_violations_count >= 1
        assert packet.coupling_violations_count >= 1
        assert np.all(np.isfinite(packet.sanitized_tensor))
        # Ensure SBP is clamped below 260
        assert np.max(packet.sanitized_tensor[:, 1]) <= 260.0

    # --- Test 64: Explicit target columns selection ---
    def test_64_explicit_target_columns(self):
        exporter = SanityGateExporter()
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 72.0, 74.0],
            "spo2_percent": [98.0, 98.0, 97.0],
            "unused_sensor": [999.0, 999.0, 999.0],
        })
        packet = exporter.process_and_export_packet(
            df,
            target_columns=["heart_rate_bpm", "spo2_percent"],
        )
        assert packet.sanitized_tensor.shape == (3, 2)
        assert "unused_sensor" not in packet.channel_names

    # --- Test 65: With external validity mask DataFrame ---
    def test_65_with_validity_df_mask(self):
        exporter = SanityGateExporter()
        df = pd.DataFrame({
            "heart_rate_bpm": [70.0, 85.0, 72.0],
        })
        val_df = pd.DataFrame({
            "heart_rate_bpm": [True, False, True],  # 85 is flagged corrupted
        })
        packet = exporter.process_and_export_packet(df, validity_df=val_df)
        assert packet.fallback_substitutions_count == 1
        assert packet.sanitized_tensor[1, 0] == 70.0  # Held

    # --- Test 66: Exporter exceptions and error handling ---
    def test_66_exporter_exceptions(self):
        exporter = SanityGateExporter()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            exporter.process_and_export_packet("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            exporter.process_and_export_packet(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric vital channels found"):
            exporter.process_and_export_packet(text_df)

        valid_df = pd.DataFrame({"heart_rate_bpm": [70.0, 72.0]})
        with pytest.raises(KeyError, match="Target column 'missing' not present"):
            exporter.process_and_export_packet(valid_df, target_columns=["missing"])

    # --- Test 67: Non-finite fallback scrub branch in exporter ---
    def test_67_non_finite_scrub_branch(self):
        # Mock coupling guard that injects an Inf value into the DataFrame
        class CorruptingCouplingGuard(PhysiologicalCouplingGuard):
            def audit_telemetry_frame(self, telemetry_df):
                out_df = telemetry_df.copy()
                out_df.loc[0, "heart_rate_bpm"] = np.inf
                dummy_audit = CouplingAuditResult(
                    is_physiologically_coupled=True,
                    violations=[],
                    sanitized_values={},
                )
                return out_df, [dummy_audit] * len(out_df), True

        corrupt_exporter = SanityGateExporter(coupling_guard=CorruptingCouplingGuard())
        df = pd.DataFrame({"heart_rate_bpm": [70.0, 72.0, 74.0]})
        packet = corrupt_exporter.process_and_export_packet(df)
        assert np.all(np.isfinite(packet.sanitized_tensor))
        assert packet.is_gate_passed is False




