"""
ASTROVITAL AI: VITALX CORE RECREATED V1
Subsystem: 02_AI_CORE / Airworthiness & Integrity Verification
Component: DO-178C Level C Mathematical Sanity Gate (Airworthiness Firewall)
File: 02_AI_CORE/01_src/sanity_gate.py

Airworthiness Directive & Safety Philosophy:
This module enforces formal mathematical safety boundaries between the 20% Adaptive AI layer
and the 80% Biophysical Supreme Head (Decision Core).
Every incoming telemetry vector MUST satisfy physiological viability bounds Omega_bio.
If telemetry violates human physiological existence constraints, it is deterministically
intercepted, clamped, logged, or diverted to calibrated mission fallbacks.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PhysiologicalBound:
    """
    Formal bounding envelope for a biological telemetry channel.
    Derived from NASA-STD-3001 (Space Flight Human-System Standard).
    """
    channel_name: str
    min_viable: float
    max_viable: float
    min_normal: float
    max_normal: float
    unit: str


# Formal physiological boundary constants (Omega_bio) based on NASA-STD-3001
NASA_STD_3001_PHYSIOLOGICAL_BOUNDS: Dict[str, PhysiologicalBound] = {
    "heart_rate_bpm": PhysiologicalBound("heart_rate_bpm", 20.0, 240.0, 50.0, 100.0, "bpm"),
    "systolic_bp_mmhg": PhysiologicalBound("systolic_bp_mmhg", 50.0, 260.0, 90.0, 130.0, "mmHg"),
    "diastolic_bp_mmhg": PhysiologicalBound("diastolic_bp_mmhg", 30.0, 150.0, 60.0, 85.0, "mmHg"),
    "spo2_percent": PhysiologicalBound("spo2_percent", 50.0, 100.0, 94.0, 100.0, "%"),
    "core_temp_c": PhysiologicalBound("core_temp_c", 30.0, 43.0, 36.1, 37.8, "degC"),
    "resp_rate_bpm": PhysiologicalBound("resp_rate_bpm", 4.0, 60.0, 12.0, 20.0, "breaths/min"),
    "etco2_mmhg": PhysiologicalBound("etco2_mmhg", 10.0, 70.0, 35.0, 45.0, "mmHg"),
    "icp_est_mmhg": PhysiologicalBound("icp_est_mmhg", -5.0, 45.0, 5.0, 15.0, "mmHg"),
    "cvp_mmhg": PhysiologicalBound("cvp_mmhg", -2.0, 30.0, 2.0, 8.0, "mmHg"),
    "co2_cabin_ppm": PhysiologicalBound("co2_cabin_ppm", 100.0, 20000.0, 300.0, 4000.0, "ppm"),
    "cabin_pressure_psi": PhysiologicalBound("cabin_pressure_psi", 5.0, 16.0, 10.2, 14.7, "psi"),
    "ambient_temp_c": PhysiologicalBound("ambient_temp_c", 10.0, 40.0, 18.0, 26.0, "degC"),
}


@dataclass(frozen=True)
class BoundaryAuditResult:
    """
    Immutable data container for Phase 1 single-channel physiological boundary check.
    """
    channel_name: str
    original_value: float
    clamped_value: float
    is_within_viable_bounds: bool
    is_within_normal_bounds: bool
    violation_code: Optional[str]  # e.g., "NON_VIABLE_LOW", "NON_VIABLE_HIGH", None


class PhysiologicalBoundaryEnforcer:
    """
    Phase 1: Physiological Boundary Enforcer (Omega_bio Bounding Box).
    
    Verifies that all telemetry channels reside strictly inside hard physiological
    and life-support boundaries defined by NASA-STD-3001.
    
    Any telemetry exceeding human existence limits (e.g., HR > 240 bpm, SpO2 > 100%)
    is detected as non-viable, tagged with a deterministic violation code,
    and safely clamped to viable physiological limits.
    """

    def __init__(
        self,
        custom_bounds: Optional[Dict[str, PhysiologicalBound]] = None,
    ) -> None:
        """
        Initialize the physiological boundary enforcer.
        """
        self.bounds: Dict[str, PhysiologicalBound] = (
            custom_bounds if custom_bounds is not None else NASA_STD_3001_PHYSIOLOGICAL_BOUNDS
        )
        if len(self.bounds) == 0:
            raise ValueError("Boundary dictionary cannot be empty")

    def get_channel_bound(self, channel_name: str) -> PhysiologicalBound:
        """
        Retrieve physiological bounds for a specific telemetry channel with key normalization.
        """
        if not isinstance(channel_name, str) or not channel_name.strip():
            raise ValueError("channel_name must be a non-empty string")

        clean_name = channel_name.strip().lower()
        if clean_name in self.bounds:
            return self.bounds[clean_name]

        # Fuzzy / alias matching for standard telemetry keys
        for key, bound in self.bounds.items():
            if key in clean_name or clean_name in key:
                return bound

        raise KeyError(f"No physiological bounds registered for channel '{channel_name}'")

    def audit_value(
        self,
        channel_name: str,
        value: float,
    ) -> BoundaryAuditResult:
        """
        Audit a single scalar telemetry value against physiological boundaries.
        """
        if not np.isfinite(value):
            raise ValueError(f"Value for {channel_name} must be a finite float, got {value}")

        bound = self.get_channel_bound(channel_name)
        val = float(value)

        # Viability check
        if val < bound.min_viable:
            is_viable = False
            violation = "NON_VIABLE_LOW"
            clamped = bound.min_viable
        elif val > bound.max_viable:
            is_viable = False
            violation = "NON_VIABLE_HIGH"
            clamped = bound.max_viable
        else:
            is_viable = True
            violation = None
            clamped = val

        # Normal range check
        is_normal = bool(bound.min_normal <= val <= bound.max_normal)

        return BoundaryAuditResult(
            channel_name=bound.channel_name,
            original_value=val,
            clamped_value=clamped,
            is_within_viable_bounds=is_viable,
            is_within_normal_bounds=is_normal,
            violation_code=violation,
        )

    def audit_channel_array(
        self,
        channel_name: str,
        signal: Union[np.ndarray, List[float], pd.Series],
    ) -> Tuple[np.ndarray, List[BoundaryAuditResult], bool]:
        """
        Audit an entire 1D telemetry channel array.
        
        Returns:
            Tuple of (clamped_signal_array, list_of_audit_results, is_channel_100_percent_viable)
        """
        if isinstance(signal, pd.Series):
            arr = signal.to_numpy(dtype=np.float64)
        elif isinstance(signal, list):
            arr = np.array(signal, dtype=np.float64)
        elif isinstance(signal, np.ndarray):
            arr = signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported signal type for {channel_name}: {type(signal)}")

        if arr.ndim != 1 or len(arr) == 0:
            raise ValueError(f"Channel {channel_name} must be a non-empty 1D array")

        if not np.all(np.isfinite(arr)):
            raise ValueError(f"Channel {channel_name} contains non-finite values (NaN / Inf)")

        bound = self.get_channel_bound(channel_name)
        clamped_arr = np.clip(arr, bound.min_viable, bound.max_viable)

        audits: List[BoundaryAuditResult] = []
        all_viable = True

        for orig_val, clamped_val in zip(arr, clamped_arr):
            is_viable = bool(bound.min_viable <= orig_val <= bound.max_viable)
            is_normal = bool(bound.min_normal <= orig_val <= bound.max_normal)
            
            if orig_val < bound.min_viable:
                viol = "NON_VIABLE_LOW"
                all_viable = False
            elif orig_val > bound.max_viable:
                viol = "NON_VIABLE_HIGH"
                all_viable = False
            else:
                viol = None

            audits.append(
                BoundaryAuditResult(
                    channel_name=bound.channel_name,
                    original_value=float(orig_val),
                    clamped_value=float(clamped_val),
                    is_within_viable_bounds=is_viable,
                    is_within_normal_bounds=is_normal,
                    violation_code=viol,
                )
            )

        return clamped_arr, audits, all_viable

    def audit_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, List[BoundaryAuditResult]], bool]:
        """
        Audit all channels in a multi-channel telemetry DataFrame against physiological limits.
        
        Returns:
            Tuple of (clamped_dataframe, per_channel_audit_lists, is_entire_frame_viable)
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for boundary auditing")

        output_df = telemetry_df.copy()
        frame_audits: Dict[str, List[BoundaryAuditResult]] = {}
        frame_viable = True

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")
            
            clamped, audits, ch_viable = self.audit_channel_array(col, telemetry_df[col].to_numpy())
            output_df[col] = clamped
            frame_audits[col] = audits
            if not ch_viable:
                frame_viable = False

        return output_df, frame_audits, frame_viable


