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
excel_path = os.path.join(script_dir, 'vehicle_report.xlsx')
templates_pnml = os.path.join(project_root, 'src', 'templates.pnml')
output_path = os.path.normpath(os.path.join(
    project_root, 'docs', 'vehicle_summary.md'))


# A tiny transparent pixel to use when real graphics are missing
EMPTY_PNG_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


def parse_templates(file_path):
    """Parses templates.pnml to create a map of template names to (width, height)."""
    templates = {}
    if not os.path.exists(file_path):
        return templates
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract template definitions
    matches = re.finditer(
        r'template\s+(template_purchase\w*)\s*\([^)]*\)\s*\{([\s\S]*?)\}', content)
    for match in matches:
        name = match.group(1)
        body = match.group(2)
        # Find coordinate lines [x, y, w, h, ...]
        # We skip lines that look like Empty.png (1x1)
        coords = re.findall(
            r'\[\s*(?:x\+?)?(\d+)?\s*,\s*(?:y\+?)?(\d+)?\s*,\s*(\d+)\s*,\s*(\d+)', body)
        for c in coords:
            w, h = int(c[2]), int(c[3])
            if w > 1:
                templates[name] = (w, h)
                break
    return templates


def get_purchase_image_base64(pnml_path, excel_png_path, templates):
    """Extracts the purchase sprite using the specific template name found in the PNML."""
    if not os.path.exists(pnml_path):
        return EMPTY_PNG_B64

    try:
        with open(pnml_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Extract the template name and coordinates from the PNML
        # Logic: spriteset(ID, "png_path") { template_name(X, Y) }
        pattern = r'spriteset\s*\(\s*[^,]+_purchase\s*,\s*"([^"]+)"\s*\)\s*\{\s*(\w+)\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)\s*\}'
        match = re.search(pattern, content)
        if not match:
            return EMPTY_PNG_B64

        pnml_png_rel_path = match.group(1)  # The path inside the PNML
        tpl_name = match.group(2)
        x_start = int(match.group(3))
        y_start = int(match.group(4))

        # 2. Lookup dimensions (Handles 43x12 for wagons vs 53x12 for engines)
        if tpl_name not in templates:
            return EMPTY_PNG_B64
        w, h = templates[tpl_name]

        # 3. Resolve the PNG path
        # Some coaches use a separate _purchase.png. If the PNML points to one, try to find it.
        if "_purchase.png" in pnml_png_rel_path:
            # Construct path based on the folder of the pnml file
            pnml_dir = os.path.dirname(pnml_path)
            png_filename = os.path.basename(pnml_png_rel_path)
            png_path = os.path.join(pnml_dir, png_filename).replace(
                'src/', 'gfx/').replace('src\\', 'gfx/')
        else:
            png_path = excel_png_path

        if not os.path.exists(png_path):
            return EMPTY_PNG_B64

        # 4. Process Image
        img = Image.open(png_path).convert("RGBA")
        crop = img.crop((x_start, y_start, x_start + w, y_start + h))

        # Blue (0,0,255) to Alpha 0
        pixdata = crop.load()
        for y in range(crop.size[1]):
            for x in range(crop.size[0]):
                if pixdata[x, y][:3] == (0, 0, 255):
                    pixdata[x, y] = (0, 0, 0, 0)

        buffered = BytesIO()
        crop.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except:
        return EMPTY_PNG_B64


def generate_markdown():
    print("--- Starting Vehicle Summary Generation ---")

    sheets = pd.read_excel(excel_path, sheet_name=None)
    df_control = sheets['control']
    df_props = sheets['properties']
    df_roster = sheets['roster']

    df = df_control.merge(df_props, on='VEHIDCODE', how='inner')
    df = df.merge(df_roster, on='VEHIDCODE',
                  how='inner', suffixes=('', '_roster'))

    templates = parse_templates(templates_pnml)
    region_cols = ['AFRICA', 'ASIA', 'SOUTHERN_EUROPE', 'EASTERN_EUROPE',
                   'WESTERN_EUROPE', 'NORTHERN_EUROPE', 'NORTH_AMERICA', 'SOUTH_AMERICA', 'OCEANIA']

    markdown = "# Vehicle Summary\n\n"

    for cat in sorted(df['COST_CAT'].unique()):
        markdown += f"## {cat}\n\n"
        markdown += "| Graphics | Name | Intro | Speed | Power | Role | Cap | Regions |\n"
        markdown += "| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :--- |\n"

        cat_df = df[df['COST_CAT'] == cat].sort_values('INTRODUCTION_YEAR')
        for _, row in cat_df.iterrows():
            save_to = str(row['SAVE_TO']).replace('\\', '/')
            base_fn = str(row['FILENAMES_EXPECTED'])

            pnml_p = os.path.join(
                project_root, save_to, f"{base_fn}_graphics.pnml")
            gfx_path = save_to.replace("src/", "gfx/").replace("src\\", "gfx/")
            png_p = os.path.join(project_root, gfx_path, f"{base_fn}.png")

            b64 = get_purchase_image_base64(pnml_p, png_p, templates)
            img_tag = f"![{row['ENGLISH']}](data:image/png;base64,{b64})"

            # Capacity logic
            cap = int(row['HEAD_CAPACITY']) if pd.notnull(
                row['HEAD_CAPACITY']) else 0
            if cat == 'METRO' or int(row.get('DUAL_HEADED', 0)) == 1:
                cap *= 2

            regions = [c.replace('_', ' ').title() for c in region_cols if str(
                row.get(c)).upper() == 'TRUE']

            markdown += f"| {img_tag} | {row['ENGLISH']} | {row['INTRODUCTION_YEAR']} | {row['SPEED']} | {row['POWER']} | {row['ROLE']} | {cap} | {', '.join(regions)} |\n"
        markdown += "\n"

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)


if __name__ == "__main__":
    generate_markdown()
    print("--- Vehicle Summary Generation Complete ---")
