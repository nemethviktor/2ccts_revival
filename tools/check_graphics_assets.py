import os
import re

def check_graphics_sync(pnml_file):
    "clear||cls"
    # Base directories relative to script location
    root_dir = os.path.dirname(os.path.abspath(__file__))
    gfx_dir = os.path.join(root_dir, 'gfx')
    
    if not os.path.exists(pnml_file):
        print(f"Error: Could not find PNML file: {pnml_file}")
        return
    if not os.path.exists(gfx_dir):
        print(f"Error: Could not find 'gfx' folder at: {gfx_dir}")
        return

    # 1. Map all PNG files in gfx recursively
    # Key: Filename without extension, Value: Full relative path for reporting
    gfx_inventory = {}
    for root, dirs, files in os.walk(gfx_dir):
        for file in files:
            if file.lower().endswith('.png'):
                name_no_ext = os.path.splitext(file)[0]
                gfx_inventory[name_no_ext] = os.path.join(root, file)

    # 2. Parse PNML for _graphics.pnml includes
    # Pattern looks for: src/.../Something_graphics.pnml
    include_pattern = re.compile(r'#include\s+"src/([^"]+)_graphics\.pnml"')
    
    referenced_graphics = []
    with open(pnml_file, 'r', encoding='utf-8') as f:
        for line in f:
            match = include_pattern.search(line)
            if match:
                # This extracts "EMU/Russia_RZD_ES1_Lastochka" from the path
                full_path_stub = match.group(1)
                # We just want the filename part: "Russia_RZD_ES1_Lastochka"
                base_name = os.path.basename(full_path_stub)
                referenced_graphics.append(base_name)

    # 3. Compare
    missing_pngs = []
    found_count = 0

    for ref in referenced_graphics:
        if ref in gfx_inventory:
            found_count += 1
        else:
            missing_pngs.append(ref)

    # 4. Report
    print("--- Graphics Asset Check ---")
    print(f"Unique graphics includes found in PNML: {len(referenced_graphics)}")
    print(f"Total PNG files found in /gfx: {len(gfx_inventory)}")
    print(f"Matched: {found_count}")
    
    if missing_graphics := sorted(list(set(missing_pngs))):
        print(f"\n[!] MISSING ASSETS ({len(missing_graphics)}):")
        print("The following are included in PNML but have no matching .png in /gfx:")
        for item in missing_graphics:
            print(f" - {item}.png")
    else:
        print("\n[+] Success: All referenced graphics have corresponding PNG files.")

if __name__ == "__main__":
    # Ensure this matches your filename
    check_graphics_sync('2ccts_revival.pnml')