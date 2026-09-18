import pandas as pd
import os
import warnings


def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def generate_vehicle_id_pnml(df_master: pd.DataFrame, copyright_text: str, df_ranges: pd.DataFrame):
    print("--- Starting Vehicle ID File Generation (with Free ID Comments) ---")

    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, "vehicle_report.xlsx")
    output_path = os.path.normpath(os.path.join(project_root, "src/vehicleID.pnml"))

    content = []
    content.append(f"\n{copyright_text}\n\n\n")
    content.append("// This file sets all vehicle IDs.\n\n")

    # Pre-process properties into a dictionary for O(1) lookup
    # Key: VEHID_ID, Value: ITEM name
    # We only care about rows that have a numeric ID
    # Convert VEHID_ID to numeric (coerce creates NaNs for bad data)
    df_master["VEHID_ID"] = pd.to_numeric(df_master["VEHID_ID"], errors="coerce")

    # Drop NaNs, lowercase the ITEM column, and map it
    id_map = {
        int(row["VEHID_ID"]): {"name": row["ITEM"].lower(), "exclude": is_true(row.get("EXCLUDE_READONLY", False))}
        for _, row in df_master.iterrows()
        if pd.notnull(row["VEHID_ID"])
    }

    # 4. Process Category Blocks
    for _, row in df_ranges.iterrows():
        cat_id = str(row["ID Type"]).strip()
        eng_title = row["English Title"]
        r_start = int(row["Range Start"])
        r_end = int(row["Range End"])

        hex_range = f"0x{r_start:04X}..0x{r_end:04X}"

        content.append(f"// {eng_title}, available ID range: {r_start}-{r_end} (hex {hex_range})\n")
        content.append(f"#define {cat_id} {hex_range}\n")

        # Iterate through EVERY number in the range
        for current_id in range(r_start, r_end + 1):
            if current_id in id_map:
                veh_info = id_map[current_id]
                # Check the exclusion status from the vehicle data, not the range data
                if veh_info["exclude"]:
                    content.append(
                        f"// item(FEAT_TRAINS, {veh_info['name']}, {current_id}) {{}} // vehicle is excluded\n"
                    )
                else:
                    content.append(f"item(FEAT_TRAINS, {veh_info['name']}, {current_id}) {{}}\n")
            else:
                content.append(f"// {current_id} free\n")

        content.append("\n")

    # 5. Write the file
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(content)
        print(f"Success! Generated: {output_path}")
    except Exception as e:
        print(f"Error writing to {output_path}: {e}")


if __name__ == "__main__":
    from helpers.read_excel_file import load_master_data, load_vehicle_id_ranges, get_excel_path

    # Direct execution test logic:
    df_m, c_text, _ = load_master_data(get_excel_path())
    df_ranges = load_vehicle_id_ranges(excel_path=get_excel_path())

    generate_vehicle_id_pnml(df_master=df_m, copyright_text=c_text, df_ranges=df_ranges)
    print("--- Vehicle ID File Generation Complete ---")
