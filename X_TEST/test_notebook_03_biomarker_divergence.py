"""
ASTROVITAL AI : VITALX CORE RECREATED (V1)
===========================================
Module: test_notebook_03_biomarker_divergence.py
Subsystem: X_TEST
Design Standard: RTCA DO-178C Level C (DAL C) / NASA-STD-3001
Author: Team VITALX CORE (NASA Space Apps Challenge 2026)

Independent Verification & Validation (IV&V) test suite for:
Notebook 03: 03_inno6_biomarker_divergence.ipynb
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
nb_path = lab_dir / "03_inno6_biomarker_divergence.ipynb"
summary_path = docs_lab_dir / "summaries" / "03_inno6_biomarker_divergence_summary.json"
figures_dir = docs_lab_dir / "figures" / "03_figures"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_notebook_03_file_exists_and_valid_json():
    """Verifies that Notebook 03 exists, is non-empty, and parses as valid JSON."""
    assert nb_path.exists(), f"Notebook file missing: {nb_path}"
    assert nb_path.stat().st_size > 10000, f"Notebook file unexpectedly small: {nb_path.stat().st_size} bytes"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    assert "cells" in nb_data, "Invalid notebook structure: 'cells' key missing."
    assert len(nb_data["cells"]) >= 20, f"Expected >= 20 cells, got {len(nb_data['cells'])}"


def test_notebook_03_execution_outputs_present():
    """Verifies that all code cells in Notebook 03 have executed and produced outputs without errors."""
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


def test_notebook_03_user_governance_rules():
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


def test_notebook_03_figures_generated_and_valid():
    """Verifies that all 4 publication-grade figures were generated and are valid PNG files."""
    expected_figures = [
        "figure_01_context_prior_distributions.png",
        "figure_02_sensitivity_gradient_heatmap.png",
        "figure_03_convex_fusion_decomposition.png",
        "figure_04_sensitivity_temporal_trajectories.png",
    ]

    for fig_name in expected_figures:
        fig_path = figures_dir / fig_name
        assert fig_path.exists(), f"Figure missing: {fig_name}"
        assert fig_path.stat().st_size > 30000, f"Figure unexpectedly small ({fig_path.stat().st_size} bytes): {fig_name}"


def test_notebook_03_summary_json_integrity():
    """Verifies the audit summary JSON produced by Notebook 03."""
    assert summary_path.exists(), f"Summary JSON missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["verification_status"] == "DO-178C_LEVEL_C_VERIFIED"
    assert summary["subsystem"] == "02_AI_CORE/01_src/inno6_biomarker_ranker.py"
    assert summary["total_phases_evaluated"] == 8
    assert summary["mission_profile_hours"] == 72.0
    assert len(summary["figures_generated"]) == 4

    top_bio = summary["top_biomarkers_by_phase"]
    assert "nominal_cruise" in top_bio
    assert "early_microgravity_fluid_shift" in top_bio
    assert "cumulative_fatigue_debt" in top_bio


def test_notebook_03_inno6_simplex_and_monotonicity():
    """Verifies mathematical simplex sum constraint (sum == 1.0) and non-negativity across all phases."""
    import sys
    src_dir = repo_root / "02_AI_CORE" / "01_src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from inno6_biomarker_ranker import MissionContextMatrix, MissionOperationalPhase

    matrix = MissionContextMatrix()
    for phase in MissionOperationalPhase:
        res = matrix.get_phase_weights(phase)
        assert np.isclose(np.sum(res.weight_vector), 1.0, atol=1e-5), f"Simplex sum violation for {phase}"
        assert np.all(res.weight_vector >= 0.0), f"Negative weight violation for {phase}"
        assert res.is_normalized is True


def test_notebook_03_only_ipynb_in_vitalx_lab():
    """Verifies user rule that 05_VITALX_LAB/ contains ONLY .ipynb files."""
    lab_files = list(lab_dir.iterdir())
    for f in lab_files:
        if f.is_file():
            assert f.suffix == ".ipynb", f"Illegal non-notebook file found in 05_VITALX_LAB: {f.name}"
