import openpyxl
import pandas as pd
from pathlib import Path
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def get_excel_path() -> str:
    project_root = Path(__file__).resolve().parent.parent

    excel_path = project_root / "vehicle_report.xlsx"
    return str(excel_path)


def load_master_data(excel_path: str):
    print("--- Loading and Merging Excel Sheets with Note Extraction ---")
    # Load raw data for pandas
    sheets = pd.read_excel(excel_path, sheet_name=None)

    # Load workbook for openpyxl (to get notes/comments)
    wb = openpyxl.load_workbook(excel_path)

    # This will store notes as: notes_lookup[VEHIDCODE][COLUMN_NAME] = "Note Text"
    notes_lookup = {}

    def extract_notes(sheet_name, dataframe):
        if sheet_name not in wb.sheetnames:
            return
        ws = wb[sheet_name]

        # Identify where 'VEHIDCODE' is in this specific sheet
        try:
            vehid_col_idx = list(dataframe.columns).index("VEHIDCODE")
        except ValueError:
            return  # Skip sheets without the ID key

        for r_idx, row in enumerate(ws.iter_rows(min_row=2), start=0):
            # Get the cell object instead of just the value first
            veh_id_cell = ws.cell(row=r_idx + 2, column=vehid_col_idx + 1)
            veh_id = veh_id_cell.value

            if veh_id is None:
                continue

            # --- NEW LOGIC TO HANDLE ARRAY FORMULAS ---
            # If the cell is an ArrayFormula object, get its text representation
            if hasattr(veh_id, "ref"):  # This is how openpyxl identifies ArrayFormulas
                # We can't evaluate the formula here, but we can take its string value
                veh_id = str(veh_id)

            # Ensure it's a string before calling .lower()
            veh_id = str(veh_id).lower().strip()
            # ------------------------------------------

            if veh_id not in notes_lookup:
                notes_lookup[veh_id] = {}

            for c_idx, cell in enumerate(row):
                if cell.comment:
                    col_name = dataframe.columns[c_idx]
                    # Clean the note text (removing Excel's 'Author:' prefix if present)
                    clean_note = cell.comment.text.split(":")[-1].strip()
                    notes_lookup[veh_id][col_name] = f"{cell.value} -- {clean_note}"

    # 1. Start with the 'control' sheet as the base
    df_master = sheets["control"]

    # FIX: Restore Namibia 'NA' specifically for the COUNTRY_CODE column
    # We replace actual NaN values with the string 'NA' ONLY in the properties sheet
    # This is to handle the country code 'NA' for Namibia
    # if 'properties' in sheets:
    #     sheets['properties']['COUNTRY_CODE'] = sheets['properties']['COUNTRY_CODE'].fillna(
    #         'NA')
    extract_notes("control", sheets["control"])

    # 2. List of sheets that provide extra vehicle properties
    data_sheets = [
        "properties",
        "track_types",
        "graphics_properties",
        "roster",
    ]

    text_columns = ["ITEM", "NAME", "VEHIDCODE", "CARGODEF", "WEB"]

    for sheet_name in data_sheets:
        if sheet_name in sheets:
            current_sheet = sheets[sheet_name]

            # Extract notes from this sheet before merging
            extract_notes(sheet_name, current_sheet)

            cols_to_fix = [c for c in text_columns if c in current_sheet.columns]
            for col in cols_to_fix:
                current_sheet[col] = current_sheet[col].astype("string").fillna("")

            overlapping_cols = [c for c in current_sheet.columns if c in df_master.columns and c != "VEHIDCODE"]

            df_master = df_master.drop(columns=overlapping_cols)

            df_master = pd.merge(df_master, current_sheet, on="VEHIDCODE", how="left")

    # 3. Load Copyright

    df_copyright = sheets["copyright_text"]
    copyright_txt = ""
    if not df_copyright.empty:
        copyright_txt = str(df_copyright.iloc[0, 0])
    elif len(df_copyright.columns) > 0 and "Unnamed" not in str(df_copyright.columns[0]):
        copyright_txt = str(df_copyright.columns[0])

    # Final safety check before returning from load_master_data
    # df_master['COUNTRY_CODE'] = df_master['COUNTRY_CODE'].fillna('NA')

    return df_master, copyright_txt, notes_lookup


def load_vehicle_id_ranges(excel_path: str) -> pd.DataFrame:
    """Reads the vehicle ID range info from the Excel sheet and returns as a sorted DF"""
    sheets = pd.read_excel(excel_path, sheet_name=None)

    # Load workbook for openpyxl (to get notes/comments)
    wb = openpyxl.load_workbook(excel_path)
    df_ranges = sheets["vehicle_id_ranges"]
    df_ranges = df_ranges.sort_values(by="Range Start")
    return df_ranges