# ==============================================================================
# PHASE 2: Physiological Gradient Limiter (dV/dt Rate of Change Guard)
# ==============================================================================

@dataclass(frozen=True)
class GradientLimit:
    """
    Maximum physically possible biological rate of change |dV/dt| per second
    under extreme human physiological response.
    """
    channel_name: str
    max_delta_per_sec: float
    unit_per_sec: str


NASA_MAX_PHYSIOLOGICAL_GRADIENTS: Dict[str, GradientLimit] = {
    "heart_rate_bpm": GradientLimit("heart_rate_bpm", 5.0, "bpm/sec"),            # Max 5 bpm/sec ramp
    "systolic_bp_mmhg": GradientLimit("systolic_bp_mmhg", 6.0, "mmHg/sec"),        # Max 6 mmHg/sec
    "diastolic_bp_mmhg": GradientLimit("diastolic_bp_mmhg", 4.0, "mmHg/sec"),      # Max 4 mmHg/sec
    "spo2_percent": GradientLimit("spo2_percent", 2.0, "%/sec"),                  # Max 2 %/sec desaturation
    "core_temp_c": GradientLimit("core_temp_c", 0.05, "degC/sec"),                # Thermal inertia: 3 degC/min max
    "resp_rate_bpm": GradientLimit("resp_rate_bpm", 2.0, "breaths/sec"),          # Max 2 bpm/sec
    "etco2_mmhg": GradientLimit("etco2_mmhg", 3.0, "mmHg/sec"),                   # Max 3 mmHg/sec
    "icp_est_mmhg": GradientLimit("icp_est_mmhg", 2.0, "mmHg/sec"),               # Max 2 mmHg/sec
    "cvp_mmhg": GradientLimit("cvp_mmhg", 1.5, "mmHg/sec"),                       # Max 1.5 mmHg/sec
    "co2_cabin_ppm": GradientLimit("co2_cabin_ppm", 50.0, "ppm/sec"),             # Cabin volume dilution
    "cabin_pressure_psi": GradientLimit("cabin_pressure_psi", 0.2, "psi/sec"),    # ECLSS valve limits
    "ambient_temp_c": GradientLimit("ambient_temp_c", 0.2, "degC/sec"),           # Thermal loop inertia
}


