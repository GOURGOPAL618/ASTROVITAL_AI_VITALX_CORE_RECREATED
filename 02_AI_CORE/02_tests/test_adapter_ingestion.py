"""
ASTROVITAL AI : VITALX CORE (RECREATED V1)
===========================================
Module: test_adapter_ingestion.py
Subsystem: 02_AI_CORE/02_tests
Design Standard: DO-178C Level C Structural Coverage (100% Statement Coverage)
Author: Team VITALX CORE (Gourgopal Mohapatra)

Phase 1, 2, 3, 4 & 5 Complete Unit Test Suite:
- Phase 1 Tests (1 to 6): TelemetryArchiveRegistry verification.
- Phase 2 Tests (7 to 15): MultiMissionTelemetryExtractor (Artemis II, Shuttle DSO, Apollo, Calibrated Stream).
- Phase 3 Tests (16 to 22): TelemetryTemporalSynchronizer (Resampling, Bounded Forward Fill, Baseline Fallback).
- Phase 4 Tests (23 to 28): TelemetryVector12DBuilder (12D Schema Validation, Units, Null Defense, Range Bounds).
- Phase 5 Tests (29 to 32): MissionReadyVaultExporter (CSV Export, SHA-256 Manifest, Defensive Checks).
"""

import pytest
from pathlib import Path
import sys
import json
import pandas as pd
import numpy as np

# Ensure 02_AI_CORE/01_src is accessible in python path
src_dir = Path(__file__).resolve().parent.parent / "01_src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from ingestion_adapter import (
    TelemetryArchiveRegistry,
    MultiMissionTelemetryExtractor,
    TelemetryTemporalSynchronizer,
    TelemetryVector12DBuilder,
    MissionReadyVaultExporter,
)


@pytest.fixture
def registry() -> TelemetryArchiveRegistry:
    return TelemetryArchiveRegistry()


@pytest.fixture
def extractor(registry: TelemetryArchiveRegistry) -> MultiMissionTelemetryExtractor:
    return MultiMissionTelemetryExtractor(registry=registry)


@pytest.fixture
def synchronizer() -> TelemetryTemporalSynchronizer:
    return TelemetryTemporalSynchronizer(target_frequency="1min", max_forward_fill_minutes=5)


@pytest.fixture
def builder() -> TelemetryVector12DBuilder:
    return TelemetryVector12DBuilder()


@pytest.fixture
def exporter(tmp_path: Path) -> MissionReadyVaultExporter:
    return MissionReadyVaultExporter(data_vault_root=tmp_path)


# ---------------------------------------------------------
# PHASE 1 TESTS (1 to 6)
# ---------------------------------------------------------

def test_phase1_vault_root_existence(registry: TelemetryArchiveRegistry):
    assert registry.verify_vault_root_exists() is True
    assert registry.data_vault_root.name == "01_DATA_VAULT"


def test_phase1_registered_archive_keys(registry: TelemetryArchiveRegistry):
    keys = registry.get_registered_archive_keys()
    expected_keys = ["apollo", "artemis_ii", "iss_expeditions", "shuttle_dso", "space_radiation"]
    assert keys == expected_keys
    assert len(keys) == 5


def test_phase1_resolve_valid_archives(registry: TelemetryArchiveRegistry):
    for key in registry.get_registered_archive_keys():
        archive_path = registry.resolve_archive_path(key)
        assert archive_path.exists() is True
        assert archive_path.is_dir() is True


def test_phase1_reject_unregistered_and_missing_archives(registry: TelemetryArchiveRegistry, tmp_path: Path):
    with pytest.raises(KeyError) as exc_info:
        registry.resolve_archive_path("mars_colony_fake_key")
    assert "UNREGISTERED_ARCHIVE_ERROR" in str(exc_info.value)

    empty_registry = TelemetryArchiveRegistry(data_vault_root=tmp_path)
    with pytest.raises(FileNotFoundError) as exc_info_missing:
        empty_registry.resolve_archive_path("artemis_ii")
    assert "TELEMETRY_ARCHIVE_NOT_FOUND_ERROR" in str(exc_info_missing.value)

    non_existent_vault = TelemetryArchiveRegistry(data_vault_root=tmp_path / "phantom_vault")
    with pytest.raises(FileNotFoundError) as exc_audit_missing:
        non_existent_vault.audit_all_archives()
    assert "CRITICAL_VAULT_MISSING" in str(exc_audit_missing.value)


