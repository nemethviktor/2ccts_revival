from typing import Literal

import pandas as pd
import os
import math
import warnings
from pandas.api.types import is_number
import re

from helpers.read_excel_file import load_master_data

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def generate_vehicle_id_pnml(copyright_text: str):
    print("--- Starting BadgeTable Generation ---")

    # 1. Setup Paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    excel_path = os.path.join(script_dir, "vehicle_report.xlsx")
    output_path = os.path.normpath(os.path.join(project_root, "src/badgetable.pnml"))

    content = []
    content.append(f"\n{copyright_text}\n\n\n")

    powers = [
        "power",
        "power/battery",
        "power/diesel",
        "power/electric",
        "power/electric/ac",
        "power/electric/dc",
        "power/steam",
        "power/turbine",
        "power/maglev",
        "power/metro",
        "power/dual",
    ]

    # currently unusued
    regions = [
        "region",
        "region/africa",
        "region/africa/eastern",
        "region/africa/middle",
        "region/africa/northern",
        "region/africa/southern",
        "region/africa/western",
        "region/america",
        "region/america/caribbean",
        "region/america/central",
        "region/america/northern",
        "region/america/south",
        "region/asia",
        "region/asia/central",
        "region/asia/eastern",
        "region/asia/southeastern",
        "region/asia/southern",
        "region/asia/western",
        "region/europe",
        "region/europe/eastern",
        "region/europe/northern",
        "region/europe/southern",
        "region/europe/western",
        "region/oceania",
        "region/oceania/australia_and_new_zealand",
        "region/oceania/melanesia",
        "region/oceania/micronesia",
        "region/oceania/polynesia",
    ]

    attributes = ["attribute", "attribute/push_pull"]

    roles = [
        "role",
        "role/coach__commuter_",
        "role/coach__express_",
        "role/coach__hs_",
        "role/coach__mail_",
        "role/coach__regional_",
        "role/commuter_urban",
        "role/express_passenger",
        "role/express",
        "role/universal",
        "role/heavy_freight",
        "role/light_freight",
        "role/metro",
        # why not shunter (noun) is beyond my comprehension.
        "role/powered_unpowered_sundry",
        "role/regional_passenger",
        "role/shunting",
        "role/freight",
        "role/ultra_high_speed__pax_",
        "role/ultra_high_speed__universal_",
        "role/wagon",
    ]

    for power in powers:
        power_underlined = power.replace("/", "_")
        if "_" in power_underlined:
            content.append(
                f"""\nspriteset (sprite_{power_underlined}) {{[0, 0, 16, 12, 0, 0, "gfx/Badges/power/{power_underlined}.png"]}}"""
            )

    for attribute in attributes:
        attribute_underlined = attribute.replace("/", "_")
        if "_" in attribute_underlined:
            content.append(
                f"""\nspriteset (sprite_{attribute_underlined}) {{[0, 0, 16, 12, 0, 0, "gfx/Badges/attributes/{attribute_underlined}.png"]}}"""
            )

    content.append("badgetable {")

    # List define

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

    content.append("\n// Powers")
    for power in powers:
        power_underlined = power.replace("/", "_")
        content.append(f"""\n\t
item (FEAT_BADGES, {power_underlined}) {{
    property {{
        label: "{power}";
        name: string(STR_{power_underlined.upper()});""")
        if "_" in power_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        if "_" in power_underlined:
            content.append(f"""\n\tgraphics {{default: sprite_{power_underlined};}}\n""")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Attributes")
    for attribute in attributes:
        attribute_underlined = attribute.replace("/", "_")
        content.append(f"""\n\t
item (FEAT_BADGES, {attribute_underlined}) {{
    property {{
        label: "{attribute}";
        name: string(STR_{attribute_underlined.upper()});""")
        if "_" in attribute_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        if "_" in attribute_underlined:
            content.append(f"""\n\tgraphics {{default: sprite_{attribute_underlined};}}\n""")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Regions")
    for region in regions:
        region_underlined = region.replace("/", "_")
        content.append(f"""\n\t
item (FEAT_BADGES, {region_underlined}) {{
    property {{
        label: "{region}";
        name: string(STR_{region_underlined.upper()});""")
        if "_" in region_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        content.append(f"}}\n")

    content.append("\n")

    content.append("\n// Roles")
    for role in roles:
        role_underlined = role.replace("/", "_")
        content.append(f"""\n\t
item (FEAT_BADGES, {role_underlined}) {{
    property {{
        label: "{role}";
        name: string(STR_{role_underlined.upper()});""")
        if "_" in role_underlined:
            content.append(f"""
        flags: bitmask(BADGE_FLAG_COPY_TO_RELATED_ENTITY);""")
        content.append(f"\n\t}}")
        content.append(f"}}\n")

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
    from helpers.read_excel_file import load_master_data, get_excel_path

    # Direct execution test logic:
    _, c_text, _ = load_master_data(get_excel_path())
    generate_vehicle_id_pnml(copyright_text=c_text)
    print("--- BadgeTable Generation Complete ---")
