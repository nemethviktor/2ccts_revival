import os
import re

def check_pnml_includes(file_path):
    "clear||cls"
    # Set the base directory to the 'src' folder relative to this script
    base_dir = os.path.join(os.path.dirname(__file__), 'src')
    
    if not os.path.exists(file_path):
        print(f"Error: The script could not find the main file: {file_path}")
        return

    # Regular expression to find #include "path/to/file.pnml"
    include_pattern = re.compile(r'#include\s+"([^"]+)"')
    
    missing_files = []
    total_includes = 0

    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            match = include_pattern.search(line)
            if match:
                total_includes += 1
                # Extract the path from the include line
                relative_path = match.group(1)
                
                # Logic: if the path starts with 'src/', we strip it to check 
                # against the base_dir (since src is the subfolder)
                actual_path_to_check = relative_path
                if relative_path.startswith('src/'):
                    actual_path_to_check = relative_path[4:]
                
                full_path = os.path.join(base_dir, actual_path_to_check)
                
                if not os.path.exists(full_path):
                    missing_files.append((line_num, relative_path))

    # Output results
    print(f"--- PNML Include Check ---")
    print(f"Total #include lines found: {total_includes}")
    
    if missing_files:
        print(f"Found {len(missing_files)} missing files:\n")
        for line_num, path in missing_files:
            print(f"Line {line_num}: {path}")
    else:
        print("Success: All included files were found in the 'src' directory.")

if __name__ == "__main__":
    # Replace with your actual filename if different
    check_pnml_includes('2ccts_revival.pnml')