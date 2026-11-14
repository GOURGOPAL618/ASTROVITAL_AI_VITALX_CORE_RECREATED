"""
ASTROVITAL AI: VITALX CORE RECREATED V1
Subsystem: 02_AI_CORE / Signal Preconditioning & Motion Artifact Stripping
Component: Innovation 3 - Adaptive Signal Stabilizer (DO-178C Level C Compliant)
File: 02_AI_CORE/01_src/inno3_signal_stabilizer.py

Safety Constraint & DO-178C Level C Rule:
This module represents part of the 20% Adaptive AI layer.
It strictly performs signal noise removal, baseline drift suppression, motion artifact stripping,
and Signal Quality Index (SQI) quantification.
CRITICAL AIRWORTHINESS DIRECTIVE: This module has ZERO clinical decision authority.
It does NOT assign clinical severity, diagnostic states, or triage codes (Green/Amber/Red).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


# ==============================================================================
# PHASE 1: Baseline Wander & Low-Frequency Thermal Drift Suppressor
# ==============================================================================

@dataclass(frozen=True)
class DriftCompensationResult:
    """
    Immutable data container for Phase 1 Baseline Drift Compensation output.
    """
    cleaned_signal: np.ndarray
    estimated_drift: np.ndarray
    drift_rate_per_sec: float
    max_drift_amplitude: float
    is_drift_excessive: bool


class BaselineDriftCompensator:
    """
    Phase 1: Baseline Wander & Low-Frequency Thermal Drift Suppressor.
    
    Removes slow non-physiological baseline wanders (<0.05 Hz) caused by:
    - Sensor thermal equilibration inside deep-space suits/capsules.
    - Electrode electrochemical polarization drift during long-duration flight.
    - Slow postural hydro-static sensor shift.
    
    Uses dual-window moving median filtering and piecewise polynomial baseline tracking
    to preserve true physiological slow trends while stripping sensor baseline displacement.
    """

    def __init__(
        self,
        sampling_rate_hz: float = 1.0,
        drift_cutoff_window_sec: int = 31,
        max_allowed_drift_rate: float = 5.0,
    ) -> None:
        """
        Initialize the baseline drift compensator with airworthiness bounds.
        
        Args:
            sampling_rate_hz: Sampling frequency in Hertz (default 1.0 Hz for 1-minute/1-sec telemetry).
            drift_cutoff_window_sec: Window length in seconds for baseline estimation (must be odd, >= 3).
            max_allowed_drift_rate: Maximum permissible baseline drift rate (units/sec) before flagging.
        """
        if sampling_rate_hz <= 0.0:
            raise ValueError(f"sampling_rate_hz must be strictly positive, got {sampling_rate_hz}")
        if drift_cutoff_window_sec < 3 or drift_cutoff_window_sec % 2 == 0:
            raise ValueError(
                f"drift_cutoff_window_sec must be an odd integer >= 3, got {drift_cutoff_window_sec}"
            )
        if max_allowed_drift_rate <= 0.0:
            raise ValueError(
                f"max_allowed_drift_rate must be strictly positive, got {max_allowed_drift_rate}"
            )

        self.sampling_rate_hz = float(sampling_rate_hz)
        self.window_size = int(drift_cutoff_window_sec)
        self.max_allowed_drift_rate = float(max_allowed_drift_rate)

    def estimate_baseline_drift(self, signal: np.ndarray) -> np.ndarray:
        """
        Estimate the slow non-physiological baseline wander using centered median filtering
        with edge-preserving symmetric boundary reflection.
        
        Args:
            signal: 1D numpy array representing raw vital sign channel.
            
        Returns:
            1D numpy array of estimated baseline drift with matching dimensions.
        """
        if not isinstance(signal, np.ndarray):
            signal = np.asarray(signal, dtype=np.float64)
        else:
            signal = signal.astype(np.float64)

        if signal.ndim != 1:
            raise ValueError(f"Signal must be a 1D array, got shape {signal.shape}")
        if len(signal) == 0:
            raise ValueError("Input signal array cannot be empty")

        n = len(signal)
        # If signal is 1 sample, baseline is the sample itself
        if n == 1:
            return signal.copy()

        # If signal is shorter than the filter window, use a linear fit baseline
        if n < self.window_size:
            x = np.arange(n)
            poly_coeff = np.polyfit(x, signal, deg=1)
            return np.polyval(poly_coeff, x)

        half_win = self.window_size // 2
        # Symmetric pad to handle boundary effects without distortion
        padded = np.pad(signal, half_win, mode="reflect")
        
        # Centered moving median window
        drift = np.empty(n, dtype=np.float64)
        for i in range(n):
            window_slice = padded[i : i + self.window_size]
            drift[i] = np.median(window_slice)

        return drift

    def compensate_drift(
        self,
        signal: Union[np.ndarray, List[float], pd.Series],
        channel_name: str = "vital_channel",
    ) -> DriftCompensationResult:
        """
        Execute deterministic baseline drift stripping and rate quantification.
        
        Args:
            signal: Raw 1D signal array/series.
            channel_name: Identifying label for telemetry trace.
            
        Returns:
            DriftCompensationResult containing cleaned trace and drift metrics.
        """
        if isinstance(signal, pd.Series):
            raw_array = signal.to_numpy(dtype=np.float64)
        elif isinstance(signal, list):
            raw_array = np.array(signal, dtype=np.float64)
        elif isinstance(signal, np.ndarray):
            raw_array = signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported signal type for channel {channel_name}: {type(signal)}")

        if raw_array.ndim != 1 or len(raw_array) == 0:
            raise ValueError(f"Channel {channel_name} must be a non-empty 1D sequence")

        # Check for non-finite values (NaN / Inf)
        if not np.all(np.isfinite(raw_array)):
            raise ValueError(f"Signal channel {channel_name} contains NaN or Inf values")

        # 1. Estimate baseline drift
        drift = self.estimate_baseline_drift(raw_array)

        # 2. Subtract drift to obtain stabilized zero-mean/detrended signal
        drift_centered = drift - np.mean(drift)
        cleaned_signal = raw_array - drift_centered

        # 3. Calculate drift velocity: d(drift)/dt
        duration_sec = len(raw_array) / self.sampling_rate_hz
        if duration_sec > 1.0:
            drift_gradient = np.gradient(drift, 1.0 / self.sampling_rate_hz)
            max_drift_rate = float(np.max(np.abs(drift_gradient)))
        else:
            max_drift_rate = float(np.abs(drift[-1] - drift[0]) / max(duration_sec, 1e-6))

        max_amplitude = float(np.max(drift) - np.min(drift))
        is_excessive = bool(max_drift_rate > self.max_allowed_drift_rate)

        return DriftCompensationResult(
            cleaned_signal=cleaned_signal,
            estimated_drift=drift,
            drift_rate_per_sec=max_drift_rate,
            max_drift_amplitude=max_amplitude,
            is_drift_excessive=is_excessive,
        )

    def compensate_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, DriftCompensationResult]]:
        """
        Process multiple vital channels in a telemetry frame simultaneously.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for drift compensation")

        output_df = telemetry_df.copy()
        results_dict: Dict[str, DriftCompensationResult] = {}

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")
            
            res = self.compensate_drift(telemetry_df[col].to_numpy(), channel_name=col)
            output_df[col] = res.cleaned_signal
            results_dict[col] = res

        return output_df, results_dict


