#!/bin/bash 
clear
python3 ./tools/check_src_files_exist.py
python3 ./tools/pnml_property_to_csv.py
make
echo "Finished!"