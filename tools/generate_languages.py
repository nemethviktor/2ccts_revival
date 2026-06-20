import pandas as pd
import os
import glob
import csv
import warnings
import re
from datetime import datetime


# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
lang_dir = os.path.join(project_root, 'lang')

# BLACKLIST: Categories that should have NO technical tags at all
BLACKLIST = ['COACH', 'WAGON']


def is_true(val):
    return (val == True or str(val).upper() == 'TRUE') or (val == 1)


def load_excel_data():
    """Loads vehicle IDs and technical data from Excel sheets."""
    df_control = pd.read_excel(excel_path, sheet_name='control')
    df_props = pd.read_excel(excel_path, sheet_name='properties')
    df_tracks = pd.read_excel(excel_path, sheet_name='track_types')

    df = df_control[['VEHIDCODE', 'NAME', 'ENGLISH', 'IS_POWERED_UNPOWERED_SUNDRY', 'VEHID_ID', 'WEB']].merge(
        df_props[['VEHIDCODE', 'ENGINE_CLASS', 'COST_CAT',
                  'DUAL_HEADED', 'IS_TURBINE']],
        on='VEHIDCODE', how='left'
    )
    df = df.merge(df_tracks, on='VEHIDCODE', how='left')
    return df


def sync_csv_with_excel(df_vehicles):
    """
    Updates CSV files with changes from Excel.
    - Updates English names in english.csv.
    - Adds missing keys to other languages as blank (not-translated).
    """
    excel_map = {str(row['NAME']).strip().lower(): str(row['ENGLISH']).strip()
                 for _, row in df_vehicles.iterrows()}

    for csv_file in glob.glob(os.path.join(lang_dir, "*.csv")):
        lang_filename = os.path.basename(csv_file).lower()
        is_english = (lang_filename == 'english.csv')
        rows = []
        existing_keys = set()
        file_changed = False

        if os.path.exists(csv_file):
            with open(csv_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.reader(f)
                for row in reader:
                    if not row:
                        continue
                    key = row[0].strip().lower()
                    existing_keys.add(key)

                    if key in excel_map:
                        new_excel_val = excel_map[key]
                        # Update English file if Excel changed
                        if is_english and row[1] != new_excel_val:
                            row[1] = new_excel_val
                            file_changed = True
                    rows.append(row)

        # Add entirely new vehicle IDs found in Excel
        for v_id, v_eng in excel_map.items():
            if v_id not in existing_keys:
                # English gets the name, others get an empty string (not-translated)
                new_val = v_eng if is_english else ""
                rows.append([v_id, new_val])
                file_changed = True

        if file_changed:
            with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                writer.writerows(rows)
            # print(f"Synced changes into {os.path.basename(csv_file)}.")


def get_tech_suffixes(row, lang_map, english_map):
    """Determines tech suffixes with adjective/noun split and redundancy filters."""
    suffixes_list = []
    suffixes_set = set()

    v_id = str(row.get('NAME', '')).lower()
    c_cat = str(row.get('COST_CAT', '')).upper().strip()
    e_class = str(row.get('ENGINE_CLASS', '')).upper().strip()

    def get_val(key):
        return lang_map.get(key) or english_map.get(key.lower(), "")

    def add_to_list(val):
        if val and val not in suffixes_set:
            suffixes_list.append(val)
            suffixes_set.add(val)

    # Generic Wagon Rule
    if "wagon" in v_id and (v_id.endswith("_powered") or v_id.endswith("_unpowered")):
        p_key = "STR_SUFFIX_UNPOWERED" if "_unpowered" in v_id else "STR_SUFFIX_POWERED"
        add_to_list(get_val(p_key))
        return f" ({', '.join(suffixes_list)})" if suffixes_list else ""

    if c_cat in BLACKLIST or e_class in BLACKLIST:
        return ""

    # Primary Noun
    class_map = {
        "STEAMENGINE": "STR_SUFFIX_STEAMENGINE", "DIESELENGINE": "STR_SUFFIX_DIESELENGINE",
        "ELECTRICENGINE": "STR_SUFFIX_ELECTRICENGINE", "STEAMRAILBUS": "STR_SUFFIX_STEAMRAILBUS",
        "DIESELRAILBUS": "STR_SUFFIX_DIESELRAILBUS", "ELECTRICRAILBUS": "STR_SUFFIX_ELECTRICRAILBUS",
        "METRORAILBUS": "STR_SUFFIX_METRORAILBUS", "MAGLEVRAILBUS": "STR_SUFFIX_MAGLEVRAILBUS",
        "DMU": "STR_SUFFIX_DMU", "EMU": "STR_SUFFIX_EMU", "METRO": "STR_SUFFIX_METRO",
        "MMU": "STR_SUFFIX_MMU", "MAGLEV": "STR_SUFFIX_MAGLEVENGINE"
    }
    target_class = c_cat if c_cat in class_map else e_class
    primary_noun = get_val(class_map.get(target_class, ""))
    add_to_list(primary_noun)

    # Adjective Logic
    adj_map = {
        "STEAM": "STR_SUFFIX_STEAM", "DIESEL": "STR_SUFFIX_DIESEL",
        "ELECTRIC": "STR_SUFFIX_ELECTRIC", "MAGLEV": "STR_SUFFIX_MAGLEV",
        "DMU": "STR_SUFFIX_DIESEL", "EMU": "STR_SUFFIX_ELECTRIC", "METRO": "STR_SUFFIX_ELECTRIC"
    }
    effective_e_class = e_class
    if "METRO" in c_cat:
        effective_e_class = "ELECTRIC"

    adjective = get_val(adj_map.get(effective_e_class, ""))

    if adjective and primary_noun:
        adj_l, noun_l = adjective.lower(), primary_noun.lower()
        if adj_l in noun_l or (adj_l == "electric" and "emu" in noun_l) or (adj_l == "diesel" and "dmu" in noun_l):
            adjective = ""

    # Tech Suffixes
    if is_true(row.get('IS_POWERED_UNPOWERED_SUNDRY')):
        p_key = "STR_SUFFIX_UNPOWERED" if "UNPOWERED" in str(
            row.get('VEHIDCODE', '')).upper() else "STR_SUFFIX_POWERED"
        add_to_list(get_val(p_key))

    if is_true(row.get('IS_TURBINE')):
        add_to_list(get_val("STR_SUFFIX_GAS_TURBINE"))

    track_cols = [c for c in row.index if str(
        c).startswith('TRACK_TYPE_') and is_true(row[c])]
    if track_cols:
        v_vals = []
        for col in track_cols:
            v_text = get_val(f"STR_SUFFIX_{col.split('_')[-1].upper()}")
            if v_text and v_text not in v_vals:
                v_vals.append(v_text)
        if v_vals:
            if adjective:
                v_vals[0] = f"{adjective} {v_vals[0]}".strip()
            for vv in v_vals:
                add_to_list(vv)

    if is_true(row.get('DUAL_HEADED')):
        add_to_list(get_val("STR_SUFFIX_DUAL_UNIT"))

    return f" ({', '.join(suffixes_list)})" if suffixes_list else ""


def generate_languages():
    df_vehicles = load_excel_data()

    # 1. Sync Excel names to CSVs
    sync_csv_with_excel(df_vehicles)

    # Reload English map for generation fallback
    english_csv = os.path.join(lang_dir, 'english.csv')
    english_map = {}
    master_keys = []
    if os.path.exists(english_csv):
        with open(english_csv, 'r', encoding='utf-8-sig') as f:
            for r in csv.reader(f):
                if r:
                    k = r[0].strip()
                    english_map[k.lower()] = r[1].strip()
                    if k.isupper():
                        master_keys.append(k)

    for csv_file in glob.glob(os.path.join(lang_dir, "*.csv")):
        lang_id = os.path.splitext(os.path.basename(csv_file))[0]
        is_english_lang = (lang_id.lower() == 'english')
        lng_file = os.path.join(lang_dir, f"{lang_id}.lng")

        metadata, hardcoded, existing_vehicles = [], {}, {}
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            for r in csv.reader(f):
                if not r:
                    continue
                k, v = r[0].strip(), (r[1].strip() if len(r) > 1 else "")
                if k.startswith("##"):
                    metadata.append(k)
                elif k.isupper():
                    hardcoded[k] = v
                else:
                    existing_vehicles[k.lower()] = v

        output = metadata + [""]
        output.append("# Hardcoded Strings")

        for k in master_keys:
            v = hardcoded.get(k, "")
            if not is_english_lang and not v:
                output.append(f"# {k.ljust(65)} : not translated")
            else:
                now = datetime.now()
                build_string  = f"{{}}{{SILVER}}Build: {now.strftime("%Y-%m-%d-%H:%M:%S")}"
                final_val = v if (
                    v or not is_english_lang) else english_map.get(k.lower(), "")
                output.append(f"{k.ljust(65)} :{final_val}{build_string if k == 'STR_GRF_DESCRIPTION' else ''}")

        normal_word = hardcoded.get("STR_WORD_NORMAL") or (
            english_map.get("str_word_normal") if not is_english_lang else "default")
        output.append("\n# Parameters")
        for d in ["16", "8", "4", "2"]:
            output.append(f"{f'STR_PARAM_DIVIDE_{d}'.ljust(65)} :1/{d}")
        output.append(f"{'STR_PARAM_NORMAL'.ljust(65)} :1 ({normal_word})")
        for m in ["2", "4", "8", "16"]:
            output.append(f"{f'STR_PARAM_TIMES_{m}'.ljust(65)} :{m}")

        output.append("\n# Vehicles")
        df_sorted = df_vehicles.sort_values(
            by=['COST_CAT', 'VEHID_ID'], na_position='last')
        last_header = None

        for _, v_row in df_sorted.iterrows():
            curr_header = str(v_row['COST_CAT']).capitalize()
            if curr_header != last_header:
                output.append(f"\n# {curr_header}")
                last_header = curr_header

            v_id = str(v_row['NAME']).strip().lower()
            v_eng_base = str(v_row['ENGLISH']).strip()

            # Logic: If item is in local CSV and NOT empty, use it.
            # Otherwise, English file falls back to Excel, non-English file marks "not translated".
            if v_id in existing_vehicles and existing_vehicles[v_id]:
                v_base_name = existing_vehicles[v_id]
            elif is_english_lang:
                v_base_name = v_eng_base
            else:
                v_base_name = ""

            v_base_name = re.sub(r'\s*\([^)]*\)$', '', v_base_name).strip()
            suffix = get_tech_suffixes(v_row, hardcoded, english_map)

            if not v_base_name:
                output.append(f"# {v_id.ljust(65)} : not translated")
            else:
                output.append(f"{v_id.ljust(65)} :{v_base_name}{suffix}")

            #if is_english_lang:
            #    v_web_val = v_row.get('WEB')
            #    url_token_name = f"{str(v_row['NAME']).strip().lower()}_url"
            #    # If the cell is populated and isn't an Excel NaN/empty string
            #    if pd.notna(v_web_val) and str(v_web_val).strip() != "" and str(v_web_val).strip().lower() != "nan":
            #        clean_url_string = str(v_web_val).strip()
            #        
            #        # Append it directly to the output without running modification or change tracking checks
            #        output.append(f"{url_token_name.ljust(65)} :{{BLACK}}Data: {{GOLD}}{clean_url_string}")
            #    else:
            #        output.append(f"{url_token_name.ljust(65)} :{{BLACK}}Data: NA")

        with open(lng_file, 'w', encoding='utf-8') as f:
            for line in output:
                f.write(line + "\n")
        # print(f"Exported: {lng_file}")


if __name__ == "__main__":
    generate_languages()
