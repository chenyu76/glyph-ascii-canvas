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


def generate_ascii_art_auto_args(
    image_path,
    width,
    threshold=None,
    font_path=None,
    ascii_chars="".join(chr(i) for i in range(32, 127)),
    char_ratio=2,
):
    import concurrent.futures

    img = Image.open(image_path).convert("L")
    if threshold is not None:
        img = img.point(lambda p: 255 if p > threshold else 0)

    block_size = 8
    img = resize_image_by_width(img, max_width=width*block_size)

    char_scale_list = [1.0, 1.2, 1.6, 2.0, 2.4]
    linewidths = [0, 1, 2]
    shift_xs = [-2, 0, 2, 4]
    shift_ys = [int(char_ratio * x) for x in shift_xs]

    fonts = [load_font(font_path, int(block_size * char_scale))
             for char_scale in char_scale_list]

    step_x = block_size
    step_y = int(block_size * char_ratio)

    linewidth_templates_datas = [
        [
            generate_chars_template_stack(
                font, ascii_chars, step_x, step_y, linewidth
            ) for font in fonts
        ] for linewidth in linewidths
    ]

    futures = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        for shift_x in shift_xs:
            for shift_y in shift_ys:
                for templates_datas in linewidth_templates_datas:
                    for templates_data in templates_datas:
                        future = executor.submit(
                            image2ascii,  # function
                            img,          # follows by args...
                            templates_data,
                            ascii_chars,
                            step_x, step_y,
                            shift_x, shift_y
                        )
                        futures.append(future)
        mse_ascii_art = [f.result() for f in futures]

    best_result = min(mse_ascii_art, key=lambda x: x[0])
    _, best_ascii_art = best_result
    return best_ascii_art


# Main function to generate ASCII art
def generate_ascii_art(
    image_path,
    width,
    threshold=None,
    font_path=None,
    ascii_chars="".join(chr(i) for i in range(32, 127)),
    linewidth=0,
    char_scale=1.0,
    char_ratio=2,
    shift_x=0,
    shift_y=0,
):
    img = Image.open(image_path).convert("L")
    if threshold is not None:
        img = img.point(lambda p: 255 if p > threshold else 0)

    block_size = img.width // width

    font_size = int(block_size * char_scale)
    font = load_font(font_path, font_size)

    step_x = block_size
    step_y = int(block_size * char_ratio)

    templates_data = generate_chars_template_stack(
        font, ascii_chars, step_x, step_y, linewidth
    )

    _, ascii_art = image2ascii(
        img,
        templates_data,
        ascii_chars,
        step_x, step_y,
        shift_x, shift_y,
    )
    return ascii_art


def resize_image_by_width(img: Image.Image, max_width: int) -> Image.Image:
    # resize img if its width exceeds max_width
    original_width, original_height = img.size

    if original_width > max_width:
        ratio = max_width / original_width
        new_height = int(original_height * ratio)
        new_size = (max_width, new_height)
        resized_img = img.resize(new_size, Image.Resampling.LANCZOS)
        return resized_img
    else:
        return img


# Convert image to ASCII art using sliding window and template matching
# returns (total_score, ascii_art_lines)
def image2ascii(
    img: Image.Image,
    templates_data: (np.ndarray, int, int),
    ascii_chars: str,
    step_x: int,
    step_y: int,
    shift_x: int = 0,
    shift_y: int = 0,
):
    (templates_stack, win_w, win_h) = templates_data

    # Prepare image data
    img_w, img_h = img.size
    img_arr = np.array(img, dtype=np.float32)

    # Calculate grid dimensions
    n_cols = (img_w + step_x - 1) // step_x
    n_rows = (img_h + step_y - 1) // step_y

    target_h = n_rows * step_y
    target_w = n_cols * step_x

    # Create canvas (background set to white 255)
    canvas_h = target_h + win_h
    canvas_w = target_w + win_w
    canvas = np.full((canvas_h, canvas_w), 255, dtype=np.float32)

    # Calculate paste position (including shift offset)
    pad_top = win_h // 2 - step_y // 2
    pad_left = win_w // 2 - step_x // 2

    # Theoretical starting coordinates of the image on the canvas
    pos_y = pad_top + shift_y
    pos_x = pad_left + shift_x

    # Calculate intersection area between
    # canvas (Destination) and image (Source)
    # Valid paste area on canvas:
    # cannot be less than 0, cannot exceed canvas size
    dst_y_start = max(0, pos_y)
    dst_x_start = max(0, pos_x)
    dst_y_end = min(canvas_h, pos_y + img_h)
    dst_x_end = min(canvas_w, pos_x + img_w)

    # Corresponding slice area on the image
    src_y_start = dst_y_start - pos_y
    src_x_start = dst_x_start - pos_x
    src_y_end = src_y_start + (dst_y_end - dst_y_start)
    src_x_end = src_x_start + (dst_x_end - dst_x_start)

    # Perform paste (only when there is an overlapping area)
    if dst_y_end > dst_y_start and dst_x_end > dst_x_start:
        canvas[dst_y_start:dst_y_end, dst_x_start:dst_x_end] = img_arr[
            src_y_start:src_y_end, src_x_start:src_x_end
        ]

    # Sliding Window View (Extract sliding windows)
    shape = (n_rows, n_cols, win_h, win_w)
    strides = (
        step_y * canvas.strides[0],
        step_x * canvas.strides[1],
        canvas.strides[0],
        canvas.strides[1]
    )

    windows = as_strided(canvas, shape=shape, strides=strides)

    # windows_flat: (n_rows, n_cols, win_h*win_w)
    windows_flat = windows.reshape(n_rows, n_cols, -1)
    # templates_flat: (n_chars, win_h*win_w)
    templates_flat = templates_stack.reshape(len(ascii_chars), -1)

    # Calculate MSE and select the best character
    result_indices = np.zeros((n_rows, n_cols), dtype=int)
    best_score = np.full((n_rows, n_cols), float('inf'))

    # Iterate through each character template for matching
    for i, tmpl in enumerate(templates_flat):
        # NOTE: here all windows will be compared with the current template
        # Calculate squared difference using broadcasting
        diff = windows_flat - tmpl
        mse = np.mean(diff ** 2, axis=2)

        # Update with better matching results
        mask = mse < best_score
        best_score[mask] = mse[mask]
        result_indices[mask] = i

    total_score = np.sum(best_score)

    # 8. Assemble result strings
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
    parser.add_argument(
        "-x", "--shift-x", type=int, default=0,
        help="Shift image position in X direction"
    )
    parser.add_argument(
        "-y", "--shift-y", type=int, default=0,
        help="Shift image position in Y direction"
    )
    parser.add_argument(
        "-a", "--auto", action='store_true',
        help="Try automatic parameter tuning for better quality"
    )

    args = parser.parse_args()

    if args.auto:
        art = generate_ascii_art_auto_args(
            args.image,
            args.width,
            threshold=args.threshold,
            font_path=args.font,
            ascii_chars=args.chars,
            char_ratio=args.char_ratio,
        )
    else:
        art = generate_ascii_art(
            args.image,
            args.width,
            threshold=args.threshold,
            font_path=args.font,
            ascii_chars=args.chars,
            linewidth=args.linewidth,
            char_scale=args.char_scale,
            char_ratio=args.char_ratio,
            shift_x=args.shift_x,
            shift_y=args.shift_y,
        )
    for line in art:
        print(line)
