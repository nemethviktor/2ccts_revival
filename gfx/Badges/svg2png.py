import os
import skia
import re
from PIL import Image, ImageChops

# Exclusion ranges: D9-E2 (217-226), E3-E7 (227-231), E8-EE (232-238), EF-F0 (239-240), F1-F4 (241-244)
# Combined Decimal Range: 217 to 244
EXCLUSION_START = 217
EXCLUSION_END = 244


def parse_gpl(gpl_path):
    """Extracts RGB values from a GIMP .gpl file and pads to 256 colors."""
    colors = []
    with open(gpl_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0].isdigit():
                colors.extend([int(parts[0]), int(parts[1]), int(parts[2])])
    while len(colors) < 768:
        colors.extend([0, 0, 0])
    return colors[:768]


def get_svg_viewbox(svg_path):
    """Extracts the true coordinate bounds from the SVG file."""
    try:
        with open(svg_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(4000)  # Only need the header
            # Find viewBox="x y w h"
            vb_match = re.search(
                r'viewBox=["\'](-?[\d.]+)[ ,]+(-?[\d.]+)[ ,]+([\d.]+)[ ,]+([\d.]+)["\']', content)
            if vb_match:
                return [float(x) for x in vb_match.groups()]
            # Fallback to width/height attributes
            w_match = re.search(r'width=["\']([\d.]+)["\']', content)
            h_match = re.search(r'height=["\']([\d.]+)["\']', content)
            if w_match and h_match:
                return [0.0, 0.0, float(w_match.group(1)), float(h_match.group(1))]
    except:
        pass
    return None


def svg_to_pil_rgba(svg_path, width, height):
    """Renders SVG by stretching its content to fill the exact target bounds."""
    with open(svg_path, 'rb') as f:
        svg_data = f.read()

    stream = skia.MemoryStream(svg_data)
    dom = skia.SVGDOM.MakeFromStream(stream)
    surface = skia.Surface(width, height)

    vb = get_svg_viewbox(svg_path)

    with surface as canvas:
        canvas.clear(skia.ColorTRANSPARENT)
        if dom:
            if vb:
                vx, vy, vw, vh = vb
                # Force DOM to internal content size
                dom.setContainerSize(skia.Size(vw, vh))
                # Map that content exactly to our 18x12 canvas (Forced Stretch)
                canvas.scale(width / vw, height / vh)
                canvas.translate(-vx, -vy)
                dom.render(canvas)
            else:
                # Last resort: Skia's internal guess
                dom.setContainerSize(skia.Size(width, height))
                dom.render(canvas)

    image = surface.makeImageSnapshot()
    pil_img = Image.frombuffer(
        "RGBA", (width, height), image.toarray(), "raw", "BGRA", 0, 1)

    # "Crunchy Alpha": Set alpha to 0 or 255. This prevents semi-transparent
    # 'halo' pixels from corrupting the Index 0 Blue background.
    r, g, b, a = pil_img.split()
    a = a.point(lambda p: 255 if p > 128 else 0)
    return Image.merge("RGBA", (r, g, b, a))


def process_flags_color_safe(svg_folder, output_folder, gloss_path, gpl_path):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    raw_palette = parse_gpl(gpl_path)
    bg_r, bg_g, bg_b = raw_palette[0], raw_palette[1], raw_palette[2]
    bg_color = (bg_r, bg_g, bg_b)

    # Prepare Quantization Template (Mask forbidden hex ranges)
    quant_palette = list(raw_palette)
    # Range: D9 to F4 (Decimal 217 to 244)
    for i in range(217, 245):
        quant_palette[i*3: i*3+3] = [bg_r, bg_g, bg_b]

    palette_template = Image.new('P', (1, 1))
    palette_template.putpalette(quant_palette)

    # 1. Prep Gloss - We use Luminance now
    gloss_img = None
    if os.path.exists(gloss_path):
        # We convert gloss to grayscale to ensure it doesn't "re-color" the flag
        gloss_img = Image.open(gloss_path).convert(
            "L").resize((18, 12), Image.Resampling.LANCZOS)

    for file in os.listdir(svg_folder):
        if not file.lower().endswith(".svg"):
            continue

        svg_path = os.path.join(svg_folder, file)
        save_path = os.path.join(
            output_folder, os.path.splitext(file)[0] + ".png")

        # Render SVG
        flag_rgba = svg_to_pil_rgba(svg_path, 18, 12)

        # 2. APPLY GLOSS WITHOUT MUDDYING
        if gloss_img:
            # Split flag into RGB and Alpha
            r, g, b, a = flag_rgba.split()
            rgb_flag = Image.merge("RGB", (r, g, b))

            # Grayscale highlights from the gloss
            highlights = Image.eval(gloss_img, lambda x: x if x > 128 else 0)
            highlight_rgb = Image.merge(
                "RGB", (highlights, highlights, highlights))

            glossed_rgb = ImageChops.screen(rgb_flag, highlight_rgb)
            flag_rgb = Image.blend(rgb_flag, glossed_rgb, 0.35)

            # Re-merge with original alpha
            flag_rgba = Image.merge("RGBA", (
                flag_rgb.split()[0],
                flag_rgb.split()[1],
                flag_rgb.split()[2],
                a
            ))

        # 3. Flatten onto 'Magic Blue'
        final_img = Image.new("RGB", (18, 12), bg_color)
        final_img.paste(flag_rgba, (0, 0), flag_rgba)

        # 4. Quantize
        # method=0 (Median Cut) can sometimes be better for keeping 'Pure' colors
        # than the default if you're seeing brown.
        indexed = final_img.quantize(palette=palette_template, dither=0)

        indexed.putpalette(raw_palette)
        indexed.save(save_path, format="PNG", optimize=False)
        print(f"Color-Safe Export: {file}")


if __name__ == "__main__":
    process_flags_color_safe('flag_svg', 'flag',
                             'flag-overlay-1x-18x12.png', 'palette.gpl')
