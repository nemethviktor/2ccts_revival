import os
import re

def check_pnml_includes(file_path):
    print("--- PNML Include & Order Check Start ---")
    
    # Script is in root/tools, src is in root/src
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    if not os.path.exists(file_path):
        print(f"Error: Could not find main file: {file_path}")
        return

    include_pattern = re.compile(r'#include\s+"([^"]+)"')
    
    missing_files = []
    order_errors = []
    vehicle_buffer = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            match = include_pattern.search(line.strip())
            if not match:
                continue
                
            rel_path = match.group(1)
            full_path = os.path.normpath(os.path.join(project_root, rel_path))
            
            # 1. Check if file actually exists
            if not os.path.exists(full_path):
                missing_files.append((line_num, rel_path))

            # 2. Sequence/Order Logic for Vehicles
            # Ignore headers and TypeInitialization
            if "src/" in rel_path and "_CodeSupport/TypeInitialization" not in rel_path:
                # We only care about the property/graphics/item sets
                if any(suffix in rel_path for suffix in ["_property.pnml", "_graphics.pnml", "_item.pnml"]):
                    vehicle_buffer.append((line_num, rel_path))
                    
                    # Once we have 3 files in the buffer, validate them
                    if len(vehicle_buffer) == 3:
                        p, g, i = vehicle_buffer
                        
                        # Verify suffixes
                        if not p[1].endswith("_property.pnml"):
                            order_errors.append(f"Line {p[0]}: Expected _property, found {p[1]}")
                        if not g[1].endswith("_graphics.pnml"):
                            order_errors.append(f"Line {g[0]}: Expected _graphics, found {g[1]}")
                        if not i[1].endswith("_item.pnml"):
                            order_errors.append(f"Line {i[0]}: Expected _item, found {i[1]}")
                            
                        # Verify they belong to the same vehicle (base name check)
                        base_p = p[1].replace("_property.pnml", "")
                        base_g = g[1].replace("_graphics.pnml", "")
                        base_i = i[1].replace("_item.pnml", "")
                        
                        if not (base_p == base_g == base_i):
                            order_errors.append(f"Line {p[0]}-{i[0]}: Mismatched vehicle set: {base_p}, {base_g}, {base_i}")
                        
                        vehicle_buffer = []

    # Final Check: Did we leave any files in the buffer? (e.g. only 1 or 2 files found)
    if vehicle_buffer:
        for line_num, path in vehicle_buffer:
            order_errors.append(f"Line {line_num}: Incomplete triumvirate for {path}")

    # Output results
    print(f"Check finished for: {file_path}")
    
    if missing_files:
        print(f"\n[!] MISSING FILES ({len(missing_files)}):")
        for line_num, path in missing_files:
            print(f"  Line {line_num}: {path}")
    else:
        print("\n[+] All included files exist.")

    if order_errors:
        print(f"\n[!] ORDER/SEQUENCE ERRORS ({len(order_errors)}):")
        for err in order_errors:
            print(f"  {err}")
    else:
        print("[+] All vehicle file sequences are correct (Property -> Graphics -> Item).")

if __name__ == "__main__":
    # Assuming the master file is in the root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    master_file = os.path.join(os.path.dirname(script_dir), '2ccts_revival.pnml')
    check_pnml_includes(master_file)
    print("--- PNML Include & Order Check End ---")