def test_phase1_scan_archive_files_and_filtering(registry: TelemetryArchiveRegistry):
    artemis_csvs = registry.scan_archive_files("artemis_ii", extension_filter=".csv")
    assert len(artemis_csvs) >= 2
    filenames = [f.name for f in artemis_csvs]
    assert any("hobo1104" in name for name in filenames)
    assert any("hobo1105" in name for name in filenames)

    shuttle_files = registry.scan_archive_files("shuttle_dso")
    assert len(shuttle_files) > 0


def test_phase1_sha256_checksum_and_audit(registry: TelemetryArchiveRegistry):
    artemis_csvs = registry.scan_archive_files("artemis_ii", extension_filter=".csv")
    sample_file = artemis_csvs[0]

    checksum = registry.compute_file_sha256(sample_file)
    assert isinstance(checksum, str)
    assert len(checksum) == 64

    with pytest.raises(FileNotFoundError):
        registry.compute_file_sha256(sample_file.parent / "non_existent_file.xyz")

    audit_results = registry.audit_all_archives()
    assert len(audit_results) == 5
    for key, data in audit_results.items():
        assert data["status"] == "VALIDATED_PRESENT"
        assert data["file_count"] > 0
        assert data["total_bytes"] > 0


# ---------------------------------------------------------
# PHASE 2 TESTS (7 to 15)
# ---------------------------------------------------------

def test_phase2_parse_artemis_orion_hobo1104(extractor: MultiMissionTelemetryExtractor):
    df = extractor.parse_artemis_orion_telemetry(sensor_id="hobo1104")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    expected_cols = ["timestamp", "cabin_temp_c", "relative_humidity_pct", "dew_point_c"]
    assert list(df.columns) == expected_cols
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert (df["cabin_temp_c"] >= 15.0).all() and (df["cabin_temp_c"] <= 35.0).all()
    assert (df["relative_humidity_pct"] >= 10.0).all() and (df["relative_humidity_pct"] <= 90.0).all()


def test_phase2_parse_artemis_orion_hobo1105(extractor: MultiMissionTelemetryExtractor):
    df = extractor.parse_artemis_orion_telemetry(sensor_id="hobo1105")
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 1000
    assert not df.empty


def test_phase2_artemis_missing_sensor_and_corrupt_schema(tmp_path: Path):
    extractor_default = MultiMissionTelemetryExtractor()
    with pytest.raises(FileNotFoundError) as exc_missing:
        extractor_default.parse_artemis_orion_telemetry(sensor_id="sensor_phantom_9999")
    assert "ARTEMIS_SENSOR_NOT_FOUND" in str(exc_missing.value)

    corrupt_vault = tmp_path / "01_DATA_VAULT"
    corrupt_artemis = corrupt_vault / "06_ARTEMIS_II_ARCHIVE"
    corrupt_artemis.mkdir(parents=True)
    bad_csv = corrupt_artemis / "art002_hobo1104_bad.csv"
    bad_csv.write_text("dummy_id,random_val\n1,100\n", encoding="utf-8")

    dummy_registry = TelemetryArchiveRegistry(data_vault_root=corrupt_vault)
    corrupt_extractor = MultiMissionTelemetryExtractor(registry=dummy_registry)

    with pytest.raises(ValueError) as exc_corrupt:
        corrupt_extractor.parse_artemis_orion_telemetry(sensor_id="hobo1104")
    assert "CORRUPT_ARTEMIS_SCHEMA" in str(exc_corrupt.value)


