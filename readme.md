# Glyph-ASCII-Canvas

This program generates ASCII art from images using a different contextual matching approach. Unlike simpler ASCII converters that map pixels directly to characters based on brightness, this algorithm considers the spatial relationships between adjacent blocks for more accurate representations. So it may generate a better result, especially when processing line drawing.

## Usage

```bash
python glyph-ascii-canvas.py [IMAGE_PATH] [OPTIONS]
```

### Options:
| Option              | Description                    | Default              |
| ------------------- | ------------------------------ | -------------------- |
| `-s`, `--size`      | Per-block size (pixels)        | 10                   |
| `-t`, `--threshold` | Binarization threshold (0-255) | None                 |
| `-f`, `--font`      | Path to custom font file       | System default       |
| `-c`, `--chars`     | Custom character set           | All ASCII characters |


## How It Works

The algorithm uses following approach to generate ASCII art:

1. **Character Template Generation**:
   - Creates templates for each ASCII character at the specified block size
   - Templates include the character rendered with the selected font
   - Stores templates as grayscale images (6n × 3n pixels)

2. **Image Processing**:
   - Converts input image to grayscale
   - Applies threshold-based binarization (if specified)
   - Pads image to make dimensions divisible by block size

3. **Contextual Block Matching**:
   - For each target block in the image:
     - Creates a "big block" (6n × 3n) containing the target block and its neighbors
     - Compares this big block against all character templates
     - Selects character with the smallest mean squared error (MSE)


## Requirements

- Python 3.6+
- Pillow (PIL Fork)
- NumPy
