@echo off
REM ============================================================
REM  NFS The Run Trainer - Windows Build Script
REM ============================================================
REM  This script compiles nfs_trainer.py to NFSTR_Trainer.exe
REM  Just double-click this file (or run it from CMD).
REM ============================================================

echo ============================================================
echo   NFS The Run Trainer - Building EXE
echo ============================================================
echo.

REM Check if Python is installed
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found!
    echo Please install Python 3.8+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Install required packages
echo [*] Installing required packages (this may take a minute)...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install pymem keyboard pyinstaller >nul 2>&1
echo [OK] Packages installed.
echo.

REM Build the EXE
echo [*] Building NFSTR_Trainer.exe...
echo     (This takes 1-2 minutes)
echo.
python -m PyInstaller --onefile --console ^
    --name "NFSTR_Trainer" ^
    --hidden-import pymem ^
    --hidden-import pymem.process ^
    --hidden-import pymem.pattern ^
    --collect-all pymem ^
    --collect-all keyboard ^
    nfs_trainer.py

if exist "dist\NFSTR_Trainer.exe" (
    echo.
    echo ============================================================
    echo   SUCCESS!
    echo   Your trainer is ready: dist\NFSTR_Trainer.exe
    echo ============================================================
    echo.
    echo HOW TO USE:
    echo   1. Copy NFSTR_Trainer.exe to your NFS The Run folder
    echo      (where Need For Speed The Run.exe is)
    echo   2. Launch NFS The Run, get into a race
    echo   3. Run NFSTR_Trainer.exe (as Administrator)
    echo   4. Press INSERT to activate trainer
    echo   5. Press F9 for infinite nitro (twice: scan + activate)
    echo.
    explorer dist
) else (
    echo.
    echo [ERROR] Build failed. Check the messages above.
)

echo.
pause
