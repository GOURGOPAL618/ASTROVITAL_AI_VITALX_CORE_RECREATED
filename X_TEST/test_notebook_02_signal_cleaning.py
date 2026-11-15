"""
ASTROVITAL AI : VITALX CORE RECREATED (V1)
===========================================
Module: test_notebook_02_signal_cleaning.py
Subsystem: X_TEST
Design Standard: RTCA DO-178C Level C (DAL C) / NASA-STD-3001
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)

Independent Verification & Validation (IV&V) test suite for:
Notebook 02: 02_inno3_signal_cleaning_validation.ipynb
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
nb_path = lab_dir / "02_inno3_signal_cleaning_validation.ipynb"
summary_path = docs_lab_dir / "summaries" / "02_inno3_signal_cleaning_summary.json"
figures_dir = docs_lab_dir / "figures" / "02_figures"
mission_ready_dir = repo_root / "01_DATA_VAULT" / "02_MISSION_READY"
stabilized_pq_path = mission_ready_dir / "stabilized_astronaut_telemetry.parquet"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_notebook_02_file_exists_and_valid_json():
    """Verifies that Notebook 02 exists, is non-empty, and parses as valid JSON."""
    assert nb_path.exists(), f"Notebook file missing: {nb_path}"
    assert nb_path.stat().st_size > 10000, f"Notebook file unexpectedly small: {nb_path.stat().st_size} bytes"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    assert "cells" in nb_data, "Invalid notebook structure: 'cells' key missing."
    assert len(nb_data["cells"]) >= 20, f"Expected >= 20 cells, got {len(nb_data['cells'])}"


def test_notebook_02_execution_outputs_present():
    """Verifies that all code cells in Notebook 02 have executed and produced outputs without errors."""
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    code_cells = [c for c in nb_data["cells"] if c.get("cell_type") == "code"]
    assert len(code_cells) >= 12, f"Expected >= 12 code cells, got {len(code_cells)}"

    for idx, cell in enumerate(code_cells):
        assert cell.get("execution_count") is not None, f"Code cell #{idx} was not executed!"
        outputs = cell.get("outputs", [])
        assert len(outputs) > 0, f"Code cell #{idx} has empty outputs!"

        # Assert no cell execution errors
        for out in outputs:
            assert out.get("output_type") != "error", f"Error in cell #{idx}: {out.get('ename')}: {out.get('evalue')}"


def test_notebook_02_user_governance_rules():
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


def test_notebook_02_figures_generated_and_valid():
    """Verifies that all 4 publication-grade figures were generated and are valid PNG files."""
    expected_figures = [
        "figure_01_baseline_drift_compensation.png",
        "figure_02_spectral_noise_attenuation.png",
        "figure_03_motion_cancellation_traces.png",
        "figure_04_sqi_channel_certification.png",
    ]

    for fig_name in expected_figures:
        fig_path = figures_dir / fig_name
        assert fig_path.exists(), f"Figure missing: {fig_name}"
        assert fig_path.stat().st_size > 50000, f"Figure unexpectedly small ({fig_path.stat().st_size} bytes): {fig_name}"


def test_notebook_02_summary_json_integrity():
    """Verifies the audit summary JSON produced by Notebook 02."""
    assert summary_path.exists(), f"Summary JSON missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["verification_status"] == "DO-178C_LEVEL_C_VERIFIED"
    assert summary["total_records_processed"] == 4320
    assert summary["is_telemetry_flight_ready"] is True
    assert summary["frame_mean_sqi"] >= 0.85, f"Mean SQI below threshold: {summary['frame_mean_sqi']}"
    assert len(summary["figures_generated"]) == 4


def test_notebook_02_stabilized_parquet_dataset():
    """Verifies that the stabilized parquet dataset is saved in 02_MISSION_READY and has 0 nulls."""
    assert stabilized_pq_path.exists(), f"Stabilized parquet dataset missing: {stabilized_pq_path}"
    assert stabilized_pq_path.stat().st_size > 100000

    df = pd.read_parquet(stabilized_pq_path)
    assert len(df) == 4320, f"Expected 4,320 rows, got {len(df)}"
    assert df.isnull().sum().sum() == 0, "Null values detected in stabilized dataset!"


def test_notebook_02_channel_sqi_thresholds():
    """Verifies that all dynamic physiological vital channels meet the SQI >= 0.85 airworthiness bar."""
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    sqi_map = summary["channel_sqi_scores"]
    assert len(sqi_map) == 9, f"Expected 9 dynamic vital channels, got {len(sqi_map)}"

    for ch, score in sqi_map.items():
        assert score >= 0.85, f"Channel '{ch}' failed certification threshold with SQI = {score:.4f}"
