"""
ASTROVITAL AI: VITALX CORE RECREATED V1
Subsystem: 02_AI_CORE / Dynamic Telemetry Sensitivity & Prioritization
Component: Innovation 6 - Biomarker Sensitivity Ranker (DO-178C Level C Compliant)
File: 02_AI_CORE/01_src/inno6_biomarker_ranker.py

Airworthiness Directive & Safety Philosophy:
This module represents the second component of the 20% Adaptive AI layer.
Its sole function is to quantify dynamic sensitivity weights (w_i) for telemetry channels
based on spaceflight mission phase, robust physiological deviation, and information entropy.
CRITICAL AIRWORTHINESS DIRECTIVE:
This module has ZERO clinical decision authority. It does NOT diagnose pathological conditions,
assess clinical risk scores, or emit triage codes (Green/Amber/Red).
All clinical decision rights reside exclusively in the 80% Biophysical Supreme Head (Decision Core).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


class MissionOperationalPhase(str, Enum):
    """
    Formal spaceflight operational phases with distinct physiological vulnerability profiles.
    Derived from NASA Human Research Program (HRP) spaceflight risks.
    """
    PRE_LAUNCH_RESTING = "PRE_LAUNCH_RESTING"
    LAUNCH_AND_ASCENT_G_STRESS = "LAUNCH_AND_ASCENT_G_STRESS"
    EARLY_MICROGRAVITY_FLUID_SHIFT = "EARLY_MICROGRAVITY_FLUID_SHIFT"
    INTRA_VEHICULAR_NOMINAL = "INTRA_VEHICULAR_NOMINAL"
    EXTRAVEHICULAR_ACTIVITY_EVA = "EXTRAVEHICULAR_ACTIVITY_EVA"
    HEAVY_EXERCISE_COUNTERMEASURE = "HEAVY_EXERCISE_COUNTERMEASURE"
    SOLAR_PARTICLE_EVENT_ALERT = "SOLAR_PARTICLE_EVENT_ALERT"
    LUNAR_EARTH_REENTRY_DECELERATION = "LUNAR_EARTH_REENTRY_DECELERATION"


# Standard 12-dimensional telemetry channel register
STANDARD_12D_CHANNELS: Tuple[str, ...] = (
    "heart_rate_bpm",
    "systolic_bp_mmhg",
    "diastolic_bp_mmhg",
    "spo2_percent",
    "core_temp_c",
    "resp_rate_bpm",
    "etco2_mmhg",
    "icp_est_mmhg",
    "cvp_mmhg",
    "co2_cabin_ppm",
    "cabin_pressure_psi",
    "ambient_temp_c",
)


# Mission-phase dynamic base prior weights (sum to 1.0 for each profile)
MISSION_PHASE_PRIOR_WEIGHTS: Dict[MissionOperationalPhase, Dict[str, float]] = {
    MissionOperationalPhase.PRE_LAUNCH_RESTING: {
        "heart_rate_bpm": 0.12, "systolic_bp_mmhg": 0.12, "diastolic_bp_mmhg": 0.10,
        "spo2_percent": 0.12, "core_temp_c": 0.08, "resp_rate_bpm": 0.10,
        "etco2_mmhg": 0.08, "icp_est_mmhg": 0.06, "cvp_mmhg": 0.06,
        "co2_cabin_ppm": 0.06, "cabin_pressure_psi": 0.05, "ambient_temp_c": 0.05,
    },
    MissionOperationalPhase.LAUNCH_AND_ASCENT_G_STRESS: {
        "heart_rate_bpm": 0.18, "systolic_bp_mmhg": 0.18, "diastolic_bp_mmhg": 0.14,
        "spo2_percent": 0.10, "core_temp_c": 0.04, "resp_rate_bpm": 0.10,
        "etco2_mmhg": 0.06, "icp_est_mmhg": 0.06, "cvp_mmhg": 0.06,
        "co2_cabin_ppm": 0.03, "cabin_pressure_psi": 0.03, "ambient_temp_c": 0.02,
    },
    MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT: {
        # ICP and CVP are paramount due to headward cephalad fluid translocation
        "heart_rate_bpm": 0.08, "systolic_bp_mmhg": 0.08, "diastolic_bp_mmhg": 0.06,
        "spo2_percent": 0.08, "core_temp_c": 0.06, "resp_rate_bpm": 0.06,
        "etco2_mmhg": 0.08, "icp_est_mmhg": 0.22, "cvp_mmhg": 0.18,
        "co2_cabin_ppm": 0.04, "cabin_pressure_psi": 0.03, "ambient_temp_c": 0.03,
    },
    MissionOperationalPhase.INTRA_VEHICULAR_NOMINAL: {
        "heart_rate_bpm": 0.10, "systolic_bp_mmhg": 0.10, "diastolic_bp_mmhg": 0.08,
        "spo2_percent": 0.10, "core_temp_c": 0.08, "resp_rate_bpm": 0.08,
        "etco2_mmhg": 0.08, "icp_est_mmhg": 0.12, "cvp_mmhg": 0.10,
        "co2_cabin_ppm": 0.06, "cabin_pressure_psi": 0.05, "ambient_temp_c": 0.05,
    },
    MissionOperationalPhase.EXTRAVEHICULAR_ACTIVITY_EVA: {
        # High metabolic output: RR, EtCO2, Core Temp, HR dominate
        "heart_rate_bpm": 0.16, "systolic_bp_mmhg": 0.10, "diastolic_bp_mmhg": 0.06,
        "spo2_percent": 0.12, "core_temp_c": 0.14, "resp_rate_bpm": 0.14,
        "etco2_mmhg": 0.14, "icp_est_mmhg": 0.04, "cvp_mmhg": 0.04,
        "co2_cabin_ppm": 0.02, "cabin_pressure_psi": 0.02, "ambient_temp_c": 0.02,
    },
    MissionOperationalPhase.HEAVY_EXERCISE_COUNTERMEASURE: {
        "heart_rate_bpm": 0.20, "systolic_bp_mmhg": 0.18, "diastolic_bp_mmhg": 0.12,
        "spo2_percent": 0.12, "core_temp_c": 0.10, "resp_rate_bpm": 0.12,
        "etco2_mmhg": 0.08, "icp_est_mmhg": 0.02, "cvp_mmhg": 0.02,
        "co2_cabin_ppm": 0.01, "cabin_pressure_psi": 0.01, "ambient_temp_c": 0.02,
    },
    MissionOperationalPhase.SOLAR_PARTICLE_EVENT_ALERT: {
        "heart_rate_bpm": 0.12, "systolic_bp_mmhg": 0.10, "diastolic_bp_mmhg": 0.08,
        "spo2_percent": 0.10, "core_temp_c": 0.10, "resp_rate_bpm": 0.08,
        "etco2_mmhg": 0.08, "icp_est_mmhg": 0.10, "cvp_mmhg": 0.08,
        "co2_cabin_ppm": 0.06, "cabin_pressure_psi": 0.05, "ambient_temp_c": 0.05,
    },
    MissionOperationalPhase.LUNAR_EARTH_REENTRY_DECELERATION: {
        # Cardiovascular deconditioning + Orthostatic hypotension risk
        "heart_rate_bpm": 0.18, "systolic_bp_mmhg": 0.18, "diastolic_bp_mmhg": 0.14,
        "spo2_percent": 0.10, "core_temp_c": 0.06, "resp_rate_bpm": 0.10,
        "etco2_mmhg": 0.06, "icp_est_mmhg": 0.08, "cvp_mmhg": 0.06,
        "co2_cabin_ppm": 0.01, "cabin_pressure_psi": 0.01, "ambient_temp_c": 0.02,
    },
}


@dataclass(frozen=True)
class ContextWeightResult:
    """
    Immutable data container for Phase 1 Mission Context weighting output.
    """
    phase: MissionOperationalPhase
    weight_dict: Dict[str, float]
    weight_vector: np.ndarray
    channel_order: Tuple[str, ...]
    is_normalized: bool


class MissionContextMatrix:
    """
    Phase 1: Mission-Phase Dynamic Context Matrix.
    
    Assigns prior baseline sensitivity weights based on operational mission phase.
    Ensures formal mathematical normalization (sum w_i = 1.0, w_i > 0) and
    provides deterministic lookup and custom profile overriding.
    """

    def __init__(
        self,
        custom_phase_priors: Optional[Dict[MissionOperationalPhase, Dict[str, float]]] = None,
        channels: Tuple[str, ...] = STANDARD_12D_CHANNELS,
    ) -> None:
        """
        Initialize the context matrix.
        """
        self.channels = tuple(channels)
        if len(self.channels) == 0:
            raise ValueError("channels tuple cannot be empty")

        self.priors: Dict[MissionOperationalPhase, Dict[str, float]] = (
            custom_phase_priors if custom_phase_priors is not None else MISSION_PHASE_PRIOR_WEIGHTS
        )
        if len(self.priors) == 0:
            raise ValueError("Priors dictionary cannot be empty")

    def resolve_phase(self, phase_input: Union[MissionOperationalPhase, str]) -> MissionOperationalPhase:
        """
        Resolve phase enum from string or enum value.
        """
        if isinstance(phase_input, MissionOperationalPhase):
            return phase_input

        if not isinstance(phase_input, str) or not phase_input.strip():
            raise ValueError("phase_input must be a non-empty string or MissionOperationalPhase enum")

        clean = phase_input.strip().upper()
        for p in MissionOperationalPhase:
            if p.value == clean or p.name == clean:
                return p

        raise KeyError(f"Unknown operational mission phase: '{phase_input}'")

    def get_phase_weights(
        self,
        phase: Union[MissionOperationalPhase, str],
        target_channels: Optional[List[str]] = None,
    ) -> ContextWeightResult:
        """
        Retrieve and normalize prior weights for a designated mission phase.
        
        Args:
            phase: Mission operational phase enum or string identifier.
            target_channels: Optional subset of channel names to restrict weighting.
            
        Returns:
            ContextWeightResult containing normalized weight map and vector.
        """
        resolved_phase = self.resolve_phase(phase)
        raw_map = self.priors[resolved_phase]

        selected_channels = tuple(target_channels) if target_channels is not None else self.channels
        if len(selected_channels) == 0:
            raise ValueError("selected_channels cannot be empty")

        raw_weights = []
        for ch in selected_channels:
            if ch in raw_map:
                raw_weights.append(float(raw_map[ch]))
            else:
                # Fallback to uniform default weight if channel not explicitly mapped
                raw_weights.append(1.0 / len(selected_channels))

        weight_arr = np.array(raw_weights, dtype=np.float64)
        total_sum = float(np.sum(weight_arr))

        if total_sum <= 0.0:
            # Degenerate case fallback: uniform distribution
            normalized_vec = np.ones(len(selected_channels), dtype=np.float64) / len(selected_channels)
        else:
            normalized_vec = weight_arr / total_sum

        weight_dict = {
            ch: float(normalized_vec[idx]) for idx, ch in enumerate(selected_channels)
        }

        # Check normalization precision
        is_norm = bool(np.isclose(float(np.sum(normalized_vec)), 1.0, atol=1e-6))

        return ContextWeightResult(
            phase=resolved_phase,
            weight_dict=weight_dict,
            weight_vector=normalized_vec,
            channel_order=selected_channels,
            is_normalized=is_norm,
        )


# ==============================================================================
# PHASE 2: Z-Score & Robust Deviation Scorer (PhysiologicalDeviationScorer)
# ==============================================================================

@dataclass(frozen=True)
class ChannelDeviationMetric:
    """
    Immutable representation of an individual biomarker's statistical deviation.
    """
    channel_name: str
    current_value: float
    baseline_median: float
    mad_scale: float
    robust_z_score: float
    deviation_urgency_weight: float


@dataclass(frozen=True)
class DeviationScoringResult:
    """
    Immutable result containing per-channel deviations and normalized deviation weight vector.
    """
    channel_metrics: Dict[str, ChannelDeviationMetric]
    deviation_weight_vector: np.ndarray
    channel_order: Tuple[str, ...]
    max_deviating_channel: str
    max_z_score: float


# Calibrated astronaut resting baselines (Apollo/ISS medical monitoring reference)
ASTRONAUT_RESTING_BASELINES: Dict[str, Tuple[float, float]] = {
    # channel_name: (baseline_median, baseline_mad_scale)
    "heart_rate_bpm": (72.0, 6.0),
    "systolic_bp_mmhg": (118.0, 8.0),
    "diastolic_bp_mmhg": (76.0, 5.0),
    "spo2_percent": (98.0, 1.0),
    "core_temp_c": (36.8, 0.3),
    "resp_rate_bpm": (14.0, 2.0),
    "etco2_mmhg": (38.0, 3.0),
    "icp_est_mmhg": (10.0, 2.0),
    "cvp_mmhg": (5.0, 1.5),
    "co2_cabin_ppm": (1000.0, 200.0),
    "cabin_pressure_psi": (14.7, 0.2),
    "ambient_temp_c": (22.0, 1.5),
}


class PhysiologicalDeviationScorer:
    """
    Phase 2: Z-Score & Robust Deviation Scorer.
    
    Quantifies how far each telemetry channel has deviated from the astronaut's
    individualized resting physiological baseline.
    
    Uses robust Median Absolute Deviation (MAD) scaling:
        Z_i = |x_i - baseline_median| / (1.4826 * MAD)
    
    Translates absolute Z-scores into non-linear clinical sensitivity weights
    using a sigmoidal saturation function, ensuring channels undergoing acute
    displacement receive higher dynamic analytical priority.
    """

    def __init__(
        self,
        reference_baselines: Optional[Dict[str, Tuple[float, float]]] = None,
        min_weight_floor: float = 0.02,
        z_score_saturation_limit: float = 6.0,
    ) -> None:
        """
        Initialize the deviation scorer with baselines and safety bounds.
        """
        if min_weight_floor <= 0.0 or min_weight_floor >= 0.5:
            raise ValueError(f"min_weight_floor must be in (0.0, 0.5), got {min_weight_floor}")
        if z_score_saturation_limit <= 1.0:
            raise ValueError(f"z_score_saturation_limit must be > 1.0, got {z_score_saturation_limit}")

        self.baselines: Dict[str, Tuple[float, float]] = (
            reference_baselines if reference_baselines is not None else ASTRONAUT_RESTING_BASELINES
        )
        if len(self.baselines) == 0:
            raise ValueError("Reference baselines dictionary cannot be empty")

        self.min_weight_floor = float(min_weight_floor)
        self.z_saturation = float(z_score_saturation_limit)

    def calculate_channel_z_score(
        self,
        channel_name: str,
        current_value: float,
    ) -> Tuple[float, float, float]:
        """
        Compute robust Z-score against registered baseline.
        
        Returns:
            Tuple of (robust_z_score, baseline_median, mad_scale)
        """
        if not np.isfinite(current_value):
            raise ValueError(f"current_value for {channel_name} must be finite, got {current_value}")

        clean = channel_name.strip().lower()
        if clean in self.baselines:
            med, mad = self.baselines[clean]
        else:
            # Fuzzy match
            matched = False
            for key, val in self.baselines.items():
                if key in clean or clean in key:
                    med, mad = val
                    matched = True
                    break
            if not matched:
                raise KeyError(f"No resting baseline registered for channel '{channel_name}'")

        if mad <= 0.0:
            mad = 1.0

        # Robust Z-score: difference divided by (1.4826 * MAD)
        denom = 1.4826 * mad
        z = abs(float(current_value) - med) / denom
        return float(z), float(med), float(mad)

    def score_telemetry_vector(
        self,
        current_values: Dict[str, float],
        target_channels: Optional[List[str]] = None,
    ) -> DeviationScoringResult:
        """
        Score an entire instantaneous telemetry vector and produce normalized deviation weights.
        
        Args:
            current_values: Dictionary of current biomarker readings.
            target_channels: Optional subset of channels to evaluate.
            
        Returns:
            DeviationScoringResult containing per-channel metrics and normalized weight vector.
        """
        if not isinstance(current_values, dict) or len(current_values) == 0:
            raise ValueError("current_values must be a non-empty dictionary")

        selected_channels = tuple(target_channels) if target_channels is not None else tuple(current_values.keys())
        if len(selected_channels) == 0:
            raise ValueError("selected_channels cannot be empty")

        metrics_map: Dict[str, ChannelDeviationMetric] = {}
        raw_weights = []
        max_ch = ""
        max_z = -1.0

        for ch in selected_channels:
            if ch not in current_values:
                raise KeyError(f"Target channel '{ch}' not present in current_values")

            val = float(current_values[ch])
            z, med, mad = self.calculate_channel_z_score(ch, val)

            # Sigmoidal urgency weight scaling: floor + (z / (1 + z / saturation))
            z_clamped = min(z, self.z_saturation)
            urgency = self.min_weight_floor + (z_clamped / (1.0 + (z_clamped / self.z_saturation)))

            raw_weights.append(urgency)
            if z > max_z:
                max_z = z
                max_ch = ch

            metrics_map[ch] = ChannelDeviationMetric(
                channel_name=ch,
                current_value=val,
                baseline_median=med,
                mad_scale=mad,
                robust_z_score=z,
                deviation_urgency_weight=urgency,
            )

        weight_arr = np.array(raw_weights, dtype=np.float64)
        total_sum = float(np.sum(weight_arr))
        normalized_weights = weight_arr / total_sum if total_sum > 0.0 else np.ones(len(selected_channels)) / len(selected_channels)

        # Update metrics_map with normalized urgency weight
        for idx, ch in enumerate(selected_channels):
            m = metrics_map[ch]
            metrics_map[ch] = ChannelDeviationMetric(
                channel_name=m.channel_name,
                current_value=m.current_value,
                baseline_median=m.baseline_median,
                mad_scale=m.mad_scale,
                robust_z_score=m.robust_z_score,
                deviation_urgency_weight=float(normalized_weights[idx]),
            )

        return DeviationScoringResult(
            channel_metrics=metrics_map,
            deviation_weight_vector=normalized_weights,
            channel_order=selected_channels,
            max_deviating_channel=max_ch,
            max_z_score=float(max_z),
        )

    def score_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, List[DeviationScoringResult], np.ndarray]:
        """
        Evaluate deviation scoring frame-by-frame across a telemetry time-series DataFrame.
        
        Returns:
            Tuple of (augmented_df_with_max_z, list_of_row_results, mean_deviation_weights_vector)
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for deviation scoring")

        row_results: List[DeviationScoringResult] = []
        weight_matrix = np.empty((len(telemetry_df), len(target_columns)), dtype=np.float64)
        max_z_col = np.empty(len(telemetry_df), dtype=np.float64)

        for i in range(len(telemetry_df)):
            row_dict = telemetry_df.iloc[i].to_dict()
            res = self.score_telemetry_vector(row_dict, target_channels=target_columns)
            row_results.append(res)
            weight_matrix[i, :] = res.deviation_weight_vector
            max_z_col[i] = res.max_z_score

        augmented_df = telemetry_df.copy()
        augmented_df["telemetry_max_z_score"] = max_z_col

        mean_weights = np.mean(weight_matrix, axis=0)
        mean_weights = mean_weights / np.sum(mean_weights)  # Re-normalize mean vector

        return augmented_df, row_results, mean_weights