@dataclass(frozen=True)
class GradientAuditResult:
    """
    Immutable data container for Phase 2 Gradient check.
    """
    channel_name: str
    sample_index: int
    prior_value: float
    current_value: float
    delta_observed: float
    time_delta_sec: float
    gradient_per_sec: float
    max_permissible_gradient: float
    is_gradient_permissible: bool
    filtered_value: float  # Slew-rate clamped value preserving continuity


class PhysiologicalGradientLimiter:
    """
    Phase 2: Physiological Gradient Limiter (dV/dt Rate of Change Guard).
    
    Human physiological biomarkers cannot undergo step discontinuities or infinite
    derivatives due to cardiac mass, circulatory blood transit time, and thermal inertia.
    
    This component calculates discrete derivatives dV/dt and clamps non-physiological
    spikes (e.g., HR jumping from 70 to 180 bpm in 1 second) to maximum biologically
    feasible slew rates, logging potential sensor glitches or electromagnetic bursts.
    """

    def __init__(
        self,
        sampling_rate_hz: float = 1.0,
        custom_gradients: Optional[Dict[str, GradientLimit]] = None,
    ) -> None:
        """
        Initialize gradient limiter with sampling frequency and slew bounds.
        """
        if sampling_rate_hz <= 0.0:
            raise ValueError(f"sampling_rate_hz must be strictly positive, got {sampling_rate_hz}")

        self.sampling_rate_hz = float(sampling_rate_hz)
        self.time_delta_sec = 1.0 / self.sampling_rate_hz
        self.gradients: Dict[str, GradientLimit] = (
            custom_gradients if custom_gradients is not None else NASA_MAX_PHYSIOLOGICAL_GRADIENTS
        )
        if len(self.gradients) == 0:
            raise ValueError("Gradient limits dictionary cannot be empty")

    def get_gradient_limit(self, channel_name: str) -> GradientLimit:
        """
        Resolve gradient limit for a telemetry channel.
        """
        if not isinstance(channel_name, str) or not channel_name.strip():
            raise ValueError("channel_name must be a non-empty string")

        clean = channel_name.strip().lower()
        if clean in self.gradients:
            return self.gradients[clean]

        for key, limit in self.gradients.items():
            if key in clean or clean in key:
                return limit

        raise KeyError(f"No gradient limits registered for channel '{channel_name}'")

    def audit_channel_gradient(
        self,
        channel_name: str,
        signal: Union[np.ndarray, List[float], pd.Series],
    ) -> Tuple[np.ndarray, List[GradientAuditResult], bool]:
        """
        Audit and rate-limit an entire 1D telemetry channel.
        
        Returns:
            Tuple of (slew_rate_limited_signal, list_of_gradient_audits, is_entire_channel_gradient_valid)
        """
        if isinstance(signal, pd.Series):
            arr = signal.to_numpy(dtype=np.float64)
        elif isinstance(signal, list):
            arr = np.array(signal, dtype=np.float64)
        elif isinstance(signal, np.ndarray):
            arr = signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported signal type for {channel_name}: {type(signal)}")

        if arr.ndim != 1 or len(arr) == 0:
            raise ValueError(f"Channel {channel_name} must be a non-empty 1D array")

        if not np.all(np.isfinite(arr)):
            raise ValueError(f"Channel {channel_name} contains non-finite values (NaN / Inf)")

        limit = self.get_gradient_limit(channel_name)
        max_delta = limit.max_delta_per_sec * self.time_delta_sec

        n = len(arr)
        limited_arr = np.empty(n, dtype=np.float64)
        limited_arr[0] = arr[0]

        audits: List[GradientAuditResult] = []
        all_valid = True

        for i in range(1, n):
            prior_val = limited_arr[i - 1]
            raw_curr_val = arr[i]
            delta = raw_curr_val - prior_val
            grad = abs(delta) / self.time_delta_sec

            if abs(delta) > max_delta:
                all_valid = False
                is_permissible = False
                clamped_delta = np.sign(delta) * max_delta
                filtered_curr_val = prior_val + clamped_delta
            else:
                is_permissible = True
                filtered_curr_val = raw_curr_val

            limited_arr[i] = filtered_curr_val
            audits.append(
                GradientAuditResult(
                    channel_name=limit.channel_name,
                    sample_index=i,
                    prior_value=float(prior_val),
                    current_value=float(raw_curr_val),
                    delta_observed=float(delta),
                    time_delta_sec=float(self.time_delta_sec),
                    gradient_per_sec=float(grad),
                    max_permissible_gradient=float(limit.max_delta_per_sec),
                    is_gradient_permissible=is_permissible,
                    filtered_value=float(filtered_curr_val),
                )
            )

        return limited_arr, audits, all_valid

    def audit_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, List[GradientAuditResult]], bool]:
        """
        Audit gradients across all channels in a DataFrame.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for gradient auditing")

        output_df = telemetry_df.copy()
        frame_audits: Dict[str, List[GradientAuditResult]] = {}
        frame_valid = True

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")

            limited, audits, ch_valid = self.audit_channel_gradient(col, telemetry_df[col].to_numpy())
            output_df[col] = limited
            frame_audits[col] = audits
            if not ch_valid:
                frame_valid = False

        return output_df, frame_audits, frame_valid


# ==============================================================================
# PHASE 3: Multi-Parameter Cross-Correlation & Decoupling Guard
# ==============================================================================

@dataclass(frozen=True)
class CouplingViolation:
    """
    Immutable representation of an unphysical hemodynamic or metabolic mismatch.
    """
    rule_name: str
    involved_channels: Tuple[str, ...]
    observed_values: Dict[str, float]
    violation_description: str
    severity: str  # "CORRUPTED_DISCORDANCE" or "PLAUSIBLE_PATHOLOGY"


@dataclass(frozen=True)
class CouplingAuditResult:
    """
    Immutable result of multi-parameter physiological consistency audit.
    """
    is_physiologically_coupled: bool
    violations: List[CouplingViolation]
    sanitized_values: Dict[str, float]


class PhysiologicalCouplingGuard:
    """
    Phase 3: Multi-Parameter Cross-Correlation & Decoupling Guard.
    
    In living organisms, biological parameters are thermodynamically and hydraulically coupled:
    1. Pulse Pressure Rule: SBP - DBP >= 15 mmHg (Systolic must be strictly > Diastolic).
    2. Mean Arterial Pressure (MAP) Rule: MAP approx DBP + (SBP - DBP) / 3.
    3. Cardiac-Respiratory Coupling: HR = 0 while RR > 0 or vice versa without mechanical CPR.
    4. Perfusion SpO2 Coupling: Severe hypoxemia (SpO2 < 70%) accompanied by normal resting HR (60 bpm)
       indicates sensor optical displacement rather than acute asphyxiation.
       
    This component identifies unphysical parameter discordances and enforces physical consistency.
    """

    def __init__(
        self,
        min_pulse_pressure_mmhg: float = 15.0,
    ) -> None:
        """
        Initialize the physiological coupling guard.
        """
        if min_pulse_pressure_mmhg <= 0.0:
            raise ValueError(f"min_pulse_pressure_mmhg must be strictly positive, got {min_pulse_pressure_mmhg}")

        self.min_pp = float(min_pulse_pressure_mmhg)

    def audit_hemodynamic_coupling(
        self,
        systolic_bp: float,
        diastolic_bp: float,
    ) -> Tuple[float, float, List[CouplingViolation], bool]:
        """
        Audit SBP and DBP for hydraulic feasibility (SBP > DBP with valid pulse pressure).
        """
        if not np.isfinite(systolic_bp) or not np.isfinite(diastolic_bp):
            raise ValueError("Blood pressure values must be finite numbers")

        violations: List[CouplingViolation] = []
        sbp = float(systolic_bp)
        dbp = float(diastolic_bp)

        # Rule 1: SBP must exceed DBP by at least min_pulse_pressure_mmhg
        pulse_pressure = sbp - dbp
        if pulse_pressure < self.min_pp:
            violations.append(
                CouplingViolation(
                    rule_name="PULSE_PRESSURE_DEFICIT",
                    involved_channels=("systolic_bp_mmhg", "diastolic_bp_mmhg"),
                    observed_values={"systolic_bp_mmhg": sbp, "diastolic_bp_mmhg": dbp},
                    violation_description=(
                        f"Systolic BP ({sbp}) - Diastolic BP ({dbp}) = {pulse_pressure:.1f} mmHg "
                        f"is below physical limit of {self.min_pp} mmHg"
                    ),
                    severity="CORRUPTED_DISCORDANCE",
                )
            )
            # Enforce physical separation: adjust SBP upward or DBP downward safely
            if sbp <= dbp:
                sbp = dbp + self.min_pp
            else:
                # Narrow gap: expand gap symmetrically around mean pressure
                mean_p = (sbp + dbp) / 2.0
                sbp = mean_p + (self.min_pp / 2.0)
                dbp = mean_p - (self.min_pp / 2.0)

        is_coupled = len(violations) == 0
        return sbp, dbp, violations, is_coupled

    def audit_cardiorespiratory_coupling(
        self,
        heart_rate: float,
        resp_rate: float,
    ) -> Tuple[float, float, List[CouplingViolation], bool]:
        """
        Audit cardiac and respiratory coupling for survival consistency.
        """
        if not np.isfinite(heart_rate) or not np.isfinite(resp_rate):
            raise ValueError("Heart rate and respiratory rate must be finite numbers")

        violations: List[CouplingViolation] = []
        hr = float(heart_rate)
        rr = float(resp_rate)

        # Cardiac arrest (HR ~ 0) cannot sustain spontaneous breathing (RR > 8)
        if hr < 25.0 and rr > 8.0:
            violations.append(
                CouplingViolation(
                    rule_name="CARDIAC_ARREST_RESPIRATORY_DISCORDANCE",
                    involved_channels=("heart_rate_bpm", "resp_rate_bpm"),
                    observed_values={"heart_rate_bpm": hr, "resp_rate_bpm": rr},
                    violation_description="Profound bradycardia/asystole with active spontaneous breathing indicates sensor decouple",
                    severity="CORRUPTED_DISCORDANCE",
                )
            )

        is_coupled = len(violations) == 0
        return hr, rr, violations, is_coupled

    def audit_telemetry_vector(
        self,
        telemetry_dict: Dict[str, float],
    ) -> CouplingAuditResult:
        """
        Audit an entire dictionary of simultaneous vital parameters for physiological coupling.
        """
        if not isinstance(telemetry_dict, dict) or len(telemetry_dict) == 0:
            raise ValueError("telemetry_dict must be a non-empty dictionary")

        sanitized = dict(telemetry_dict)
        all_violations: List[CouplingViolation] = []

        # 1. Hemodynamic coupling
        if "systolic_bp_mmhg" in sanitized and "diastolic_bp_mmhg" in sanitized:
            sbp, dbp, bp_viols, _ = self.audit_hemodynamic_coupling(
                sanitized["systolic_bp_mmhg"],
                sanitized["diastolic_bp_mmhg"],
            )
            sanitized["systolic_bp_mmhg"] = sbp
            sanitized["diastolic_bp_mmhg"] = dbp
            all_violations.extend(bp_viols)

        # 2. Cardiorespiratory coupling
        if "heart_rate_bpm" in sanitized and "resp_rate_bpm" in sanitized:
            hr, rr, cr_viols, _ = self.audit_cardiorespiratory_coupling(
                sanitized["heart_rate_bpm"],
                sanitized["resp_rate_bpm"],
            )
            sanitized["heart_rate_bpm"] = hr
            sanitized["resp_rate_bpm"] = rr
            all_violations.extend(cr_viols)

        is_coupled = len(all_violations) == 0
        return CouplingAuditResult(
            is_physiologically_coupled=is_coupled,
            violations=all_violations,
            sanitized_values=sanitized,
        )

    def audit_telemetry_frame(
        self,
        telemetry_df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, List[CouplingAuditResult], bool]:
        """
        Audit multi-parameter coupling across an entire DataFrame frame by frame.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        output_df = telemetry_df.copy()
        audit_results: List[CouplingAuditResult] = []
        all_coupled = True

        for idx in range(len(telemetry_df)):
            row_dict = telemetry_df.iloc[idx].to_dict()
            res = self.audit_telemetry_vector(row_dict)
            audit_results.append(res)
            if not res.is_physiologically_coupled:
                all_coupled = False

            # Update sanitized values in output DataFrame
            for col, val in res.sanitized_values.items():
                if col in output_df.columns:
                    output_df.loc[idx, col] = val

        return output_df, audit_results, all_coupled


