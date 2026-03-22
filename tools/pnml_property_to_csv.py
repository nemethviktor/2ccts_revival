import os
import re
import csv

# --- Configuration ---
BLACKLIST = {
    "AIR_DRAG_COEFFICIENT",
    "BITMASK_VEHICLE_INFO",
    "CARGO_AGE_PERIOD", 
    "MISC_FLAGS", 
    "NAME",
    "POWER_PER_WAGON",
    "REFIT_COST",
    "RELIABILITY_DECAY",
    "RETIRE_EARLY",
    "RUNNING_COST_BASE",
    "SPRITE_ID",
    "VISUAL_FLAG",
    "ITEM"
}

REPLACEMENT_MAP = {
    "CARGODEF": "CARGODEF_",
    "LOADINGSPEED": "LOADINGSPEEDDEF_",
    "ENGINE_CLASS": "ENGINE_CLASS_"
}

def extract_with_context():
    # Setup paths relative to root/tools/script.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir) 
    
    master_file_path = os.path.join(project_root, '2ccts_revival.pnml')
    output_csv = os.path.join(script_dir, 'vehicle_report.csv')

    include_pattern = re.compile(r'#include\s+"([^"]+)"')
    define_pattern = re.compile(r'^#define\s+(\w+)\s+(.+)$')
    
    current_context = {}
    data_rows = []
    all_keys = set()

    if not os.path.exists(master_file_path):
        print(f"Error: Could not find master file at: {master_file_path}")
        return

    with open(master_file_path, 'r', encoding='utf-8') as mf:
        for line in mf:
            line = line.strip()
            include_match = include_pattern.search(line)
            if not include_match:
                continue

            rel_path = include_match.group(1)
            full_path = os.path.normpath(os.path.join(project_root, rel_path))

            # 1. Handle Init Files (Context Tracking)
            if "init_type" in rel_path:
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as ifile:
                        for iline in ifile:
                            d_match = define_pattern.match(iline.strip())
                            if d_match:
                                key, value = d_match.groups()
                                # Store the full name (e.g., 'CURRENT_TRACK_TYPE') 
                                # so we can match it against property file values
                                current_context[key] = value
                else:
                    print(f"Warning: Missing Init file: {full_path}")

            # 2. Handle Property Files (Data Extraction)
            elif rel_path.endswith("_property.pnml"):
                if os.path.exists(full_path):
                    file_data = {}
                    with open(full_path, 'r', encoding='utf-8') as pfile:
                        for pline in pfile:
                            p_match = define_pattern.match(pline.strip())
                            if p_match:
                                k, v = p_match.groups()
                                if k in BLACKLIST:
                                    continue

                                # LOOKUP LOGIC:
                                # In property file: #define TRACK_TYPE CURRENT_TRACK_TYPE
                                # We check if 'CURRENT_TRACK_TYPE' exists in our context
                                if v in current_context:
                                    v = current_context[v]
                                
                                # Cleanup
                                if k in REPLACEMENT_MAP:
                                    v = v.replace(REPLACEMENT_MAP[k], "")
                                
                                file_data[k] = v
                                all_keys.add(k)
                    
                    if file_data:
                        data_rows.append(file_data)
                else:
                    print(f"Warning: Missing Property file: {full_path}")

    if not data_rows:
        print("No data extracted. Verify paths and file contents.")
        return

    ordered_keys = sorted(list(all_keys))
    if "VEHIDCODE" in ordered_keys:
        ordered_keys.insert(0, ordered_keys.pop(ordered_keys.index("VEHIDCODE")))

    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ordered_keys)
        writer.writeheader()
        for row in data_rows:
            writer.writerow(row)

    print(f"Extraction complete. Found {len(data_rows)} vehicles.")

if __name__ == "__main__":
    extract_with_context()