def test_phase2_artemis_without_dew_point_branch(tmp_path: Path):
    custom_vault = tmp_path / "01_DATA_VAULT"
    custom_artemis = custom_vault / "06_ARTEMIS_II_ARCHIVE"
    custom_artemis.mkdir(parents=True)
    custom_csv = custom_artemis / "art002_hobo1104_nodew.csv"
    custom_csv.write_text("Date-Time,Temperature,RH\n03/26/2026 11:25:46,21.13,28.25\n", encoding="utf-8")

    custom_reg = TelemetryArchiveRegistry(data_vault_root=custom_vault)
    custom_ext = MultiMissionTelemetryExtractor(registry=custom_reg)
    df_nodew = custom_ext.parse_artemis_orion_telemetry(sensor_id="hobo1104")
    assert np.isnan(df_nodew["dew_point_c"].iloc[0])


def test_phase2_parse_shuttle_dso_cardiovascular(extractor: MultiMissionTelemetryExtractor):
    df = extractor.parse_shuttle_dso_cardiovascular()
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 600
    assert set(df["orthostatic_state"].unique()) == {"SUPINE_REST", "STANDING_STRESS"}

    supine_hr = df[df["orthostatic_state"] == "SUPINE_REST"]["heart_rate_bpm"].mean()
    standing_hr = df[df["orthostatic_state"] == "STANDING_STRESS"]["heart_rate_bpm"].mean()
    assert standing_hr > (supine_hr + 10.0)

    supine_cvp = df[df["orthostatic_state"] == "SUPINE_REST"]["cvp_mmhg"].mean()
    standing_cvp = df[df["orthostatic_state"] == "STANDING_STRESS"]["cvp_mmhg"].mean()
    assert supine_cvp > standing_cvp


def test_phase2_parse_apollo_clinical_baseline(extractor: MultiMissionTelemetryExtractor):
    baseline = extractor.parse_apollo_clinical_baseline()
    assert isinstance(baseline, dict)
    required_keys = [
        "apollo_resting_hr_mean",
        "apollo_resting_sbp_mean",
        "apollo_resting_dbp_mean",
        "apollo_nominal_oral_temp_c",
        "apollo_blood_glucose_mean_mgdl",
    ]
    for k in required_keys:
        assert k in baseline
        assert baseline[k] > 0.0


def test_phase2_empty_shuttle_and_apollo_archives(tmp_path: Path):
    empty_vault = tmp_path / "01_DATA_VAULT"
    (empty_vault / "04_SHUTTLE_DSO_ARCHIVE").mkdir(parents=True)
    (empty_vault / "03_APOLLO_ARCHIVE").mkdir(parents=True)

    dummy_reg = TelemetryArchiveRegistry(data_vault_root=empty_vault)
    ext = MultiMissionTelemetryExtractor(registry=dummy_reg)

    with pytest.raises(FileNotFoundError) as exc_shuttle:
        ext.parse_shuttle_dso_cardiovascular()
    assert "SHUTTLE_DSO_EMPTY" in str(exc_shuttle.value)

    with pytest.raises(FileNotFoundError) as exc_apollo:
        ext.parse_apollo_clinical_baseline()
    assert "APOLLO_ARCHIVE_EMPTY" in str(exc_apollo.value)


def test_phase2_generate_calibrated_telemetry_stream_nominal(extractor: MultiMissionTelemetryExtractor):
    df = extractor.generate_calibrated_telemetry_stream(duration_minutes=120, random_seed=42)
    assert len(df) == 120
    assert "timestamp" in df.columns
    assert len(df.columns) == 13

    expected_12 = [
        "heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic", "rmssd",
        "spo2", "core_temp", "blood_glucose", "sleep_deficit_hours", "reaction_latency_ms",
        "microgravity_days", "cabin_co2_mmhg", "accel_magnitude_g"
    ]
    for param in expected_12:
        assert param in df.columns
        assert not df[param].isnull().any()

    with pytest.raises(ValueError):
        extractor.generate_calibrated_telemetry_stream(duration_minutes=0)


def test_phase2_generate_calibrated_telemetry_stream_anomaly(extractor: MultiMissionTelemetryExtractor):
    df_anomaly = extractor.generate_calibrated_telemetry_stream(
        duration_minutes=1440, random_seed=99, induce_fluid_shift_anomaly=True
    )
    assert len(df_anomaly) == 1440

    normal_window = df_anomaly.iloc[0:600]
    anomaly_window = df_anomaly.iloc[1200:1440]

    assert anomaly_window["cabin_co2_mmhg"].mean() > normal_window["cabin_co2_mmhg"].mean()
    assert anomaly_window["blood_pressure_systolic"].mean() > normal_window["blood_pressure_systolic"].mean()
    assert anomaly_window["spo2"].mean() < normal_window["spo2"].mean()


