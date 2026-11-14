"""
ASTROVITAL AI: VITALX CORE RECREATED V1
Test Suite: DO-178C Level C Verification for inno6_biomarker_ranker.py
Phase 1 Verification Tests (MissionContextMatrix)
File: 02_AI_CORE/02_tests/test_biomarker_ranker.py
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

from inno6_biomarker_ranker import (
    MissionOperationalPhase,
    STANDARD_12D_CHANNELS,
    MISSION_PHASE_PRIOR_WEIGHTS,
    ContextWeightResult,
    MissionContextMatrix,
    ChannelDeviationMetric,
    DeviationScoringResult,
    ASTRONAUT_RESTING_BASELINES,
    PhysiologicalDeviationScorer,
    EntropyEvaluationResult,
    EntropyWeightEngine,
    RankedBiomarker,
    CompositeRankingResult,
    CompositeSensitivityRanker,
    BiomarkerSensitivityContract,
    SensitivityContractExporter,
)


class TestPhase1MissionContextMatrix:
    """
    DO-178C Level C Requirements-Based Test Suite for Phase 1.
    Tests default initialization, custom priors, phase resolution, string aliases,
    normalization constraints (sum w_i == 1.0), and exception boundaries.
    """

    # --- Test 01: Default instantiation ---
    def test_01_default_instantiation(self):
        matrix = MissionContextMatrix()
        assert len(matrix.channels) == 12
        assert len(matrix.priors) == len(MissionOperationalPhase)

    # --- Test 02: Custom channels and priors instantiation ---
    def test_02_custom_instantiation(self):
        custom_channels = ("hr", "spo2")
        custom_priors = {
            MissionOperationalPhase.INTRA_VEHICULAR_NOMINAL: {"hr": 0.6, "spo2": 0.4}
        }
        matrix = MissionContextMatrix(custom_phase_priors=custom_priors, channels=custom_channels)
        assert matrix.channels == ("hr", "spo2")
        assert len(matrix.priors) == 1

    # --- Test 03: Reject empty channels tuple or empty priors ---
    def test_03_reject_empty_inputs(self):
        with pytest.raises(ValueError, match="channels tuple cannot be empty"):
            MissionContextMatrix(channels=())
        with pytest.raises(ValueError, match="Priors dictionary cannot be empty"):
            MissionContextMatrix(custom_phase_priors={})

    # --- Test 04: Phase resolution from enum, exact string, and lowercase ---
    def test_04_resolve_phase_variants(self):
        matrix = MissionContextMatrix()
        # Direct enum
        assert matrix.resolve_phase(MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT) == MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT
        # Exact string
        assert matrix.resolve_phase("EARLY_MICROGRAVITY_FLUID_SHIFT") == MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT
        # Lowercase / mixed case with spaces
        assert matrix.resolve_phase("  early_microgravity_fluid_shift  ") == MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT

    # --- Test 05: Reject invalid phase identifiers ---
    def test_05_reject_invalid_phase(self):
        matrix = MissionContextMatrix()
        with pytest.raises(ValueError, match="phase_input must be a non-empty string"):
            matrix.resolve_phase("")
        with pytest.raises(ValueError, match="phase_input must be a non-empty string"):
            matrix.resolve_phase(None)
        with pytest.raises(KeyError, match="Unknown operational mission phase"):
            matrix.resolve_phase("INTERSTELLAR_WARP_DRIVE")

    # --- Test 06: Early microgravity fluid shift boosts ICP and CVP ---
    def test_06_early_microgravity_profile(self):
        matrix = MissionContextMatrix()
        res = matrix.get_phase_weights(MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT)
        assert isinstance(res, ContextWeightResult)
        assert res.is_normalized is True
        np.testing.assert_allclose(np.sum(res.weight_vector), 1.0, atol=1e-6)
        # ICP and CVP must have top weights during early cephalad fluid shift
        assert res.weight_dict["icp_est_mmhg"] >= 0.20
        assert res.weight_dict["cvp_mmhg"] >= 0.15
        assert res.weight_dict["icp_est_mmhg"] > res.weight_dict["heart_rate_bpm"]

    # --- Test 07: EVA phase boosts RR, EtCO2, and Core Temp ---
    def test_07_eva_metabolic_profile(self):
        matrix = MissionContextMatrix()
        res = matrix.get_phase_weights(MissionOperationalPhase.EXTRAVEHICULAR_ACTIVITY_EVA)
        assert res.is_normalized is True
        # Metabolic parameters elevated
        assert res.weight_dict["resp_rate_bpm"] >= 0.12
        assert res.weight_dict["etco2_mmhg"] >= 0.12
        assert res.weight_dict["core_temp_c"] >= 0.12

    # --- Test 08: All standard mission phases satisfy strict unit normalization (sum == 1.0) ---
    def test_08_all_phases_normalized(self):
        matrix = MissionContextMatrix()
        for phase in MissionOperationalPhase:
            res = matrix.get_phase_weights(phase)
            assert res.is_normalized is True
            np.testing.assert_allclose(np.sum(res.weight_vector), 1.0, atol=1e-6)
            # All weights strictly positive
            assert np.all(res.weight_vector > 0.0)

    # --- Test 09: Target channels subset weighting and normalization ---
    def test_09_target_channels_subset(self):
        matrix = MissionContextMatrix()
        subset = ["heart_rate_bpm", "spo2_percent"]
        res = matrix.get_phase_weights("INTRA_VEHICULAR_NOMINAL", target_channels=subset)
        assert len(res.channel_order) == 2
        assert len(res.weight_vector) == 2
        np.testing.assert_allclose(np.sum(res.weight_vector), 1.0, atol=1e-6)

    # --- Test 10: Reject empty target channels list ---
    def test_10_reject_empty_target_channels(self):
        matrix = MissionContextMatrix()
        with pytest.raises(ValueError, match="selected_channels cannot be empty"):
            matrix.get_phase_weights("INTRA_VEHICULAR_NOMINAL", target_channels=[])

    # --- Test 11: Unmapped channel in subset receives uniform fallback weight ---
    def test_11_unmapped_channel_fallback(self):
        custom_priors = {
            MissionOperationalPhase.PRE_LAUNCH_RESTING: {"hr": 1.0}
        }
        matrix = MissionContextMatrix(custom_phase_priors=custom_priors, channels=("hr",))
        # Request channel not in custom prior map
        res = matrix.get_phase_weights("PRE_LAUNCH_RESTING", target_channels=["unmapped_ch"])
        assert res.weight_dict["unmapped_ch"] == 1.0

    # --- Test 12: Degenerate zero sum prior fallback branch ---
    def test_12_zero_sum_degenerate_fallback(self):
        custom_priors = {
            MissionOperationalPhase.PRE_LAUNCH_RESTING: {"ch1": 0.0, "ch2": 0.0}
        }
        matrix = MissionContextMatrix(custom_phase_priors=custom_priors, channels=("ch1", "ch2"))
        res = matrix.get_phase_weights("PRE_LAUNCH_RESTING")
        assert res.is_normalized is True
        np.testing.assert_allclose(res.weight_vector, [0.5, 0.5])


class TestPhase2PhysiologicalDeviationScorer:
    """
    DO-178C Level C Verification for Phase 2 PhysiologicalDeviationScorer.
    Tests robust MAD scaling, Z-score calculation, alias lookup, sigmoidal urgency
    weighting, vector scoring, and time-series DataFrame batch evaluation.
    """

    # --- Test 13: Default instantiation ---
    def test_13_default_instantiation(self):
        scorer = PhysiologicalDeviationScorer()
        assert len(scorer.baselines) == len(ASTRONAUT_RESTING_BASELINES)
        assert scorer.min_weight_floor == 0.02
        assert scorer.z_saturation == 6.0

    # --- Test 14: Custom instantiation and parameter rejection ---
    def test_14_custom_instantiation_and_validation(self):
        custom = {"hr": (70.0, 5.0)}
        scorer = PhysiologicalDeviationScorer(reference_baselines=custom, min_weight_floor=0.05, z_score_saturation_limit=5.0)
        assert len(scorer.baselines) == 1

        with pytest.raises(ValueError, match="min_weight_floor must be in"):
            PhysiologicalDeviationScorer(min_weight_floor=0.0)
        with pytest.raises(ValueError, match="min_weight_floor must be in"):
            PhysiologicalDeviationScorer(min_weight_floor=0.6)
        with pytest.raises(ValueError, match="z_score_saturation_limit must be > 1.0"):
            PhysiologicalDeviationScorer(z_score_saturation_limit=1.0)
        with pytest.raises(ValueError, match="Reference baselines dictionary cannot be empty"):
            PhysiologicalDeviationScorer(reference_baselines={})

    # --- Test 15: Exact baseline match yields zero Z-score ---
    def test_15_zero_z_score_on_exact_baseline(self):
        scorer = PhysiologicalDeviationScorer()
        # Baseline for heart_rate_bpm is (72.0, 6.0)
        z, med, mad = scorer.calculate_channel_z_score("heart_rate_bpm", 72.0)
        assert z == 0.0
        assert med == 72.0
        assert mad == 6.0

    # --- Test 16: Robust Z-score calculation with known deviation ---
    def test_16_robust_z_score_calculation(self):
        scorer = PhysiologicalDeviationScorer()
        # Baseline for heart_rate_bpm: med=72.0, mad=6.0 -> denom = 1.4826 * 6.0 = 8.8956
        # At HR = 90.0: delta = 18.0 -> z = 18.0 / 8.8956 ≈ 2.02347
        z, med, mad = scorer.calculate_channel_z_score("heart_rate_bpm", 90.0)
        expected_z = 18.0 / (1.4826 * 6.0)
        np.testing.assert_allclose(z, expected_z, atol=1e-5)

    # --- Test 17: Alias resolution and case-insensitivity ---
    def test_17_alias_lookup(self):
        scorer = PhysiologicalDeviationScorer()
        z1, med1, _ = scorer.calculate_channel_z_score("  SPO2_PERCENT  ", 98.0)
        assert med1 == 98.0
        z2, med2, _ = scorer.calculate_channel_z_score("spo2", 95.0)
        assert med2 == 98.0
        assert z2 > 0.0

    # --- Test 18: Reject non-finite values and unregistered channels ---
    def test_18_reject_invalid_z_score_inputs(self):
        scorer = PhysiologicalDeviationScorer()
        with pytest.raises(ValueError, match="must be finite"):
            scorer.calculate_channel_z_score("heart_rate_bpm", np.nan)
        with pytest.raises(ValueError, match="must be finite"):
            scorer.calculate_channel_z_score("heart_rate_bpm", np.inf)
        with pytest.raises(KeyError, match="No resting baseline registered"):
            scorer.calculate_channel_z_score("unknown_biomarker_qwe", 10.0)

    # --- Test 19: Handling zero/negative MAD gracefully ---
    def test_19_zero_mad_fallback(self):
        custom = {"ch_zero_mad": (50.0, 0.0)}
        scorer = PhysiologicalDeviationScorer(reference_baselines=custom)
        z, med, mad = scorer.calculate_channel_z_score("ch_zero_mad", 60.0)
        # Should fallback to MAD=1.0, so denom = 1.4826
        np.testing.assert_allclose(z, 10.0 / 1.4826, atol=1e-4)

    # --- Test 20: Vector scoring and relative urgency weight allocation ---
    def test_20_score_telemetry_vector_urgency_allocation(self):
        scorer = PhysiologicalDeviationScorer()
        # Construct telemetry where ICP is severely deviated (normal 10 -> now 25)
        # while HR, SpO2, and BP are close to normal baseline
        vec = {
            "heart_rate_bpm": 73.0,     # z ≈ 0.11
            "systolic_bp_mmhg": 119.0,  # z ≈ 0.08
            "spo2_percent": 98.0,       # z = 0.0
            "icp_est_mmhg": 25.0,       # z = 15.0 / (1.4826 * 2.0) ≈ 5.05 (Severe!)
        }
        res = scorer.score_telemetry_vector(vec)
        assert isinstance(res, DeviationScoringResult)
        assert res.max_deviating_channel == "icp_est_mmhg"
        assert res.max_z_score > 5.0
        np.testing.assert_allclose(np.sum(res.deviation_weight_vector), 1.0, atol=1e-6)
        # ICP should have the highest urgency weight
        assert res.channel_metrics["icp_est_mmhg"].deviation_urgency_weight > res.channel_metrics["heart_rate_bpm"].deviation_urgency_weight
        assert res.channel_metrics["icp_est_mmhg"].deviation_urgency_weight > res.channel_metrics["spo2_percent"].deviation_urgency_weight

    # --- Test 21: Vector scoring target channels subset ---
    def test_21_score_telemetry_vector_subset(self):
        scorer = PhysiologicalDeviationScorer()
        vec = {
            "heart_rate_bpm": 80.0,
            "spo2_percent": 97.0,
            "extra_channel": 123.0,
        }
        res = scorer.score_telemetry_vector(vec, target_channels=["heart_rate_bpm", "spo2_percent"])
        assert len(res.channel_order) == 2
        assert "extra_channel" not in res.channel_metrics
        np.testing.assert_allclose(np.sum(res.deviation_weight_vector), 1.0, atol=1e-6)

    # --- Test 22: Reject invalid inputs in score_telemetry_vector ---
    def test_22_reject_invalid_vector_inputs(self):
        scorer = PhysiologicalDeviationScorer()
        with pytest.raises(ValueError, match="current_values must be a non-empty dictionary"):
            scorer.score_telemetry_vector({})
        with pytest.raises(ValueError, match="current_values must be a non-empty dictionary"):
            scorer.score_telemetry_vector("invalid_string")
        with pytest.raises(ValueError, match="selected_channels cannot be empty"):
            scorer.score_telemetry_vector({"heart_rate_bpm": 70.0}, target_channels=[])
        with pytest.raises(KeyError, match="Target channel 'missing' not present"):
            scorer.score_telemetry_vector({"heart_rate_bpm": 70.0}, target_channels=["missing"])

    # --- Test 23: Batch DataFrame deviation scoring ---
    def test_23_score_telemetry_frame_auto(self):
        scorer = PhysiologicalDeviationScorer()
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=5, freq="min"),
            "heart_rate_bpm": [72.0, 80.0, 95.0, 85.0, 74.0],
            "spo2_percent": [98.0, 98.0, 96.0, 97.0, 98.0],
            "icp_est_mmhg": [10.0, 12.0, 22.0, 15.0, 11.0],
        })
        augmented_df, row_results, mean_weights = scorer.score_telemetry_frame(df)
        assert isinstance(augmented_df, pd.DataFrame)
        assert "telemetry_max_z_score" in augmented_df.columns
        assert len(row_results) == 5
        assert len(mean_weights) == 3  # hr, spo2, icp
        np.testing.assert_allclose(np.sum(mean_weights), 1.0, atol=1e-6)
        # Row 2 (index 2) had HR=95 and ICP=22, so max_z must be highest there
        assert augmented_df["telemetry_max_z_score"].iloc[2] > augmented_df["telemetry_max_z_score"].iloc[0]

    # --- Test 24: Error handling in score_telemetry_frame ---
    def test_24_score_telemetry_frame_exceptions(self):
        scorer = PhysiologicalDeviationScorer()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            scorer.score_telemetry_frame("invalid")
        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            scorer.score_telemetry_frame(pd.DataFrame())

        text_df = pd.DataFrame({"astronaut": ["AS01", "AS02"]})
        with pytest.raises(ValueError, match="No valid numeric target columns"):
            scorer.score_telemetry_frame(text_df)


class TestPhase3EntropyWeightEngine:
    """
    DO-178C Level C Verification for Phase 3 EntropyWeightEngine.
    Tests Shannon entropy calculation, information divergence d_j = 1 - E_j,
    flatline zero-dispersion handling, short sample horizons, and Dirichlet normalization.
    """

    # --- Test 25: Default initialization ---
    def test_25_default_instantiation(self):
        engine = EntropyWeightEngine()
        assert engine.min_entropy_floor == 0.01
        assert engine.epsilon == 1e-12

    # --- Test 26: Custom initialization and parameter validation ---
    def test_26_custom_instantiation(self):
        engine = EntropyWeightEngine(min_entropy_floor=0.05, epsilon=1e-8)
        assert engine.min_entropy_floor == 0.05
        assert engine.epsilon == 1e-8

        with pytest.raises(ValueError, match="min_entropy_floor must be in"):
            EntropyWeightEngine(min_entropy_floor=0.0)
        with pytest.raises(ValueError, match="min_entropy_floor must be in"):
            EntropyWeightEngine(min_entropy_floor=0.55)
        with pytest.raises(ValueError, match="epsilon must be strictly positive"):
            EntropyWeightEngine(epsilon=0.0)

    # --- Test 27: Short temporal horizon (samples < 3) uniform fallback ---
    def test_27_short_horizon_uniform_fallback(self):
        engine = EntropyWeightEngine()
        # 2 samples, 3 channels
        mat = np.array([
            [70.0, 120.0, 98.0],
            [72.0, 122.0, 97.0],
        ])
        res = engine.calculate_entropy_weights(mat, channel_names=["hr", "bp", "spo2"])
        assert isinstance(res, EntropyEvaluationResult)
        assert res.is_valid is True
        np.testing.assert_allclose(res.weight_vector, [1/3, 1/3, 1/3], atol=1e-6)

    # --- Test 28: Active variable channel receives higher entropy weight than flatline ---
    def test_28_active_vs_flatline_channel(self):
        engine = EntropyWeightEngine()
        n = 50
        np.random.seed(42)
        # Channel 0: active dynamic fluctuation (high information dispersion)
        ch_active = 75.0 + 10.0 * np.sin(np.linspace(0, 10, n))
        # Channel 1: flatline sensor (zero dispersion)
        ch_flat = np.ones(n) * 98.0

        data_df = pd.DataFrame({
            "hr_active": ch_active,
            "spo2_flat": ch_flat,
        })

        res = engine.calculate_entropy_weights(data_df)
        assert res.is_valid is True
        np.testing.assert_allclose(np.sum(res.weight_vector), 1.0, atol=1e-6)
        # Flatline entropy should be 1.0 (zero information divergence)
        assert res.channel_entropies["spo2_flat"] == 1.0
        # Active channel entropy must be lower than 1.0
        assert res.channel_entropies["hr_active"] < 1.0
        # Consequently, active channel receives higher weight
        assert res.entropy_weights["hr_active"] > res.entropy_weights["spo2_flat"]

    # --- Test 29: Support 2D numpy array with explicit channel names ---
    def test_29_numpy_array_input(self):
        engine = EntropyWeightEngine()
        np.random.seed(42)
        mat = np.random.normal(50, 5, size=(30, 4))
        names = ["c1", "c2", "c3", "c4"]
        res = engine.calculate_entropy_weights(mat, channel_names=names)
        assert len(res.channel_order) == 4
        np.testing.assert_allclose(np.sum(res.weight_vector), 1.0, atol=1e-6)

    # --- Test 30: Reject invalid data types and non-2D matrices ---
    def test_30_reject_invalid_data_inputs(self):
        engine = EntropyWeightEngine()
        with pytest.raises(TypeError, match="Unsupported data type"):
            engine.calculate_entropy_weights("invalid_string")
        with pytest.raises(ValueError, match="Input DataFrame data cannot be empty"):
            engine.calculate_entropy_weights(pd.DataFrame())
        with pytest.raises(ValueError, match="Input ndarray must be 2D"):
            engine.calculate_entropy_weights(np.array([1, 2, 3]))
        with pytest.raises(ValueError, match="Input ndarray must be 2D"):
            engine.calculate_entropy_weights(np.empty((0, 2)))
        with pytest.raises(ValueError, match="channel_names must match column count"):
            engine.calculate_entropy_weights(np.ones((10, 3)), channel_names=["c1", "c2"])

    # --- Test 31: Reject NaN and Inf in calculate_entropy_weights ---
    def test_31_reject_nan_inf_entropy(self):
        engine = EntropyWeightEngine()
        nan_mat = np.array([[1.0, np.nan], [2.0, 3.0], [4.0, 5.0]])
        with pytest.raises(ValueError, match="contains NaN or Inf"):
            engine.calculate_entropy_weights(nan_mat, channel_names=["c1", "c2"])

    # --- Test 32: DataFrame with no numeric columns rejection ---
    def test_32_reject_df_without_numeric(self):
        engine = EntropyWeightEngine()
        text_df = pd.DataFrame({"pilot": ["P1", "P2", "P3"]})
        with pytest.raises(ValueError, match="No valid numeric channels found"):
            engine.calculate_entropy_weights(text_df)


class TestPhase4CompositeSensitivityRanker:
    """
    DO-178C Level C Verification for Phase 4 CompositeSensitivityRanker.
    Tests convex fusion (alpha, beta, gamma), Dirichlet simplex normalization,
    minimum floor enforcement, ranking sort accuracy, and error handling.
    """

    # --- Test 33: Default instantiation ---
    def test_33_default_instantiation(self):
        ranker = CompositeSensitivityRanker()
        assert ranker.alpha == 0.35
        assert ranker.beta == 0.45
        assert ranker.gamma == 0.20
        assert ranker.min_floor == 0.01

    # --- Test 34: Custom initialization and coefficient auto-normalization ---
    def test_34_custom_instantiation(self):
        # 2, 2, 1 -> total 5 -> alpha=0.4, beta=0.4, gamma=0.2
        ranker = CompositeSensitivityRanker(alpha_context=2.0, beta_deviation=2.0, gamma_entropy=1.0)
        np.testing.assert_allclose(ranker.alpha + ranker.beta + ranker.gamma, 1.0)
        assert ranker.alpha == 0.4
        assert ranker.beta == 0.4
        assert ranker.gamma == 0.2

    # --- Test 35: Reject invalid parameters in initialization ---
    def test_35_reject_invalid_parameters(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            CompositeSensitivityRanker(alpha_context=-0.1)
        with pytest.raises(ValueError, match="Sum of fusion coefficients must be strictly positive"):
            CompositeSensitivityRanker(alpha_context=0.0, beta_deviation=0.0, gamma_entropy=0.0)
        with pytest.raises(ValueError, match="min_weight_floor must be in"):
            CompositeSensitivityRanker(min_weight_floor=0.0)
        with pytest.raises(ValueError, match="min_weight_floor must be in"):
            CompositeSensitivityRanker(min_weight_floor=0.3)

    # --- Test 36: Full fusion with dictionary inputs ---
    def test_36_fuse_dict_inputs(self):
        ranker = CompositeSensitivityRanker(alpha_context=0.3, beta_deviation=0.5, gamma_entropy=0.2)
        ctx = {"hr": 0.2, "bp": 0.3, "icp": 0.5}
        dev = {"hr": 0.1, "bp": 0.1, "icp": 0.8}
        ent = {"hr": 0.4, "bp": 0.3, "icp": 0.3}

        res = ranker.fuse_sensitivity_vectors(ctx, dev, ent)
        assert isinstance(res, CompositeRankingResult)
        assert res.is_strictly_normalized is True
        np.testing.assert_allclose(np.sum(res.composite_weight_vector), 1.0, atol=1e-6)
        # ICP has highest weights across context and deviation, so it must be rank 1
        assert res.ranked_biomarkers[0].channel_name == "icp"
        assert res.ranked_biomarkers[0].rank == 1
        assert res.ranked_biomarkers[0].composite_weight > res.ranked_biomarkers[1].composite_weight

    # --- Test 37: Full fusion with 1D numpy array inputs and channel names ---
    def test_37_fuse_numpy_array_inputs(self):
        ranker = CompositeSensitivityRanker()
        w_ctx = np.array([0.25, 0.25, 0.25, 0.25])
        w_dev = np.array([0.10, 0.60, 0.15, 0.15])  # channel 1 dominant
        w_ent = np.array([0.25, 0.25, 0.25, 0.25])
        names = ["c0", "c1", "c2", "c3"]

        res = ranker.fuse_sensitivity_vectors(w_ctx, w_dev, w_ent, channel_names=names)
        assert res.is_strictly_normalized is True
        # c1 must be top rank
        assert res.ranked_biomarkers[0].channel_name == "c1"
        assert res.ranked_biomarkers[0].rank == 1

    # --- Test 38: Minimum weight floor enforcement ---
    def test_38_min_weight_floor_enforcement(self):
        # A channel with zero weights in all 3 components must still receive >= floor
        ranker = CompositeSensitivityRanker(min_weight_floor=0.05)
        ctx = {"c1": 1.0, "c2": 0.0}
        dev = {"c1": 1.0, "c2": 0.0}
        ent = {"c1": 1.0, "c2": 0.0}

        res = ranker.fuse_sensitivity_vectors(ctx, dev, ent)
        assert res.composite_weight_dict["c2"] >= 0.045  # Near 0.05 after final normalization
        assert res.composite_weight_dict["c1"] > res.composite_weight_dict["c2"]

    # --- Test 39: Error handling on mismatched dimensions and empty inputs ---
    def test_39_fuse_exceptions(self):
        ranker = CompositeSensitivityRanker()
        with pytest.raises(TypeError, match="Unsupported input type"):
            ranker.fuse_sensitivity_vectors("invalid", {}, {})

        with pytest.raises(ValueError, match="channel_names cannot be empty"):
            ranker.fuse_sensitivity_vectors({}, {}, {}, channel_names=[])

        with pytest.raises(ValueError, match="channel_names must match array length"):
            ranker.fuse_sensitivity_vectors(np.ones(3), np.ones(3), np.ones(3), channel_names=["c1", "c2"])

        with pytest.raises(ValueError, match="matching dimensions"):
            ranker.fuse_sensitivity_vectors(np.ones(3), np.ones(2), np.ones(3), channel_names=["c1", "c2", "c3"])


class TestPhase5SensitivityContractExporter:
    """
    DO-178C Level C Verification for Phase 5 SensitivityContractExporter.
    Tests master pipeline orchestration, contract data schema, flight certification,
    channel subset selection, and exception safety.
    """

    # --- Test 40: Default instantiation ---
    def test_40_default_instantiation(self):
        exporter = SensitivityContractExporter()
        assert isinstance(exporter.context_matrix, MissionContextMatrix)
        assert isinstance(exporter.deviation_scorer, PhysiologicalDeviationScorer)
        assert isinstance(exporter.entropy_engine, EntropyWeightEngine)
        assert isinstance(exporter.composite_ranker, CompositeSensitivityRanker)

    # --- Test 41: Custom subcomponents instantiation ---
    def test_41_custom_instantiation(self):
        cm = MissionContextMatrix()
        ds = PhysiologicalDeviationScorer(min_weight_floor=0.03)
        ee = EntropyWeightEngine(min_entropy_floor=0.02)
        cr = CompositeSensitivityRanker(alpha_context=0.4, beta_deviation=0.4, gamma_entropy=0.2)

        exporter = SensitivityContractExporter(
            context_matrix=cm,
            deviation_scorer=ds,
            entropy_engine=ee,
            composite_ranker=cr,
        )
        assert exporter.context_matrix == cm
        assert exporter.deviation_scorer == ds
        assert exporter.entropy_engine == ee
        assert exporter.composite_ranker == cr

    # --- Test 42: End-to-end contract execution on early microgravity fluid shift ---
    def test_42_end_to_end_early_microgravity_contract(self):
        exporter = SensitivityContractExporter()
        n = 50
        np.random.seed(42)
        # Create synthetic microgravity transition telemetry:
        # ICP and CVP elevated due to cephalad fluid shift
        df = pd.DataFrame({
            "timestamp": pd.date_range("2026-11-14 12:00", periods=n, freq="min"),
            "heart_rate_bpm": 72.0 + np.random.normal(0, 1.0, n),
            "systolic_bp_mmhg": 118.0 + np.random.normal(0, 2.0, n),
            "diastolic_bp_mmhg": 76.0 + np.random.normal(0, 1.5, n),
            "spo2_percent": 98.0 + np.random.normal(0, 0.5, n),
            "icp_est_mmhg": 24.0 + np.random.normal(0, 2.0, n),  # Significant elevation
            "cvp_mmhg": 14.0 + np.random.normal(0, 1.0, n),      # Significant elevation
        })

        contract = exporter.process_and_export_contract(
            telemetry_df=df,
            phase=MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT,
        )

        assert isinstance(contract, BiomarkerSensitivityContract)
        assert contract.is_flight_certified is True
        assert contract.phase == MissionOperationalPhase.EARLY_MICROGRAVITY_FLUID_SHIFT
        assert len(contract.channel_order) == 6
        assert len(contract.sensitivity_weights) == 6
        np.testing.assert_allclose(np.sum(contract.sensitivity_weights), 1.0, atol=1e-5)
        # In early microgravity with high ICP/CVP, top critical channel should be ICP or CVP
        assert contract.top_critical_channel in ["icp_est_mmhg", "cvp_mmhg"]
        assert contract.top_critical_weight > 0.15
        assert contract.audit_manifest["is_flight_certified"] is True

    # --- Test 43: End-to-end contract on EVA phase with explicit channel subset ---
    def test_43_eva_phase_contract(self):
        exporter = SensitivityContractExporter()
        n = 30
        np.random.seed(42)
        df = pd.DataFrame({
            "heart_rate_bpm": 95.0 + np.random.normal(0, 3.0, n),
            "resp_rate_bpm": 22.0 + np.random.normal(0, 2.0, n),
            "core_temp_c": 37.6 + np.random.normal(0, 0.2, n),
        })

        contract = exporter.process_and_export_contract(
            telemetry_df=df,
            phase="EXTRAVEHICULAR_ACTIVITY_EVA",
            target_columns=["heart_rate_bpm", "resp_rate_bpm", "core_temp_c"],
        )

        assert contract.phase == MissionOperationalPhase.EXTRAVEHICULAR_ACTIVITY_EVA
        assert len(contract.ranked_biomarkers) == 3
        assert contract.ranked_biomarkers[0].rank == 1
        assert contract.ranked_biomarkers[1].rank == 2
        assert contract.ranked_biomarkers[2].rank == 3
        np.testing.assert_allclose(np.sum(contract.sensitivity_weights), 1.0, atol=1e-5)

    # --- Test 44: Exporter exceptions and defensive error handling ---
    def test_44_exporter_exceptions(self):
        exporter = SensitivityContractExporter()
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            exporter.process_and_export_contract("invalid")

        with pytest.raises(ValueError, match="telemetry_df cannot be empty"):
            exporter.process_and_export_contract(pd.DataFrame())

        text_df = pd.DataFrame({"pilot": ["P1", "P2"]})
        with pytest.raises(ValueError, match="No valid numeric channels found"):
            exporter.process_and_export_contract(text_df)

        valid_df = pd.DataFrame({"heart_rate_bpm": [70.0, 72.0, 74.0]})
        with pytest.raises(KeyError, match="Target column 'missing' not present"):
            exporter.process_and_export_contract(valid_df, target_columns=["missing"])




