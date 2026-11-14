"""
ASTROVITAL AI: VITALX CORE RECREATED V1
Test Suite: DO-178C Level C Verification for inno3_signal_stabilizer.py
Phase 1 Verification Tests (Targeting 100% statement coverage of Phase 1 implementation)
File: 02_AI_CORE/02_tests/test_signal_stabilizer.py
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

from inno3_signal_stabilizer import (
    BaselineDriftCompensator,
    DriftCompensationResult,
    MorphologyPreservingFilter,
    FilteringResult,
    AdaptiveMotionCanceller,
    MotionCancellationResult,
    SignalQualityEvaluator,
    SQIEvaluationResult,
    StabilizedFrameExporter,
    StabilizedFrameContract,
)


class TestPhase1BaselineDriftCompensator:
    """
    DO-178C Level C Requirements-Based Test Suite for Phase 1.
    Tests every boundary, exception, mathematical transformation, and branch.
    """

    # --- Test 1: Instantiation with default parameters ---
    def test_01_default_instantiation(self):
        comp = BaselineDriftCompensator()
        assert comp.sampling_rate_hz == 1.0
        assert comp.window_size == 31
        assert comp.max_allowed_drift_rate == 5.0

    # --- Test 2: Instantiation with valid custom parameters ---
    def test_02_custom_valid_instantiation(self):
        comp = BaselineDriftCompensator(
            sampling_rate_hz=10.0,
            drift_cutoff_window_sec=15,
            max_allowed_drift_rate=2.5,
        )
        assert comp.sampling_rate_hz == 10.0
        assert comp.window_size == 15
        assert comp.max_allowed_drift_rate == 2.5

    # --- Test 3: Rejection of non-positive sampling rates ---
    def test_03_reject_non_positive_sampling_rate(self):
        with pytest.raises(ValueError, match="sampling_rate_hz must be strictly positive"):
            BaselineDriftCompensator(sampling_rate_hz=0.0)
        with pytest.raises(ValueError, match="sampling_rate_hz must be strictly positive"):
            BaselineDriftCompensator(sampling_rate_hz=-2.0)

    # --- Test 4: Rejection of invalid window sizes (< 3 or even) ---
    def test_04_reject_invalid_window_size(self):
        with pytest.raises(ValueError, match="must be an odd integer >= 3"):
            BaselineDriftCompensator(drift_cutoff_window_sec=2)
        with pytest.raises(ValueError, match="must be an odd integer >= 3"):
            BaselineDriftCompensator(drift_cutoff_window_sec=10)
        with pytest.raises(ValueError, match="must be an odd integer >= 3"):
            BaselineDriftCompensator(drift_cutoff_window_sec=-5)

    # --- Test 5: Rejection of non-positive max allowed drift rate ---
    def test_05_reject_non_positive_drift_rate_threshold(self):
        with pytest.raises(ValueError, match="max_allowed_drift_rate must be strictly positive"):
            BaselineDriftCompensator(max_allowed_drift_rate=0.0)
        with pytest.raises(ValueError, match="max_allowed_drift_rate must be strictly positive"):
            BaselineDriftCompensator(max_allowed_drift_rate=-1.5)

    # --- Test 6: Estimate baseline drift on valid 1D numpy array ---
    def test_06_estimate_baseline_drift_linear_synthetic(self):
        comp = BaselineDriftCompensator(sampling_rate_hz=1.0, drift_cutoff_window_sec=5)
        # Create a stationary signal with linear thermal drift: y = 2 * x + 50
        x = np.arange(50, dtype=np.float64)
        drift_true = 0.5 * x
        oscillation = 2.0 * np.sin(2 * np.pi * 0.2 * x)
        raw_signal = 75.0 + drift_true + oscillation

        est_drift = comp.estimate_baseline_drift(raw_signal)
        assert isinstance(est_drift, np.ndarray)
        assert est_drift.shape == raw_signal.shape
        # Drift estimation should track the linear trend closely
        np.testing.assert_allclose(est_drift, 75.0 + drift_true, atol=2.5)

    # --- Test 7: Signal shorter than filter window size triggers polynomial fallback ---
    def test_07_signal_shorter_than_window_polynomial_fallback(self):
        comp = BaselineDriftCompensator(sampling_rate_hz=1.0, drift_cutoff_window_sec=31)
        short_signal = np.array([10.0, 12.0, 14.0, 16.0, 18.0], dtype=np.float64)
        est_drift = comp.estimate_baseline_drift(short_signal)
        assert len(est_drift) == len(short_signal)
        # Linear ramp should be fit accurately
        np.testing.assert_allclose(est_drift, short_signal, atol=1e-5)

    # --- Test 8: Rejection of non-1D array input to estimate_baseline_drift ---
    def test_08_reject_non_1d_input_in_estimate(self):
        comp = BaselineDriftCompensator()
        matrix_2d = np.ones((10, 2))
        with pytest.raises(ValueError, match="Signal must be a 1D array"):
            comp.estimate_baseline_drift(matrix_2d)

    # --- Test 9: Rejection of empty array in estimate_baseline_drift ---
    def test_09_reject_empty_array_in_estimate(self):
        comp = BaselineDriftCompensator()
        empty_arr = np.array([])
        with pytest.raises(ValueError, match="Input signal array cannot be empty"):
            comp.estimate_baseline_drift(empty_arr)

    # --- Test 9b: estimate_baseline_drift with non-ndarray input list ---
    def test_09b_estimate_with_list_input(self):
        comp = BaselineDriftCompensator(drift_cutoff_window_sec=5)
        raw_list = [70.0, 71.0, 72.0, 73.0, 74.0]
        drift = comp.estimate_baseline_drift(raw_list)
        assert isinstance(drift, np.ndarray)
        assert len(drift) == len(raw_list)

    # --- Test 10: Compensate drift with list input and type conversion ---
    def test_10_compensate_drift_list_input(self):
        comp = BaselineDriftCompensator(drift_cutoff_window_sec=5)
        raw_list = [70.0, 72.0, 71.0, 73.0, 72.0, 74.0, 73.0]
        result = comp.compensate_drift(raw_list, channel_name="heart_rate")
        assert isinstance(result, DriftCompensationResult)
        assert isinstance(result.cleaned_signal, np.ndarray)
        assert len(result.cleaned_signal) == len(raw_list)
        # Original mean level preserved
        np.testing.assert_allclose(np.mean(result.cleaned_signal), np.mean(raw_list), atol=1e-5)

    # --- Test 11: Compensate drift with pandas Series input ---
    def test_11_compensate_drift_pandas_series_input(self):
        comp = BaselineDriftCompensator(drift_cutoff_window_sec=5)
        series = pd.Series([120.0, 122.0, 121.0, 123.0, 125.0, 124.0, 126.0], name="systolic_bp")
        result = comp.compensate_drift(series, channel_name="systolic_bp")
        assert len(result.cleaned_signal) == len(series)
        assert result.max_drift_amplitude >= 0.0

    # --- Test 12: Rejection of invalid types in compensate_drift ---
    def test_12_reject_invalid_signal_type(self):
        comp = BaselineDriftCompensator()
        with pytest.raises(TypeError, match="Unsupported signal type"):
            comp.compensate_drift("invalid_string_telemetry")
        with pytest.raises(TypeError, match="Unsupported signal type"):
            comp.compensate_drift({"channel": 123})

    # --- Test 13: Rejection of NaN or Inf values in telemetry signal ---
    def test_13_reject_nan_or_inf_in_signal(self):
        comp = BaselineDriftCompensator()
        nan_signal = np.array([72.0, np.nan, 75.0])
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            comp.compensate_drift(nan_signal, channel_name="hr")
        
        inf_signal = np.array([72.0, np.inf, 75.0])
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            comp.compensate_drift(inf_signal, channel_name="hr")

    # --- Test 14: Detection of excessive drift exceeding threshold ---
    def test_14_excessive_drift_rate_flag(self):
        # Sampling rate 1 Hz, extreme slope (10.0 units/sec)
        comp = BaselineDriftCompensator(sampling_rate_hz=1.0, drift_cutoff_window_sec=5, max_allowed_drift_rate=2.0)
        x = np.arange(20, dtype=np.float64)
        severe_drift = 10.0 * x  # 10 units/sec slope
        res = comp.compensate_drift(severe_drift, channel_name="extreme_drift_channel")
        assert res.is_drift_excessive is True
        assert res.drift_rate_per_sec > 2.0

    # --- Test 15: Non-excessive drift within normal physiological range ---
    def test_15_normal_drift_within_bounds(self):
        comp = BaselineDriftCompensator(sampling_rate_hz=1.0, drift_cutoff_window_sec=7, max_allowed_drift_rate=5.0)
        x = np.arange(30, dtype=np.float64)
        gentle_drift = 0.05 * x  # 0.05 units/sec slope
        res = comp.compensate_drift(gentle_drift, channel_name="stable_channel")
        assert res.is_drift_excessive is False
        assert res.drift_rate_per_sec < 5.0

    # --- Test 16: Telemetry frame batch processing with valid DataFrame ---
    def test_16_compensate_telemetry_frame_auto_numeric(self):
        comp = BaselineDriftCompensator(drift_cutoff_window_sec=5)
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=10, freq="min"),
            "heart_rate_bpm": [70.0, 71.0, 72.0, 73.0, 72.0, 71.0, 70.0, 72.0, 73.0, 74.0],
            "spo2_percent": [98.0, 98.0, 97.0, 98.0, 98.0, 97.0, 98.0, 99.0, 98.0, 98.0],
        })
        out_df, results = comp.compensate_telemetry_frame(df)
        assert isinstance(out_df, pd.DataFrame)
        assert "heart_rate_bpm" in results
        assert "spo2_percent" in results
        assert "timestamp" not in results  # Timestamp should be excluded from processing
        assert len(out_df) == 10

    # --- Test 17: Telemetry frame batch processing with explicit target columns ---
    def test_17_compensate_telemetry_frame_explicit_columns(self):
        comp = BaselineDriftCompensator(drift_cutoff_window_sec=5)
        df = pd.DataFrame({
            "hr": [70.0, 71.0, 72.0, 73.0, 74.0, 75.0, 76.0],
            "bp": [120.0, 121.0, 122.0, 123.0, 124.0, 125.0, 126.0],
            "aux": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
        })
        out_df, results = comp.compensate_telemetry_frame(df, target_columns=["hr", "bp"])
        assert "hr" in results
        assert "bp" in results
        assert "aux" not in results

    # --- Test 18: Telemetry frame error handling on invalid inputs ---
    def test_18_compensate_telemetry_frame_exceptions(self):
        comp = BaselineDriftCompensator()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            comp.compensate_telemetry_frame("invalid_df")
        
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            comp.compensate_telemetry_frame(pd.DataFrame())

        # No numeric columns
        text_df = pd.DataFrame({"astronaut_id": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            comp.compensate_telemetry_frame(text_df)

        # Missing explicit column
        valid_df = pd.DataFrame({"hr": [70.0, 72.0, 74.0]})
        with pytest.raises(KeyError, match="Target column 'missing_col' not present"):
            comp.compensate_telemetry_frame(valid_df, target_columns=["missing_col"])

    # --- Test 19: Edge Case: Single sample duration <= 1.0 sec ---
    def test_19_single_sample_duration_boundary(self):
        comp = BaselineDriftCompensator(sampling_rate_hz=1.0, drift_cutoff_window_sec=3)
        single_point = np.array([80.0])
        res = comp.compensate_drift(single_point, channel_name="single_sample")
        assert len(res.cleaned_signal) == 1
        assert res.drift_rate_per_sec == 0.0
        assert res.max_drift_amplitude == 0.0

    # --- Test 20: Input array with ndim != 1 in compensate_drift ---
    def test_20_reject_multi_dim_array_in_compensate_drift(self):
        comp = BaselineDriftCompensator()
        matrix = np.ones((5, 5))
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            comp.compensate_drift(matrix, channel_name="2d_matrix")


class TestPhase2MorphologyPreservingFilter:
    """
    DO-178C Level C Verification for Phase 2 MorphologyPreservingFilter.
    Tests filter initialization, mathematical kernel convolution, SNR tracking,
    exception handling, and batch telemetry execution.
    """

    # --- Test 21: Default instantiation ---
    def test_21_default_instantiation(self):
        filt = MorphologyPreservingFilter()
        assert filt.window_length == 7
        assert filt.poly_order == 2

    # --- Test 22: Custom valid parameters ---
    def test_22_custom_instantiation(self):
        filt = MorphologyPreservingFilter(window_length=11, poly_order=3)
        assert filt.window_length == 11
        assert filt.poly_order == 3

    # --- Test 23: Reject invalid window_length (<3 or even) ---
    def test_23_reject_invalid_window_length(self):
        with pytest.raises(ValueError, match="window_length must be an odd integer >= 3"):
            MorphologyPreservingFilter(window_length=2)
        with pytest.raises(ValueError, match="window_length must be an odd integer >= 3"):
            MorphologyPreservingFilter(window_length=8)
        with pytest.raises(ValueError, match="window_length must be an odd integer >= 3"):
            MorphologyPreservingFilter(window_length=-3)

    # --- Test 24: Reject invalid poly_order (<1 or >= window_length) ---
    def test_24_reject_invalid_poly_order(self):
        with pytest.raises(ValueError, match="poly_order must be an integer >= 1 and < window_length"):
            MorphologyPreservingFilter(window_length=7, poly_order=0)
        with pytest.raises(ValueError, match="poly_order must be an integer >= 1 and < window_length"):
            MorphologyPreservingFilter(window_length=7, poly_order=7)
        with pytest.raises(ValueError, match="poly_order must be an integer >= 1 and < window_length"):
            MorphologyPreservingFilter(window_length=7, poly_order=9)

    # --- Test 25: SNR computation edge cases (zero noise / zero signal) ---
    def test_25_snr_computation_edge_cases(self):
        filt = MorphologyPreservingFilter()
        zero_noise = np.zeros(10)
        sig = np.ones(10) * 5.0
        assert filt._compute_snr_db(sig, zero_noise) == 100.0

        zero_sig = np.zeros(10)
        noise = np.ones(10) * 2.0
        assert filt._compute_snr_db(zero_sig, noise) == -100.0

    # --- Test 26: Signal shorter than window returns safe identity copy ---
    def test_26_short_signal_safe_passthrough(self):
        filt = MorphologyPreservingFilter(window_length=9, poly_order=2)
        short_sig = np.array([1.0, 2.0, 3.0, 4.0])
        res = filt.filter_signal(short_sig, channel_name="short_sig")
        assert isinstance(res, FilteringResult)
        assert np.array_equal(res.filtered_signal, short_sig)
        assert res.snr_improvement_db == 0.0
        assert res.noise_variance == 0.0

    # --- Test 27: Smooth sinusoidal signal with high-frequency noise removal ---
    def test_27_noise_filtering_effectiveness(self):
        filt = MorphologyPreservingFilter(window_length=11, poly_order=2)
        x = np.linspace(0, 4 * np.pi, 100)
        pure_signal = 10.0 * np.sin(x) + 70.0
        np.random.seed(42)
        noise = np.random.normal(0, 1.5, size=100)
        noisy_signal = pure_signal + noise

        res = filt.filter_signal(noisy_signal, channel_name="ecg_lead_ii")
        assert len(res.filtered_signal) == 100
        # The variance of filtered signal with respect to pure signal should be significantly reduced
        raw_error = np.mean((noisy_signal - pure_signal) ** 2)
        filtered_error = np.mean((res.filtered_signal - pure_signal) ** 2)
        assert filtered_error < raw_error

    # --- Test 28: Support list and pandas Series types in filter_signal ---
    def test_28_filter_signal_input_types(self):
        filt = MorphologyPreservingFilter(window_length=5, poly_order=2)
        # List
        res_list = filt.filter_signal([10.0, 12.0, 11.0, 13.0, 12.0, 14.0, 13.0])
        assert isinstance(res_list.filtered_signal, np.ndarray)

        # Series
        s = pd.Series([98.0, 97.0, 99.0, 98.0, 97.0, 98.0, 99.0])
        res_series = filt.filter_signal(s)
        assert len(res_series.filtered_signal) == len(s)

    # --- Test 29: Reject invalid input types in filter_signal ---
    def test_29_reject_invalid_input_types_filter_signal(self):
        filt = MorphologyPreservingFilter()
        with pytest.raises(TypeError, match="Unsupported signal type"):
            filt.filter_signal("text_signal")
        with pytest.raises(TypeError, match="Unsupported signal type"):
            filt.filter_signal({"data": [1, 2, 3]})

    # --- Test 30: Reject non-1D or empty input in filter_signal ---
    def test_30_reject_non_1d_or_empty_filter_signal(self):
        filt = MorphologyPreservingFilter()
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            filt.filter_signal(np.array([]))
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            filt.filter_signal(np.ones((5, 2)))

    # --- Test 31: Reject NaN and Inf in filter_signal ---
    def test_31_reject_nan_inf_filter_signal(self):
        filt = MorphologyPreservingFilter()
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            filt.filter_signal(np.array([10.0, np.nan, 12.0]))
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            filt.filter_signal(np.array([10.0, np.inf, 12.0]))

    # --- Test 32: Batch telemetry frame filtering with automatic numeric columns ---
    def test_32_filter_telemetry_frame_auto(self):
        filt = MorphologyPreservingFilter(window_length=5, poly_order=2)
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=10, freq="min"),
            "spo2": [98.0, 97.5, 98.0, 98.2, 97.8, 98.1, 98.0, 98.4, 98.1, 98.0],
            "hr": [72.0, 74.0, 71.0, 73.0, 75.0, 72.0, 74.0, 73.0, 72.0, 71.0],
        })
        out_df, results = filt.filter_telemetry_frame(df)
        assert isinstance(out_df, pd.DataFrame)
        assert "spo2" in results
        assert "hr" in results
        assert "timestamp" not in results

    # --- Test 33: Batch telemetry frame filtering with explicit columns ---
    def test_33_filter_telemetry_frame_explicit(self):
        filt = MorphologyPreservingFilter(window_length=5, poly_order=2)
        df = pd.DataFrame({
            "hr": [70.0, 71.0, 72.0, 73.0, 74.0, 75.0],
            "temp": [36.5, 36.6, 36.5, 36.7, 36.6, 36.5],
        })
        out_df, results = filt.filter_telemetry_frame(df, target_columns=["hr"])
        assert "hr" in results
        assert "temp" not in results

    # --- Test 34: Telemetry frame error handling for filter_telemetry_frame ---
    def test_34_filter_telemetry_frame_exceptions(self):
        filt = MorphologyPreservingFilter()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            filt.filter_telemetry_frame([1, 2, 3])
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            filt.filter_telemetry_frame(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            filt.filter_telemetry_frame(text_df)

        valid_df = pd.DataFrame({"hr": [70.0, 72.0, 74.0, 73.0, 75.0]})
        with pytest.raises(KeyError, match="Target column 'nonexistent' not present"):
            filt.filter_telemetry_frame(valid_df, target_columns=["nonexistent"])


class TestPhase3AdaptiveMotionCanceller:
    """
    DO-178C Level C Verification for Phase 3 AdaptiveMotionCanceller.
    Tests NLMS filter initialization, motion-artifact correlation reduction,
    boundary condition safety, dimensional validation, and batch multi-channel execution.
    """

    # --- Test 35: Default instantiation ---
    def test_35_default_instantiation(self):
        canceller = AdaptiveMotionCanceller()
        assert canceller.filter_order == 4
        assert canceller.mu == 0.05
        assert canceller.leakage == 0.999
        assert canceller.epsilon == 1e-6

    # --- Test 36: Custom valid parameters ---
    def test_36_custom_instantiation(self):
        canceller = AdaptiveMotionCanceller(
            filter_order=6,
            step_size_mu=0.1,
            leakage_factor=0.98,
            epsilon=1e-5,
        )
        assert canceller.filter_order == 6
        assert canceller.mu == 0.1
        assert canceller.leakage == 0.98

    # --- Test 37: Reject invalid parameters ---
    def test_37_reject_invalid_parameters(self):
        with pytest.raises(ValueError, match="filter_order must be an integer >= 1"):
            AdaptiveMotionCanceller(filter_order=0)
        with pytest.raises(ValueError, match="step_size_mu must be in"):
            AdaptiveMotionCanceller(step_size_mu=0.0)
        with pytest.raises(ValueError, match="step_size_mu must be in"):
            AdaptiveMotionCanceller(step_size_mu=0.6)
        with pytest.raises(ValueError, match="leakage_factor must be in"):
            AdaptiveMotionCanceller(leakage_factor=0.0)
        with pytest.raises(ValueError, match="leakage_factor must be in"):
            AdaptiveMotionCanceller(leakage_factor=1.5)
        with pytest.raises(ValueError, match="epsilon must be strictly positive"):
            AdaptiveMotionCanceller(epsilon=0.0)

    # --- Test 38: Pearson correlation edge cases (constant signals / short arrays) ---
    def test_38_correlation_edge_cases(self):
        canceller = AdaptiveMotionCanceller()
        # Single element or empty
        assert canceller._compute_correlation(np.array([1.0]), np.array([2.0])) == 0.0
        # Constant signals
        assert canceller._compute_correlation(np.ones(10), np.ones(10)) == 0.0
        # Normal correlated signals
        a = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        b = np.array([2.0, 4.0, 6.0, 8.0, 10.0])
        np.testing.assert_allclose(canceller._compute_correlation(a, b), 1.0, atol=1e-5)

    # --- Test 39: Short sequence <= filter_order passthrough safety ---
    def test_39_short_sequence_passthrough(self):
        canceller = AdaptiveMotionCanceller(filter_order=4)
        short_d = np.array([72.0, 73.0, 72.0])
        short_x = np.array([0.1, 0.2, 0.1])
        res = canceller.cancel_motion_artifact(short_d, short_x, channel_name="hr")
        assert isinstance(res, MotionCancellationResult)
        assert np.array_equal(res.cleaned_signal, short_d)
        assert res.artifact_suppression_ratio == 0.0

    # --- Test 40: Effective motion artifact cancellation on correlated signal ---
    def test_40_cancel_motion_artifact_effectiveness(self):
        canceller = AdaptiveMotionCanceller(filter_order=4, step_size_mu=0.1, leakage_factor=0.999)
        n = 200
        t = np.linspace(0, 10, n)
        # True clean physiological signal (e.g. ECG pulse wave)
        clean_vital = 75.0 + 3.0 * np.sin(2 * np.pi * 0.5 * t)
        # Astronaut treadmill motion acceleration
        motion_ref = 1.2 * np.sin(2 * np.pi * 1.5 * t) + 0.3 * np.cos(2 * np.pi * 3.0 * t)
        # Corrupted signal: physiological + motion artifact
        corrupted = clean_vital + 2.5 * motion_ref

        res = canceller.cancel_motion_artifact(corrupted, motion_ref, channel_name="heart_rate")
        assert len(res.cleaned_signal) == n
        # Correlation with motion artifact should be reduced
        assert abs(res.motion_correlation_after) < abs(res.motion_correlation_before)
        # Artifact suppression ratio should be positive
        assert res.artifact_suppression_ratio > 0.0

    # --- Test 41: Support list and pandas Series types ---
    def test_41_input_types_support(self):
        canceller = AdaptiveMotionCanceller(filter_order=2)
        # Lists
        res_list = canceller.cancel_motion_artifact(
            [70.0, 71.0, 72.0, 73.0, 74.0, 75.0],
            [0.1, 0.2, 0.3, 0.2, 0.1, 0.0],
        )
        assert isinstance(res_list.cleaned_signal, np.ndarray)

        # Series
        s_d = pd.Series([120.0, 122.0, 121.0, 123.0, 122.0, 124.0])
        s_x = pd.Series([0.05, 0.1, 0.15, 0.1, 0.05, 0.0])
        res_series = canceller.cancel_motion_artifact(s_d, s_x)
        assert len(res_series.cleaned_signal) == len(s_d)

    # --- Test 42: Reject invalid types in cancel_motion_artifact ---
    def test_42_reject_invalid_types_cancel_motion(self):
        canceller = AdaptiveMotionCanceller()
        valid = np.ones(10)
        with pytest.raises(TypeError, match="Unsupported primary_signal type"):
            canceller.cancel_motion_artifact("invalid", valid)
        with pytest.raises(TypeError, match="Unsupported reference_motion type"):
            canceller.cancel_motion_artifact(valid, "invalid")

    # --- Test 43: Dimension mismatch and non-1D empty rejection ---
    def test_43_reject_dimension_mismatch_and_empty(self):
        canceller = AdaptiveMotionCanceller()
        # Empty
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            canceller.cancel_motion_artifact(np.array([]), np.array([1.0]))
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            canceller.cancel_motion_artifact(np.array([1.0]), np.array([]))
        # Length mismatch
        with pytest.raises(ValueError, match="Dimension mismatch"):
            canceller.cancel_motion_artifact(np.ones(10), np.ones(8))

    # --- Test 44: Reject NaN and Inf in cancel_motion_artifact ---
    def test_44_reject_nan_inf_motion(self):
        canceller = AdaptiveMotionCanceller()
        nan_arr = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        inf_arr = np.array([1.0, np.inf, 3.0, 4.0, 5.0])
        valid = np.ones(5)
        with pytest.raises(ValueError, match="contain NaN or Inf"):
            canceller.cancel_motion_artifact(nan_arr, valid)
        with pytest.raises(ValueError, match="contain NaN or Inf"):
            canceller.cancel_motion_artifact(valid, inf_arr)

    # --- Test 45: Batch frame cancellation with auto numeric columns ---
    def test_45_cancel_motion_telemetry_frame_auto(self):
        canceller = AdaptiveMotionCanceller(filter_order=2)
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=10, freq="min"),
            "accel_z_mag": [0.1, 0.5, 1.2, 0.8, 0.2, 0.1, 0.0, 0.4, 0.9, 0.3],
            "ecg_hr": [72.0, 78.0, 85.0, 80.0, 74.0, 72.0, 71.0, 75.0, 82.0, 73.0],
            "spo2": [98.0, 97.0, 96.0, 97.0, 98.0, 98.0, 98.0, 97.0, 96.0, 98.0],
        })
        out_df, results = canceller.cancel_motion_telemetry_frame(
            telemetry_df=df,
            reference_column="accel_z_mag",
        )
        assert isinstance(out_df, pd.DataFrame)
        assert "ecg_hr" in results
        assert "spo2" in results
        assert "accel_z_mag" not in results
        assert "timestamp" not in results

    # --- Test 46: Batch frame cancellation with explicit columns ---
    def test_46_cancel_motion_telemetry_frame_explicit(self):
        canceller = AdaptiveMotionCanceller(filter_order=2)
        df = pd.DataFrame({
            "motion_ref": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "hr": [70.0, 72.0, 74.0, 76.0, 78.0, 80.0],
            "temp": [36.5, 36.6, 36.5, 36.7, 36.6, 36.5],
        })
        out_df, results = canceller.cancel_motion_telemetry_frame(
            df,
            reference_column="motion_ref",
            target_columns=["hr"],
        )
        assert "hr" in results
        assert "temp" not in results

    # --- Test 47: Error handling in cancel_motion_telemetry_frame ---
    def test_47_cancel_motion_telemetry_frame_exceptions(self):
        canceller = AdaptiveMotionCanceller()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            canceller.cancel_motion_telemetry_frame("invalid", reference_column="accel")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            canceller.cancel_motion_telemetry_frame(pd.DataFrame(), reference_column="accel")

        valid_df = pd.DataFrame({"accel": [1.0, 2.0], "hr": [70.0, 72.0]})
        with pytest.raises(KeyError, match="not found in telemetry DataFrame"):
            canceller.cancel_motion_telemetry_frame(valid_df, reference_column="missing_ref")

        no_target_df = pd.DataFrame({"accel": [1.0, 2.0]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            canceller.cancel_motion_telemetry_frame(no_target_df, reference_column="accel")

        with pytest.raises(KeyError, match="Target column 'missing_target' not present"):
            canceller.cancel_motion_telemetry_frame(
                valid_df,
                reference_column="accel",
                target_columns=["missing_target"],
            )


class TestPhase4SignalQualityEvaluator:
    """
    DO-178C Level C Verification for Phase 4 SignalQualityEvaluator.
    Tests Kurtosis, Skewness, Variance metrics, decoupling detection,
    SQI bounds [0.0, 1.0], exception handling, and frame batch processing.
    """

    # --- Test 48: Default initialization ---
    def test_48_default_instantiation(self):
        evaluator = SignalQualityEvaluator()
        assert evaluator.min_valid_sqi == 0.50
        assert evaluator.decoupling_threshold == 1e-4

    # --- Test 49: Custom valid parameters ---
    def test_49_custom_instantiation(self):
        evaluator = SignalQualityEvaluator(min_valid_sqi=0.65, decoupling_variance_threshold=1e-5)
        assert evaluator.min_valid_sqi == 0.65
        assert evaluator.decoupling_threshold == 1e-5

    # --- Test 50: Reject invalid initialization parameters ---
    def test_50_reject_invalid_parameters(self):
        with pytest.raises(ValueError, match="min_valid_sqi must be in"):
            SignalQualityEvaluator(min_valid_sqi=0.0)
        with pytest.raises(ValueError, match="min_valid_sqi must be in"):
            SignalQualityEvaluator(min_valid_sqi=1.0)
        with pytest.raises(ValueError, match="decoupling_variance_threshold must be strictly positive"):
            SignalQualityEvaluator(decoupling_variance_threshold=0.0)
        with pytest.raises(ValueError, match="decoupling_variance_threshold must be strictly positive"):
            SignalQualityEvaluator(decoupling_variance_threshold=-1e-4)

    # --- Test 51: Short sequence (< 4 samples) safe evaluation ---
    def test_51_short_sequence_handling(self):
        evaluator = SignalQualityEvaluator()
        res = evaluator.evaluate_sqi(np.array([72.0, 73.0, 72.0]), channel_name="hr")
        assert isinstance(res, SQIEvaluationResult)
        assert res.overall_sqi == 0.50
        assert res.quality_grade == "ACCEPTABLE"
        assert res.is_sensor_decoupled is False

    # --- Test 52: Sensor decoupled flatline detection ---
    def test_52_sensor_decoupled_detection(self):
        evaluator = SignalQualityEvaluator(decoupling_variance_threshold=1e-4)
        # Constant flatline signal (sensor detached or wire cut)
        flatline = np.ones(50) * 80.0
        res = evaluator.evaluate_sqi(flatline, channel_name="ecg_lead_i")
        assert res.is_sensor_decoupled is True
        assert res.is_telemetry_valid is False
        assert res.overall_sqi == 0.0
        assert res.quality_grade == "DECOUPLED"

    # --- Test 53: High quality physiological waveform (Grade: EXCELLENT) ---
    def test_53_excellent_quality_signal(self):
        evaluator = SignalQualityEvaluator(min_valid_sqi=0.50)
        np.random.seed(42)
        # Clean gaussian physiological variation around mean 75 bpm
        good_signal = 75.0 + np.random.normal(0, 1.0, 200)
        res = evaluator.evaluate_sqi(good_signal, channel_name="ppg")
        assert res.overall_sqi >= 0.80
        assert res.quality_grade == "EXCELLENT"
        assert res.is_telemetry_valid is True

    # --- Test 54: Degraded quality signal with extreme skewness and kurtosis ---
    def test_54_degraded_quality_signal(self):
        evaluator = SignalQualityEvaluator(min_valid_sqi=0.60)
        # Signal with massive impulsive outlier spikes
        noisy_arr = np.ones(100) * 70.0
        noisy_arr[10:15] = 500.0  # Massive non-physiological spike
        res = evaluator.evaluate_sqi(noisy_arr, channel_name="bp")
        assert res.is_telemetry_valid is False
        assert res.quality_grade == "DEGRADED"

    # --- Test 55: Acceptable quality signal ---
    def test_55_acceptable_quality_signal(self):
        evaluator = SignalQualityEvaluator(min_valid_sqi=0.50)
        # Construct signal that specifically lands in [0.50, 0.80)
        x = np.linspace(0, 10, 100)
        arr = np.sin(x) * 15.0 + 80.0
        res = evaluator.evaluate_sqi(arr, channel_name="temp")
        assert 0.50 <= res.overall_sqi < 0.80
        assert res.quality_grade == "ACCEPTABLE"

    # --- Test 56: Support list and pandas Series types ---
    def test_56_input_types_support(self):
        evaluator = SignalQualityEvaluator()
        # List
        res_list = evaluator.evaluate_sqi([70.0, 72.0, 71.0, 73.0, 72.0, 74.0, 71.0, 73.0])
        assert isinstance(res_list.overall_sqi, float)
        # Series
        s = pd.Series([98.0, 97.0, 98.0, 99.0, 98.0, 97.0, 98.0, 99.0])
        res_series = evaluator.evaluate_sqi(s)
        assert isinstance(res_series.overall_sqi, float)

    # --- Test 57: Rejection of invalid types, dimensions, and NaN/Inf ---
    def test_57_reject_invalid_inputs(self):
        evaluator = SignalQualityEvaluator()
        with pytest.raises(TypeError, match="Unsupported signal type"):
            evaluator.evaluate_sqi("invalid_string")
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            evaluator.evaluate_sqi(np.array([]))
        with pytest.raises(ValueError, match="must be a non-empty 1D sequence"):
            evaluator.evaluate_sqi(np.ones((5, 5)))
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            evaluator.evaluate_sqi(np.array([70.0, np.nan, 72.0, 74.0]))
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            evaluator.evaluate_sqi(np.array([70.0, np.inf, 72.0, 74.0]))

    # --- Test 58: Frame evaluation with automatic numeric columns ---
    def test_58_evaluate_telemetry_frame_auto(self):
        evaluator = SignalQualityEvaluator(min_valid_sqi=0.50)
        np.random.seed(42)
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=50, freq="min"),
            "hr": 75.0 + np.random.normal(0, 1.0, 50),
            "spo2": 98.0 + np.random.normal(0, 0.5, 50),
        })
        results, mean_sqi, frame_valid = evaluator.evaluate_telemetry_frame(df)
        assert "hr" in results
        assert "spo2" in results
        assert "timestamp" not in results
        assert 0.0 <= mean_sqi <= 1.0
        assert frame_valid is True

    # --- Test 59: Frame evaluation with explicit columns ---
    def test_59_evaluate_telemetry_frame_explicit(self):
        evaluator = SignalQualityEvaluator()
        df = pd.DataFrame({
            "hr": [70.0, 72.0, 71.0, 73.0, 72.0, 74.0],
            "aux": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
        })
        results, mean_sqi, frame_valid = evaluator.evaluate_telemetry_frame(df, target_columns=["hr"])
        assert "hr" in results
        assert "aux" not in results

    # --- Test 60: Error handling in evaluate_telemetry_frame ---
    def test_60_evaluate_telemetry_frame_exceptions(self):
        evaluator = SignalQualityEvaluator()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            evaluator.evaluate_telemetry_frame("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            evaluator.evaluate_telemetry_frame(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            evaluator.evaluate_telemetry_frame(text_df)

        valid_df = pd.DataFrame({"hr": [70.0, 72.0, 74.0, 73.0, 75.0]})
        with pytest.raises(KeyError, match="Target column 'nonexistent' not present"):
            evaluator.evaluate_telemetry_frame(valid_df, target_columns=["nonexistent"])


class TestPhase5StabilizedFrameExporter:
    """
    DO-178C Level C Verification for Phase 5 StabilizedFrameExporter.
    Tests end-to-end multi-stage pipeline orchestration, contract schema,
    motion reference integration, numerical scrub branches, and exception safety.
    """

    # --- Test 61: Default instantiation ---
    def test_61_default_instantiation(self):
        exporter = StabilizedFrameExporter()
        assert isinstance(exporter.drift_comp, BaselineDriftCompensator)
        assert isinstance(exporter.noise_filt, MorphologyPreservingFilter)
        assert isinstance(exporter.motion_canc, AdaptiveMotionCanceller)
        assert isinstance(exporter.sqi_eval, SignalQualityEvaluator)

    # --- Test 62: Custom subcomponents instantiation ---
    def test_62_custom_subcomponents_instantiation(self):
        dc = BaselineDriftCompensator(drift_cutoff_window_sec=5)
        nf = MorphologyPreservingFilter(window_length=5)
        mc = AdaptiveMotionCanceller(filter_order=2)
        sq = SignalQualityEvaluator(min_valid_sqi=0.60)

        exporter = StabilizedFrameExporter(
            drift_compensator=dc,
            noise_filter=nf,
            motion_canceller=mc,
            sqi_evaluator=sq,
        )
        assert exporter.drift_comp == dc
        assert exporter.noise_filt == nf
        assert exporter.motion_canc == mc
        assert exporter.sqi_eval == sq

    # --- Test 63: Full end-to-end pipeline execution with motion reference ---
    def test_63_full_pipeline_with_motion(self):
        exporter = StabilizedFrameExporter()
        n = 50
        np.random.seed(42)
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=n, freq="min"),
            "accel_mag": 0.2 * np.sin(np.linspace(0, 10, n)),
            "heart_rate": 75.0 + 2.0 * np.sin(np.linspace(0, 5, n)) + np.random.normal(0, 0.5, n),
            "spo2": 98.0 + np.random.normal(0, 0.2, n),
        })

        contract = exporter.process_and_export_frame(
            raw_telemetry_df=df,
            reference_motion_col="accel_mag",
        )

        assert isinstance(contract, StabilizedFrameContract)
        assert isinstance(contract.stabilized_data, pd.DataFrame)
        assert isinstance(contract.tensor_matrix, np.ndarray)
        assert contract.tensor_matrix.shape == (n, 2)  # heart_rate, spo2
        assert "heart_rate" in contract.channel_sqi_map
        assert "spo2" in contract.channel_sqi_map
        assert "accel_mag" not in contract.channel_sqi_map
        assert contract.frame_mean_sqi > 0.50
        assert contract.is_telemetry_flight_ready is True
        assert contract.stabilization_metadata["motion_cancellation_applied"] is True

    # --- Test 64: Pipeline execution without motion reference ---
    def test_64_pipeline_without_motion(self):
        exporter = StabilizedFrameExporter()
        n = 30
        np.random.seed(42)
        df = pd.DataFrame({
            "hr": 70.0 + np.random.normal(0, 1.0, n),
            "bp": 120.0 + np.random.normal(0, 2.0, n),
        })
        contract = exporter.process_and_export_frame(df)
        assert contract.stabilization_metadata["motion_cancellation_applied"] is False
        assert contract.stabilization_metadata["mean_motion_suppression_ratio"] == 0.0

    # --- Test 65: Explicit vital columns selection ---
    def test_65_explicit_vital_columns(self):
        exporter = StabilizedFrameExporter()
        df = pd.DataFrame({
            "hr": [70.0, 71.0, 72.0, 73.0, 74.0, 75.0, 76.0, 77.0],
            "temp": [36.5, 36.6, 36.5, 36.7, 36.6, 36.5, 36.6, 36.7],
            "unused_aux": [1, 2, 3, 4, 5, 6, 7, 8],
        })
        contract = exporter.process_and_export_frame(df, vital_columns=["hr", "temp"])
        assert contract.tensor_matrix.shape == (8, 2)
        assert "unused_aux" not in contract.channel_sqi_map

    # --- Test 66: Error handling on invalid inputs ---
    def test_66_exporter_exceptions(self):
        exporter = StabilizedFrameExporter()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            exporter.process_and_export_frame("invalid")
        with pytest.raises(ValueError, match="raw_telemetry_df cannot be empty"):
            exporter.process_and_export_frame(pd.DataFrame())

        # No numeric columns
        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric vital channels found"):
            exporter.process_and_export_frame(text_df)

        # Missing explicit column
        valid_df = pd.DataFrame({"hr": [70.0, 72.0, 74.0]})
        with pytest.raises(KeyError, match="Vital column 'missing_vital' not present"):
            exporter.process_and_export_frame(valid_df, vital_columns=["missing_vital"])

        # Missing motion column
        with pytest.raises(KeyError, match="Reference motion column 'missing_motion' not found"):
            exporter.process_and_export_frame(valid_df, reference_motion_col="missing_motion")

    # --- Test 67: Non-finite values fallback scrub branch ---
    def test_67_non_finite_scrub_branch(self):
        exporter = StabilizedFrameExporter()
        # Mock motion canceller that produces inf/nan to trigger the safety branch
        class CorruptingCanceller(AdaptiveMotionCanceller):
            def cancel_motion_telemetry_frame(self, telemetry_df, reference_column, target_columns=None):
                out_df = telemetry_df.copy()
                out_df.loc[0, "hr"] = np.inf
                dummy_res = MotionCancellationResult(
                    cleaned_signal=out_df["hr"].to_numpy(),
                    estimated_motion_artifact=np.zeros(len(out_df)),
                    final_filter_weights=np.zeros(4),
                    motion_correlation_before=0.0,
                    motion_correlation_after=0.0,
                    artifact_suppression_ratio=0.0,
                )
                return out_df, {"hr": dummy_res}

        # Mock SQI evaluator that doesn't reject NaN so we can test the downstream scrub branch
        class PermissiveSQIEvaluator(SignalQualityEvaluator):
            def evaluate_telemetry_frame(self, telemetry_df, target_columns=None):
                results = {
                    "hr": SQIEvaluationResult(
                        overall_sqi=0.8,
                        kurtosis_sqi=0.8,
                        skewness_sqi=0.8,
                        variance_sqi=0.8,
                        is_sensor_decoupled=False,
                        is_telemetry_valid=True,
                        quality_grade="EXCELLENT",
                    )
                }
                return results, 0.8, True

        corrupt_exporter = StabilizedFrameExporter(
            motion_canceller=CorruptingCanceller(),
            sqi_evaluator=PermissiveSQIEvaluator(),
        )
        df = pd.DataFrame({
            "accel": [0.1, 0.2, 0.1, 0.2, 0.1],
            "hr": [70.0, 72.0, 74.0, 72.0, 70.0],
        })
        contract = corrupt_exporter.process_and_export_frame(df, reference_motion_col="accel")
        # Scrub branch should replace Inf and set flight_ready to False
        assert np.all(np.isfinite(contract.tensor_matrix))
        assert contract.is_telemetry_flight_ready is False




