#!/usr/bin/env bash
set -e

BUILD_ONLY="${1:-n}"
REQ_FILES="tools/requirements.txt tools/linux_requirements.txt"

clear

read -p "Use .venv? [y/N] " VENV_ANSWER
case "$VENV_ANSWER" in
    y|Y)
        [[ -f .venv/bin/activate ]] || { echo "Error: .venv not found. Create it first."; exit 1; }
        source .venv/bin/activate
        PIP_FLAGS=""
        AUTO=1 ;;
    *)
        printf '\033[31mWARNING: system-wide install. May conflict with Debian packages (PEP 668).\033[0m\n'
        printf '\033[31mSystem python is %s; project targets 3.12.\033[0m\n' "$(python3 -V 2>&1)"
        PIP_FLAGS="--break-system-packages"
        AUTO=0 ;;
esac

# One source of truth: pip itself decides what is unsatisfied.
pending=""
for f in $REQ_FILES; do
    [[ -f "$f" ]] || continue
    pending+=$(python3 -m pip install --dry-run -q -r "$f" 2>/dev/null | grep '^Would install' || true)
    pending+=$'\n'
done

if [[ -n "${pending// /}" ]]; then
    echo "Unsatisfied requirements:"
    echo "$pending"
    if [[ "$AUTO" == 1 ]] || read -p "Install into system Python? [y/N] " A && [[ "$A" == "y" || "$A" == "Y" ]]; then
        for f in $REQ_FILES; do
            [[ -f "$f" ]] || continue
            python3 -m pip install $PIP_FLAGS -r "$f"
        done
    fi
fi

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