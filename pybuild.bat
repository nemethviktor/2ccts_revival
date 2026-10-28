@echo off
cls

:: Use the project venv (.venv in repo root); create it on first run
set "PY=%~dp0.venv\Scripts\python.exe"
if not exist "%PY%" call "%~dp0tools\installpyrequirements.bat"
if not exist "%PY%" exit /b 1

:: Capture the first argument, default to 'n' if empty
set "BUILD_ONLY=%~1"
if "%BUILD_ONLY%"=="" set "BUILD_ONLY=n"

:: Print start time
powershell -Command "Get-Date -Format 'yyyy-MM-dd:HH:mm:ss'"

:: If user passed 'y' or 'Y', skip straight to the build process
if /I "%BUILD_ONLY%"=="y" goto build_process

"%PY%" -m tools.build

:build_process
echo --- Build Start ---
del 2ccts_revival.grf
gcc -E -x c -o 2ccts_revival.nml ./2ccts_revival.pnml
nmlc -c --quiet 2ccts_revival.nml -o "2ccts_revival.grf" -t custom_tags.txt -n 
echo --- Build Finished ---

IF EXIST copygrftogoogledriveshare.bat (
    :: Added 'call' here so control returns to this script
    call copygrftogoogledriveshare.bat
)

:: Skip the gap analysis if we are in build-only mode
if /I "%BUILD_ONLY%"=="y" goto end_process

rem the below takes ages and so we run it after the build. no need to wait just to test if build works.
"%PY%" -m tools.generators.gap_analysis

:end_process
:: Print end time
powershell -Command "Get-Date -Format 'yyyy-MM-dd:HH:mm:ss'"