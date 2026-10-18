import openpyxl
import pandas as pd
import warnings

from tools.helpers.paths import EXCEL_PATH, match_disk_case

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


# The old 'roster' sheet derived these from REGION1..4 (concatenated with "_") via substring searches.
# The tokens are what its formulas looked for, in addition to the region's own name.
REGION_FLAG_TOKENS = {
    "AFRICA": ["ALL_REGION", "AFRICA", "OLD_WORLD", "NON_EUROPEAN"],
    "ASIA": ["ALL_REGION", "ASIA", "OLD_WORLD", "NON_EUROPEAN", "APAC", "COMECON", "POST_SOVIET_BALTIC"],
    "SOUTHERN_EUROPE": ["ALL_REGION", "ALL_EUROPE", "SOUTHERN_EUROPE", "OLD_WORLD"],
    "EASTERN_EUROPE": ["ALL_REGION", "ALL_EUROPE", "EASTERN_EUROPE", "OLD_WORLD", "COMECON", "POST_SOVIET_BALTIC"],
    "WESTERN_EUROPE": ["ALL_REGION", "ALL_EUROPE", "WESTERN_EUROPE", "OLD_WORLD", "NORTH_WEST_EUROPE"],
    "NORTHERN_EUROPE": [
        "ALL_REGION",
        "ALL_EUROPE",
        "NORTHERN_EUROPE",
        "OLD_WORLD",
        "NORTH_WEST_EUROPE",
        "POST_SOVIET_BALTIC",
    ],
    "NORTH_AMERICA": ["ALL_REGION", "ALL_AMERICA", "NORTH_AMERICA", "NON_EUROPEAN"],
    "SOUTH_AMERICA": ["ALL_REGION", "ALL_AMERICA", "SOUTH_AMERICA", "NON_EUROPEAN", "COMECON_EXTENDED"],
    "OCEANIA": ["ALL_REGION", "OCEANIA", "APAC"],
}


def add_region_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Adds REGION_CONC plus one boolean column per region (AFRICA, ASIA, ...) based on REGION1..REGION4."""
    region_cols = [c for c in ("REGION1", "REGION2", "REGION3", "REGION4") if c in df.columns]
    region_conc = (
        df[region_cols].astype("string").fillna("").agg("_".join, axis=1).str.upper()
        if region_cols
        else pd.Series("", index=df.index)
    )
    df["REGION_CONC"] = region_conc
    for flag, tokens in REGION_FLAG_TOKENS.items():
        df[flag] = region_conc.apply(lambda conc, t=tokens: any(tok in conc for tok in t))
    return df


def get_excel_path() -> str:
    return EXCEL_PATH


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

    # Folder casing must match the disk (case-sensitive on Linux)
    if "SAVE_TO" in df_master.columns:
        df_master["SAVE_TO"] = df_master["SAVE_TO"].map(
            lambda p: match_disk_case(p) if isinstance(p, str) else p
        )

    # Region flags used to live in the (now removed) 'roster' sheet
    df_master = add_region_flags(df_master)

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