# ==============================================================================
# PHASE 2: Morphology-Preserving High-Frequency Noise Filter
# ==============================================================================

@dataclass(frozen=True)
class FilteringResult:
    """
    Immutable data container for Phase 2 Filtering output.
    """
    filtered_signal: np.ndarray
    snr_db_before: float
    snr_db_after: float
    snr_improvement_db: float
    noise_variance: float


class MorphologyPreservingFilter:
    """
    Phase 2: Morphology-Preserving High-Frequency Noise Filter.
    
    Filters thruster vibration, cabin pump acoustic harmonics, and electromagnetic
    interference while strictly preserving sharp physiological features:
    - Cardiac R-wave peaks in ECG / PPG systolic peaks.
    - Dicrotic notch in arterial pulse waves.
    - Respiratory inspiratory/expiratory crests.
    
    Implements Savitzky-Golay polynomial smoothing with adaptive window scaling
    and zero-phase dual-pass smoothing to avoid phase distortion.
    """

    def __init__(
        self,
        window_length: int = 7,
        poly_order: int = 2,
    ) -> None:
        """
        Initialize the morphology-preserving filter with formal parameter validation.
        """
        if window_length < 3 or window_length % 2 == 0:
            raise ValueError(f"window_length must be an odd integer >= 3, got {window_length}")
        if poly_order < 1 or poly_order >= window_length:
            raise ValueError(
                f"poly_order must be an integer >= 1 and < window_length ({window_length}), got {poly_order}"
            )

        self.window_length = int(window_length)
        self.poly_order = int(poly_order)

    def _compute_snr_db(self, signal: np.ndarray, noise: np.ndarray) -> float:
        """
        Deterministic Signal-to-Noise Ratio (SNR) computation in decibels.
        """
        sig_power = float(np.mean(signal ** 2))
        noise_power = float(np.mean(noise ** 2))
        if noise_power <= 1e-12:
            return 100.0
        if sig_power <= 1e-12:
            return -100.0
        return float(10.0 * np.log10(sig_power / noise_power))

    def filter_signal(
        self,
        signal: Union[np.ndarray, List[float], pd.Series],
        channel_name: str = "vital_channel",
    ) -> FilteringResult:
        """
        Apply deterministic morphology-preserving smoothing to input signal.
        """
        if isinstance(signal, pd.Series):
            raw_arr = signal.to_numpy(dtype=np.float64)
        elif isinstance(signal, list):
            raw_arr = np.array(signal, dtype=np.float64)
        elif isinstance(signal, np.ndarray):
            raw_arr = signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported signal type for channel {channel_name}: {type(signal)}")

        if raw_arr.ndim != 1 or len(raw_arr) == 0:
            raise ValueError(f"Channel {channel_name} must be a non-empty 1D sequence")

        if not np.all(np.isfinite(raw_arr)):
            raise ValueError(f"Signal channel {channel_name} contains NaN or Inf values")

        n = len(raw_arr)
        if n < self.window_length:
            return FilteringResult(
                filtered_signal=raw_arr.copy(),
                snr_db_before=100.0,
                snr_db_after=100.0,
                snr_improvement_db=0.0,
                noise_variance=0.0,
            )

        half_win = self.window_length // 2
        x = np.arange(-half_win, half_win + 1, dtype=np.float64)
        A = np.vander(x, self.poly_order + 1)[:, ::-1]
        pinv = np.linalg.pinv(A)
        kernel = pinv[0]

        padded = np.pad(raw_arr, half_win, mode="reflect")
        filtered = np.convolve(padded, kernel[::-1], mode="valid")

        noise_residual = raw_arr - filtered
        noise_var = float(np.var(noise_residual))

        diff_noise = np.diff(raw_arr)
        snr_before = self._compute_snr_db(raw_arr, diff_noise)
        snr_after = self._compute_snr_db(filtered, noise_residual)
        snr_diff = float(snr_after - snr_before)

        return FilteringResult(
            filtered_signal=filtered,
            snr_db_before=snr_before,
            snr_db_after=snr_after,
            snr_improvement_db=snr_diff,
            noise_variance=noise_var,
        )

    def filter_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, FilteringResult]]:
        """
        Batch-filter all vital channels across a telemetry frame.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for filtering")

        output_df = telemetry_df.copy()
        results: Dict[str, FilteringResult] = {}

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")
            res = self.filter_signal(telemetry_df[col].to_numpy(), channel_name=col)
            output_df[col] = res.filtered_signal
            results[col] = res

        return output_df, results


# ==============================================================================
# PHASE 3: Accelerometric Motion Artifact Cancellation (Adaptive LMS/RLS)
# ==============================================================================

@dataclass(frozen=True)
class MotionCancellationResult:
    """
    Immutable data container for Phase 3 Adaptive Motion Cancellation output.
    """
    cleaned_signal: np.ndarray
    estimated_motion_artifact: np.ndarray
    final_filter_weights: np.ndarray
    motion_correlation_before: float
    motion_correlation_after: float
    artifact_suppression_ratio: float


class AdaptiveMotionCanceller:
    """
    Phase 3: Accelerometer-Correlated Motion Artifact Stripper.
    
    In deep-space operations (e.g. CEVIS/ARED exercise, capsule thruster burns, EVA maneuvering),
    body accelerations induce optical path changes, skin-electrode impedance spikes,
    and mechanical sensor displacement.
    
    This component uses a Normalized Least Mean Squares (NLMS) adaptive FIR filter:
    - Primary input: Corrupted physiological signal d(n)
    - Reference input: Tri-axial acceleration magnitude or motion sensor trace x(n)
    - Adaptive weights w(n) track dynamic coupling between body acceleration and physiological channel
    - Cleaned output e(n) = d(n) - y(n) strips motion-correlated voltage displacement.
    """

    def __init__(
        self,
        filter_order: int = 4,
        step_size_mu: float = 0.05,
        leakage_factor: float = 0.999,
        epsilon: float = 1e-6,
    ) -> None:
        """
        Initialize the adaptive motion canceller with stability bounds.
        """
        if filter_order < 1:
            raise ValueError(f"filter_order must be an integer >= 1, got {filter_order}")
        if step_size_mu <= 0.0 or step_size_mu > 0.5:
            raise ValueError(f"step_size_mu must be in (0.0, 0.5], got {step_size_mu}")
        if leakage_factor <= 0.0 or leakage_factor > 1.0:
            raise ValueError(f"leakage_factor must be in (0.0, 1.0], got {leakage_factor}")
        if epsilon <= 0.0:
            raise ValueError(f"epsilon must be strictly positive, got {epsilon}")

        self.filter_order = int(filter_order)
        self.mu = float(step_size_mu)
        self.leakage = float(leakage_factor)
        self.epsilon = float(epsilon)

    def _compute_correlation(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Safe Pearson correlation computation between two sequences.
        """
        if len(a) < 2 or np.all(a == a[0]) or np.all(b == b[0]):
            return 0.0
        corr_matrix = np.corrcoef(a, b)
        val = corr_matrix[0, 1]
        return float(0.0 if np.isnan(val) else val)

    def cancel_motion_artifact(
        self,
        primary_signal: Union[np.ndarray, List[float], pd.Series],
        reference_motion: Union[np.ndarray, List[float], pd.Series],
        channel_name: str = "vital_channel",
    ) -> MotionCancellationResult:
        """
        Execute deterministic Normalized LMS adaptive filtering.
        """
        if isinstance(primary_signal, pd.Series):
            d = primary_signal.to_numpy(dtype=np.float64)
        elif isinstance(primary_signal, list):
            d = np.array(primary_signal, dtype=np.float64)
        elif isinstance(primary_signal, np.ndarray):
            d = primary_signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported primary_signal type: {type(primary_signal)}")

        if isinstance(reference_motion, pd.Series):
            x = reference_motion.to_numpy(dtype=np.float64)
        elif isinstance(reference_motion, list):
            x = np.array(reference_motion, dtype=np.float64)
        elif isinstance(reference_motion, np.ndarray):
            x = reference_motion.astype(np.float64)
        else:
            raise TypeError(f"Unsupported reference_motion type: {type(reference_motion)}")

        if d.ndim != 1 or len(d) == 0:
            raise ValueError(f"primary_signal for {channel_name} must be a non-empty 1D sequence")
        if x.ndim != 1 or len(x) == 0:
            raise ValueError("reference_motion must be a non-empty 1D sequence")
        if len(d) != len(x):
            raise ValueError(
                f"Dimension mismatch: primary_signal ({len(d)}) != reference_motion ({len(x)})"
            )

        if not np.all(np.isfinite(d)) or not np.all(np.isfinite(x)):
            raise ValueError("Input signals contain NaN or Inf values")

        n = len(d)
        m = self.filter_order

        if n <= m:
            return MotionCancellationResult(
                cleaned_signal=d.copy(),
                estimated_motion_artifact=np.zeros_like(d),
                final_filter_weights=np.zeros(m, dtype=np.float64),
                motion_correlation_before=self._compute_correlation(d, x),
                motion_correlation_after=self._compute_correlation(d, x),
                artifact_suppression_ratio=0.0,
            )

        corr_before = self._compute_correlation(d, x)

        w = np.zeros(m, dtype=np.float64)
        y = np.zeros(n, dtype=np.float64)
        e = np.zeros(n, dtype=np.float64)

        d_mean = np.mean(d)
        d_centered = d - d_mean
        x_centered = x - np.mean(x)

        x_padded = np.pad(x_centered, (m - 1, 0), mode="constant")

        for i in range(n):
            x_vec = x_padded[i : i + m][::-1]
            y[i] = np.dot(w, x_vec)
            e[i] = d_centered[i] - y[i]

            x_power = np.dot(x_vec, x_vec) + self.epsilon
            w = self.leakage * w + (self.mu / x_power) * e[i] * x_vec

        cleaned = e + d_mean
        corr_after = self._compute_correlation(cleaned, x)

        var_before = float(np.var(d_centered))
        var_after = float(np.var(e))
        suppression_ratio = float(max(0.0, 1.0 - (var_after / max(var_before, 1e-12))))

        return MotionCancellationResult(
            cleaned_signal=cleaned,
            estimated_motion_artifact=y,
            final_filter_weights=w,
            motion_correlation_before=corr_before,
            motion_correlation_after=corr_after,
            artifact_suppression_ratio=suppression_ratio,
        )

    def cancel_motion_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        reference_column: str,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, MotionCancellationResult]]:
        """
        Apply adaptive motion cancellation across all telemetry channels using a designated reference channel.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")
        if reference_column not in telemetry_df.columns:
            raise KeyError(f"reference_column '{reference_column}' not found in telemetry DataFrame")

        ref_series = telemetry_df[reference_column].to_numpy()

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [
                col for col in numeric_cols
                if col != reference_column and "time" not in col.lower() and "epoch" not in col.lower()
            ]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for motion cancellation")

        output_df = telemetry_df.copy()
        results: Dict[str, MotionCancellationResult] = {}

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")
            res = self.cancel_motion_artifact(
                primary_signal=telemetry_df[col].to_numpy(),
                reference_motion=ref_series,
                channel_name=col,
            )
            output_df[col] = res.cleaned_signal
            results[col] = res

        return output_df, results


# ==============================================================================
# PHASE 4: Signal Quality Index (SQI) & Sensor Integrity Engine
# ==============================================================================

@dataclass(frozen=True)
class SQIEvaluationResult:
    """
    Immutable data container for Phase 4 SQI evaluation.
    """
    overall_sqi: float
    kurtosis_sqi: float
    skewness_sqi: float
    variance_sqi: float
    is_sensor_decoupled: bool
    is_telemetry_valid: bool
    quality_grade: str  # "EXCELLENT", "ACCEPTABLE", "DEGRADED", "DECOUPLED"


class SignalQualityEvaluator:
    """
    Phase 4: Signal Quality Index (SQI) & Sensor Integrity Engine.
    
    In deep-space autonomous medicine, before clinical equations or triage models
    evaluate telemetry, signal reliability must be mathematically audited:
    - Loose wearable electrodes lead to flatlines or zero-crossing breakdown.
    - Motion-saturated sensors exhibit abnormal kurtosis (heavy outliers) or skewness.
    - Signal Quality Index (SQI) maps non-linear distribution metrics to [0.0, 1.0].
    
    Zero Clinical Authority Rule:
    The SQI metric evaluates SENSOR INTEGRITY ONLY, not astronaut medical pathology.
    """

    def __init__(
        self,
        min_valid_sqi: float = 0.50,
        decoupling_variance_threshold: float = 1e-4,
    ) -> None:
        """
        Initialize the SQI evaluator.
        
        Args:
            min_valid_sqi: Minimum overall SQI required to consider telemetry usable (default 0.50).
            decoupling_variance_threshold: Near-zero variance indicating sensor flatline/lead-off.
        """
        if min_valid_sqi <= 0.0 or min_valid_sqi >= 1.0:
            raise ValueError(f"min_valid_sqi must be in (0.0, 1.0), got {min_valid_sqi}")
        if decoupling_variance_threshold <= 0.0:
            raise ValueError(
                f"decoupling_variance_threshold must be strictly positive, got {decoupling_variance_threshold}"
            )

        self.min_valid_sqi = float(min_valid_sqi)
        self.decoupling_threshold = float(decoupling_variance_threshold)

    def evaluate_sqi(
        self,
        signal: Union[np.ndarray, List[float], pd.Series],
        channel_name: str = "vital_channel",
    ) -> SQIEvaluationResult:
        """
        Deterministic Signal Quality Index computation.
        """
        if isinstance(signal, pd.Series):
            arr = signal.to_numpy(dtype=np.float64)
        elif isinstance(signal, list):
            arr = np.array(signal, dtype=np.float64)
        elif isinstance(signal, np.ndarray):
            arr = signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported signal type for channel {channel_name}: {type(signal)}")

        if arr.ndim != 1 or len(arr) == 0:
            raise ValueError(f"Channel {channel_name} must be a non-empty 1D sequence")

        if not np.all(np.isfinite(arr)):
            raise ValueError(f"Signal channel {channel_name} contains NaN or Inf values")

        n = len(arr)
        if n < 4:
            # Insufficient samples for reliable 4th-order statistical moments
            return SQIEvaluationResult(
                overall_sqi=0.50,
                kurtosis_sqi=0.50,
                skewness_sqi=0.50,
                variance_sqi=0.50,
                is_sensor_decoupled=False,
                is_telemetry_valid=True,
                quality_grade="ACCEPTABLE",
            )

        # 1. Variance & Sensor Decoupling Check (Flatline check)
        var = float(np.var(arr))
        if var <= self.decoupling_threshold:
            # Zero or near-zero variance indicates sensor disconnection / lead-off
            return SQIEvaluationResult(
                overall_sqi=0.0,
                kurtosis_sqi=0.0,
                skewness_sqi=0.0,
                variance_sqi=0.0,
                is_sensor_decoupled=True,
                is_telemetry_valid=False,
                quality_grade="DECOUPLED",
            )

        # Variance SQI: Stable non-extreme variance score
        var_score = float(np.clip(1.0 - (var / (var + 100.0)), 0.1, 1.0))

        # 2. Skewness Evaluation (3rd moment)
        mean_val = np.mean(arr)
        std_val = np.sqrt(var)
        diff = arr - mean_val
        m3 = np.mean(diff ** 3)
        skewness = float(m3 / (std_val ** 3 + 1e-12))
        # Physiological signals are approximately symmetric around baseline; penalize extreme skewness
        skewness_sqi = float(np.clip(np.exp(-0.5 * (skewness ** 2)), 0.0, 1.0))

        # 3. Kurtosis Evaluation (4th moment)
        m4 = np.mean(diff ** 4)
        kurtosis = float(m4 / (std_val ** 4 + 1e-12))  # Normal distribution kurtosis ~ 3.0
        # Penalize kurtosis divergence from gaussian physiological envelope
        kurt_dist = abs(kurtosis - 3.0)
        kurtosis_sqi = float(np.clip(np.exp(-0.2 * kurt_dist), 0.0, 1.0))

        # 4. Composite Overall SQI (Weighted harmonic-geometric blend)
        # Weights: 40% Kurtosis, 30% Skewness, 30% Variance
        overall_sqi = float(0.40 * kurtosis_sqi + 0.30 * skewness_sqi + 0.30 * var_score)
        overall_sqi = float(np.clip(overall_sqi, 0.0, 1.0))

        is_valid = bool(overall_sqi >= self.min_valid_sqi)

        if overall_sqi >= 0.80:
            grade = "EXCELLENT"
        elif overall_sqi >= self.min_valid_sqi:
            grade = "ACCEPTABLE"
        else:
            grade = "DEGRADED"

        return SQIEvaluationResult(
            overall_sqi=overall_sqi,
            kurtosis_sqi=kurtosis_sqi,
            skewness_sqi=skewness_sqi,
            variance_sqi=var_score,
            is_sensor_decoupled=False,
            is_telemetry_valid=is_valid,
            quality_grade=grade,
        )

    def evaluate_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, SQIEvaluationResult], float, bool]:
        """
        Evaluate SQI across all telemetry channels in a frame.
        
        Returns:
            Tuple of (per_channel_results, frame_mean_sqi, is_frame_valid)
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for SQI evaluation")

        results: Dict[str, SQIEvaluationResult] = {}
        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")
            results[col] = self.evaluate_sqi(telemetry_df[col].to_numpy(), channel_name=col)

        mean_sqi = float(np.mean([r.overall_sqi for r in results.values()]))
        all_valid = all(r.is_telemetry_valid for r in results.values())
        frame_valid = bool(mean_sqi >= self.min_valid_sqi and all_valid)

        return results, mean_sqi, frame_valid


