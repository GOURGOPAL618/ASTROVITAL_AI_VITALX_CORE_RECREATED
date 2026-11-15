"""
ASTROVITAL AI : VITALX CORE RECREATED (V1)
===========================================
Module: test_notebook_04_biophysical_proofs.py
Subsystem: X_TEST
Design Standard: RTCA DO-178C Level C (DAL C) / NASA-STD-3001
Author: Gourgopal Mohapatra (Lead Architect & Sole Developer, Team VITALX CORE)

Independent Verification & Validation (IV&V) test suite for:
Notebook 04: 04_inno1_biophysical_triage_proof.ipynb
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
nb_path = lab_dir / "04_inno1_biophysical_triage_proof.ipynb"
summary_path = docs_lab_dir / "summaries" / "04_inno1_biophysical_triage_summary.json"
figures_dir = docs_lab_dir / "figures" / "04_figures"


def compute_sha256(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_notebook_04_file_exists_and_valid_json():
    """Verifies that Notebook 04 exists, is non-empty, and parses as valid JSON."""
    assert nb_path.exists(), f"Notebook file missing: {nb_path}"
    assert nb_path.stat().st_size > 10000, f"Notebook file unexpectedly small: {nb_path.stat().st_size} bytes"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    assert "cells" in nb_data, "Invalid notebook structure: 'cells' key missing."
    assert len(nb_data["cells"]) >= 20, f"Expected >= 20 cells, got {len(nb_data['cells'])}"


def test_notebook_04_execution_outputs_present():
    """Verifies that all code cells in Notebook 04 have executed and produced outputs without errors."""
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


def test_notebook_04_user_governance_rules():
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


def test_notebook_04_figures_generated_and_valid():
    """Verifies that all 4 publication-grade figures were generated and are valid PNG files."""
    expected_figures = [
        "figure_01_cephalad_fluid_shift_hydrodynamics.png",
        "figure_02_cardiac_stroke_volume_atrophy.png",
        "figure_03_mission_hemodynamic_triage_timeline.png",
        "figure_04_triage_latency_and_cmo_override.png",
    ]

    for fig_name in expected_figures:
        fig_path = figures_dir / fig_name
        assert fig_path.exists(), f"Figure missing: {fig_name}"
        assert fig_path.stat().st_size > 30000, f"Figure unexpectedly small ({fig_path.stat().st_size} bytes): {fig_name}"


def test_notebook_04_summary_json_integrity():
    """Verifies the audit summary JSON produced by Notebook 04."""
    assert summary_path.exists(), f"Summary JSON missing: {summary_path}"

    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["verification_status"] == "DO-178C_LEVEL_C_VERIFIED"
    assert summary["subsystem"] == "03_DECISION_CORE"
    assert summary["total_frames_triaged"] == 4320
    assert summary["latency_benchmark_ms"]["is_within_10ms_ceiling"] is True
    assert summary["latency_benchmark_ms"]["mean_latency_ms"] < 2.0
    assert summary["biophysical_proofs"]["cephalad_fluid_shift_monotonic"] is True
    assert summary["biophysical_proofs"]["cmo_override_verified"] is True
    assert len(summary["figures_generated"]) == 4


def test_notebook_04_cmo_override_determinism():
    """Verifies that human CMO override assert and clear operate deterministically."""
    import sys
    src_dir = repo_root / "03_DECISION_CORE"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

    from triage_model_engine import TriageModelEngine

    engine = TriageModelEngine()
    dummy_frame = {
        "heart_rate_bpm": 70.0,
        "systolic_bp_mmhg": 120.0,
        "diastolic_bp_mmhg": 80.0,
        "spo2_percent": 98.0,
        "core_temp_c": 37.0,
        "cabin_co2_ppm": 1000.0,
        "icp_est_mmhg": 10.0,
        "rmssd_ms": 45.0,
    }

    p1 = engine.process_telemetry_frame(dummy_frame)
    assert p1.triage_state == "GREEN"

    engine.apply_cmo_override("RED", "Test rationale", "CDR_TEST")
    p2 = engine.process_telemetry_frame(dummy_frame)
    assert p2.triage_state == "RED"
    assert p2.cmo_override["is_active"] is True

    engine.clear_cmo_override()
    p3 = engine.process_telemetry_frame(dummy_frame)
    assert p3.triage_state == "GREEN"
    assert p3.cmo_override["is_active"] is False


def test_notebook_04_only_ipynb_in_vitalx_lab():
    """Verifies user rule that 05_VITALX_LAB/ contains ONLY .ipynb files."""
    lab_files = list(lab_dir.iterdir())
    for f in lab_files:
        if f.is_file():
            assert f.suffix == ".ipynb", f"Illegal non-notebook file found in 05_VITALX_LAB: {f.name}"
