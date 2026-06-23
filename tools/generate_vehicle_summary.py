import pandas as pd
import re
import os
import base64
from PIL import Image
from io import BytesIO
import warnings

# Silence openpyxl warnings
warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")

# --- Configuration ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
excel_path = os.path.join(script_dir, "vehicle_report.xlsx")
templates_pnml_path = os.path.join(project_root, "src", "templates.pnml")
output_path = os.path.normpath(os.path.join(project_root, "docs", "vehicle_summary.md"))
gfx_output_dir = os.path.join(project_root, "docs", "vehicle_graphics")


def parse_templates(file_path):
    """Parses templates.pnml to create a map of template names to (width, height)."""
    templates = {}
    if not os.path.exists(file_path):
        return templates
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r"template\s+(template_purchase\w*)\s*\([^)]*\)\s*\{([\s\S]*?)\}"
    matches = re.finditer(pattern, content)

    for match in matches:
        name = match.group(1)
        body = match.group(2)
        coords = re.findall(
            r"\[\s*(?:x\+?)?(\d+)?\s*,\s*(?:y\+?)?(\d+)?\s*,\s*(\d+)\s*,\s*(\d+)", body
        )
        for c in coords:
            w, h = int(c[2]), int(c[3])
            if w > 1:
                templates[name] = (w, h)
                break
    return templates


