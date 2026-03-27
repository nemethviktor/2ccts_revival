import pandas as pd
import os
import warnings

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def generate_vehiclesort_pnml():
    print("--- Starting Vehicle Sort File Generation ---")
    
    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.normpath(os.path.join(project_root, 'src/vehiclesort.pnml'))

    try:
        sheets = pd.read_excel(excel_path, sheet_name=None)
    
        # 1. Start with the 'control' sheet as the base (defines what to generate)
        df_master = sheets['control']
        
        # 2. List of sheets that provide extra vehicle properties (keyed by VEHIDCODE)
        data_sheets = [
            'properties'
        ]
        
        for sheet_name in data_sheets:
            if sheet_name in sheets:
                # Merge on VEHIDCODE. 'left' join ensures we keep only what's in 'control'
                df_master = pd.merge(df_master, sheets[sheet_name], on='VEHIDCODE', how='left', suffixes=('', '_dup'))
                # Drop any duplicate columns created by the merge
                df_master = df_master.loc[:, ~df_master.columns.str.endswith('_dup')]
                
        df_ranges = sheets['vehicle_id_ranges']
        df_copyright = sheets['copyright_text']
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # 2. Extract Copyright
    header_text = str(df_copyright.columns[0]) if "Unnamed" not in str(df_copyright.columns[0]) else ""
    if not df_copyright.empty:
        data_text = str(df_copyright.iloc[0, 0])
        raw_copyright = data_text if header_text == "" else f"{header_text}\n{data_text}"
    else:
        raw_copyright = header_text
    
    content = [f"\n{raw_copyright}\n\n\n"]
    content.append("/*\tThis file is used to set the sort order in the vehicle purchase window.\n")
    content.append(" *\tIt starts with #defining the partial lists per vehicle type.\n")
    content.append(" *\tThese partial lists are then combined to the sort-list.\n")
    content.append(" *\tThis way future extensions based on parameters can easily be included.\n*/\n\n")

    # 3. Sort ranges by ID Start to ensure consistent block order
    df_ranges = df_ranges.sort_values(by='Range Start')

    # 4. Process each Category Block
    sorting_macros = [] # To store the names of the macros for the final list

    for _, r_row in df_ranges.iterrows():
        cat_id = str(r_row['ID Type']).strip()
        # Clean the ID Type for the macro name (e.g., ID_RANGE_RBS -> SORTING_RBS)
        macro_name = cat_id.replace('ID_RANGE_', 'SORTING_')
        sorting_macros.append(macro_name)

        content.append(f"#define {macro_name} \\\n")

        # Filter properties for this category
        cat_items = df_master[df_master['VEHID_ID_CATEGORY'].astype(str).str.strip() == cat_id].copy()
        
        # Sort by Intro Year, then by ID
        cat_items = cat_items.sort_values(by=['INTRODUCTION_YEAR', 'VEHID_ID'])

        item_count = len(cat_items)
        for i, (_, p_row) in enumerate(cat_items.iterrows()):
            item_name = str(p_row['ITEM'])
            year = int(p_row['INTRODUCTION_YEAR']) if pd.notna(p_row['INTRODUCTION_YEAR']) else 0
            
            # Add backslash if it's NOT the last item in the block
            suffix = " \\" if i < item_count - 1 else ""
            content.append(f"{item_name}, /*Year: {year}*/{suffix}\n")
        
        content.append("\n")

    # 5. The Master Sort List
    content.append("// Combine all categories into the final sort list\n")
    content.append("sort(FEAT_TRAINS, [\n")
    # Using join to add indentation for cleaner look
    content.append("    " + " \n    ".join(sorting_macros) + "\n")
    content.append("]);\n")

    # 6. Save
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"Success! Generated: {output_path}")
    except Exception as e:
        print(f"Error writing: {e}")

if __name__ == "__main__":
    generate_vehiclesort_pnml()
    print("--- Vehicle Sort File Generation Complete ---")