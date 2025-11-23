@echo off
REM Quick launcher for LangGraph Gemini POC
REM Uses hydro_env virtual environment

echo.
echo ======================================================================
echo   LangGraph + Gemini POC - Taiwan Hydrological GraphRAG
echo ======================================================================
echo.

echo [INFO] Using virtual environment: hydro_env
echo [INFO] Starting POC...
echo.

hydro_env\Scripts\python.exe scripts\langgraph_gemini_poc.py

echo.
echo ======================================================================
echo   POC Execution Completed
echo ======================================================================
echo.
pause
