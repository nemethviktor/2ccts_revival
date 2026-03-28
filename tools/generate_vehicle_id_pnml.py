import pandas as pd
import os
import warnings

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def generate_vehicle_id_pnml():
    print("--- Starting Vehicle ID File Generation (with Free ID Comments) ---")

    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.normpath(
        os.path.join(project_root, 'src/vehicleID.pnml'))

    if not os.path.exists(excel_path):
        print(f"Error: Could not find Excel file at {excel_path}")
        return

    try:
        sheets = pd.read_excel(excel_path, sheet_name=None)
        df_control = sheets['control']
        df_ranges = sheets['vehicle_id_ranges']
        df_copyright = sheets['copyright_text']
    except Exception as e:
        print(f"Error reading Excel sheets: {e}")
        return

    # 2. Extract Copyright
    header_text = str(df_copyright.columns[0]) if "Unnamed" not in str(
        df_copyright.columns[0]) else ""
    if not df_copyright.empty:
        data_text = str(df_copyright.iloc[0, 0])
        raw_copyright = data_text if header_text == "" else f"{header_text}\n{data_text}"
    else:
        raw_copyright = header_text

    content = []
    content.append(f"\n{raw_copyright}\n\n\n")
    content.append("// This file sets all vehicle IDs.\n\n")

    # 3. Sort Ranges by Start ID
    df_ranges = df_ranges.sort_values(by='Range Start')

    # Pre-process properties into a dictionary for O(1) lookup
    # Key: VEHID_ID, Value: ITEM name
    # We only care about rows that have a numeric ID
    # Convert VEHID_ID to numeric (coerce creates NaNs for bad data)
    df_control['VEHID_ID'] = pd.to_numeric(
        df_control['VEHID_ID'], errors='coerce')

    # Drop NaNs, lowercase the ITEM column, and map it
    id_map = df_control.dropna(subset=['VEHID_ID']).set_index(
        'VEHID_ID')['ITEM'].str.lower().to_dict()

    # 4. Process Category Blocks
    for _, r_row in df_ranges.iterrows():
        cat_id = str(r_row['ID Type']).strip()
        eng_title = r_row['English Title']
        r_start = int(r_row['Range Start'])
        r_end = int(r_row['Range End'])

        hex_range = f"0x{r_start:04X}..0x{r_end:04X}"

        content.append(
            f"// {eng_title}, available ID range: {r_start}-{r_end} (hex {hex_range})\n")
        content.append(f"#define {cat_id} {hex_range}\n")

        # Iterate through EVERY number in the range
        for current_id in range(r_start, r_end + 1):
            if current_id in id_map:
                item_name = id_map[current_id]
                content.append(
                    f"item(FEAT_TRAINS, {item_name}, {current_id}) {{}}\n")
            else:
                content.append(f"// {current_id} free\n")

        content.append("\n")

    # 5. Write the file
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(content)
        print(f"Success! Generated: {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")


if __name__ == "__main__":
    generate_vehicle_id_pnml()
    print("--- Vehicle ID File Generation Complete ---")
