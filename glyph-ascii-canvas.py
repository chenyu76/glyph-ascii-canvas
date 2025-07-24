import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def generate_ascii_art(
    image_path,
    block_size,
    threshold=None,
    font_path=None,
    ascii_chars="".join(chr(i) for i in range(32, 127)),
):
    # Load font
    default_fonts = [
        "arial.ttf",
        "cour.ttf",
        "courbd.ttf",
        "couri.ttf",
        "lucon.ttf",
        "consola.ttf",
        "DejaVuSansMono.ttf",
    ]
    font = None

    if font_path and os.path.exists(font_path):
        try:
            font = ImageFont.truetype(font_path, 2 * block_size)
        except:
            pass

    if font is None:
        for f in default_fonts:
            try:
                font = ImageFont.truetype(f, 2 * block_size)
                break
            except:
                continue

    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            print("Failed to load any fonts. Please specify a valid font path.")
            sys.exit(1)

    # Create ASCII character templates (6n x 3n)
    char_templates = {}
    for c in ascii_chars:
        template_img = Image.new("L", (3 * block_size, 6 * block_size), 255)
        char_img = Image.new("L", (3 * block_size, 6 * block_size), 255)
        char_draw = ImageDraw.Draw(char_img)

        try:
            char_draw.text((0, 0), c, fill=0, font=font)
        except:
            char_draw.text((0, 0), c, fill=0)

        # Crop character boundaries
        bbox = char_img.getbbox()
        if bbox:
            char_img = char_img.crop(bbox)

        template_img.paste(char_img, (0, 0))
        char_templates[c] = np.array(template_img)

    # Load and process image
    img = Image.open(image_path).convert("L")

    # Apply thresholding if specified
    if threshold is not None:
        img = img.point(lambda p: 255 if p > threshold else 0)

    width, height = img.size

    # Calculate new dimensions (multiples of block size)
    new_width = ((width + block_size - 1) // block_size) * block_size
    new_height = ((height + 2 * block_size - 1) // (2 * block_size)) * (2 * block_size)

    # Create new image and paste original
    new_img = Image.new("L", (new_width, new_height), 255)
    new_img.paste(img, (0, 0))
    img_array = np.array(new_img)

    # Generate ASCII art
    ascii_art = []
    grid_width = new_width // block_size
    grid_height = new_height // (2 * block_size)

    for j in range(grid_height):
        row = []
        for i in range(grid_width):
            # Create 6n x 3n block
            big_block = np.full((6 * block_size, 3 * block_size), 255, dtype=np.uint8)

            # Fill 3x3 grid
            for y_offset in range(-1, 2):
                for x_offset in range(-1, 2):
                    grid_y = j + y_offset
                    grid_x = i + x_offset

                    if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                        x_start = grid_x * block_size
                        y_start = grid_y * 2 * block_size
                        block = img_array[
                            y_start : y_start + 2 * block_size,
                            x_start : x_start + block_size,
                        ]

                        dest_x = (x_offset + 1) * block_size
                        dest_y = (y_offset + 1) * 2 * block_size
                        big_block[
                            dest_y : dest_y + 2 * block_size,
                            dest_x : dest_x + block_size,
                        ] = block

            # Find best matching character
            best_char = None
            best_score = float("inf")

            for char, template in char_templates.items():
                mse = np.mean((big_block.astype(float) - template.astype(float)) ** 2)
                if mse < best_score:
                    best_score = mse
                    best_char = char

            row.append(best_char or " ")
        ascii_art.append("".join(row))

    return ascii_art


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate ASCII art from images")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument(
        "-s", "--size", type=int, default=10, help="Block size (default: 10)"
    )
    parser.add_argument(
        "-t", "--threshold", type=int, help="Binarization threshold (0-255)"
    )
    parser.add_argument("-f", "--font", help="Path to custom font file")
    parser.add_argument(
        "-c",
        "--chars",
        default="".join(chr(i) for i in range(32, 127)),
        help="Custom ASCII character set",
    )

    args = parser.parse_args()

    try:
        art = generate_ascii_art(
            args.image,
            args.size,
            threshold=args.threshold,
            font_path=args.font,
            ascii_chars=args.chars,
        )
        for line in art:
            print(line)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
