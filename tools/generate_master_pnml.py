import pandas as pd
import os
import warnings
import shutil

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def generate_master_pnml(df_master: pd.DataFrame, copyright_text: str):
    print("--- Starting Master PNML Generation ---")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.join(project_root, "2ccts_revival.pnml")

    content = [f"\n{copyright_text}\n\n\n"]

    # 2. Restored GRF HEADER Boilerplate
    content.append("//// ------------------------------------\n")
    content.append("//// GRF HEADER\n")
    content.append("//// ------------------------------------\n\n")

    boilerplate = [
        ("// Regions have to come first", "src/regions.pnml"),
        ("// Define grf", "src/header.pnml"),
        ("// Check for valid settings", "src/checks.pnml"),
        ("// Loading speeds", "src/loadingspeeds.pnml"),
        ("// Include sprite templates", "src/templates.pnml"),
        ("// Cargo translation table", "src/cargotable.pnml"),
        ("// Give unique IDs to vehicles", "src/vehicleID.pnml"),
        ("// Can (not) attach vehcile", "src/wagon_attach.pnml"),
        ("// Capacities", "src/capacities.pnml"),
        ("// Rail types", "src/railtypetable.pnml"),
        ("// Badges", "src/badgetable.pnml"),
        ("// Purchase text switch", "src/purchasetext.pnml"),
        ("// Cleanup", "src/undefine_properties.pnml"),
    ]

    for comment, path in boilerplate:
        if comment:
            content.append(f"{comment}\n")
        content.append(f'#include "{path}"\n')

    content.append("\n")

    # 3. Sorting and Grouping Headers
    # We sort by SAVE_TO and VEHID_ID to maintain chronological/type order within categories
    df_master = df_master.sort_values(by=["SAVE_TO", "VEHID_ID"])

    current_group = None

    for _, row in df_master.iterrows():
        if is_true(row["EXCLUDE_READONLY"]):
            continue

        folder_path = str(row["SAVE_TO"]).replace("\\", "/")

        # Logic to insert section headers based on folder path
        # This mimics the "Broad Gauge", "15KV AC" type headers in the original file
        group_label = folder_path.replace("src/", "").replace("/", " - ")
        if group_label != current_group:
            content.append(f"\n//// {group_label.upper()}\n")
            current_group = group_label

        base_name = row["FILENAMES_EXPECTED"]

        # The mandatory 2-file sequence
        content.append(f'#include "{folder_path}/{base_name}_graphics.pnml"\n')
        content.append(f'#include "{folder_path}/{base_name}_item.pnml"\n\n')

    content.append(f"// Sort vehicles in purchase list\n")
    content.append(f'#include "src/vehiclesort.pnml"\n')

    # 4. Save
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(content)
        print(f"Success! Master file generated: {output_path}")
    except Exception as e:
        print(f"Error writing: {e}")

    # 5 Delete cache
    shutil.rmtree(project_root + "/.nmlcache", ignore_errors=True)


if __name__ == "__main__":
    generate_master_pnml()
    print("--- Master PNML Generation Complete ---")
