"""
ASTROVITAL AI : VITALX CORE RECREATED (V1)
===========================================
Module: test_notebook_05_master_verification.py
Subsystem: X_TEST
Design Standard: RTCA DO-178C Level C (DAL C) / NASA-STD-3001
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)

Independent Verification & Validation (IV&V) test suite for:
Notebook 05: 05_master_flight_verification.ipynb
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
nb_path = lab_dir / "05_master_flight_verification.ipynb"
summary_path = docs_lab_dir / "summaries" / "05_master_flight_verification_summary.json"
figures_dir = docs_lab_dir / "figures" / "05_figures"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_notebook_05_file_exists_and_valid_json():
    """Verifies that Notebook 05 exists, is non-empty, and parses as valid JSON."""
    assert nb_path.exists(), f"Notebook file missing: {nb_path}"
    assert nb_path.stat().st_size > 10000, f"Notebook file unexpectedly small: {nb_path.stat().st_size} bytes"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    assert "cells" in nb_data, "Invalid notebook structure: 'cells' key missing."
    assert len(nb_data["cells"]) >= 20, f"Expected >= 20 cells, got {len(nb_data['cells'])}"


def test_notebook_05_execution_outputs_present():
    """Verifies that all code cells in Notebook 05 have executed and produced outputs without errors."""
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    code_cells = [c for c in nb_data["cells"] if c.get("cell_type") == "code"]
    assert len(code_cells) >= 11, f"Expected >= 11 code cells, got {len(code_cells)}"

    for idx, cell in enumerate(code_cells):
        assert cell.get("execution_count") is not None, f"Code cell #{idx} was not executed!"
        outputs = cell.get("outputs", [])
        assert len(outputs) > 0, f"Code cell #{idx} has empty outputs!"

        # Assert no cell execution errors
        for out in outputs:
            assert out.get("output_type") != "error", f"Error in cell #{idx}: {out.get('ename')}: {out.get('evalue')}"


def test_notebook_05_user_governance_rules():
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


def test_notebook_05_figures_generated_and_valid():
    """Verifies that all 4 publication-grade figures were generated and are valid PNG files."""
    expected_figures = [
        "figure_01_multi_mission_master_timeline.png",
        "figure_02_master_confusion_matrix_and_roc.png",
        "figure_03_head_to_head_comparative_benchmark.png",
        "figure_04_latency_waterfall_and_compliance.png",
    ]

    for fig_name in expected_figures:
        fig_path = figures_dir / fig_name
        assert fig_path.exists(), f"Figure missing: {fig_name}"
        assert fig_path.stat().st_size > 30000, f"Figure unexpectedly small ({fig_path.stat().st_size} bytes): {fig_name}"


def test_notebook_05_summary_json_integrity():
    """Verifies the audit summary JSON produced by Notebook 05."""
    assert summary_path.exists(), f"Summary JSON missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["verification_status"] == "DO-178C_LEVEL_C_AIRWORTHY_VERIFIED"
    assert summary["system_name"] == "ASTROVITAL AI : VITALX CORE RECREATED (V1)"
    assert summary["total_frames_triaged"] == 4320
    assert summary["accuracy_metrics"]["overall_accuracy_percent"] >= 99.0
    assert summary["accuracy_metrics"]["red_sensitivity_recall"] >= 0.99
    assert summary["latency_benchmark_ms"]["safety_margin_factor"] > 1000.0
    assert summary["compliance_certifications"]["rtca_do_178c_level_c"] is True
    assert len(summary["figures_generated"]) == 4


def test_notebook_05_head_to_head_v1_advantage():
    """Verifies empirical accuracy advantage of ASTROVITAL RECREATED over legacy V1."""
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    acc_metrics = summary["accuracy_metrics"]
    v1_acc = acc_metrics["v1_accuracy_percent"]
    recreated_acc = acc_metrics["overall_accuracy_percent"]
    gain = acc_metrics["accuracy_gain_percent"]

    assert v1_acc == 85.25
    assert recreated_acc >= 99.0
    assert gain >= 13.0, f"Expected gain >= 13%, got {gain}%"


def test_all_five_notebooks_exist_in_vitalx_lab_strictly_ipynb():
    """Verifies user rule that 05_VITALX_LAB/ contains ONLY .ipynb files and all 5 notebooks are present."""
    expected_notebooks = [
        "01_multi_mission_data_synthesis.ipynb",
        "02_inno3_signal_cleaning_validation.ipynb",
        "03_inno6_biomarker_divergence.ipynb",
        "04_inno1_biophysical_triage_proof.ipynb",
        "05_master_flight_verification.ipynb",
    ]

    lab_files = list(lab_dir.iterdir())
    file_names = [f.name for f in lab_files if f.is_file()]

    for nb_name in expected_notebooks:
        assert nb_name in file_names, f"Missing notebook in 05_VITALX_LAB: {nb_name}"

    for f in lab_files:
        if f.is_file():
            assert f.suffix == ".ipynb", f"Illegal non-notebook file found in 05_VITALX_LAB: {f.name}"
