import pandas as pd
import os
import warnings
from helpers.read_excel_file import load_master_data, load_vehicle_id_ranges

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def generate_vehiclesort_pnml(df_master: pd.DataFrame, copyright_text: str, df_ranges: pd.DataFrame):
    print("--- Starting Vehicle Sort File Generation ---")

    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.normpath(os.path.join(project_root, "src/vehiclesort.pnml"))

    df_master = df_master[~(df_master.get("EXCLUDE", False).apply(is_true))]

    content = [f"\n{copyright_text}\n\n\n"]
    content.append("/*\tThis file is used to set the sort order in the vehicle purchase window.\n")
    content.append(" *\tIt starts with #defining the partial lists per vehicle type.\n")
    content.append(" *\tThese partial lists are then combined to the sort-list.\n")
    content.append(" *\tThis way future extensions based on parameters can easily be included.\n*/\n\n")

    # 4. Process each Category Block
    sorting_macros = []  # To store the names of the macros for the final list

    for _, r_row in df_ranges.iterrows():
        cat_id = str(r_row["ID Type"]).strip()
        # Clean the ID Type for the macro name (e.g., ID_RANGE_RBS -> SORTING_RBS)
        macro_name = cat_id.replace("ID_RANGE_", "SORTING_")
        sorting_macros.append(macro_name)

        content.append(f"#define {macro_name} \\\n")

        # Filter properties for this category
        cat_items = df_master[df_master["VEHID_ID_CATEGORY"].astype(str).str.strip() == cat_id].copy()

        # Sort by Intro Year, then by ID
        cat_items = cat_items.sort_values(by=["INTRODUCTION_YEAR", "VEHID_ID"])

        item_count = len(cat_items)
        for i, (_, p_row) in enumerate(cat_items.iterrows()):
            item_name = str(p_row["ITEM"]).lower()
            year = int(p_row["INTRODUCTION_YEAR"]) if pd.notna(p_row["INTRODUCTION_YEAR"]) else 0

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
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(content)
        print(f"Success! Generated: {output_path}")
    except Exception as e:
        print(f"Error writing: {e}")


if __name__ == "__main__":
    from helpers.read_excel_file import load_master_data, load_vehicle_id_ranges, get_excel_path

    # Direct execution test logic:
    df_m, c_text, _ = load_master_data(get_excel_path())
    df_ranges = load_vehicle_id_ranges(excel_path=get_excel_path())

    generate_vehiclesort_pnml(df_master=df_m, copyright_text=c_text, df_ranges=df_ranges)

    print("--- Vehicle Sort File Generation Complete ---")
