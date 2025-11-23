@echo off
REM Git Configuration Script for HydroGraph-TW
echo.
echo ======================================================================
echo   Git Configuration Setup
echo ======================================================================
echo.
echo Please enter your Git information:
echo.

set /p GIT_NAME="Your Name (e.g., John Doe): "
set /p GIT_EMAIL="Your Email (e.g., john@example.com): "

echo.
echo Setting Git configuration...
git config --global user.name "%GIT_NAME%"
git config --global user.email "%GIT_EMAIL%"

echo.
echo [OK] Git configuration complete:
git config --global user.name
git config --global user.email

echo.
echo ======================================================================
echo   Ready to commit!
echo ======================================================================
echo.
echo Next steps:
echo   1. Run: git status
echo   2. Run: git commit -m "your message"
echo   3. Create repository on GitHub
echo   4. Run: git remote add origin https://github.com/yourusername/HydroGraph-TW.git
echo   5. Run: git push -u origin master
echo.
pause