# ==============================================================================
# PHASE 3: Information-Theoretic Shannon Entropy Weighter (EntropyWeightEngine)
# ==============================================================================

@dataclass(frozen=True)
class EntropyEvaluationResult:
    """
    Immutable representation of Phase 3 Entropy calculation output.
    """
    channel_entropies: Dict[str, float]
    entropy_weights: Dict[str, float]
    weight_vector: np.ndarray
    channel_order: Tuple[str, ...]
    is_valid: bool


class EntropyWeightEngine:
    """
    Phase 3: Information-Theoretic Shannon Entropy Weighter.
    
    In multivariate biomedical telemetry, static prior weights cannot account for
    dynamic information content. A biomarker exhibiting rich physiological variability
    carries higher transmission entropy and clinical utility than a static flatline.
    
    This engine computes objective Shannon entropy across a rolling temporal telemetry window:
        1. Min-max normalization of telemetry channels into probability distributions p_{ij}:
           p_{ij} = (x_{ij} - min_j) / (sum_i (x_{ij} - min_j) + eps)
        2. Information Entropy:
           E_j = -k * sum_i (p_{ij} * ln(p_{ij})), where k = 1 / ln(m)
        3. Information Utility / Divergence:
           d_j = 1 - E_j
        4. Objective Entropy Weight:
           w_j = d_j / sum_k (d_k)
           
    Enforces strict Dirichlet bounds: sum w_j = 1.0, w_j >= min_entropy_floor.
    """

    def __init__(
        self,
        min_entropy_floor: float = 0.01,
        epsilon: float = 1e-12,
    ) -> None:
        """
        Initialize the Entropy Weight Engine.
        """
        if min_entropy_floor <= 0.0 or min_entropy_floor >= 0.5:
            raise ValueError(f"min_entropy_floor must be in (0.0, 0.5), got {min_entropy_floor}")
        if epsilon <= 0.0:
            raise ValueError(f"epsilon must be strictly positive, got {epsilon}")

        self.min_entropy_floor = float(min_entropy_floor)
        self.epsilon = float(epsilon)

    def calculate_entropy_weights(
        self,
        data: Union[np.ndarray, pd.DataFrame],
        channel_names: Optional[List[str]] = None,
    ) -> EntropyEvaluationResult:
        """
        Compute objective Shannon entropy weights across telemetry columns.
        
        Args:
            data: 2D numpy array or pandas DataFrame of shape (num_samples, num_channels).
            channel_names: Optional labels for channels (required if data is ndarray).
            
        Returns:
            EntropyEvaluationResult containing per-channel entropy and normalized weights.
        """
        if isinstance(data, pd.DataFrame):
            if data.empty:
                raise ValueError("Input DataFrame data cannot be empty")
            numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude timestamp/epoch
            cols = [c for c in numeric_cols if "time" not in c.lower() and "epoch" not in c.lower()]
            if len(cols) == 0:
                raise ValueError("No valid numeric channels found in DataFrame")
            matrix = data[cols].to_numpy(dtype=np.float64)
            names = tuple(cols)
        elif isinstance(data, np.ndarray):
            if data.ndim != 2 or data.shape[0] == 0 or data.shape[1] == 0:
                raise ValueError(f"Input ndarray must be 2D with non-zero dimensions, got shape {data.shape}")
            matrix = data.astype(np.float64)
            if channel_names is None or len(channel_names) != matrix.shape[1]:
                raise ValueError(
                    f"channel_names must match column count ({matrix.shape[1]}), got {channel_names}"
                )
            names = tuple(channel_names)
        else:
            raise TypeError(f"Unsupported data type: {type(data)}")

        if not np.all(np.isfinite(matrix)):
            raise ValueError("Input matrix contains NaN or Inf values")

        m_samples, n_channels = matrix.shape

        # For very short temporal horizons (m < 3), entropy cannot be meaningfully resolved
        if m_samples < 3:
            uniform_w = np.ones(n_channels, dtype=np.float64) / n_channels
            return EntropyEvaluationResult(
                channel_entropies={ch: 1.0 for ch in names},
                entropy_weights={ch: float(uniform_w[idx]) for idx, ch in enumerate(names)},
                weight_vector=uniform_w,
                channel_order=names,
                is_valid=True,
            )

        k = 1.0 / np.log(m_samples)
        entropies = np.empty(n_channels, dtype=np.float64)

        for j in range(n_channels):
            col_vals = matrix[:, j]
            min_val = np.min(col_vals)
            max_val = np.max(col_vals)
            spread = max_val - min_val

            if spread <= self.epsilon:
                # Flatline channel has zero dispersion / zero information gain
                # In entropy weighting, flatlines have max entropy E = 1.0, divergence d = 0.0
                entropies[j] = 1.0
            else:
                # Probability distribution transformation
                shifted = col_vals - min_val + self.epsilon
                p = shifted / np.sum(shifted)
                # Compute Shannon entropy
                e_j = -k * np.sum(p * np.log(p + self.epsilon))
                entropies[j] = float(np.clip(e_j, 0.0, 1.0))

        # Information utility / divergence: d_j = 1 - E_j
        divergences = 1.0 - entropies
        # Apply minimum floor so every channel retains some minimal baseline sensitivity
        divergences = np.maximum(divergences, self.min_entropy_floor)

        div_sum = np.sum(divergences)
        weights = divergences / div_sum

        entropy_map = {ch: float(entropies[idx]) for idx, ch in enumerate(names)}
        weight_map = {ch: float(weights[idx]) for idx, ch in enumerate(names)}

        return EntropyEvaluationResult(
            channel_entropies=entropy_map,
            entropy_weights=weight_map,
            weight_vector=weights,
            channel_order=names,
            is_valid=True,
        )