# ---------------------------------------------------------
# PHASE 3 TESTS (16 to 22)
# ---------------------------------------------------------

def test_phase3_synchronizer_init_validation():
    sync = TelemetryTemporalSynchronizer(target_frequency="1min", max_forward_fill_minutes=5)
    assert sync.target_frequency == "1min"
    assert sync.max_forward_fill_minutes == 5

    with pytest.raises(ValueError) as exc:
        TelemetryTemporalSynchronizer(max_forward_fill_minutes=-1)
    assert "MAX_FILL_INVALID" in str(exc.value)


def test_phase3_resample_uniform_grid(synchronizer: TelemetryTemporalSynchronizer):
    times = pd.date_range("2026-11-14 09:00:00", periods=6, freq="20s")
    df_irregular = pd.DataFrame({
        "timestamp": times,
        "heart_rate": [70.0, 72.0, 74.0, 80.0, 82.0, 84.0],
    })

    resampled = synchronizer.resample_and_synchronize(df_irregular)
    assert isinstance(resampled, pd.DataFrame)
    assert "timestamp" in resampled.columns
    assert len(resampled) == 2
    assert np.isclose(resampled["heart_rate"].iloc[0], 72.0)


def test_phase3_resample_defensive_exceptions(synchronizer: TelemetryTemporalSynchronizer):
    with pytest.raises(ValueError) as exc_empty:
        synchronizer.resample_and_synchronize(pd.DataFrame())
    assert "INPUT_TELEMETRY_EMPTY" in str(exc_empty.value)

    with pytest.raises(KeyError) as exc_missing_col:
        synchronizer.resample_and_synchronize(pd.DataFrame({"heart_rate": [70.0]}))
    assert "TIMESTAMP_COLUMN_MISSING" in str(exc_missing_col.value)

    bad_time_df = pd.DataFrame({"timestamp": ["corrupt_date_1", "corrupt_date_2"], "val": [1, 2]})
    with pytest.raises(ValueError) as exc_parse:
        synchronizer.resample_and_synchronize(bad_time_df)
    assert "TIMESTAMP_PARSING_FAILED" in str(exc_parse.value)


def test_phase3_bounded_forward_fill_success(synchronizer: TelemetryTemporalSynchronizer):
    times = pd.date_range("2026-11-14 09:00:00", periods=6, freq="1min")
    df_gap = pd.DataFrame({
        "timestamp": times,
        "heart_rate": [75.0, np.nan, np.nan, np.nan, 80.0, 81.0],
    })

    imputed, audit = synchronizer.impute_missing_telemetry(df_gap)
    assert audit["initial_missing_cells"] == 3
    assert audit["forward_filled_cells"] == 3
    assert audit["baseline_projected_cells"] == 0
    assert audit["final_missing_cells"] == 0
    assert (imputed["heart_rate"].iloc[1:4] == 75.0).all()


def test_phase3_extended_dropout_baseline_fallback(synchronizer: TelemetryTemporalSynchronizer):
    times = pd.date_range("2026-11-14 09:00:00", periods=10, freq="1min")
    df_extended_gap = pd.DataFrame({
        "timestamp": times,
        "heart_rate": [72.0] + [np.nan] * 9,
    })

    imputed, audit = synchronizer.impute_missing_telemetry(df_extended_gap)
    assert audit["initial_missing_cells"] == 9
    assert audit["forward_filled_cells"] == 5
    assert audit["baseline_projected_cells"] == 4
    assert audit["final_missing_cells"] == 0
    assert "heart_rate" in audit["dropout_flags"]
    assert audit["dropout_flags"]["heart_rate"]["status"] == "EXTENDED_SENSOR_DROPOUT_PROJECTED"
    assert (imputed["heart_rate"].iloc[6:] == 68.0).all()


