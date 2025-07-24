import os
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np


def generate_ascii_art(
    image_path, n, font_path=None, ascii_chars="".join(chr(i) for i in range(32, 127))
):
    # 加载字体
    fonts = [
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
            font = ImageFont.truetype(font_path, 2 * n)
        except:
            pass

    if font is None:
        for f in fonts:
            try:
                font = ImageFont.truetype(f, 2 * n)
                break
            except:
                continue

    if font is None:
        try:
            font = ImageFont.load_default()
        except:
            print("无法加载任何字体，请指定字体路径")
            sys.exit(1)

    # 生成ASCII字符模板 (6n x 3n)
    # ascii_chars = "[]|\\_-+=/()*^!?XO~`:;\"',.<> "
    char_templates = {}
    for c in ascii_chars:
        # 创建6n x 3n的模板图像
        template_img = Image.new("L", (3 * n, 6 * n), 255)

        # 创建单个字符图像
        char_img = Image.new("L", (3 * n, 6 * n), 255)
        char_draw = ImageDraw.Draw(char_img)
        try:
            char_draw.text((0, 0), c, fill=0, font=font)
        except:
            char_draw.text((0, 0), c, fill=0)

        # 裁剪字符边界
        bbox = char_img.getbbox()
        if bbox:
            char_img = char_img.crop(bbox)

        # 缩放到n x 2n
        # char_img = char_img.resize((n, 2 * n), Image.LANCZOS)

        # 粘贴到模板中的对应位置
        # x_pos = i * n
        # y_pos = j * 2 * n
        template_img.paste(char_img, (0, 0))

        char_templates[c] = np.array(template_img)

    # 加载并处理图像
    img = Image.open(image_path).convert("L")
    width, height = img.size

    # 计算新尺寸（n的倍数）
    new_width = ((width + n - 1) // n) * n
    new_height = ((height + 2 * n - 1) // (2 * n)) * (2 * n)

    # 创建新图像并粘贴原图
    new_img = Image.new("L", (new_width, new_height), 255)
    new_img.paste(img, (0, 0))
    img_array = np.array(new_img)

    # 生成ASCII艺术
    ascii_art = []
    # 计算网格尺寸
    grid_width = new_width // n
    grid_height = new_height // (2 * n)

    for j in range(grid_height):
        row = []
        for i in range(grid_width):
            # 创建6n x 3n的大块
            big_block = np.full((6 * n, 3 * n), 255, dtype=np.uint8)

            # 填充3x3网格
            for y_offset in range(-1, 2):
                for x_offset in range(-1, 2):
                    # 计算当前网格位置
                    grid_y = j + y_offset
                    grid_x = i + x_offset

                    # 检查边界
                    if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                        # 计算图像中的位置
                        x_start = grid_x * n
                        y_start = grid_y * 2 * n
                        block = img_array[
                            y_start : y_start + 2 * n, x_start : x_start + n
                        ]

                        # 在大块中的位置
                        dest_x = (x_offset + 1) * n
                        dest_y = (y_offset + 1) * 2 * n
                        big_block[dest_y : dest_y + 2 * n, dest_x : dest_x + n] = block

            # 寻找最佳匹配字符
            best_char = None
            best_score = float("inf")

            for char, template in char_templates.items():
                # 计算均方误差(MSE)
                mse = np.mean((big_block.astype(float) - template.astype(float)) ** 2)
                if mse < best_score:
                    best_score = mse
                    best_char = char

            row.append(best_char or " ")
        ascii_art.append("".join(row))

    return ascii_art


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(
            "Usage: python ascii_art.py <path/to/image> <character size> [path/to/font]"
        )
        sys.exit(1)

    image_path = sys.argv[1]
    n = int(sys.argv[2])
    font_path = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        art = generate_ascii_art(image_path, n, font_path)
        for line in art:
            print(line)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