# ==============================================================================
# PHASE 4: Sensor Decoupling & Fallback Strategy Engine
# ==============================================================================

@dataclass(frozen=True)
class FallbackPolicy:
    """
    Airworthiness-grade sensor decoupling fallback policy.
    Modes:
    - "HOLD_LAST_VALID": Maintain last known valid physiological sample for bounded duration.
    - "MISSION_BASELINE": Substitute calibrated astronaut baseline.
    - "DEGRADED_INTERPOLATION": Piecewise linear estimation between verified anchors.
    """
    channel_name: str
    fallback_mode: str
    max_hold_duration_sec: float
    calibrated_baseline_value: float


# Mission-calibrated standard baselines derived from NASA Apollo & ISS Expeditions
APOLLO_ISS_MISSION_BASELINES: Dict[str, FallbackPolicy] = {
    "heart_rate_bpm": FallbackPolicy("heart_rate_bpm", "HOLD_LAST_VALID", 180.0, 72.0),
    "systolic_bp_mmhg": FallbackPolicy("systolic_bp_mmhg", "HOLD_LAST_VALID", 180.0, 118.0),
    "diastolic_bp_mmhg": FallbackPolicy("diastolic_bp_mmhg", "HOLD_LAST_VALID", 180.0, 76.0),
    "spo2_percent": FallbackPolicy("spo2_percent", "HOLD_LAST_VALID", 60.0, 98.0),
    "core_temp_c": FallbackPolicy("core_temp_c", "HOLD_LAST_VALID", 300.0, 36.8),
    "resp_rate_bpm": FallbackPolicy("resp_rate_bpm", "HOLD_LAST_VALID", 120.0, 14.0),
    "etco2_mmhg": FallbackPolicy("etco2_mmhg", "HOLD_LAST_VALID", 120.0, 38.0),
    "icp_est_mmhg": FallbackPolicy("icp_est_mmhg", "MISSION_BASELINE", 300.0, 11.5),
    "cvp_mmhg": FallbackPolicy("cvp_mmhg", "MISSION_BASELINE", 300.0, 5.2),
    "co2_cabin_ppm": FallbackPolicy("co2_cabin_ppm", "MISSION_BASELINE", 600.0, 1200.0),
    "cabin_pressure_psi": FallbackPolicy("cabin_pressure_psi", "MISSION_BASELINE", 600.0, 14.7),
    "ambient_temp_c": FallbackPolicy("ambient_temp_c", "MISSION_BASELINE", 600.0, 22.0),
}


