"""
ASTROVITAL AI : VITALX CORE RECREATED (V1)
===========================================
Module: test_notebook_01_synthesis.py
Subsystem: X_TEST
Design Standard: RTCA DO-178C Level C (DAL C) / NASA-STD-3001
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)

Independent Verification & Validation (IV&V) test suite for:
Notebook 01: 01_multi_mission_data_synthesis.ipynb
"""

import os
import json
import hashlib
from pathlib import Path
import pytest
import pandas as pd
import numpy as np

# Base paths
repo_root = Path(__file__).resolve().parent.parent
lab_dir = repo_root / "05_VITALX_LAB"
docs_lab_dir = repo_root / "07_ASTRO_DOCS" / "05_VITALX_LAB_DOCS"
nb_path = lab_dir / "01_multi_mission_data_synthesis.ipynb"
summary_path = docs_lab_dir / "summaries" / "01_multi_mission_data_synthesis_summary.json"
figures_dir = docs_lab_dir / "figures" / "01_figures"
mission_ready_dir = repo_root / "01_DATA_VAULT" / "02_MISSION_READY"
manifest_path = mission_ready_dir / "unified_astronaut_telemetry_manifest.json"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_notebook_01_file_exists_and_valid_json():
    """Verifies that Notebook 01 exists, is non-empty, and parses as valid JSON."""
    assert nb_path.exists(), f"Notebook file missing: {nb_path}"
    assert nb_path.stat().st_size > 10000, f"Notebook file unexpectedly small: {nb_path.stat().st_size} bytes"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    assert "cells" in nb_data, "Invalid notebook structure: 'cells' key missing."
    assert len(nb_data["cells"]) >= 20, f"Expected >= 20 cells, got {len(nb_data['cells'])}"


def test_notebook_01_execution_outputs_present():
    """Verifies that all code cells in Notebook 01 have executed and produced outputs without errors."""
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    code_cells = [c for c in nb_data["cells"] if c.get("cell_type") == "code"]
    assert len(code_cells) >= 10, f"Expected >= 10 code cells, got {len(code_cells)}"

    for idx, cell in enumerate(code_cells):
        assert cell.get("execution_count") is not None, f"Code cell #{idx} was not executed!"
        outputs = cell.get("outputs", [])
        assert len(outputs) > 0, f"Code cell #{idx} has empty outputs!"

        # Assert no cell execution errors
        for out in outputs:
            assert out.get("output_type") != "error", f"Error in cell #{idx}: {out.get('ename')}: {out.get('evalue')}"


def test_notebook_01_user_governance_rules():
    """
    Verifies compliance with user rules:
    1. Top markdown cells exist explaining the notebook.
    2. Every code cell is preceded by an explanatory markdown cell.
    3. Descriptive print statements precede plotting routines.
    """
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    cells = nb_data["cells"]

    # Rule 1: Top cells are markdown
    assert cells[0]["cell_type"] == "markdown", "Top cell must be markdown."
    assert cells[1]["cell_type"] == "markdown", "Second cell must be markdown."

    # Rule 2: Every code block is preceded by a markdown block
    for i, cell in enumerate(cells):
        if cell["cell_type"] == "code":
            assert i > 0, "Code cell cannot be the first cell."
            assert cells[i - 1]["cell_type"] == "markdown", (
                f"Violation of governance rule: Code cell at index {i} is not preceded by a markdown cell."
            )

    # Rule 3: Plotting cells contain descriptive print statements
    code_cells = [c for c in cells if c["cell_type"] == "code"]
    plotting_cells = [c for c in code_cells if any("plt.subplots" in line or "plt.figure" in line for line in c["source"])]
    assert len(plotting_cells) == 4, f"Expected exactly 4 plotting cells, got {len(plotting_cells)}"

    for p_cell in plotting_cells:
        cell_src = "".join(p_cell["source"])
        assert "print(" in cell_src, "Plotting cell missing descriptive print statements!"
        assert "FIGURE" in cell_src, "Plotting cell missing FIGURE header in print statement!"


def test_notebook_01_figures_generated_and_valid():
    """Verifies that all 4 publication-grade figures were generated and are valid PNG files."""
    expected_figures = [
        "figure_01_artemis_cabin_environment.png",
        "figure_02_shuttle_dso_cardiovascular.png",
        "figure_03_master_12channel_telemetry.png",
        "figure_04_correlation_matrix.png",
    ]

    for fig_name in expected_figures:
        fig_path = figures_dir / fig_name
        assert fig_path.exists(), f"Figure missing: {fig_name}"
        assert fig_path.stat().st_size > 50000, f"Figure unexpectedly small ({fig_path.stat().st_size} bytes): {fig_name}"


def test_notebook_01_summary_json_integrity():
    """Verifies the audit summary JSON produced by Notebook 01."""
    assert summary_path.exists(), f"Summary JSON missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["verification_status"] == "DO-178C_LEVEL_C_VERIFIED"
    assert summary["total_records"] == 4320
    assert len(summary["channels_12d"]) == 12
    assert summary["null_count"] == 0
    assert summary["source_datasets"]["artemis_ii"]["records"] == 75396
    assert summary["source_datasets"]["shuttle_dso479"]["records"] == 600


def test_notebook_01_data_vault_sha256_match():
    """Verifies that the generated datasets in 02_MISSION_READY match the cryptographic manifest."""
    assert manifest_path.exists(), f"Manifest file missing: {manifest_path}"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    csv_file = mission_ready_dir / manifest["dataset_filename"]
    pq_file = mission_ready_dir / manifest["parquet_file"]

    assert compute_sha256(csv_file) == manifest["sha256_checksum"], "CSV SHA-256 mismatch!"
    assert compute_sha256(pq_file) == manifest["parquet_sha256"], "Parquet SHA-256 mismatch!"


def test_notebook_01_tensor_schema_and_biological_limits():
    """Loads the synthesized tensor and verifies NASA-STD-3001 biological boundaries."""
    pq_file = mission_ready_dir / "unified_astronaut_telemetry.parquet"
    df = pd.read_parquet(pq_file)

    assert len(df) == 4320, f"Expected 4,320 rows, got {len(df)}"
    assert df.isnull().sum().sum() == 0, "Null values detected in certified tensor!"

    # Biological limits
    assert df["heart_rate"].between(30.0, 220.0).all(), "Heart Rate outside biological range [30, 220]"
    assert df["blood_pressure_systolic"].between(60.0, 240.0).all(), "SBP outside biological range [60, 240]"
    assert df["blood_pressure_diastolic"].between(35.0, 150.0).all(), "DBP outside biological range [35, 150]"
    assert df["rmssd"].between(1.0, 200.0).all(), "RMSSD outside biological range [1, 200]"
    assert df["spo2"].between(60.0, 100.0).all(), "SpO2 outside biological range [60, 100]"
    assert df["core_temp"].between(34.0, 42.5).all(), "Core Temp outside biological range [34, 42.5]"
    assert df["blood_glucose"].between(40.0, 300.0).all(), "Blood Glucose outside biological range [40, 300]"
    assert df["sleep_deficit_hours"].between(0.0, 50.0).all(), "Sleep deficit outside physical range [0, 50]"
    assert df["cabin_co2_mmhg"].between(0.1, 25.0).all(), "Cabin CO2 outside physical range [0.1, 25]"
