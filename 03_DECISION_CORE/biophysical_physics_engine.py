"""
=============================================================================
ASTROVITAL AI : VITALX CORE RECREATED V1
Subsystem: 03_DECISION_CORE
Module: biophysical_physics_engine.py
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)
Safety Standard: DO-178C Level C (DAL C) / ARP4754A Deterministic Engine
Governance: First-Principles Spaceflight Biophysics (80% Biophysical Supreme Head)
=============================================================================
"""

import math
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Union, Any
import numpy as np
import pandas as pd

from rule_schema_validator import (
    BiophysicalConstantsContract,
    DecisionConfigManager,
    load_default_decision_configuration,
)


# =============================================================================
# DO-178C DETERMINISTIC BIOPHYSICAL OUTPUT PACKETS
# =============================================================================

@dataclass(frozen=True)
class HemodynamicPacket:
    """Calculated cardiovascular hemodynamic parameters."""
    pulse_pressure_mmhg: float
    map_mmhg: float
    shock_index: float
    modified_shock_index: float
    cerebral_perfusion_pressure_mmhg: float
    is_shock_indicated: bool
    is_cerebral_ischemia_threat: bool


@dataclass(frozen=True)
class FluidShiftPacket:
    """Calculated Cephalad Fluid Shift & ICP Hydrodynamic parameters."""
    icp_gradient_index: float
    alpha_1_contribution: float
    alpha_2_contribution: float
    alpha_3_contribution: float
    alpha_4_contribution: float
    is_green_equilibrium: bool
    is_amber_warning: bool
    is_red_critical: bool
    clinical_risk_tier: str


@dataclass(frozen=True)
class CardiacOutputPacket:
    """Calculated myocardial stroke volume and cardiac performance."""
    stroke_volume_ml: float
    cardiac_output_l_min: float
    atrophy_factor: float
    exercise_attenuation: float
    is_stroke_volume_depleted: bool


@dataclass(frozen=True)
class BiophysicalEnrichedPacket:
    """Comprehensive biophysical snapshot combining all first-principles derivations."""
    raw_telemetry: Dict[str, float]
    hemodynamics: HemodynamicPacket
    fluid_shift: FluidShiftPacket
    cardiac_output: CardiacOutputPacket
    enriched_telemetry: Dict[str, float]


# =============================================================================
# FIRST-PRINCIPLES BIOPHYSICAL PHYSICS ENGINE
# =============================================================================

