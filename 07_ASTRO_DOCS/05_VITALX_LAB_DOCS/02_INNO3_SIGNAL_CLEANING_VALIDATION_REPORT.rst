.. _inno3_signal_cleaning_validation_report:

================================================================================
ASTROVITAL AI : VITALX CORE (RECREATED V1)
================================================================================
SUBSYSTEM 05: VITALX LAB — RESEARCH SYNTHESIS REPORT
REPORT: 02_inno3_signal_cleaning_validation.ipynb Synthesis & Analysis
================================================================================

.. note::
   **REPORT IDENTIFIER:** ASTROVITAL-LAB-REP-02 : INNO 3 SIGNAL CLEANING VALIDATION
   **SUBSYSTEM LOCATION:** 05_VITALX_LAB/ & 07_ASTRO_DOCS/05_VITALX_LAB_DOCS/
   **RESEARCH ARTIFACT:** 02_inno3_signal_cleaning_validation.ipynb
   **FOCUS:** Wavelet Denoising, Savitzky-Golay, NLMS Motion Cancellation & SQI
   **LEAD RESEARCHER & ARCHITECT:** Commander Gouragopal Mohapatra (GOURGOPAL618)
   **DATE OF CERTIFICATION:** November 15, 2026

--------------------------------------------------------------------------------
1. Research Scope & Adaptive Denoising Architecture
--------------------------------------------------------------------------------

This report evaluates the performance of the 20% Adaptive AI Auxiliary Layer in
isolating true biological signals from microgravity-induced artifacts:

1. **Moving Median Baseline Detrending:** Eliminates thermal and respiratory wander (<0.05 Hz) while retaining high-frequency R-wave peaks.
2. **Savitzky-Golay Spectral Smoothing:** Attenuates thruster acoustic noise and 60 Hz electrical interference.
3. **Adaptive NLMS Motion Canceller:** Leverages 3-axis IMU acceleration channels to cancel exercise-induced motion artifacts (:math:`>15\text{ dB}` SNR gain).
4. **Signal Quality Index (SQI) Certification:** Computes statistical quality indices certifying flight readiness (:math:`\text{SQI} \ge 0.95`).