# ==============================================================================
# PHASE 4: Composite Sensitivity Fusion & Normalization Engine (CompositeSensitivityRanker)
# ==============================================================================

@dataclass(frozen=True)
class RankedBiomarker:
    """
    Immutable representation of an individual ranked biomarker in priority order.
    """
    rank: int
    channel_name: str
    composite_weight: float
    context_weight: float
    deviation_weight: float
    entropy_weight: float


@dataclass(frozen=True)
class CompositeRankingResult:
    """
    Immutable result containing composite weights, sorted ranking, and component vectors.
    """
    ranked_biomarkers: List[RankedBiomarker]
    composite_weight_vector: np.ndarray
    composite_weight_dict: Dict[str, float]
    channel_order: Tuple[str, ...]
    fusion_coefficients: Tuple[float, float, float]  # (alpha, beta, gamma)
    is_strictly_normalized: bool


class CompositeSensitivityRanker:
    """
    Phase 4: Composite Sensitivity Fusion & Normalization Engine.
    
    Synthesizes the three distinct epistemic sources of biomarker sensitivity:
    1. Mission Operational Context Prior (alpha * W_context)
    2. Physiological Deviation Urgency (beta * W_deviation)
    3. Information-Theoretic Shannon Entropy (gamma * W_entropy)
    
    Mathematical Formulation:
        W_raw = alpha * W_context + beta * W_deviation + gamma * W_entropy
        where alpha + beta + gamma = 1.0 (Convex linear combination)
        
    Enforces Dirichlet floor (w_i >= min_floor) and exact unit simplex normalization:
        sum_{i=1}^N w_i = 1.0
        
    Produces an ordered ranking of biomarkers based on their acute analytical priority.
    """

    def __init__(
        self,
        alpha_context: float = 0.35,
        beta_deviation: float = 0.45,
        gamma_entropy: float = 0.20,
        min_weight_floor: float = 0.01,
    ) -> None:
        """
        Initialize composite ranker with fusion hyper-parameters.
        
        Args:
            alpha_context: Prior context weight proportion (default 0.35).
            beta_deviation: Physiological deviation urgency proportion (default 0.45).
            gamma_entropy: Information entropy proportion (default 0.20).
            min_weight_floor: Strictly positive weight minimum floor per channel (default 0.01).
        """
        if alpha_context < 0.0 or beta_deviation < 0.0 or gamma_entropy < 0.0:
            raise ValueError("Fusion coefficients (alpha, beta, gamma) must be non-negative")

        total_coeff = alpha_context + beta_deviation + gamma_entropy
        if total_coeff <= 0.0:
            raise ValueError("Sum of fusion coefficients must be strictly positive")

        if min_weight_floor <= 0.0 or min_weight_floor >= 0.2:
            raise ValueError(f"min_weight_floor must be in (0.0, 0.2), got {min_weight_floor}")

        # Normalize coefficients so alpha + beta + gamma == 1.0
        self.alpha = float(alpha_context / total_coeff)
        self.beta = float(beta_deviation / total_coeff)
        self.gamma = float(gamma_entropy / total_coeff)
        self.min_floor = float(min_weight_floor)

    def fuse_sensitivity_vectors(
        self,
        context_weights: Union[np.ndarray, Dict[str, float]],
        deviation_weights: Union[np.ndarray, Dict[str, float]],
        entropy_weights: Union[np.ndarray, Dict[str, float]],
        channel_names: Optional[List[str]] = None,
    ) -> CompositeRankingResult:
        """
        Execute convex fusion and Dirichlet normalization across the 3 sensitivity sources.
        
        Args:
            context_weights: Array or dict of mission context prior weights.
            deviation_weights: Array or dict of physiological deviation weights.
            entropy_weights: Array or dict of information entropy weights.
            channel_names: Optional ordered channel names (required if inputs are ndarrays).
            
        Returns:
            CompositeRankingResult containing ranked list and normalized composite vector.
        """
        # Align inputs to dicts and channel order
        if isinstance(context_weights, dict):
            names = tuple(channel_names) if channel_names is not None else tuple(context_weights.keys())
            w_ctx = np.array([float(context_weights[ch]) for ch in names], dtype=np.float64)
            w_dev = np.array([float(deviation_weights[ch]) for ch in names], dtype=np.float64)
            w_ent = np.array([float(entropy_weights[ch]) for ch in names], dtype=np.float64)
        elif isinstance(context_weights, np.ndarray):
            if channel_names is None or len(channel_names) != len(context_weights):
                raise ValueError("channel_names must match array length when ndarrays are passed")
            names = tuple(channel_names)
            w_ctx = context_weights.astype(np.float64)
            w_dev = np.asarray(deviation_weights, dtype=np.float64)
            w_ent = np.asarray(entropy_weights, dtype=np.float64)
        else:
            raise TypeError("Unsupported input type for sensitivity weights")

        if len(names) == 0:
            raise ValueError("channel_names cannot be empty")
        if len(w_ctx) != len(names) or len(w_dev) != len(names) or len(w_ent) != len(names):
            raise ValueError("All sensitivity weight vectors must have matching dimensions")

        # 1. Convex linear combination
        w_raw = (self.alpha * w_ctx) + (self.beta * w_dev) + (self.gamma * w_ent)

        # 2. Enforce minimum floor per channel
        w_floored = np.maximum(w_raw, self.min_floor)

        # 3. Unit simplex normalization: sum w_i = 1.0
        w_composite = w_floored / np.sum(w_floored)

        is_norm = bool(np.isclose(float(np.sum(w_composite)), 1.0, atol=1e-6))

        # 4. Generate sorted priority ranking
        ranked_list: List[RankedBiomarker] = []
        # Sort descending by composite weight
        sorted_indices = np.argsort(-w_composite)

        comp_dict: Dict[str, float] = {}
        for rank_idx, original_idx in enumerate(sorted_indices):
            ch_name = names[original_idx]
            c_weight = float(w_composite[original_idx])
            comp_dict[ch_name] = c_weight
            ranked_list.append(
                RankedBiomarker(
                    rank=rank_idx + 1,
                    channel_name=ch_name,
                    composite_weight=c_weight,
                    context_weight=float(w_ctx[original_idx]),
                    deviation_weight=float(w_dev[original_idx]),
                    entropy_weight=float(w_ent[original_idx]),
                )
            )

        return CompositeRankingResult(
            ranked_biomarkers=ranked_list,
            composite_weight_vector=w_composite,
            composite_weight_dict=comp_dict,
            channel_order=names,
            fusion_coefficients=(self.alpha, self.beta, self.gamma),
            is_strictly_normalized=is_norm,
        )