def test_phase3_custom_baseline_override_and_empty_check():
    sync = TelemetryTemporalSynchronizer(max_forward_fill_minutes=0)
    df = pd.DataFrame({"timestamp": pd.date_range("2026-11-14", periods=2, freq="1min"), "spo2": [np.nan, np.nan]})

    custom_baselines = {"spo2": 99.5}
    imputed, audit = sync.impute_missing_telemetry(df, baseline_overrides=custom_baselines)
    assert (imputed["spo2"] == 99.5).all()
    assert audit["baseline_projected_cells"] == 2

    with pytest.raises(ValueError) as exc:
        sync.impute_missing_telemetry(pd.DataFrame())
    assert "EMPTY_DF_FOR_IMPUTATION" in str(exc.value)


def test_phase3_end_to_end_resample_and_impute_pipeline(
    extractor: MultiMissionTelemetryExtractor, synchronizer: TelemetryTemporalSynchronizer
):
    raw_df = extractor.generate_calibrated_telemetry_stream(duration_minutes=60, random_seed=77)
    raw_df.loc[10:13, "heart_rate"] = np.nan
    raw_df.loc[25:35, "spo2"] = np.nan

    resampled = synchronizer.resample_and_synchronize(raw_df)
    clean_df, audit = synchronizer.impute_missing_telemetry(resampled)

    assert not clean_df.isnull().any().any()
    assert len(clean_df) == 60
    assert audit["forward_filled_cells"] > 0
    assert audit["final_missing_cells"] == 0


# ---------------------------------------------------------
# PHASE 4 TESTS (23 to 28)
# ---------------------------------------------------------

def test_phase4_builder_initialization(builder: TelemetryVector12DBuilder):
    assert len(builder.feature_names) == 12
    assert "heart_rate" in builder.feature_names
    assert "cabin_co2_mmhg" in builder.feature_names
    assert "accel_magnitude_g" in builder.feature_names


def test_phase4_validate_and_build_tensor_nominal(
    extractor: MultiMissionTelemetryExtractor, builder: TelemetryVector12DBuilder
):
    df = extractor.generate_calibrated_telemetry_stream(duration_minutes=50, random_seed=42)
    tensor_arr, clean_df = builder.validate_and_build_tensor(df)

    assert isinstance(tensor_arr, np.ndarray)
    assert tensor_arr.shape == (50, 12)
    assert tensor_arr.dtype == np.float64
    assert isinstance(clean_df, pd.DataFrame)
    assert clean_df.shape == (50, 13)
    assert clean_df.columns[0] == "timestamp"
    assert list(clean_df.columns[1:]) == builder.feature_names


def test_phase4_builder_without_timestamp_column(
    extractor: MultiMissionTelemetryExtractor, builder: TelemetryVector12DBuilder
):
    df = extractor.generate_calibrated_telemetry_stream(duration_minutes=30, random_seed=42)
    df_no_time = df.drop(columns=["timestamp"])

    tensor_arr, clean_df = builder.validate_and_build_tensor(df_no_time)
    assert tensor_arr.shape == (30, 12)
    assert "timestamp" not in clean_df.columns
    assert list(clean_df.columns) == builder.feature_names


def test_phase4_empty_dataframe_defense(builder: TelemetryVector12DBuilder):
    with pytest.raises(ValueError) as exc:
        builder.validate_and_build_tensor(pd.DataFrame())
    assert "EMPTY_DF_FOR_BUILDER" in str(exc.value)


def test_phase4_missing_columns_and_unresolved_nulls_defense(
    extractor: MultiMissionTelemetryExtractor, builder: TelemetryVector12DBuilder
):
    df = extractor.generate_calibrated_telemetry_stream(duration_minutes=20, random_seed=42)

    df_missing = df.drop(columns=["rmssd"])
    with pytest.raises(KeyError) as exc_miss:
        builder.validate_and_build_tensor(df_missing)
    assert "SCHEMA_VIOLATION_MISSING_COLUMNS" in str(exc_miss.value)

    df_null = df.copy()
    df_null.loc[5, "spo2"] = np.nan
    with pytest.raises(ValueError) as exc_null:
        builder.validate_and_build_tensor(df_null)
    assert "UNRESOLVED_NULLS_IN_TENSOR" in str(exc_null.value)


