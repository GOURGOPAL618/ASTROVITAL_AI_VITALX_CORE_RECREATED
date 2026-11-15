@echo off
title ASTROVITAL AI : VITALX CORE - ASTRONAUT COCKPIT HUD LAUNCHER
echo ===============================================================================
echo ASTROVITAL AI : VITALX CORE (RECREATED V1)
echo RTCA DO-178C LEVEL C (DAL C) / NASA-STD-3001 ASTRONAUT COCKPIT HUD
echo NASA Space Apps Challenge 2026 - Human Body in Deep Space
echo ===============================================================================
echo.
echo [1/2] Setting flight environment variables...
set PYTHONPATH=04_ASTRONAUT_COCKPIT;04_ASTRONAUT_COCKPIT\01_components;02_AI_CORE\01_src;03_DECISION_CORE;08_EXTREME_SIMULATION_LAB

echo [2/2] Launching certified Streamlit Cockpit HUD on http://localhost:8501 ...
echo.
.\vitalx_env\Scripts\python.exe -m streamlit run 04_ASTRONAUT_COCKPIT\app.py --server.port 8501 --server.headless false
pause