# ==============================================================================
# PHASE 5: Master Sensitivity Contract & Exporter (SensitivityContractExporter)
# ==============================================================================

@dataclass(frozen=True)
class BiomarkerSensitivityContract:
    """
    Immutable data contract passed from Innovation 6 to the
    80% Biophysical Supreme Head (Decision Core).
    """
    phase: MissionOperationalPhase
    channel_order: Tuple[str, ...]
    sensitivity_weights: np.ndarray
    sensitivity_dict: Dict[str, float]
    ranked_biomarkers: List[RankedBiomarker]
    top_critical_channel: str
    top_critical_weight: float
    is_flight_certified: bool
    audit_manifest: Dict[str, Union[str, int, float, bool]]


class SensitivityContractExporter:
    """
    Phase 5: Master Sensitivity Contract & Exporter.
    
    Orchestrates the entire Innovation 6 pipeline:
    1. Mission Operational Context Prior Matrix (`MissionContextMatrix`)
    2. Physiological Deviation & Robust Z-Score Engine (`PhysiologicalDeviationScorer`)
    3. Information-Theoretic Shannon Entropy Weighter (`EntropyWeightEngine`)
    4. Composite Convex Fusion & Dirichlet Simplex Ranker (`CompositeSensitivityRanker`)
    
    Validates mathematical compliance (no negative weights, sum == 1.0) and generates
    an immutable `BiomarkerSensitivityContract` ready for deterministic clinical triage.
    """

    def __init__(
        self,
        context_matrix: Optional[MissionContextMatrix] = None,
        deviation_scorer: Optional[PhysiologicalDeviationScorer] = None,
        entropy_engine: Optional[EntropyWeightEngine] = None,
        composite_ranker: Optional[CompositeSensitivityRanker] = None,
    ) -> None:
        """
        Initialize the Master Sensitivity Exporter.
        """
        self.context_matrix = context_matrix if context_matrix is not None else MissionContextMatrix()
        self.deviation_scorer = deviation_scorer if deviation_scorer is not None else PhysiologicalDeviationScorer()
        self.entropy_engine = entropy_engine if entropy_engine is not None else EntropyWeightEngine()
        self.composite_ranker = composite_ranker if composite_ranker is not None else CompositeSensitivityRanker()

    def process_and_export_contract(
        self,
        telemetry_df: pd.DataFrame,
        phase: Union[MissionOperationalPhase, str] = MissionOperationalPhase.INTRA_VEHICULAR_NOMINAL,
        target_columns: Optional[List[str]] = None,
    ) -> BiomarkerSensitivityContract:
        """
        Execute end-to-end biomarker sensitivity evaluation on a telemetry DataFrame.
        
        Args:
            telemetry_df: Sanitized telemetry DataFrame (from Sanity Gate).
            phase: Current spaceflight operational mission phase.
            target_columns: Optional subset of channels to evaluate.
            
        Returns:
            BiomarkerSensitivityContract containing normalized sensitivity vector and ranked list.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric channels found for sensitivity evaluation")

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")

        resolved_phase = self.context_matrix.resolve_phase(phase)

        # 1. Mission Context Weights
        ctx_result = self.context_matrix.get_phase_weights(
            phase=resolved_phase,
            target_channels=target_columns,
        )

        # 2. Physiological Deviation Weights (averaged across frame)
        _, _, dev_weights = self.deviation_scorer.score_telemetry_frame(
            telemetry_df=telemetry_df,
            target_columns=target_columns,
        )

        # 3. Shannon Entropy Weights
        ent_result = self.entropy_engine.calculate_entropy_weights(
            data=telemetry_df[target_columns],
        )

        # 4. Composite Fusion & Ranking
        comp_result = self.composite_ranker.fuse_sensitivity_vectors(
            context_weights=ctx_result.weight_vector,
            deviation_weights=dev_weights,
            entropy_weights=ent_result.weight_vector,
            channel_names=target_columns,
        )

        # 5. Numerical Integrity Validation
        weights = comp_result.composite_weight_vector
        is_strictly_positive = bool(np.all(weights > 0.0))
        is_normalized = bool(np.isclose(float(np.sum(weights)), 1.0, atol=1e-5))
        is_finite = bool(np.all(np.isfinite(weights)))

        is_certified = is_strictly_positive and is_normalized and is_finite

        top_biomarker = comp_result.ranked_biomarkers[0]

        manifest: Dict[str, Union[str, int, float, bool]] = {
            "mission_phase": resolved_phase.value,
            "samples_analyzed": len(telemetry_df),
            "channels_ranked": len(target_columns),
            "top_channel": top_biomarker.channel_name,
            "top_weight": top_biomarker.composite_weight,
            "alpha_context": self.composite_ranker.alpha,
            "beta_deviation": self.composite_ranker.beta,
            "gamma_entropy": self.composite_ranker.gamma,
            "is_flight_certified": is_certified,
        }

        return BiomarkerSensitivityContract(
            phase=resolved_phase,
            channel_order=tuple(target_columns),
            sensitivity_weights=weights,
            sensitivity_dict=comp_result.composite_weight_dict,
            ranked_biomarkers=comp_result.ranked_biomarkers,
            top_critical_channel=top_biomarker.channel_name,
            top_critical_weight=top_biomarker.composite_weight,
            is_flight_certified=is_certified,
            audit_manifest=manifest,
        )




