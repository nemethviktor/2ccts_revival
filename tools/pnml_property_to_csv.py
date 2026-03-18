import os
import re
import csv

def extract_pnml_data(root_directory, output_csv):
    data_rows = []
    all_keys = set()
    
    # Regex to match: #define KEY VALUE
    # It captures the key and the rest of the line as the value
    define_pattern = re.compile(r'^#define\s+(\w+)\s+(.+)$')

    print(f"Scanning directory: {root_directory}...")

    # Recursively walk through folders
    for root, dirs, files in os.walk(root_directory):
        for file in files:
            if file.endswith("_property.pnml"):
                file_path = os.path.join(root, file)
                file_data = {}
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        match = define_pattern.match(line)
                        if match:
                            key, value = match.groups()
                            file_data[key] = value
                            all_keys.add(key)
                
                if file_data:
                    data_rows.append(file_data)

    if not data_rows:
        print("No matching files or data found.")
        return

    # Ensure VEHIDCODE is the first column for better readability
    ordered_keys = sorted(list(all_keys))
    if "VEHIDCODE" in ordered_keys:
        ordered_keys.insert(0, ordered_keys.pop(ordered_keys.index("VEHIDCODE")))

    # Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=ordered_keys)
        writer.writeheader()
        for row in data_rows:
            writer.writerow(row)

    print(f"Success! Extracted data from {len(data_rows)} files into '{output_csv}'.")

# --- Configuration ---
target_folder = './../src'
output_file = 'vehicle_properties.csv'

extract_pnml_data(target_folder, output_file)