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
    """Renders SVG by stretching its internal content to the 18x12 canvas."""
    with open(svg_path, 'rb') as f:
        svg_data = f.read()

    stream = skia.MemoryStream(svg_data)
    dom = skia.SVGDOM.MakeFromStream(stream)

    surface = skia.Surface(width, height)

    with surface as canvas:
        canvas.clear(skia.ColorTRANSPARENT)
        if dom:
            # 1. Get whatever size the SVG thinks it is
            c_size = dom.containerSize()
            svg_w, svg_h = c_size.width(), c_size.height()

            # 2. If it has no size, try to look at the viewBox
            # (Skia-python doesn't always expose getRoot, so we check containerSize first)
            if svg_w <= 0 or svg_h <= 0:
                # Fallback: Assume it's a unitless viewBox and force it to our target
                dom.setContainerSize(skia.Size(width, height))
                dom.render(canvas)
            else:
                # 3. If it HAS a size (the 'normal' flags), we MUST scale the canvas
                # to map that size down to 18x12, otherwise it renders off-screen.
                canvas.scale(width / svg_w, height / svg_h)
                dom.render(canvas)
        else:
            print(f"FAILED TO LOAD SVG: {svg_path}")

    image = surface.makeImageSnapshot()
    if not image:
        return Image.new("RGBA", (width, height), (0, 0, 0, 0))

    # Skia (BGRA) -> Pillow (RGBA)
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

            # 2. Layer Gloss (Only on the flag pixels)
            if gloss_img:
                # Create a blank transparent canvas the same size as the flag
                gloss_layer = Image.new("RGBA", (18, 12), (0, 0, 0, 0))

                # Use the flag's alpha channel as a mask to apply gloss ONLY to the flag
                # This prevents gloss from bleeding into the 'Transparent Blue' area
                flag_mask = flag_rgba.split()[3]
                gloss_layer.paste(gloss_img, (0, 0), mask=flag_mask)

                # Composite the masked gloss over the flag
                flag_rgba = Image.alpha_composite(flag_rgba, gloss_layer)

            # 3. Flatten onto Index 0 Blue
            # Now, the pixels at (0,0) are guaranteed to be exactly bg_color
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
