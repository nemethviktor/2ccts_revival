import pandas as pd
import os
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# --- Configuration ---
EXCEL_FILE = 'vehicle_report.xlsx'
TEST_CASE_ONLY = True 

def generate_property_files():
    print("--- Property File Generation Starting ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, EXCEL_FILE)

    if not os.path.exists(excel_path):
        print(f"Error: Could not find Excel file at {excel_path}")
        return

    try:
        sheets = pd.read_excel(excel_path, sheet_name=None)
        df = sheets['properties']
        copyright_df = sheets['copyright_text']
    except Exception as e:
        print(f"Error reading Excel: {e}")
        return

    # Extract Copyright from A1
    header_text = str(copyright_df.columns[0]) if "Unnamed" not in str(copyright_df.columns[0]) else ""
    raw_copyright = header_text
    if not copyright_df.empty:
        data_text = str(copyright_df.iloc[0, 0])
        raw_copyright = data_text if header_text == "" else f"{header_text}\n{data_text}"
    header_block = f"\n{raw_copyright}\n\n"

    for index, row in df.iterrows():
        if pd.isna(row['VEHIDCODE']):
            continue

        rel_save_folder = str(row['SAVE_TO']).replace('\\', '/')
        file_name = f"{row['FILENAMES_EXPECTED']}_property.pnml"
        abs_save_folder = os.path.normpath(os.path.join(project_root, rel_save_folder))
        full_path = os.path.join(abs_save_folder, file_name)

        os.makedirs(abs_save_folder, exist_ok=True)

        content = []
        content.append(header_block)
        content.append('#include "../undefine_properties.pnml"\n\n')

        # Identity
        content.append(f"#define VEHIDCODE {row['VEHIDCODE']}\n")
        content.append(f"#define ITEM {row['ITEM']}\n")
        content.append(f"#define NAME string({row['NAME']})\n\n")

        # Region & Context
        content.append(f"#define VEHICLE_REGION REGION({row['REGION1']},{row['REGION2']},{row['REGION3']})\n")
        # Now pulling from column L (ENGINE_CLASS) and column AA (RUNNING_COST_BASE)
        content.append(f"#define ENGINE_CLASS {row['ENGINE_CLASS']}\n")
        content.append(f"#define RUNNING_COST_BASE {row['RUNNING_COST_BASE']}\n")
        
        # Track Type Logic (Handles Bool, Int, or String)
        track_types = []
        for col in df.columns:
            if col.startswith('TRACK_TYPE_'):
                val = row[col]
                if (isinstance(val, bool) and val) or (str(val).strip().upper() == 'TRUE') or (val == 1):
                    track_types.append(col.replace('TRACK_TYPE_', ''))
        content.append(f"#define TRACK_TYPE [{', '.join(track_types)}]\n\n")

        # Fixed Defaults Block
        content.append(f"#define INTRODUCTION_YEAR {row['INTRODUCTION_YEAR']}\n")
        content.append(f"#define MODEL_LIFE {row['MODEL_LIFE']}\n")
        content.append(f"#define RETIRE_EARLY {row['RETIRE_EARLY']}\n")
        content.append(f"#define VEHICLE_LIFE {row['VEHICLE_LIFE']}\n")

        # Prefixed Values
        content.append(f"#define LOADINGSPEED LOADINGSPEEDDEF_{row['LOADINGSPEED']}\n")
        content.append(f"#define CARGODEF CARGODEF_{row['CARGODEF']}\n\n")

        # Technical Specs
        tech_specs = ['SPEED', 'POWER', 'WEIGHT', 'TE_COEFFICIENT', 'AIR_DRAG_COEFFICIENT', 'LENGTH', 'ACTUAL_LENGTH', 'HEAD_CAPACITY']
        for spec in tech_specs:
            content.append(f"#define {spec} {row[spec]}\n")

        content.append(f"#define DUAL_HEADED {row['DUAL_HEADED']}\n")
        content.append(f"#define PASSENGER {row['PASSENGER']}\n")

        # Misc Flags
        misc_flags = []
        for col in df.columns:
            if col.startswith('MISC_FLAGS_'):
                val = row[col]
                if (isinstance(val, bool) and val) or (str(val).strip().upper() == 'TRUE') or (val == 1):
                    misc_flags.append(col.replace('MISC_FLAGS_', ''))
        content.append(f"#define MISC_FLAGS bitmask({', '.join(misc_flags)})\n")

        # Visual Flag (Prepending VISUAL_EFFECT_ to the first element)
        v1 = f"VISUAL_EFFECT_{row['VISUAL_EFFECT_1']}" if str(row['VISUAL_EFFECT_1']) != "0" else "0"
        content.append(f"#define VISUAL_FLAG visual_effect_and_powered({v1}, {row['VISUAL_EFFECT_2']}, {row['VISUAL_EFFECT_3']})\n")

        content.append(f"#define REFIT_COST DEFAULT_REFIT_COST\n")
        content.append(f"#define RELIABILITY_DECAY DEFAULT_RELIABILITY_DECAY\n")
        content.append(f"#define CARGO_AGE_PERIOD DEFAULT_CARGO_AGE_PERIOD\n")
        content.append(f"#define POWER_PER_WAGON DEFAULT_POWER_PER_WAGON\n")
        content.append(f"#define BITMASK_VEHICLE_INFO DEFAULT_BITMASK\n")
        content.append(f"#define SPRITE_ID DEFAULT_SPRITE_ID\n\n")

        df.to_csv(os.path.join(script_dir, 'vehicle_report.csv'), index=False)

        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.writelines(content)
            print(f"Generated: {full_path}")
        except Exception as e:
            print(f"Error writing {full_path}: {e}")

        if TEST_CASE_ONLY:
            break

if __name__ == "__main__":
    generate_property_files()
    print("--- Property File Generation Complete ---")