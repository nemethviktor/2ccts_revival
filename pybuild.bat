@echo off
cls

:: Capture the first argument, default to 'n' if empty
set "BUILD_ONLY=%~1"
if "%BUILD_ONLY%"=="" set "BUILD_ONLY=n"

:: Print start time
powershell -Command "Get-Date -Format 'yyyy-MM-dd:HH:mm:ss'"

:: If user passed 'y' or 'Y', skip straight to the build process
if /I "%BUILD_ONLY%"=="y" goto build_process

python ./tools/custom_tags_generator.py
python ./tools/generate_badgetable.py
python ./tools/generate_languages.py
python ./tools/generate_graphics_pnml.py
python ./tools/generate_master_pnml.py
python ./tools/generate_unified_items.py
python ./tools/generate_vehicle_id_pnml.py
python ./tools/generate_vehicle_sort.py
python ./tools/generate_vehicle_summary.py

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
python ./tools/generate_gap_analysis.py

:end_process
:: Print end time
powershell -Command "Get-Date -Format 'yyyy-MM-dd:HH:mm:ss'"