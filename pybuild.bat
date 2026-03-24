@echo off
cls
python ./tools/custom_tags_generator.py
python ./tools/generate_master_pnml.py
python ./tools/check_src_files_exist.py
python ./tools/generate_vehicle_id_pnml.py
python ./tools/generate_vehicle_sort.py
python ./tools/data_to_property.py
echo --- Build Start ---
gcc -E -x c -o 2ccts_revival.nml ./2ccts_revival.pnml
nmlc -c --quiet 2ccts_revival.nml -o "2ccts_revival.grf" -t custom_tags.txt
echo --- Build Finished ---