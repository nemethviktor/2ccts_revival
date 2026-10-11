#!/usr/bin/env bash
set -e

BUILD_ONLY="${1:-n}"

clear

date '+%Y-%m-%d:%H:%M:%S'

if [[ "$BUILD_ONLY" != "y" && "$BUILD_ONLY" != "Y" ]]; then
    python3 -m tools.build
fi

echo "--- Build Start ---"
rm -f 2ccts_revival.grf
gcc -E -x c -o 2ccts_revival.nml ./2ccts_revival.pnml
nmlc -c --quiet 2ccts_revival.nml -o "2ccts_revival.grf" -t custom_tags.txt -n
echo "--- Build Finished ---"

# if [[ "$BUILD_ONLY" != "y" && "$BUILD_ONLY" != "Y" ]]; then
#     python3 -m tools.generators.gap_analysis
# fi

date '+%Y-%m-%d:%H:%M:%S'