class BiophysicalPhysicsEngine:
    """
    DO-178C Level C Certified Closed-Form Spaceflight Biophysics Engine.
    Executes first-principles physiological formulations:
    1. Cephalad Fluid Shift & Intracranial Pressure (ICP) Index:
       I_ICP(t) = alpha1*(MAP/MAP_base) + alpha2*ln(1 + t_ug) + alpha3*(P_CO2/P_CO2_base) - alpha4*(RMSSD/RMSSD_base)
    2. Left Ventricular Stroke Volume Degradation:
       SV(t) = SV_0 * exp(-kappa * t_ug) * [1 + beta * ExerciseMetric]
    3. Hemodynamic indices: MAP, PP, Shock Index (SI), Modified Shock Index (MSI), CPP.
    """

    def __init__(self, config_manager: Optional[DecisionConfigManager] = None):
        if config_manager is None:
            self.config_manager = load_default_decision_configuration()
        else:
            self.config_manager = config_manager

        self.constants: BiophysicalConstantsContract = self.config_manager.biophysical_constants

    # -------------------------------------------------------------------------
    # 1. HEMODYNAMIC EQUATIONS (MAP, PP, SI, MSI, CPP)
    # -------------------------------------------------------------------------
    def compute_hemodynamics(
        self,
        systolic_bp: float,
        diastolic_bp: float,
        heart_rate: float,
        icp_est: Optional[float] = None
    ) -> HemodynamicPacket:
        """
        Computes closed-form cardiovascular hemodynamics.
        Mathematical Formulas:
        - Pulse Pressure: PP = SBP - DBP
        - Mean Arterial Pressure: MAP = DBP + (1/3) * PP = (2*DBP + SBP) / 3
        - Shock Index: SI = HR / SBP
        - Modified Shock Index: MSI = HR / MAP
        - Cerebral Perfusion Pressure: CPP = MAP - ICP
        """
        # Defensive boundary checks
        if not math.isfinite(systolic_bp) or not math.isfinite(diastolic_bp) or not math.isfinite(heart_rate):
            raise ValueError(f"DO-178C Violation: Non-finite inputs to hemodynamics (SBP={systolic_bp}, DBP={diastolic_bp}, HR={heart_rate})")

        if systolic_bp <= 0.0 or diastolic_bp <= 0.0 or heart_rate <= 0.0:
            raise ValueError(f"DO-178C Violation: Pressures and heart rate must be strictly positive (SBP={systolic_bp}, DBP={diastolic_bp}, HR={heart_rate})")

        if systolic_bp < diastolic_bp:
            raise ValueError(f"DO-178C Violation: Systolic pressure ({systolic_bp}) cannot be less than diastolic ({diastolic_bp})")

        # Closed-form derivations
        pp = systolic_bp - diastolic_bp
        map_val = diastolic_bp + (pp / 3.0)

        si = heart_rate / max(systolic_bp, 1.0)
        msi = heart_rate / max(map_val, 1.0)

        # Default ICP if not supplied
        effective_icp = icp_est if icp_est is not None and math.isfinite(icp_est) else self.constants.baselines.icp_baseline_mmhg
        cpp = map_val - effective_icp

        is_shock = si >= self.constants.si_decompensated_critical
        is_ischemia = cpp < self.constants.critical_floor_cpp_mmhg

        return HemodynamicPacket(
            pulse_pressure_mmhg=float(pp),
            map_mmhg=float(map_val),
            shock_index=float(si),
            modified_shock_index=float(msi),
            cerebral_perfusion_pressure_mmhg=float(cpp),
            is_shock_indicated=bool(is_shock),
            is_cerebral_ischemia_threat=bool(is_ischemia)
        )

    # -------------------------------------------------------------------------
    # 2. CEPHALAD FLUID SHIFT & INTRACRANIAL PRESSURE (ICP) INDEX (INNOVATION 1)
    # -------------------------------------------------------------------------
    def compute_fluid_shift_index(
        self,
        map_mmhg: float,
        microgravity_days: float,
        cabin_co2_ppm: float,
        rmssd_ms: Optional[float] = None
    ) -> FluidShiftPacket:
        """
        Closed-form formulation of the Cephalad Fluid Shift Hydrodynamic Gradient Index I_ICP:
        I_ICP = alpha1 * (MAP / MAP_0)
              + alpha2 * ln(1 + t_ug)
              + alpha3 * (P_CO2 / P_CO2_0)
              - alpha4 * (RMSSD / RMSSD_0)

        Where sum(alpha_i) == 1.0.
        """
        # Defensive input verification
        if not math.isfinite(map_mmhg) or not math.isfinite(microgravity_days) or not math.isfinite(cabin_co2_ppm):
            raise ValueError("DO-178C Violation: Non-finite inputs to fluid shift computation.")

        if microgravity_days < 0.0:
            raise ValueError(f"DO-178C Violation: Microgravity duration cannot be negative ({microgravity_days})")

        if cabin_co2_ppm < 0.0 or map_mmhg <= 0.0:
            raise ValueError(f"DO-178C Violation: Negative or zero physiological values (MAP={map_mmhg}, CO2={cabin_co2_ppm})")

        cfg = self.constants.cephalad_shift
        base = self.constants.baselines

        effective_rmssd = rmssd_ms if rmssd_ms is not None and math.isfinite(rmssd_ms) and rmssd_ms > 0 else base.rmssd_baseline_ms

        # Component contributions
        norm_map = map_mmhg / base.map_baseline_mmhg
        c1 = cfg.alpha_1 * norm_map

        # Logarithmic saturation of microgravity exposure
        c2 = cfg.alpha_2 * math.log(1.0 + microgravity_days)

        norm_co2 = cabin_co2_ppm / base.cabin_co2_baseline_ppm
        c3 = cfg.alpha_3 * norm_co2

        norm_rmssd = effective_rmssd / base.rmssd_baseline_ms
        c4 = cfg.alpha_4 * norm_rmssd

        # Closed-form index with non-negative lower bound
        i_icp = max(0.0, c1 + c2 + c3 - c4)

        # Classification into DO-178C triage envelopes
        is_green = i_icp < cfg.green_upper_bound
        is_amber = cfg.green_upper_bound <= i_icp < cfg.red_critical_threshold
        is_red = i_icp >= cfg.red_critical_threshold

        if is_red:
            tier = "CRITICAL_RED"
        elif is_amber:
            tier = "WARNING_AMBER"
        else:
            tier = "NOMINAL_GREEN"

        return FluidShiftPacket(
            icp_gradient_index=float(i_icp),
            alpha_1_contribution=float(c1),
            alpha_2_contribution=float(c2),
            alpha_3_contribution=float(c3),
            alpha_4_contribution=float(c4),
            is_green_equilibrium=bool(is_green),
            is_amber_warning=bool(is_amber),
            is_red_critical=bool(is_red),
            clinical_risk_tier=tier
        )

    # -------------------------------------------------------------------------
    # 3. MYOCARDIAL STROKE VOLUME ATROPHY & CARDIAC OUTPUT
    # -------------------------------------------------------------------------
    def compute_cardiac_deconditioning(
        self,
        heart_rate_bpm: float,
        microgravity_days: float,
        exercise_metric: float = 1.0
    ) -> CardiacOutputPacket:
        """
        Computes left ventricular stroke volume degradation under microgravity:
        SV(t) = SV_0 * exp(-kappa_atrophy * t_ug) * [1 + beta_exercise * ExerciseMetric]

        Cardiac Output:
        CO(t) = (SV(t) * HR(t)) / 1000.0 (L/min)
        """
        if not math.isfinite(heart_rate_bpm) or not math.isfinite(microgravity_days) or not math.isfinite(exercise_metric):
            raise ValueError("DO-178C Violation: Non-finite inputs to cardiac deconditioning.")

        if heart_rate_bpm <= 0.0 or microgravity_days < 0.0:
            raise ValueError("DO-178C Violation: Heart rate must be > 0 and days >= 0.")

        cfg = self.constants.stroke_volume

        # Bounded exercise compliance metric [0.0, 1.0]
        clamped_exercise = max(0.0, min(1.0, exercise_metric))

        atrophy_decay = math.exp(-cfg.kappa_atrophy * microgravity_days)
        exercise_attenuation = 1.0 + (cfg.beta_exercise * clamped_exercise)

        raw_sv = cfg.sv_0_ml * atrophy_decay * exercise_attenuation

        # Physiological clamping (bounded within viable human left ventricular chamber volumes)
        clamped_sv = max(cfg.min_viable_sv_ml, min(140.0, raw_sv))

        cardiac_output = (clamped_sv * heart_rate_bpm) / 1000.0
        is_depleted = clamped_sv <= cfg.warning_threshold_sv_ml

        return CardiacOutputPacket(
            stroke_volume_ml=float(clamped_sv),
            cardiac_output_l_min=float(cardiac_output),
            atrophy_factor=float(atrophy_decay),
            exercise_attenuation=float(exercise_attenuation),
            is_stroke_volume_depleted=bool(is_depleted)
        )

    # -------------------------------------------------------------------------
    # 4. TELEMETRY PACKET ENRICHMENT (COMBINING 12D + DERIVED METRICS)
    # -------------------------------------------------------------------------
    def enrich_telemetry_packet(
        self,
        telemetry: Dict[str, float],
        microgravity_days: float = 14.0,
        exercise_metric: float = 1.0,
        rmssd_ms: Optional[float] = None
    ) -> BiophysicalEnrichedPacket:
        """
        Enriches a raw or conditioned 12-channel telemetry dictionary with
        all first-principles biophysical metrics required by the DO-178C triage core.
        """
        sbp = telemetry.get("systolic_bp_mmhg", self.constants.baselines.systolic_bp_baseline_mmhg)
        dbp = telemetry.get("diastolic_bp_mmhg", self.constants.baselines.diastolic_bp_baseline_mmhg)
        hr = telemetry.get("heart_rate_bpm", self.constants.baselines.heart_rate_baseline_bpm)
        icp_est = telemetry.get("icp_est_mmhg", self.constants.baselines.icp_baseline_mmhg)
        co2_ppm = telemetry.get("co2_cabin_ppm", self.constants.baselines.cabin_co2_baseline_ppm)

        hemo = self.compute_hemodynamics(
            systolic_bp=sbp,
            diastolic_bp=dbp,
            heart_rate=hr,
            icp_est=icp_est
        )

        fluid = self.compute_fluid_shift_index(
            map_mmhg=hemo.map_mmhg,
            microgravity_days=microgravity_days,
            cabin_co2_ppm=co2_ppm,
            rmssd_ms=rmssd_ms
        )

        cardiac = self.compute_cardiac_deconditioning(
            heart_rate_bpm=hr,
            microgravity_days=microgravity_days,
            exercise_metric=exercise_metric
        )

        # Merge enriched metrics into telemetry dictionary for rule evaluation
        enriched = dict(telemetry)
        enriched["pulse_pressure_mmhg"] = hemo.pulse_pressure_mmhg
        enriched["map_mmhg"] = hemo.map_mmhg
        enriched["shock_index"] = hemo.shock_index
        enriched["modified_shock_index"] = hemo.modified_shock_index
        enriched["cerebral_perfusion_pressure_mmhg"] = hemo.cerebral_perfusion_pressure_mmhg
        enriched["icp_gradient_index"] = fluid.icp_gradient_index
        enriched["stroke_volume_ml"] = cardiac.stroke_volume_ml
        enriched["cardiac_output_l_min"] = cardiac.cardiac_output_l_min
        enriched["microgravity_days"] = float(microgravity_days)

        # Ensure sleep debt channel exists if not provided
        if "sleep_debt_hours" not in enriched:
            enriched["sleep_debt_hours"] = 0.0

        return BiophysicalEnrichedPacket(
            raw_telemetry=dict(telemetry),
            hemodynamics=hemo,
            fluid_shift=fluid,
            cardiac_output=cardiac,
            enriched_telemetry=enriched
        )

    # -------------------------------------------------------------------------
    # 5. VECTORIZED PANDAS STREAM ENRICHMENT (FOR PIPELINE & LAB EXPERIMENTS)
    # -------------------------------------------------------------------------
    def enrich_dataframe_stream(
        self,
        df: pd.DataFrame,
        microgravity_days: float = 14.0,
        exercise_metric: float = 1.0,
        rmssd_ms: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Enriches a multi-row DataFrame stream with vectorized biophysical computations.
        Guarantees deterministic output across all temporal frames.
        """
        df_out = df.copy()

        # Extract channels with safe fallbacks
        sbp = df_out.get("systolic_bp_mmhg", pd.Series(self.constants.baselines.systolic_bp_baseline_mmhg, index=df_out.index))
        dbp = df_out.get("diastolic_bp_mmhg", pd.Series(self.constants.baselines.diastolic_bp_baseline_mmhg, index=df_out.index))
        hr = df_out.get("heart_rate_bpm", pd.Series(self.constants.baselines.heart_rate_baseline_bpm, index=df_out.index))
        icp_est = df_out.get("icp_est_mmhg", pd.Series(self.constants.baselines.icp_baseline_mmhg, index=df_out.index))
        co2_ppm = df_out.get("co2_cabin_ppm", pd.Series(self.constants.baselines.cabin_co2_baseline_ppm, index=df_out.index))

        # Vectorized hemodynamics
        pp = sbp - dbp
        map_val = dbp + (pp / 3.0)
        si = hr / sbp.clip(lower=1.0)
        msi = hr / map_val.clip(lower=1.0)
        cpp = map_val - icp_est

        df_out["pulse_pressure_mmhg"] = pp
        df_out["map_mmhg"] = map_val
        df_out["shock_index"] = si
        df_out["modified_shock_index"] = msi
        df_out["cerebral_perfusion_pressure_mmhg"] = cpp

        # Vectorized Cephalad Fluid Shift
        cfg = self.constants.cephalad_shift
        base = self.constants.baselines

        eff_rmssd = rmssd_ms if rmssd_ms is not None and rmssd_ms > 0 else base.rmssd_baseline_ms
        c1 = cfg.alpha_1 * (map_val / base.map_baseline_mmhg)
        c2 = cfg.alpha_2 * math.log(1.0 + max(0.0, microgravity_days))
        c3 = cfg.alpha_3 * (co2_ppm / base.cabin_co2_baseline_ppm)
        c4 = cfg.alpha_4 * (eff_rmssd / base.rmssd_baseline_ms)

        i_icp = (c1 + c2 + c3 - c4).clip(lower=0.0)
        df_out["icp_gradient_index"] = i_icp

        # Vectorized Cardiac Deconditioning
        sva = self.constants.stroke_volume
        atrophy = math.exp(-sva.kappa_atrophy * max(0.0, microgravity_days))
        atten = 1.0 + (sva.beta_exercise * max(0.0, min(1.0, exercise_metric)))
        sv = (sva.sv_0_ml * atrophy * atten)
        clamped_sv = np.clip(sv, sva.min_viable_sv_ml, 140.0)

        df_out["stroke_volume_ml"] = clamped_sv
        df_out["cardiac_output_l_min"] = (clamped_sv * hr) / 1000.0
        df_out["microgravity_days"] = float(microgravity_days)

        if "sleep_debt_hours" not in df_out.columns:
            df_out["sleep_debt_hours"] = 0.0

        return df_out
