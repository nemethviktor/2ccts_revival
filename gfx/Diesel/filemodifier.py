import os
from PIL import Image, ImageDraw, ImageFont


def add_filename_overlay(
    folder_path: str, font_path: str, font_size: int = 8
) -> None:
    """Iterates through all PNG files in a folder, overlays a white box,

    and writes the filename (without extension) on top of the box.

    :param folder_path: Path to the directory containing PNG files.
    :param font_path: Path to the 'Museo 700' font file.
    :param font_size: Font size for the text (default is 8).
    """
    # Define constants
    text_color: str = "#0000ff"  # Blue
    box_color: str = "#ffffff"  # White

    # Define the exact coordinates for the top-left of the white box
    # Adjust these to change the "specific location" on the image
    target_x: int = 30
    target_y: int = 113

    # Padding to ensure the white box completely overwrites the background
    box_padding_x: int = 40
    box_padding_y: int = 10  # Adjust as needed

    # Load the font
    try:
        font: ImageFont.FreeTypeFont = ImageFont.truetype(
            font=font_path, size=font_size
        )
    except IOError:
        print(f"Error: Could not load font at {font_path}")
        return

    # Process files
    for filename in os.listdir(path=folder_path):
        if filename.lower().endswith(".png"):
            file_path: str = os.path.join(folder_path, filename)

            # Get filename without extension
            base_name: str = os.path.splitext(p=filename)[0]

            try:
                with Image.open(fp=file_path) as img:
                    # Convert to RGBA to ensure compatibility with drawing layers
                    img = img.convert(mode="RGBA")
                    draw: ImageDraw.ImageDraw = ImageDraw.Draw(im=img)

                    # Calculate text dimensions using bounding box
                    bbox: tuple[int, int, int, int] = draw.textbbox(
                        xy=(0, 0), text=base_name, font=font
                    )
                    text_width: int = bbox[2] - bbox[0]
                    text_height: int = bbox[3] - bbox[1]

                    # Define the dimensions of the white background box
                    box_x1: int = target_x
                    box_y1: int = target_y
                    box_x2: int = target_x + text_width + (box_padding_x * 2)
                    box_y2: int = target_y + text_height + (box_padding_y * 2)

                    # Draw the white background box
                    draw.rectangle(
                        xy=[box_x1, box_y1, box_x2, box_y2], fill=box_color
                    )

                    # Draw the blue text offset by the respective padding values
                    text_x: int = target_x + box_padding_x
                    text_y: int = target_y + box_padding_y
                    draw.text(
                        xy=(text_x, text_y),
                        text=base_name,
                        fill=text_color,
                        font=font,
                        fontmode="1",
                    )

                    # Save the image, overwriting the original file
                    img.save(fp=file_path)
                    print(f"Processed: {filename}")

            except Exception as e:
                print(f"Failed to process {filename}: {e}")


if __name__ == "__main__":
    # Configure your paths here
    target_folder: str = "."
    font_location: str = "E:\\Google Drive\\Sajat\\My_Actual_Documents\\Fonts\\Museo700-Regular.otf"  # Update with actual extension/path

    add_filename_overlay(
        folder_path=target_folder, font_path=font_location, font_size=8
    )