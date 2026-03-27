import os
import re
import pandas as pd

def parse_graphics_to_dump():
    print("--- Starting Graphics ID Extraction ---")
    
    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    src_dir = os.path.join(project_root, 'src')
    output_csv = os.path.join(script_dir, 'graphics_lookup_dump.csv')

    # Regex patterns
    # Spritesets: looks for spriteset(ID, ...
    re_spriteset = re.compile(r'spriteset\s*\(\s*([a-zA-Z0-9_]+)', re.IGNORECASE)
    # Switches: looks for switch(FEAT_TRAINS, SELF/PARENT, ID, ...
    re_switch = re.compile(r'(?:random_)?switch\s*\(\s*FEAT_TRAINS\s*,\s*(?:SELF|PARENT)\s*,\s*([a-zA-Z0-9_]+)', re.IGNORECASE)

    extracted_data = []

    if not os.path.exists(src_dir):
        print(f"Error: Could not find src directory at {src_dir}")
        return

    # 2. Recursive Scan
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('_graphics.pnml'):
                # Strip the suffix to get the clean VEHIDCODE
                vehidcode = file.replace('_graphics.pnml', '')
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                        # Find Spritesets
                        for s in re_spriteset.findall(content):
                            extracted_data.append({
                                'VEHIDCODE': vehidcode,
                                'Type': 'Spriteset',
                                'ID': s,
                                'Is_Purchase': '_purchase' in s.lower(),
                                'Is_Default': False
                            })
                            
                        # Find Switches
                        for sw in re_switch.findall(content):
                            extracted_data.append({
                                'VEHIDCODE': vehidcode,
                                'Type': 'Switch',
                                'ID': sw,
                                'Is_Purchase': False,
                                'Is_Default': any(x in sw.lower() for x in ['_reversed', '_position', '_livery'])
                            })
                except Exception as e:
                    print(f"Skipping {file}: {e}")

    # 3. Process and Save
    if extracted_data:
        df = pd.DataFrame(extracted_data)
        
        # Sort so that Purchase Sprites and Default Switches are easy to find
        df = df.sort_values(by=['VEHIDCODE', 'Type', 'Is_Purchase', 'Is_Default'], ascending=[True, True, False, False])
        
        df.to_csv(output_csv, index=False)
        print(f"Success! Generated {output_csv} with {len(df)} entries.")
        print("You can now import this into the 'graphics_lookup_dump' sheet in Excel.")
    else:
        print("No matches found. Check if your PNML files use 'FEAT_TRAINS' for switches.")

if __name__ == "__main__":
    parse_graphics_to_dump()
    print("--- Graphics ID Extraction Complete ---")