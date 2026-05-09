from typing import Literal

import pandas as pd
import os
import math
import warnings
from pandas.api.types import is_number
import re

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def generate_vehicle_id_pnml():
    print("--- Starting BadgeTable Generation ---")

    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
    output_path = os.path.normpath(
        os.path.join(project_root, 'src/badgetable.pnml'))

    if not os.path.exists(excel_path):
        print(f"Error: Could not find Excel file at {excel_path}")
        return

    try:
        sheets = pd.read_excel(excel_path, sheet_name=None)
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

    flags = [
        "flag", "flag/AF", "flag/AX", "flag/AL", "flag/DZ", "flag/AS", "flag/AD", "flag/AO", "flag/AI", "flag/AQ", "flag/AG", "flag/AR",
        "flag/AM", "flag/AW", "flag/AU", "flag/AT", "flag/AZ", "flag/BS", "flag/BH", "flag/BD", "flag/BB", "flag/BY", "flag/BE", "flag/BZ",
        "flag/BJ", "flag/BM", "flag/BT", "flag/BO", "flag/BQ", "flag/BA", "flag/BW", "flag/BV", "flag/BR", "flag/IO", "flag/BN", "flag/BG",
        "flag/BF", "flag/BI", "flag/KH", "flag/CM", "flag/CA", "flag/CV", "flag/KY", "flag/CF", "flag/TD", "flag/CL", "flag/CN", "flag/CX",
        "flag/CC", "flag/CO", "flag/KM", "flag/CG", "flag/CD", "flag/CK", "flag/CR", "flag/CI", "flag/HR", "flag/CU", "flag/CW", "flag/CY",
        "flag/CZ", "flag/DK", "flag/DJ", "flag/DM", "flag/DO", "flag/EC", "flag/EG", "flag/SV", "flag/GQ", "flag/ER", "flag/EE", "flag/ET",
        "flag/FK", "flag/FO", "flag/FJ", "flag/FI", "flag/FR", "flag/GF", "flag/PF", "flag/TF", "flag/GA", "flag/GM", "flag/GE", "flag/DE",
        "flag/GDR", "flag/GH", "flag/GI", "flag/GR", "flag/GL", "flag/GD", "flag/GP", "flag/GU", "flag/GT", "flag/GG", "flag/GN", "flag/GW",
        "flag/GY", "flag/HT", "flag/HM", "flag/VA", "flag/HN", "flag/HK", "flag/HU", "flag/IS", "flag/IN", "flag/ID", "flag/IR", "flag/IQ",
        "flag/IE", "flag/IM", "flag/IL", "flag/IT", "flag/JM", "flag/JP", "flag/JE", "flag/JO", "flag/KZ", "flag/KE", "flag/KI", "flag/KP",
        "flag/KR", "flag/KW", "flag/KG", "flag/LA", "flag/LV", "flag/LB", "flag/LS", "flag/LR", "flag/LY", "flag/LI", "flag/LT", "flag/LU",
        "flag/MO", "flag/MK", "flag/MG", "flag/MW", "flag/MY", "flag/MV", "flag/ML", "flag/MT", "flag/MH", "flag/MQ", "flag/MR", "flag/MU",
        "flag/YT", "flag/YU", "flag/MX", "flag/FM", "flag/MD", "flag/MC", "flag/MN", "flag/ME", "flag/MS", "flag/MA", "flag/MZ", "flag/MM",
        "flag/NA", "flag/NR", "flag/NP", "flag/NL", "flag/NC", "flag/NZ", "flag/NI", "flag/NE", "flag/NG", "flag/NU", "flag/NF", "flag/MP",
        "flag/NO", "flag/OM", "flag/PK", "flag/PW", "flag/PS", "flag/PA", "flag/PG", "flag/PY", "flag/PE", "flag/PH", "flag/PN", "flag/PL",
        "flag/PT", "flag/PR", "flag/QA", "flag/RE", "flag/RO", "flag/RU", "flag/SU", "flag/RW", "flag/BL", "flag/SH", "flag/KN", "flag/LC",
        "flag/MF", "flag/PM", "flag/VC", "flag/WS", "flag/SM", "flag/ST", "flag/SA", "flag/SN", "flag/RS", "flag/SC", "flag/SL", "flag/SG",
        "flag/SX", "flag/SK", "flag/SI", "flag/SB", "flag/SO", "flag/ZA", "flag/GS", "flag/SS", "flag/ES", "flag/LK", "flag/SD", "flag/SR",
        "flag/SJ", "flag/SZ", "flag/SE", "flag/CH", "flag/SY", "flag/TW", "flag/TJ", "flag/TZ", "flag/TH", "flag/TL", "flag/TG", "flag/TK",
        "flag/TO", "flag/TT", "flag/TN", "flag/TR", "flag/TM", "flag/TC", "flag/TV", "flag/UG", "flag/UA", "flag/AE", "flag/GB", "flag/US",
        "flag/UM", "flag/UY", "flag/UZ", "flag/VU", "flag/VE", "flag/VN", "flag/VG", "flag/VI", "flag/WF", "flag/EH", "flag/YE", "flag/ZM",
        "flag/ZW", "flag/EU", "flag/WRLD"
    ]

    powers = ["power",  "power/battery", "power/diesel", "power/electric", "power/electric/ac", "power/electric/dc",
              "power/steam", "power/turbine", "power/maglev", "power/metro"
              ]

    # currently unusued
    regions = ["region", "region/africa", "region/africa/eastern", "region/africa/middle", "region/africa/northern",
               "region/africa/southern", "region/africa/western", "region/america", "region/america/caribbean", "region/america/central",
               "region/america/northern", "region/america/south", "region/asia", "region/asia/central", "region/asia/eastern",
               "region/asia/southeastern", "region/asia/southern", "region/asia/western", "region/europe", "region/europe/eastern",
               "region/europe/northern", "region/europe/southern", "region/europe/western", "region/oceania",
               "region/oceania/australia_and_new_zealand", "region/oceania/melanesia", "region/oceania/micronesia", "region/oceania/polynesia"
               ]

    attributes = ["attribute",
                  "attribute/push_pull"
                  ]

    roles = ["role",
             "role/coach__commuter_", "role/coach__express_", "role/coach__hs_",
             "role/coach__mail_", "role/coach__regional_",
             "role/commuter_urban", "role/express_passenger",
             "role/express", "role/universal",
             "role/heavy_freight", "role/light_freight", "role/metro",
             # why not shunter (noun) is beyond my comprehension.
             "role/powered_unpowered_sundry", "role/regional_passenger", "role/shunting",
             "role/freight", "role/ultra_high_speed__pax_", "role/ultra_high_speed__universal_", "role/wagon"
             ]

    for power in powers:
        power_underlined = power.replace('/', '_')
        if '_' in power_underlined:
            content.append(
                f"""\nspriteset (sprite_{power_underlined}) {{[0, 0, 16, 12, 0, 0, "gfx/Badges/power/{power_underlined}.png"]}}""")

    for attribute in attributes:
        attribute_underlined = attribute.replace('/', '_')
        if '_' in attribute_underlined:
            content.append(
                f"""\nspriteset (sprite_{attribute_underlined}) {{[0, 0, 16, 12, 0, 0, "gfx/Badges/attributes/{attribute_underlined}.png"]}}""")

    for flag in flags:
        flag_underlined = flag.replace('/', '_')
        if '_' in flag_underlined:
            content.append(
                f"""\nspriteset (sprite_{flag_underlined}) {{[0, 0, 18, 12, 0, 0, "gfx/Badges/flag/{flag_underlined.lower().replace('flag_', '')}.png"]}}""")

    content.append("badgetable {")

    # List define

    content.append("\n// Flags\n")
    for flag in flags:
        content.append(f"""\t"{flag}",\n""")

    content.append("\n// Powers\n")
    for power in powers:
        content.append(f"""\t"{power}",\n""")

    content.append("\n// Regions\n")
    for region in regions:
        content.append(f"""\t"{region}",\n""")

    content.append("\n// Roles\n")
    for role in roles:
        content.append(f"""\t"{role}",\n""")

    content.append("\n// Attributes\n")
    for attribute in attributes:
        content.append(f"""\t"{attribute}",\n""")

    content.append("}\n")

    # Item defines

    content.append("\n// Flag Items")
    for flag in flags:
        flag_underlined = flag.replace('/', '_')
        content.append(f"""\n\t
item (FEAT_BADGES, {flag_underlined}) {{
    property {{
        label: "{flag}";
        name: string(STR_{flag_underlined.upper()});""")
        if '_' in flag_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        if '_' in flag_underlined:
            content.append(
                f"""\n\tgraphics {{default: sprite_{flag_underlined};}}\n""")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Powers")
    for power in powers:
        power_underlined = power.replace('/', '_')
        content.append(f"""\n\t
item (FEAT_BADGES, {power_underlined}) {{
    property {{
        label: "{power}";
        name: string(STR_{power_underlined.upper()});""")
        if '_' in power_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        if '_' in power_underlined:
            content.append(
                f"""\n\tgraphics {{default: sprite_{power_underlined};}}\n""")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Attributes")
    for attribute in attributes:
        attribute_underlined = attribute.replace('/', '_')
        content.append(f"""\n\t
item (FEAT_BADGES, {attribute_underlined}) {{
    property {{
        label: "{attribute}";
        name: string(STR_{attribute_underlined.upper()});""")
        if '_' in attribute_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        if '_' in attribute_underlined:
            content.append(
                f"""\n\tgraphics {{default: sprite_{attribute_underlined};}}\n""")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Regions")
    for region in regions:
        region_underlined = region.replace('/', '_')
        content.append(f"""\n\t
item (FEAT_BADGES, {region_underlined}) {{
    property {{
        label: "{region}";
        name: string(STR_{region_underlined.upper()});""")
        if '_' in region_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Roles")
    for role in roles:
        role_underlined = role.replace('/', '_')
        content.append(f"""\n\t
item (FEAT_BADGES, {role_underlined}) {{
    property {{
        label: "{role}";
        name: string(STR_{role_underlined.upper()});""")
        if '_' in role_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        content.append(f"}}\n")

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
    print("--- BadgeTable Generation Complete ---")
