import os
import sys
import argparse
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from numpy.lib.stride_tricks import as_strided


def load_font(font_path, size):
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

    if (font_path is not None):
        try:
            font = ImageFont.truetype(font_path, size)
        except Exception as e:
            if not os.path.exists(font_path):
                print("Font path does not exist.")
            print(f"Failed to load font from {font_path}. {e}")
            print("trying default fonts...")

    if font is None:
        for f in default_fonts:
            try:
                font = ImageFont.truetype(f, size)
                break
            except Exception:
                continue

    if font is None:
        print("Falling back to default PIL font...")
        try:
            font = ImageFont.load_default(size)
        except Exception as e:
            print(f"Failed to load any fonts. {e}")
            sys.exit(1)

    return font


def generate_chars_template_stack(
    font, ascii_chars, step_x, step_y, linewidth
):
    char_sizes = []
    for c in ascii_chars:
        bbox = font.getbbox(c)  # left, top, right, bottom
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        char_sizes.append((w, h))

    # choose max size
    max_w = max(s[0] for s in char_sizes) if char_sizes else step_x
    max_h = max(s[1] for s in char_sizes) if char_sizes else step_y

    # each character window size
    # make sure window size is even
    win_w = max_w + (max_w % 2)
    win_h = max_h + (max_h % 2)

    templates = []
    for c in ascii_chars:
        img_t = Image.new("L", (win_w, win_h), 255)
        draw = ImageDraw.Draw(img_t)

        bbox = draw.textbbox((0, 0), c, font=font)
        cw = bbox[2] - bbox[0]
        ch = bbox[3] - bbox[1]

        # draw text centered
        draw.text(((win_w - cw) / 2, (win_h - ch) / 2), c,
                  fill=0, font=font, stroke_width=linewidth)
        templates.append(np.array(img_t))

    # size (N_chars, win_h, win_w)
    templates_stack = np.array(templates, dtype=np.float32)

    return templates_stack, win_w, win_h


# Main function to generate ASCII art
def generate_ascii_art(
    image_path,
    width,
    threshold=None,
    font_path=None,
    ascii_chars="".join(chr(i) for i in range(32, 127)),
    linewidth=0,
    char_scale=1.0,
    char_ratio=2
):
    img = Image.open(image_path).convert("L")
    if threshold is not None:
        img = img.point(lambda p: 255 if p > threshold else 0)

    block_size = img.width // width

    font_size = int(block_size * char_scale)
    font = load_font(font_path, font_size)

    step_x = block_size
    step_y = int(block_size * char_ratio)

    templates_stack, win_w, win_h = generate_chars_template_stack(
        font, ascii_chars, step_x, step_y, linewidth
    )

    _, ascii_art = image2ascii(
        img,
        templates_stack,
        ascii_chars,
        step_x,
        step_y,
        win_w,
        win_h,
    )
    return ascii_art


# Convert image to ASCII art using sliding window and template matching
def image2ascii(
    img,
    templates_stack,
    ascii_chars,
    step_x,
    step_y,
    win_w,
    win_h,
):

    # padding
    img_w, img_h = img.size
    img_arr = np.array(img, dtype=np.float32)

    n_cols = (img_w + step_x - 1) // step_x
    n_rows = (img_h + step_y - 1) // step_y

    target_h = n_rows * step_y
    target_w = n_cols * step_x

    pad_top = win_h // 2 - step_y // 2
    pad_left = win_w // 2 - step_x // 2
    paste_y = pad_top if pad_top > 0 else 0
    paste_x = pad_left if pad_left > 0 else 0

    canvas_h = target_h + win_h
    canvas_w = target_w + win_w

    canvas = np.full((canvas_h, canvas_w), 255, dtype=np.float32)

    # protect against overflow
    h_end = min(paste_y + img_h, canvas_h)
    w_end = min(paste_x + img_w, canvas_w)
    canvas[paste_y:h_end, paste_x:w_end] = img_arr[:h_end-paste_y, :w_end-paste_x]

    # Sliding Window View
    # Exstract sliding windows from canvas
    # (n_rows, n_cols) of size of (win_h, win_w)
    shape = (n_rows, n_cols, win_h, win_w)
    strides = (
        step_y * canvas.strides[0],
        step_x * canvas.strides[1],
        canvas.strides[0],
        canvas.strides[1]
    )

    # windows size: (n_rows, n_cols, win_h, win_w)
    windows = as_strided(canvas, shape=shape, strides=strides)
    # windows_flat: (n_rows, n_cols, win_h*win_w)
    windows_flat = windows.reshape(n_rows, n_cols, -1)
    # templates_flat: (n_chars, win_h*win_w)
    templates_flat = templates_stack.reshape(len(ascii_chars), -1)

    result_indices = np.zeros((n_rows, n_cols), dtype=int)
    best_score = np.full((n_rows, n_cols), float('inf'))
    for i, tmpl in enumerate(templates_flat):
        # tmpl: (pixels,)
        # windows_flat: (rows, cols, pixels)
        # calculate MSE
        diff = windows_flat - tmpl
        mse = np.mean(diff ** 2, axis=2)

        mask = mse < best_score
        best_score[mask] = mse[mask]
        result_indices[mask] = i

    total_score = np.sum(best_score)

    ascii_art = []
    for r in range(n_rows):
        row_str = "".join(ascii_chars[idx] for idx in result_indices[r])
        ascii_art.append(row_str)

    return (total_score, ascii_art)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate ASCII art from images")
    parser.add_argument("image", help="Path to input image")
    parser.add_argument(
        "-w", "--width", type=int, default=80,
        help="Target output character number in width"
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
    parser.add_argument(
        "-l", "--linewidth", type=int, default=0, help="Font stroke width"
    )
    parser.add_argument(
        "-r", "--char-ratio", type=float, default=2.0,
        help="Character height to width ratio"
    )
    parser.add_argument(
        "-s", "--char-scale", type=float, default=1.0,
        help="Character scaling factor"
    )

    args = parser.parse_args()

    art = generate_ascii_art(
        args.image,
        args.width,
        threshold=args.threshold,
        font_path=args.font,
        ascii_chars=args.chars,
        linewidth=args.linewidth,
        char_scale=args.char_scale,
        char_ratio=args.char_ratio
    )
    for line in art:
        print(line)
