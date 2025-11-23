@echo off
REM HydroGraph-TW Quick Installation Script
REM =========================================

echo.
echo ======================================================================
echo   HydroGraph-TW Dependencies Installation
echo   Taiwan Hydrological Graph Database Project
echo ======================================================================
echo.

echo [1/3] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.12 or higher.
    pause
    exit /b 1
)

echo.
echo [2/3] Installing core dependencies from requirements.txt...
python -m pip install -r requirements.txt --upgrade
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo [3/3] Verifying critical packages...
python -c "import langgraph; import neo4j; import google.generativeai; print('[OK] All packages verified!')"
if %errorlevel% neq 0 (
    echo [WARNING] Some packages may not be installed correctly.
    pause
)

echo.
echo ======================================================================
echo [SUCCESS] Installation completed!
echo ======================================================================
echo.
echo Next steps:
echo   1. Start Neo4j database (port 7687)
echo   2. Configure Neo4j password in scripts/langgraph_gemini_poc.py
echo   3. (Optional) Get free Gemini API key from https://ai.google.dev/
echo   4. Run: python scripts/langgraph_gemini_poc.py
echo.
pause