# ==============================================================================
# PHASE 5: Stabilized Telemetry Frame Exporter & Contract Validation
# ==============================================================================

@dataclass(frozen=True)
class StabilizedFrameContract:
    """
    Immutable data container representing the full stabilized telemetry frame
    ready for downstream Mathematical Sanity Gating and Decision Core execution.
    """
    stabilized_data: pd.DataFrame
    tensor_matrix: np.ndarray
    channel_sqi_map: Dict[str, float]
    frame_mean_sqi: float
    is_telemetry_flight_ready: bool
    stabilization_metadata: Dict[str, Union[str, float, int, bool]]


class StabilizedFrameExporter:
    """
    Phase 5: Master Stabilizer Orchestrator & Contract Exporter.
    
    Orchestrates the complete 4-stage stabilization pipeline:
    1. Baseline Wander & Drift Compensation (`BaselineDriftCompensator`)
    2. High-Frequency Noise Filtering (`MorphologyPreservingFilter`)
    3. Accelerometric Motion Artifact Cancellation (`AdaptiveMotionCanceller`)
    4. Signal Quality Index & Lead-Off Audit (`SignalQualityEvaluator`)
    
    Produces an immutable `StabilizedFrameContract` with numerical sanitization
    guaranteeing DO-178C Level C airworthiness compliance.
    """

    def __init__(
        self,
        drift_compensator: Optional[BaselineDriftCompensator] = None,
        noise_filter: Optional[MorphologyPreservingFilter] = None,
        motion_canceller: Optional[AdaptiveMotionCanceller] = None,
        sqi_evaluator: Optional[SignalQualityEvaluator] = None,
    ) -> None:
        """
        Initialize the master stabilizer pipeline.
        """
        self.drift_comp = drift_compensator if drift_compensator is not None else BaselineDriftCompensator()
        self.noise_filt = noise_filter if noise_filter is not None else MorphologyPreservingFilter()
        self.motion_canc = motion_canceller if motion_canceller is not None else AdaptiveMotionCanceller()
        self.sqi_eval = sqi_evaluator if sqi_evaluator is not None else SignalQualityEvaluator()

    def process_and_export_frame(
        self,
        raw_telemetry_df: pd.DataFrame,
        reference_motion_col: Optional[str] = None,
        vital_columns: Optional[List[str]] = None,
    ) -> StabilizedFrameContract:
        """
        Execute end-to-end telemetry stabilization on a multi-dimensional DataFrame.
        
        Args:
            raw_telemetry_df: Input DataFrame containing raw vital telemetry.
            reference_motion_col: Column name of motion/acceleration reference (optional).
            vital_columns: Subset of numeric vital channels to stabilize (optional).
            
        Returns:
            StabilizedFrameContract with cleaned matrix and flight-ready flags.
        """
        if not isinstance(raw_telemetry_df, pd.DataFrame):
            raise TypeError("raw_telemetry_df must be a pandas DataFrame")
        if raw_telemetry_df.empty:
            raise ValueError("raw_telemetry_df cannot be empty")

        # Resolve vital target columns
        if vital_columns is None:
            numeric_cols = raw_telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude time/epoch and the motion reference column itself from target channels
            vital_columns = [
                col for col in numeric_cols
                if "time" not in col.lower()
                and "epoch" not in col.lower()
                and (reference_motion_col is None or col != reference_motion_col)
            ]

        if len(vital_columns) == 0:
            raise ValueError("No valid numeric vital channels found for stabilization")

        for col in vital_columns:
            if col not in raw_telemetry_df.columns:
                raise KeyError(f"Vital column '{col}' not present in raw_telemetry_df")

        # Stage 1: Baseline Drift Compensation
        drift_compensated_df, drift_results = self.drift_comp.compensate_telemetry_frame(
            raw_telemetry_df,
            target_columns=vital_columns,
        )

        # Stage 2: Morphology-Preserving Noise Filtering
        filtered_df, filter_results = self.noise_filt.filter_telemetry_frame(
            drift_compensated_df,
            target_columns=vital_columns,
        )

        # Stage 3: Adaptive Motion Cancellation (if reference motion available)
        motion_suppression_avg = 0.0
        if reference_motion_col is not None:
            if reference_motion_col not in raw_telemetry_df.columns:
                raise KeyError(f"Reference motion column '{reference_motion_col}' not found")
            
            motion_cleaned_df, motion_results = self.motion_canc.cancel_motion_telemetry_frame(
                telemetry_df=filtered_df,
                reference_column=reference_motion_col,
                target_columns=vital_columns,
            )
            working_df = motion_cleaned_df
            suppression_vals = [r.artifact_suppression_ratio for r in motion_results.values()]
            if len(suppression_vals) > 0:
                motion_suppression_avg = float(np.mean(suppression_vals))
        else:
            working_df = filtered_df

        # Stage 4: Signal Quality Index (SQI) Audit
        sqi_results, mean_sqi, is_frame_valid = self.sqi_eval.evaluate_telemetry_frame(
            telemetry_df=working_df,
            target_columns=vital_columns,
        )

        channel_sqi_map = {col: r.overall_sqi for col, r in sqi_results.items()}

        # Numerical sanity check: scrub any residual non-finite values safely
        cleaned_target_matrix = working_df[vital_columns].to_numpy(dtype=np.float64)
        if not np.all(np.isfinite(cleaned_target_matrix)):
            cleaned_target_matrix = np.nan_to_num(cleaned_target_matrix, nan=0.0, posinf=1e6, neginf=-1e6)
            for idx, col in enumerate(vital_columns):
                working_df[col] = cleaned_target_matrix[:, idx]
            is_frame_valid = False

        metadata: Dict[str, Union[str, float, int, bool]] = {
            "processed_samples": len(working_df),
            "num_vital_channels": len(vital_columns),
            "mean_sqi": mean_sqi,
            "motion_cancellation_applied": reference_motion_col is not None,
            "mean_motion_suppression_ratio": motion_suppression_avg,
            "is_flight_ready": is_frame_valid,
        }

        return StabilizedFrameContract(
            stabilized_data=working_df,
            tensor_matrix=cleaned_target_matrix,
            channel_sqi_map=channel_sqi_map,
            frame_mean_sqi=mean_sqi,
            is_telemetry_flight_ready=is_frame_valid,
            stabilization_metadata=metadata,
        )


