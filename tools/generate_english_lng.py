import pandas as pd
import os
import warnings

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

def is_true(val) -> bool:
    """ Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == 'TRUE') or (val == 1)


def get_voltage_suffix(row):
    """
    Analyzes track columns to return specific technical suffixes.
    Returns 'Dual Pickup' if both rail-based and wire-based power is detected.
    """
    # 1. Get all active track columns
    track_cols = [c for c in row.index if c.startswith('TRACK_TYPE_') and is_true(row[c])]
    
    # 2. Categorize the power sources based on the last segment of the column name
    # Wire-based (Pantograph)
    wires = [c for c in track_cols if any(v in c.split('_')[-1] for v in ['25KV', '15KV', '3KV', '1500V', 'OHLE'])]
    # Rail-based (Contact shoe)
    rails = [c for c in track_cols if any(v in c.split('_')[-1] for v in ['3RD', '4TH'])]
    # Separately confirmed 'DUAL'
    hc_dual = [c for c in track_cols if any(v in c.split('_')[-1] for v in ['DUAL'])]
    
    # 3. Dual Pickup Logic: If we have both Wires and Rails active
    if (wires and rails) or hc_dual:
        return "Dual Pickup"

    # 4. Multi-voltage Logic: If we have multiple types within the same category
    if len(wires + rails) > 1:
        return "Multi-V"

    # 5. Individual Mapping (only reached if exactly one power type exists)
    mapping = {
        '25KV':  "25kV AC",
        '15KV':  "15kV AC",
        '3KV':   "3kV DC",
        '1500V': "1500V DC",
        '3RD':   "3rd Rail",
        '4TH':   "4th Rail",
        'OHLE':  "OHLE [Multi-V]"
    }

    # Combine lists to find the single active key
    active_power_types = wires + rails
    if active_power_types:
        tag = active_power_types[0].split('_')[-1]
        return mapping.get(tag, "")
            
    return ""
def get_hardcoded_content():
    content = []
    content.append("##grflangid 0x01\n\n")
    content.append("# Main grf title and description\n")
    content.append("STR_GRF_NAME                        :{TITLE}\n")
    content.append("STR_GRF_DESCRIPTION                 :{SILVER}2cc Trains of the World in NML {}{}(c)2ccts Revival {}License:GPLv2 or higher. {}See readme for details.\n")
    content.append("STR_GRF_URL                         :https://github.com/nemethviktor/2ccts_revival\n\n")
    content.append("# General error messages\n")
    content.append("str_used_with_dynamic_engines       :dynamic_engines = true (setting in openttd.cfg)\n")
    content.append("str_error_region                    :No regions enabled, {STRING} has been disabled\n\n")
    content.append("# parameter strings\n")
    content.append("STR_PARAM_PURCHASE_COST             :Purchase cost multiplier\n")
    content.append("STR_PARAM_PURCHASE_COST_DESC        :You can use this setting to increase or decrease the purchase costs of the vehicles in this set.\n")
    content.append("STR_PARAM_RUNNING_COST              :Running cost multiplier\n")
    content.append("STR_PARAM_RUNNING_COST_DESC         :You can use this setting to increase or decrease the running costs of the vehicles in this set.\n")
    content.append("\n")
    content.append("STR_PARAM_DIVIDE_16                 :1/16\n")
    content.append("STR_PARAM_DIVIDE_8                  :1/8\n")
    content.append("STR_PARAM_DIVIDE_4                  :1/4\n")
    content.append("STR_PARAM_DIVIDE_2                  :1/2\n")
    content.append("STR_PARAM_NORMAL                    :1 (default)\n")
    content.append("STR_PARAM_TIMES_2                   :2\n")
    content.append("STR_PARAM_TIMES_4                   :4\n")
    content.append("STR_PARAM_TIMES_8                   :8\n")
    content.append("STR_PARAM_TIMES_16                  :16\n")
    content.append("\n")
    content.append("# region parameters\n")
    content.append("STR_PARAM_CONCEPT                                               :Concept vehicles\n")
    content.append("STR_PARAM_CONCEPT_DESC                                          :Use concept vehicles\n")
    content.append("STR_PARAM_REGION_AFRICA                                         :Africa\n")
    content.append("STR_PARAM_REGION_AFRICA_DESC                                    :Use vehicles from Africa\n")
    content.append("STR_PARAM_REGION_NORTH_AMERICA                                  :North America\n")
    content.append("STR_PARAM_REGION_NORTH_AMERICA_DESC                             :Use vehicles from North America\n")
    content.append("STR_PARAM_REGION_SOUTH_AMERICA                                  :South America\n")
    content.append("STR_PARAM_REGION_SOUTH_AMERICA_DESC                             :Use vehicles from South America\n")
    content.append("STR_PARAM_REGION_ASIA                                           :Asia\n")
    content.append("STR_PARAM_REGION_ASIA_DESC                                      :Use vehicles from Asia\n")
    content.append("STR_PARAM_REGION_NORTHERN_EUROPE                                :Northern Europe\n")
    content.append("STR_PARAM_REGION_NORTHERN_EUROPE_DESC                           :Use vehicles from Northern Europe\n")
    content.append("STR_PARAM_REGION_EASTERN_EUROPE                                 :Eastern Europe\n")
    content.append("STR_PARAM_REGION_EASTERN_EUROPE_DESC                            :Use vehicles from Eastern Europe\n")
    content.append("STR_PARAM_REGION_SOUTHERN_EUROPE                                :Southern Europe\n")
    content.append("STR_PARAM_REGION_SOUTHERN_EUROPE_DESC                           :Use vehicles from Southern Europe\n")
    content.append("STR_PARAM_REGION_WESTERN_EUROPE                                 :Western Europe\n")
    content.append("STR_PARAM_REGION_WESTERN_EUROPE_DESC                            :Use vehicles from Western Europe\n")
    content.append("STR_PARAM_REGION_OCEANIA                                        :Oceania\n")
    content.append("STR_PARAM_REGION_OCEANIA_DESC                                   :Use vehicles from Oceania\n")
    content.append("\n")
    content.append("# loading speed parameter\n")
    content.append("STR_PARAM_LOADINGSPEED                                          :Loading speed\n")
    content.append("STR_PARAM_LOADINGSPEED_DESC                                     :Set the loading speed of this set\n")
    content.append("STR_PARAM_LOADINGSPEED_SLOW                                     :Slow\n")
    content.append("STR_PARAM_LOADINGSPEED_NORMAL                                   :Normal (default)\n")
    content.append("STR_PARAM_LOADINGSPEED_FAST                                     :Fast\n")
    content.append("STR_PARAM_LOADINGSPEED_ULTRA                                    :As fast as possible\n")
    
    content.append("\n# VEHICLE NAMES\n")
    return content

def generate_english_lng():
    print("--- Generating English Language File ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.join(project_root, 'lang', 'english.lng')

    # Load Data
    sheets = pd.read_excel(excel_path, sheet_name=None)
    df_items = sheets['english_items']
    
    # We need track_types and properties to determine the full suffix
    df_props = sheets['properties'][['VEHIDCODE', 'COST_CAT', 'ENGINE_CLASS']]
    df_tracks = sheets['track_types']
    
    # Merge everything
    df_master = pd.merge(df_items, df_props, on='VEHIDCODE', how='left')
    df_master = pd.merge(df_master, df_tracks, on='VEHIDCODE', how='left')

    # Base Suffix Map for General Types
    base_suffixes = {
        'STEAMENGINE': '(Steam)',
        'DIESELENGINE': '(Diesel)',
        'ELECTRICENGINE': '(Electric)',
        'MAGLEVSU': '(Maglev)',
        'STEAMRAILBUS': '(Steam Railbus)',
        'DIESELRAILBUS': '(Diesel Railbus)',
        'ELECTRICRAILBUS': '(Electric Railbus)',
        'METRORAILBUS': '(Single Unit Metro)',
        'MAGLEVRAILBUS': '(Maglev Railbus)',
        'DMU': '(DMU)',
        'EMU': '(EMU)',
        'MAGLEVMU': '(MMU)',
        'COACH': '(Coach)',
        'WAGON': '(Wagon)',
        'METRO': '(Metro)',
    }

    # 2. Hardcoded Header (Top of your current file)
    content = get_hardcoded_content()

    # 3. Process Vehicles
    # Group by COST_CAT to keep the file organized like the original
    # Process by COST_CAT for organization
    for cat in df_master['COST_CAT'].unique():
        if pd.isna(cat): continue
        
        content.append(f"\n# {cat}\n")
        cat_df = df_master[df_master['COST_CAT'] == cat]
        
        for _, row in cat_df.iterrows():
            vehid = str(row['VEHIDCODE'])
            base_name = row['English_Name']
            
            # 1. Get Base Type Suffix
            suffix = base_suffixes.get(row['COST_CAT'], f"({row['COST_CAT']})")
            
            # 2. Add Voltage Specifics if it is Electric
            if row['ENGINE_CLASS'] == 'ELECTRIC' or cat == 'METRO':
                v_suffix = get_voltage_suffix(row)
                if v_suffix:
                    # e.g. (Electric) -> (Electric, 25kV AC)
                    suffix = suffix.replace(')', f", {v_suffix})")
            # For these two we just wipe the previous suffix element because it too verbose otherwise
            elif vehid.endswith('Powered'):
                suffix = "(Powered)"
            elif vehid.endswith('Unpowered'):
                suffix = "(Unpowered)"
            
            label = f"str_{vehid}"
            line = f"{label:<70}:{base_name} {suffix}\n"
            content.append(line)
            

    
    content.append("\n# PURCHASE MENU TEXTS\n")
    content.append("str_unit_wagon_passenger        :This generic wagon can ONLY be used with passenger MUs to create trains of the desired length\n")
    content.append("str_unit_wagon_cargo            :This generic wagon can ONLY be used with cargo MUs to create trains of the desired length\n\n")

    content.append("# Can(not) attach vehicle texts\n")
    content.append("str_cannot_attach_wagon_to_MU                           :Cannot attach wagon to Multiple Unit engine\n")
    content.append("str_cannot_attach_wagon_to_Unit_Wagon                   :Cannot attach regular wagon to Unit Wagon\n")
    content.append("str_cannot_attach_Unit_wagon_to_engine                  :Cannot attach Unit Wagon to regular engine\n")
    content.append("str_cannot_attach_Unit_wagon_to_wagon                   :Cannot attach Unit Wagon to regular wagon\n")
    content.append("str_cannot_attach_Unit_wagon_cargo_to_passenger         :Cannot attach cargo Unit Wagon to passenger Multiple Unit engine\n")
    content.append("str_cannot_attach_Unit_wagon_passenger_to_cargo         :Cannot attach passenger Unit Wagon to cargo Multiple Unit engine\n")


    # 5. Save File
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(content)
    
    print(f"Successfully generated {output_path}")

if __name__ == "__main__":
    generate_english_lng()
    print("--- Generating English Language File Finished ---")
    