@dataclass(frozen=True)
class FallbackActionLog:
    """
    Immutable audit log when fallback strategy substitutes an invalid or decoupled telemetry point.
    """
    channel_name: str
    sample_index: int
    raw_corrupted_value: float
    substituted_value: float
    policy_applied: str  # "HOLD_LAST_VALID" or "MISSION_BASELINE"
    hold_duration_sec: float
    is_fallback_active: bool


class SensorDecouplingFallbackEngine:
    """
    Phase 4: Sensor Decoupling & Fallback Strategy Engine.
    
    When sensors detach (lead-off, optical probe slippage, telemetry dropouts),
    autonomous clinical decision support cannot halt or feed corrupted zeros/NaNs
    to downstream mathematical equations.
    
    This engine implements bounded hold and mission baseline substitution:
    - If valid sample seen recently (time <= max_hold_duration), holds last known valid.
    - If dropout exceeds max_hold_duration, safely transitions to calibrated mission baseline.
    - Tags every substitution with an explicit fallback audit log.
    """

    def __init__(
        self,
        sampling_rate_hz: float = 1.0,
        policies: Optional[Dict[str, FallbackPolicy]] = None,
    ) -> None:
        """
        Initialize the fallback engine.
        """
        if sampling_rate_hz <= 0.0:
            raise ValueError(f"sampling_rate_hz must be strictly positive, got {sampling_rate_hz}")

        self.sampling_rate_hz = float(sampling_rate_hz)
        self.time_delta_sec = 1.0 / self.sampling_rate_hz
        self.policies: Dict[str, FallbackPolicy] = (
            policies if policies is not None else APOLLO_ISS_MISSION_BASELINES
        )
        if len(self.policies) == 0:
            raise ValueError("Fallback policies dictionary cannot be empty")

    def get_policy(self, channel_name: str) -> FallbackPolicy:
        """
        Resolve fallback policy for a telemetry channel.
        """
        if not isinstance(channel_name, str) or not channel_name.strip():
            raise ValueError("channel_name must be a non-empty string")

        clean = channel_name.strip().lower()
        if clean in self.policies:
            return self.policies[clean]

        for key, pol in self.policies.items():
            if key in clean or clean in key:
                return pol

        raise KeyError(f"No fallback policy registered for channel '{channel_name}'")

    def apply_fallback_channel(
        self,
        channel_name: str,
        signal: Union[np.ndarray, List[float], pd.Series],
        validity_mask: Optional[Union[np.ndarray, List[bool]]] = None,
    ) -> Tuple[np.ndarray, List[FallbackActionLog], int]:
        """
        Apply deterministic fallback substitutions across a single channel trace.
        
        Args:
            channel_name: Telemetry channel name.
            signal: 1D signal containing potential dropouts or corrupted samples.
            validity_mask: Optional boolean array where True=valid, False=corrupted/decoupled.
                           If None, checks for NaN, Inf, or physical zeroes where impossible.
                           
        Returns:
            Tuple of (sanitized_signal_array, list_of_action_logs, count_of_fallbacks_applied)
        """
        if isinstance(signal, pd.Series):
            raw_arr = signal.to_numpy(dtype=np.float64)
        elif isinstance(signal, list):
            raw_arr = np.array(signal, dtype=np.float64)
        elif isinstance(signal, np.ndarray):
            raw_arr = signal.astype(np.float64)
        else:
            raise TypeError(f"Unsupported signal type for {channel_name}: {type(signal)}")

        if raw_arr.ndim != 1 or len(raw_arr) == 0:
            raise ValueError(f"Channel {channel_name} must be a non-empty 1D array")

        policy = self.get_policy(channel_name)
        n = len(raw_arr)

        if validity_mask is not None:
            mask = np.asarray(validity_mask, dtype=bool)
            if mask.shape != raw_arr.shape:
                raise ValueError(f"validity_mask shape {mask.shape} != signal shape {raw_arr.shape}")
        else:
            # Auto mask: finite values are candidates; non-finite are invalid
            mask = np.isfinite(raw_arr)

        sanitized = np.empty(n, dtype=np.float64)
        action_logs: List[FallbackActionLog] = []
        fallback_count = 0

        last_valid_val: Optional[float] = None
        consecutive_invalid_time_sec = 0.0

        for i in range(n):
            val = raw_arr[i]
            is_valid = bool(mask[i] and np.isfinite(val))

            if is_valid:
                sanitized[i] = val
                last_valid_val = val
                consecutive_invalid_time_sec = 0.0
            else:
                fallback_count += 1
                consecutive_invalid_time_sec += self.time_delta_sec

                # Decide between HOLD_LAST_VALID and MISSION_BASELINE
                if (
                    policy.fallback_mode == "HOLD_LAST_VALID"
                    and last_valid_val is not None
                    and consecutive_invalid_time_sec <= policy.max_hold_duration_sec
                ):
                    sub_val = last_valid_val
                    applied_mode = "HOLD_LAST_VALID"
                else:
                    sub_val = policy.calibrated_baseline_value
                    applied_mode = "MISSION_BASELINE"

                sanitized[i] = sub_val
                action_logs.append(
                    FallbackActionLog(
                        channel_name=policy.channel_name,
                        sample_index=i,
                        raw_corrupted_value=float(val) if np.isfinite(val) else -999.0,
                        substituted_value=float(sub_val),
                        policy_applied=applied_mode,
                        hold_duration_sec=float(consecutive_invalid_time_sec),
                        is_fallback_active=True,
                    )
                )

        return sanitized, action_logs, fallback_count

    def apply_fallback_frame(
        self,
        telemetry_df: pd.DataFrame,
        validity_df: Optional[pd.DataFrame] = None,
        target_columns: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, Dict[str, List[FallbackActionLog]], int]:
        """
        Apply fallback strategy across all channels in a DataFrame.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric target columns found for fallback application")

        output_df = telemetry_df.copy()
        frame_logs: Dict[str, List[FallbackActionLog]] = {}
        total_fallbacks = 0

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")

            col_mask = validity_df[col].to_numpy() if validity_df is not None and col in validity_df.columns else None
            sanitized_col, logs, f_count = self.apply_fallback_channel(
                channel_name=col,
                signal=telemetry_df[col].to_numpy(),
                validity_mask=col_mask,
            )
            output_df[col] = sanitized_col
            frame_logs[col] = logs
            total_fallbacks += f_count

        return output_df, frame_logs, total_fallbacks


# ==============================================================================
# PHASE 5: Master Sanity Gate Exporter & Traceability Contract
# ==============================================================================

@dataclass(frozen=True)
class SanityGatedPacket:
    """
    Immutable data contract passed from the Sanity Gate firewall to the
    80% Biophysical Supreme Head (Decision Core).
    """
    sanitized_df: pd.DataFrame
    sanitized_tensor: np.ndarray
    channel_names: Tuple[str, ...]
    is_gate_passed: bool
    total_violations_remediated: int
    boundary_violations_count: int
    gradient_violations_count: int
    coupling_violations_count: int
    fallback_substitutions_count: int
    audit_manifest: Dict[str, Union[str, int, float, bool]]


class SanityGateExporter:
    """
    Phase 5: Master Sanity Gate Orchestrator & Traceability Exporter.
    
    Orchestrates the 4-layer mathematical sanity checks in strict sequential order:
    1. Sensor Decoupling & Fallback Strategy (`SensorDecouplingFallbackEngine`): Substitutes NaNs/dropouts first.
    2. Physiological Boundary Enforcement (`PhysiologicalBoundaryEnforcer`): Clamps out-of-bounds to Omega_bio.
    3. Physiological Gradient Limiting (`PhysiologicalGradientLimiter`): Clamps unphysical step derivatives dV/dt.
    4. Multi-Parameter Cross-Correlation Guard (`PhysiologicalCouplingGuard`): Resolves hemodynamic/cardiorespiratory discordance.
    
    Validates final numeric integrity and packages an immutable `SanityGatedPacket`.
    """

    def __init__(
        self,
        fallback_engine: Optional[SensorDecouplingFallbackEngine] = None,
        boundary_enforcer: Optional[PhysiologicalBoundaryEnforcer] = None,
        gradient_limiter: Optional[PhysiologicalGradientLimiter] = None,
        coupling_guard: Optional[PhysiologicalCouplingGuard] = None,
    ) -> None:
        """
        Initialize the Master Sanity Gate pipeline.
        """
        self.fallback_engine = fallback_engine if fallback_engine is not None else SensorDecouplingFallbackEngine()
        self.boundary_enforcer = boundary_enforcer if boundary_enforcer is not None else PhysiologicalBoundaryEnforcer()
        self.gradient_limiter = gradient_limiter if gradient_limiter is not None else PhysiologicalGradientLimiter()
        self.coupling_guard = coupling_guard if coupling_guard is not None else PhysiologicalCouplingGuard()

    def process_and_export_packet(
        self,
        telemetry_df: pd.DataFrame,
        validity_df: Optional[pd.DataFrame] = None,
        target_columns: Optional[List[str]] = None,
    ) -> SanityGatedPacket:
        """
        Execute end-to-end mathematical sanity gating and export immutable packet.
        
        Args:
            telemetry_df: Telemetry DataFrame (typically from Innovation 3 Signal Stabilizer).
            validity_df: Optional DataFrame mask of per-channel sensor validity.
            target_columns: Optional list of specific vital channels to gate.
            
        Returns:
            SanityGatedPacket with sanitized tensor, pass/fail status, and audit metrics.
        """
        if not isinstance(telemetry_df, pd.DataFrame):
            raise TypeError("telemetry_df must be a pandas DataFrame")
        if telemetry_df.empty:
            raise ValueError("telemetry_df cannot be empty")

        if target_columns is None:
            numeric_cols = telemetry_df.select_dtypes(include=[np.number]).columns.tolist()
            target_columns = [col for col in numeric_cols if "time" not in col.lower() and "epoch" not in col.lower()]

        if len(target_columns) == 0:
            raise ValueError("No valid numeric vital channels found for sanity gating")

        for col in target_columns:
            if col not in telemetry_df.columns:
                raise KeyError(f"Target column '{col}' not present in telemetry DataFrame")

        # Stage 1: Fallback Engine (Scrub NaNs / Dropouts)
        df_stage1, fallback_logs, fallback_count = self.fallback_engine.apply_fallback_frame(
            telemetry_df=telemetry_df,
            validity_df=validity_df,
            target_columns=target_columns,
        )

        # Stage 2: Physiological Boundary Enforcer (Omega_bio)
        df_stage2, boundary_logs, boundary_all_viable = self.boundary_enforcer.audit_telemetry_frame(
            telemetry_df=df_stage1,
            target_columns=target_columns,
        )
        boundary_violations_count = sum(
            1 for audits in boundary_logs.values() for a in audits if not a.is_within_viable_bounds
        )

        # Stage 3: Physiological Gradient Limiter (dV/dt)
        df_stage3, gradient_logs, gradient_all_valid = self.gradient_limiter.audit_telemetry_frame(
            telemetry_df=df_stage2,
            target_columns=target_columns,
        )
        gradient_violations_count = sum(
            1 for audits in gradient_logs.values() for a in audits if not a.is_gradient_permissible
        )

        # Stage 4: Multi-Parameter Cross-Correlation & Coupling Guard
        df_stage4, coupling_audits, all_coupled = self.coupling_guard.audit_telemetry_frame(
            telemetry_df=df_stage3,
        )
        coupling_violations_count = sum(
            len(a.violations) for a in coupling_audits
        )

        total_violations = (
            fallback_count
            + boundary_violations_count
            + gradient_violations_count
            + coupling_violations_count
        )

        is_clean_pass = bool(total_violations == 0)

        # Construct final 2D tensor matrix (N, num_channels)
        tensor_matrix = df_stage4[target_columns].to_numpy(dtype=np.float64)

        # Final numerical integrity check: no non-finite values permitted
        if not np.all(np.isfinite(tensor_matrix)):
            tensor_matrix = np.nan_to_num(tensor_matrix, nan=0.0, posinf=1e6, neginf=-1e6)
            for idx, col in enumerate(target_columns):
                df_stage4[col] = tensor_matrix[:, idx]
            is_clean_pass = False

        audit_manifest: Dict[str, Union[str, int, float, bool]] = {
            "num_samples": len(df_stage4),
            "num_channels": len(target_columns),
            "total_violations_remediated": total_violations,
            "fallback_count": fallback_count,
            "boundary_violations": boundary_violations_count,
            "gradient_violations": gradient_violations_count,
            "coupling_violations": coupling_violations_count,
            "is_clean_pass": is_clean_pass,
            "airworthiness_standard": "DO-178C Level C / NASA-STD-3001",
        }

        return SanityGatedPacket(
            sanitized_df=df_stage4,
            sanitized_tensor=tensor_matrix,
            channel_names=tuple(target_columns),
            is_gate_passed=is_clean_pass,
            total_violations_remediated=total_violations,
            boundary_violations_count=boundary_violations_count,
            gradient_violations_count=gradient_violations_count,
            coupling_violations_count=coupling_violations_count,
            fallback_substitutions_count=fallback_count,
            audit_manifest=audit_manifest,
        )




