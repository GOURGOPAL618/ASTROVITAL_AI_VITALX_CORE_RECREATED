"""
ASTROVITAL AI : VITALX CORE (RECREATED V1)
===========================================
Module: batch_vault_ingestor.py
Subsystem: 02_AI_CORE/01_src
Design Standard: RTCA DO-178C Level C (DAL C) High-Level Requirement HLR-BIO-001 & HLR-BIO-004
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)

Batch Ingestion & Processing Pipeline for 01_DATA_VAULT:
1. Ingests raw multi-mission archives (Artemis II Orion, Shuttle DSO, Apollo 7).
2. Sanitizes and stages intermediate sensor feeds into 01_DATA_VAULT/01_SENSOR_INTAKE/.
3. Builds certified 12D telemetry tensors via TelemetryTemporalSynchronizer & TelemetryVector12DBuilder.
4. Exports verified Parquet and CSV datasets to 01_DATA_VAULT/02_MISSION_READY/.
5. Computes and records cryptographic SHA-256 manifests for full data integrity traceability.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Ensure 02_AI_CORE/01_src is in python path
_src_dir = Path(__file__).resolve().parent
_vault_root = _src_dir.parent.parent / "01_DATA_VAULT"
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from ingestion_adapter import (
    TelemetryArchiveRegistry,
    MultiMissionTelemetryExtractor,
    TelemetryTemporalSynchronizer,
    TelemetryVector12DBuilder,
    MissionReadyVaultExporter,
)


def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 cryptographic digest of a physical file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def run_batch_ingestion() -> Dict[str, Any]:
    print("=" * 80)
    print("ASTROVITAL AI : VITALX CORE - BATCH DATA VAULT INGESTION PIPELINE")
    print("Standard: RTCA DO-178C Level C (DAL C) / NASA-STD-3001")
    print(f"Timestamp: {datetime.now().isoformat()}Z")
    print(f"Target Vault Root: {_vault_root}")
    print("=" * 80)

    sensor_intake_dir = _vault_root / "01_SENSOR_INTAKE"
    mission_ready_dir = _vault_root / "02_MISSION_READY"
    sensor_intake_dir.mkdir(parents=True, exist_ok=True)
    mission_ready_dir.mkdir(parents=True, exist_ok=True)

    registry = TelemetryArchiveRegistry(data_vault_root=_vault_root)
    extractor = MultiMissionTelemetryExtractor(registry=registry)
    synchronizer = TelemetryTemporalSynchronizer(target_frequency="1min", max_forward_fill_minutes=5)
    tensor_builder = TelemetryVector12DBuilder()
    exporter = MissionReadyVaultExporter(data_vault_root=_vault_root)

    report: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "vault_root": str(_vault_root),
        "intake_files": {},
        "mission_ready_files": {},
    }

    # -------------------------------------------------------------------------
    # STAGE 1: Process Raw Artemis II Orion Cabin Environmental Telemetry
    # -------------------------------------------------------------------------
    print("\n[STAGE 1/5] Ingesting Artemis II Orion Cabin Environmental Archives...")
    artemis_files = registry.scan_archive_files("artemis_ii", extension_filter=".csv")
    print(f"  Found {len(artemis_files)} Artemis II raw CSV archive files.")

    artemis_dfs: List[pd.DataFrame] = []
    for f in artemis_files:
        sensor_tag = "hobo1104" if "1104" in f.name else ("hobo1105" if "1105" in f.name else None)
        if sensor_tag:
            df_sensor = extractor.parse_artemis_orion_telemetry(sensor_id=sensor_tag)
            intake_path = sensor_intake_dir / f"artemis_ii_{sensor_tag}_cleaned.csv"
            df_sensor.to_csv(intake_path, index=False)
            sha = compute_sha256(intake_path)
            report["intake_files"][intake_path.name] = {
                "rows": len(df_sensor),
                "columns": df_sensor.columns.tolist(),
                "sha256": sha,
                "size_bytes": intake_path.stat().st_size,
            }
            print(f"  ✓ Processed {sensor_tag}: {len(df_sensor):,} rows -> {intake_path.name} (SHA-256: {sha[:12]}...)")
            artemis_dfs.append(df_sensor)

    if artemis_dfs:
        artemis_merged = pd.concat(artemis_dfs, ignore_index=True).drop_duplicates(subset=["timestamp"]).sort_values("timestamp").reset_index(drop=True)
        # Export to 02_MISSION_READY
        art_csv = mission_ready_dir / "artemis_ii_cabin_environment.csv"
        art_pq = mission_ready_dir / "artemis_ii_cabin_environment.parquet"
        artemis_merged.to_csv(art_csv, index=False)
        artemis_merged.to_parquet(art_pq, index=False)
        report["mission_ready_files"]["artemis_ii_cabin_environment"] = {
            "csv_sha256": compute_sha256(art_csv),
            "parquet_sha256": compute_sha256(art_pq),
            "rows": len(artemis_merged),
            "columns": artemis_merged.columns.tolist(),
        }
        print(f"  ✓ Exported unified Artemis II Cabin Environment: {len(artemis_merged):,} records (Parquet & CSV)")

    # -------------------------------------------------------------------------
    # STAGE 2: Ingest Shuttle STS-31 DSO-479 Cardiovascular Stand Test Data
    # -------------------------------------------------------------------------
    print("\n[STAGE 2/5] Ingesting Space Shuttle STS-31 DSO-479 Cardiovascular Profile...")
    df_shuttle = extractor.parse_shuttle_dso_cardiovascular()
    shuttle_intake = sensor_intake_dir / "shuttle_dso479_cardiovascular.csv"
    df_shuttle.to_csv(shuttle_intake, index=False)
    shuttle_sha = compute_sha256(shuttle_intake)
    report["intake_files"][shuttle_intake.name] = {
        "rows": len(df_shuttle),
        "columns": df_shuttle.columns.tolist(),
        "sha256": shuttle_sha,
        "size_bytes": shuttle_intake.stat().st_size,
    }
    print(f"  ✓ Staged Shuttle DSO-479 Cardiovascular Data: {len(df_shuttle):,} records -> {shuttle_intake.name}")

    shuttle_mr_csv = mission_ready_dir / "shuttle_dso479_cardiovascular.csv"
    shuttle_mr_pq = mission_ready_dir / "shuttle_dso479_cardiovascular.parquet"
    df_shuttle.to_csv(shuttle_mr_csv, index=False)
    df_shuttle.to_parquet(shuttle_mr_pq, index=False)
    report["mission_ready_files"]["shuttle_dso479_cardiovascular"] = {
        "csv_sha256": compute_sha256(shuttle_mr_csv),
        "parquet_sha256": compute_sha256(shuttle_mr_pq),
        "rows": len(df_shuttle),
    }

    # -------------------------------------------------------------------------
    # STAGE 3: Ingest Apollo 7 Clinical Baseline
    # -------------------------------------------------------------------------
    print("\n[STAGE 3/5] Extracting Apollo 7 Physiological Flight Medical Baseline...")
    apollo_baseline = extractor.parse_apollo_clinical_baseline()
    apollo_json = sensor_intake_dir / "apollo_7_clinical_baseline.json"
    with open(apollo_json, "w", encoding="utf-8") as f:
        json.dump(apollo_baseline, f, indent=2)
    report["intake_files"][apollo_json.name] = {
        "baseline_parameters": apollo_baseline,
        "sha256": compute_sha256(apollo_json),
    }
    print(f"  ✓ Stored Apollo 7 Clinical Baseline -> {apollo_json.name}")
    for k, v in apollo_baseline.items():
        print(f"    - {k}: {v}")

    # -------------------------------------------------------------------------
    # STAGE 4: Build Synchronized 12-Dimensional Master Astronaut Telemetry Tensor
    # -------------------------------------------------------------------------
    print("\n[STAGE 4/5] Building Synchronized 12D Telemetry Tensor across Mission Profile...")
    # Generating a canonical 72-hour deep-space mission timeline (4,320 1-minute steps)
    # anchored to Artemis II environmental parameters and Apollo 7 clinical ranges.
    # Includes nominal transit, fluid shift onset, and mission stress phases.
    mission_duration_min = 4320  # 72 hours
    raw_stream = extractor.generate_calibrated_telemetry_stream(
        duration_minutes=mission_duration_min,
        random_seed=42,
        induce_fluid_shift_anomaly=True,
    )
    print(f"  Raw multi-channel telemetry generated: {len(raw_stream):,} steps.")

    # Apply temporal synchronization and imputation engine
    synced_df = synchronizer.resample_and_synchronize(raw_stream, timestamp_col="timestamp")
    imputed_df, audit_log = synchronizer.impute_missing_telemetry(synced_df)
    print(f"  Synchronized & imputed to 1-minute uniform grid: {len(imputed_df):,} records (Forward filled: {audit_log['forward_filled_cells']}, Baseline projected: {audit_log['baseline_projected_cells']}).")

    # Validate against DO-178C 12D physical schema
    tensor_arr, validated_df = tensor_builder.validate_and_build_tensor(imputed_df)
    print(f"  Validated 12D Tensor shape: {tensor_arr.shape} (Zero nulls, all physical limits verified).")

    # -------------------------------------------------------------------------
    # STAGE 5: Export to 01_DATA_VAULT/02_MISSION_READY with SHA-256 Manifest
    # -------------------------------------------------------------------------
    print("\n[STAGE 5/5] Exporting Mission-Ready Telemetry Tensor with Manifest...")
    # CSV Export
    csv_filename = "unified_astronaut_telemetry.csv"
    meta_info = {
        "mission_scope": "Artemis Lunar Transit / MTV Deep Space Cruise",
        "duration_hours": mission_duration_min / 60.0,
        "features_12d": tensor_builder.feature_names,
        "standards": ["RTCA DO-178C Level C", "NASA-STD-3001 Vol 2"],
        "source_archives": ["03_APOLLO_ARCHIVE", "04_SHUTTLE_DSO_ARCHIVE", "06_ARTEMIS_II_ARCHIVE"],
        "generated_timestamp": datetime.now().isoformat(),
    }
    export_result = exporter.export_dataset(
        df=validated_df,
        filename=csv_filename,
        metadata=meta_info,
    )
    csv_path = Path(export_result["csv_path"])
    manifest_path = Path(export_result["manifest_path"])

    # Parquet Export for high-performance zero-copy tensor loading
    pq_path = mission_ready_dir / "unified_astronaut_telemetry.parquet"
    validated_df.to_parquet(pq_path, index=False)
    pq_sha256 = compute_sha256(pq_path)

    # Update manifest with Parquet details
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest_data["parquet_file"] = pq_path.name
    manifest_data["parquet_sha256"] = pq_sha256
    manifest_data["parquet_size_bytes"] = pq_path.stat().st_size
    manifest_data["row_count"] = len(validated_df)
    manifest_data["timestamp_start"] = str(validated_df["timestamp"].min())
    manifest_data["timestamp_end"] = str(validated_df["timestamp"].max())
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    report["mission_ready_files"]["unified_astronaut_telemetry"] = {
        "csv_path": str(csv_path),
        "csv_sha256": export_result["sha256_checksum"],
        "csv_size_bytes": csv_path.stat().st_size,
        "parquet_path": str(pq_path),
        "parquet_sha256": pq_sha256,
        "parquet_size_bytes": pq_path.stat().st_size,
        "manifest_path": str(manifest_path),
        "rows": len(validated_df),
        "columns": validated_df.columns.tolist(),
        "time_start": manifest_data["timestamp_start"],
        "time_end": manifest_data["timestamp_end"],
    }

    print("\n" + "=" * 80)
    print("INGESTION & DATA VAULT POPULATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    print(f"1. Unified CSV:      {csv_path.name} ({csv_path.stat().st_size:,} bytes)")
    print(f"   SHA-256:          {export_result['sha256_checksum']}")
    print(f"2. Unified Parquet:  {pq_path.name} ({pq_path.stat().st_size:,} bytes)")
    print(f"   SHA-256:          {pq_sha256}")
    print(f"3. Audit Manifest:   {manifest_path.name}")
    print(f"4. Total Records:    {len(validated_df):,} 1-minute frames (72.0 hours continuous telemetry)")
    print(f"5. 12D Channels:     {', '.join(tensor_builder.feature_names)}")
    print("=" * 80)

    return report


if __name__ == "__main__":
    run_batch_ingestion()
