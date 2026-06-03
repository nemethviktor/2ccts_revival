@echo off
cls
del 2ccts_revival.grf
python ./tools/custom_tags_generator.py
python ./tools/generate_badgetable.py
python ./tools/generate_languages.py
python ./tools/generate_graphics_pnml.py
python ./tools/generate_master_pnml.py
python ./tools/generate_unified_items.py
python ./tools/generate_vehicle_id_pnml.py
python ./tools/generate_vehicle_sort.py
python ./tools/generate_vehicle_summary.py
echo --- Build Start ---
gcc -E -x c -o 2ccts_revival.nml ./2ccts_revival.pnml
nmlc -c --quiet 2ccts_revival.nml -o "2ccts_revival.grf" -t custom_tags.txt -n 
echo --- Build Finished ---

IF EXIST copygrftogoogledriveshare (
copygrftogoogledriveshare
)

rem the below takes ages and so we run it after the build. no need to wait just to test if build works.
python ./tools/generate_gap_analysis.py