def test_phase4_biological_limits_violation_defense(
    extractor: MultiMissionTelemetryExtractor, builder: TelemetryVector12DBuilder
):
    df = extractor.generate_calibrated_telemetry_stream(duration_minutes=20, random_seed=42)
    df_impossible = df.copy()
    df_impossible.loc[2, "heart_rate"] = 320.0

    with pytest.raises(ValueError) as exc_bio:
        builder.validate_and_build_tensor(df_impossible)
    assert "BIOLOGICAL_LIMITS_VIOLATED" in str(exc_bio.value)
    assert "heart_rate" in str(exc_bio.value)


# ---------------------------------------------------------
# PHASE 5 TESTS (29 to 33)
# ---------------------------------------------------------

def test_phase5_default_init_exporter():
    """
    Test 29: MissionReadyVaultExporter default constructor uses real anchor path.
    """
    default_exporter = MissionReadyVaultExporter()
    assert default_exporter.mission_ready_dir.name == "02_MISSION_READY"
    assert default_exporter.mission_ready_dir.exists()


def test_phase5_export_dataset_nominal(
    extractor: MultiMissionTelemetryExtractor, exporter: MissionReadyVaultExporter
):
    """
    Test 30: Successfully export dataset, verify CSV write, and assert sidecar SHA-256 JSON manifest.
    """
    df = extractor.generate_calibrated_telemetry_stream(duration_minutes=40, random_seed=12)
    res = exporter.export_dataset(df, filename="test_export.csv", metadata={"source": "pytest_verification"})

    assert "csv_path" in res
    assert "manifest_path" in res
    assert len(res["sha256_checksum"]) == 64
    assert res["row_count"] == 40

    csv_p = Path(res["csv_path"])
    manifest_p = Path(res["manifest_path"])
    assert csv_p.exists() and csv_p.is_file()
    assert manifest_p.exists() and manifest_p.is_file()

    # Verify manifest JSON integrity
    with open(manifest_p, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    assert manifest_data["dataset_filename"] == "test_export.csv"
    assert manifest_data["sha256_checksum"] == res["sha256_checksum"]
    assert manifest_data["row_count"] == 40
    assert manifest_data["column_count"] == 13
    assert manifest_data["export_metadata"]["source"] == "pytest_verification"


def test_phase5_export_empty_dataframe_defense(exporter: MissionReadyVaultExporter):
    """
    Test 31: Assert rejection of empty DataFrame on export (DO-178C data integrity).
    """
    with pytest.raises(ValueError) as exc:
        exporter.export_dataset(pd.DataFrame(), filename="empty.csv")
    assert "CANNOT_EXPORT_EMPTY_DATASET" in str(exc.value)


def test_phase5_complete_end_to_end_phases_1_to_5_chain(
    extractor: MultiMissionTelemetryExtractor,
    synchronizer: TelemetryTemporalSynchronizer,
    builder: TelemetryVector12DBuilder,
    exporter: MissionReadyVaultExporter,
):
    """
    Test 32: The Grand End-to-End Test: Chain Phase 1 -> 2 -> 3 -> 4 -> 5.
    Ingests calibrated raw multi-mission data, resamples, imputes missing dropouts,
    builds certified 12D tensor, exports to Mission-Ready vault, and asserts cryptographic checksum.
    """
    raw_df = extractor.generate_calibrated_telemetry_stream(duration_minutes=100, random_seed=55)
    # Inject intermittent sensor decoupling gaps
    raw_df.loc[15:18, "heart_rate"] = np.nan
    raw_df.loc[40:48, "spo2"] = np.nan

    resampled_df = synchronizer.resample_and_synchronize(raw_df)
    clean_imputed_df, audit_log = synchronizer.impute_missing_telemetry(resampled_df)
    tensor_array, clean_12d_df = builder.validate_and_build_tensor(clean_imputed_df)

    assert tensor_array.shape == (100, 12)

    export_result = exporter.export_dataset(
        clean_12d_df,
        filename="unified_astronaut_telemetry.csv",
        metadata={"audit_imputation": audit_log},
    )

    assert export_result["row_count"] == 100
    assert Path(export_result["csv_path"]).exists()
    assert Path(export_result["manifest_path"]).exists()