def process_and_save_image(v_id, pnml_path, excel_png_path, templates):
    """Extracts purchase sprite and saves it if it doesn't exist."""
    os.makedirs(gfx_output_dir, exist_ok=True)
    filename = f"{v_id}.png"
    save_path = os.path.join(gfx_output_dir, filename)
    rel_md_path = f"vehicle_graphics/{filename}"

    if os.path.exists(save_path):
        return rel_md_path

    if not os.path.exists(pnml_path):
        return ""

    try:
        with open(pnml_path, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'spriteset\s*\(\s*[^,]+_purchase\s*,\s*"([^"]+)"\s*\)\s*\{\s*(\w+)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*\}'
        match = re.search(pattern, content)
        if not match:
            return ""

        pnml_png_rel_path = match.group(1)
        tpl_name = match.group(2)
        x_start = int(match.group(3))
        y_start = int(match.group(4))

        if tpl_name not in templates:
            return ""
        w, h = templates[tpl_name]

        if "_purchase.png" in pnml_png_rel_path:
            pnml_dir = os.path.dirname(pnml_path)
            png_filename = os.path.basename(pnml_png_rel_path)
            png_path = (
                os.path.join(pnml_dir, png_filename)
                .replace("src/", "gfx/")
                .replace("src\\", "gfx/")
            )
        else:
            png_path = excel_png_path

        if not os.path.exists(png_path):
            return ""

        img = Image.open(png_path).convert("RGBA")
        crop = img.crop((x_start, y_start, x_start + w, y_start + h))

        pixdata = crop.load()
        for y in range(crop.size[1]):
            for x in range(crop.size[0]):
                if pixdata[x, y][:3] == (0, 0, 255):
                    pixdata[x, y] = (0, 0, 0, 0)

        crop.save(save_path, format="PNG")
        return rel_md_path
    except:
        return ""


def is_true(val) -> bool:
    """Checks if a value evals to true (ie is a string that says so, or 1, or just True)"""
    return (val == True or str(val).upper() == "TRUE") or (val == 1)


def generate_markdown():
    print("--- Generating Vehicle Summary (Markdown) ---")
    sheets = pd.read_excel(excel_path, sheet_name=None)
    df_control = sheets["control"]
    df_props = sheets["properties"]
    df_roster = sheets["roster"]
    df_tracks = sheets["track_types"]

    # Merge core data
    df = df_control.merge(df_props, on="VEHIDCODE", how="inner")
    df = df.merge(df_roster, on="VEHIDCODE", how="inner", suffixes=("", "_roster"))
    df = df.merge(df_tracks, on="VEHIDCODE", how="inner", suffixes=("", "_tracks"))

    templates = parse_templates(templates_pnml_path)

    # 1. Define the Mapping (Excel Text -> NML Variable)
    region_map = {
        "AFRICA": "AFRICA",
        "NORTH_AMERICA": "NORTH_AMERICA",
        "SOUTH_AMERICA": "SOUTH_AMERICA",
        "ASIA": "ASIA",
        "NORTHERN_EUROPE": "NORTHERN_EUROPE",
        "EASTERN_EUROPE": "EASTERN_EUROPE",
        "WESTERN_EUROPE": "WESTERN_EUROPE",
        "SOUTHERN_EUROPE": "SOUTHERN_EUROPE",
        "OCEANIA": "OCEANIA",
        "ALL_EUROPE": [
            "NORTHERN_EUROPE",
            "EASTERN_EUROPE",
            "SOUTHERN_EUROPE",
            "WESTERN_EUROPE",
        ],
        "ALL_AMERICA": ["NORTH_AMERICA", "SOUTH_AMERICA"],
        "COMECON": ["ASIA", "EASTERN_EUROPE"],
        "OLD_WORLD": [
            "NORTHERN_EUROPE",
            "EASTERN_EUROPE",
            "SOUTHERN_EUROPE",
            "WESTERN_EUROPE",
            "ASIA",
            "AFRICA",
        ],
        "NON_EUROPEAN": ["NORTH_AMERICA", "SOUTH_AMERICA", "ASIA", "OCEANIA", "AFRICA"],
        "APAC": ["ASIA", "OCEANIA"],
        "COMECON_EXTENDED": ["ASIA", "EASTERN_EUROPE", "SOUTH_AMERICA"],
        "NORTH_WEST_EUROPE": ["NORTHERN_EUROPE", "WESTERN_EUROPE"],
        "POST_SOVIET_BALTIC": ["ASIA", "EASTERN_EUROPE", "NORTHERN_EUROPE"],
        "ALL_REGION": [
            "AFRICA",
            "NORTH_AMERICA",
            "SOUTH_AMERICA",
            "ASIA",
            "NORTHERN_EUROPE",
            "EASTERN_EUROPE",
            "SOUTHERN_EUROPE",
            "WESTERN_EUROPE",
            "OCEANIA",
        ],
    }

    # Identify track columns: Ignore VEHIDCODE and sundry columns
    track_cols = [
        c
        for c in df_tracks.columns
        if c != "VEHIDCODE"
        and c not in ["CHECK_ANY_TT", "IS_STANDARD", "IS_NARROW", "IS_BROAD"]
    ]

    markdown = "# Vehicle Summary\n\n"

    for cat in sorted(df["COST_CAT"].unique()):
        markdown += f"## {cat}\n\n"
        markdown += "| Graphics | Name | Intro | Speed kmh / mph | Power hp/kW | Role | Cap | Track Types | Regions | Concept? |\n"
        markdown += "| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :--- | :--- | :--- |\n"

        cat_df = df[df["COST_CAT"] == cat].sort_values(["INTRODUCTION_YEAR", "ENGLISH"])
        for _, row in cat_df.iterrows():
            if is_true(row["EXCLUDE"]):
                continue

            v_id = str(row["NAME"]).strip().lower()
            save_to = str(row["SAVE_TO"]).replace("\\", "/")
            base_fn = str(row["FILENAMES_EXPECTED"])

            pnml_p = os.path.normpath(
                os.path.join(project_root, save_to, f"{base_fn}_graphics.pnml")
            )
            gfx_path = save_to.replace("src/", "gfx/").replace("src\\", "gfx/")
            png_p = os.path.normpath(
                os.path.join(project_root, gfx_path, f"{base_fn}.png")
            )

            img_rel_path = process_and_save_image(v_id, pnml_p, png_p, templates)
            img_tag = f"![{row['ENGLISH']}]({img_rel_path})" if img_rel_path else " "

            # Track Type extraction & cleaning
            active_tracks = []
            for tc in track_cols:
                if row.get(tc) == True or str(row.get(tc)).upper() == "TRUE":
                    cleaned_name = tc.replace("TRACK_TYPE_", "").replace(
                        "_GAUGE_RAILTYPE", ""
                    )
                    active_tracks.append(cleaned_name)
            track_str = ", ".join(active_tracks)

            # Capacity logic
            cap = int(row["HEAD_CAPACITY"]) if pd.notnull(row["HEAD_CAPACITY"]) else 0
            if cat == "METRO" or int(row.get("DUAL_HEADED", 0)) == 1:
                cap *= 2

            regions = []
            for key, value in region_map.items():
                if str(row.get(key)).upper() == "TRUE":
                    # Normalize: if it's a single string, wrap it in a list; otherwise, use it as is
                    mapped_regions = [value] if isinstance(value, str) else value

                    # Format and append each sub-region
                    for r in mapped_regions:
                        formatted_region = r.replace("_", " ").title()
                        if (
                            formatted_region not in regions
                        ):  # Prevent duplicates if multiple keys are True
                            regions.append(formatted_region)

            speed_kmh = int(row["SPEED"]) if pd.notnull(row["SPEED"]) else 0
            speed_mph = int(speed_kmh * 0.621371)

            power_hp = int(row["POWER"]) if pd.notnull(row["POWER"]) else 0
            power_kw = int(power_hp * 0.7456)

            is_concept = row["IS_CONCEPT"] == "IS_CONCEPT"

            markdown += f"| {img_tag} | {row['ENGLISH']} | {row['INTRODUCTION_YEAR']} | {speed_kmh} / {speed_mph} | {power_hp} / {power_kw} | {row['ROLE']} | {cap} | {track_str} | {', '.join(regions)} | {"Yes" if is_concept else "No"} |\n"
        markdown += "\n"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Summary generated at: {output_path}")


if __name__ == "__main__":
    generate_markdown()
