import os
import skia
from PIL import Image


def parse_gpl(gpl_path):
    colors = []
    with open(gpl_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].isdigit():
                colors.extend([int(parts[0]), int(parts[1]), int(parts[2])])
    while len(colors) < 768:
        colors.extend([0, 0, 0])
    return colors[:768]


def svg_to_pil_rgba(svg_path, width, height):
    """Renders SVG using a hard-coded destination rect to force visibility."""
    with open(svg_path, 'rb') as f:
        svg_data = f.read()

    stream = skia.MemoryStream(svg_data)
    dom = skia.SVGDOM.MakeFromStream(stream)

    # Use N32 (standard RGBA/BGRA) with Premultiplied Alpha
    surface = skia.Surface(width, height)

    with surface as canvas:
        canvas.clear(skia.ColorTRANSPARENT)
        if dom:
            # Force the SVG to draw into the exact 18x12 box
            # This bypasses scaling math that might be failing
            dom.setContainerSize(skia.Size(width, height))
            dom.render(canvas)
        else:
            print(f"FAILED TO LOAD SVG: {svg_path}")

    image = surface.makeImageSnapshot()
    if not image:
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Convert Skia surface to a PIL Image
    # We use frombuffer with BGRA because that's Skia's default raster order
    return Image.frombuffer("RGBA", (width, height), image.toarray(), "raw", "BGRA", 0, 1)


def process_flags_final_attempt(svg_folder, output_folder, gloss_path, gpl_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    raw_palette = parse_gpl(gpl_path)
    # Get the "Transparent Blue" from Index 0
    bg_color = (raw_palette[0], raw_palette[1], raw_palette[2])

    palette_template = Image.new('P', (1, 1))
    palette_template.putpalette(raw_palette)

    # Prep Gloss
    gloss_img = None
    if os.path.exists(gloss_path):
        gloss_img = Image.open(gloss_path).convert(
            "RGBA").resize((18, 12), Image.Resampling.LANCZOS)
        r, g, b, a = gloss_img.split()
        gloss_img = Image.merge(
            "RGBA", (r, g, b, a.point(lambda i: int(i * 0.30))))

    for file in os.listdir(svg_folder):
        if file.lower().endswith(".svg"):
            svg_path = os.path.join(svg_folder, file)
            save_path = os.path.join(
                output_folder, os.path.splitext(file)[0] + ".png")

            # 1. Render SVG
            flag_rgba = svg_to_pil_rgba(svg_path, 18, 12)

            # --- DEBUG: Verify if the flag is actually rendered ---
            # If you still get blue files, uncomment the next line to see if the raw SVG is empty
            # flag_rgba.save("debug_raw_" + file + ".png")

            # 2. Layer Gloss
            if gloss_img:
                flag_rgba = Image.alpha_composite(flag_rgba, gloss_img)

            # 3. Flatten onto Index 0 Blue
            final_img = Image.new("RGB", (18, 12), bg_color)
            final_img.paste(flag_rgba, (0, 0), flag_rgba)

            # 4. Map to Palette & Lock Table
            indexed = final_img.quantize(palette=palette_template, dither=0)
            indexed.putpalette(raw_palette)

            # 5. Save with 256-color table forced
            indexed.save(save_path, format="PNG", optimize=False)
            print(f"Generated: {file}")


if __name__ == "__main__":
    process_flags_final_attempt(
        'flag_svg', 'flag', 'flag-overlay-1x-18x12.png', 'palette.gpl')
