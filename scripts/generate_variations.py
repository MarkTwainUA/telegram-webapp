import argparse
import os
import random
from typing import Tuple

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def clamp(value: int) -> int:
    return max(0, min(255, value))


def apply_color_tint(image: Image.Image, color: Tuple[int, int, int], intensity: float) -> Image.Image:
    base = image.convert("RGB") if image.mode != "RGB" else image
    tint_layer = Image.new("RGB", base.size, color)
    return Image.blend(base, tint_layer, alpha=max(0.0, min(1.0, intensity)))


def add_vignette(image: Image.Image, radius_scale: float = 1.2, strength: float = 0.5) -> Image.Image:
    base = image.convert("RGB") if image.mode != "RGB" else image
    width, height = base.size
    inner_w = int(width / radius_scale)
    inner_h = int(height / radius_scale)
    inner = Image.new("L", (inner_w, inner_h), color=255)
    inner = inner.resize((int(width * 0.9), int(height * 0.9)), Image.BILINEAR)
    mask = Image.new("L", (width, height), 0)
    mask.paste(inner, ((width - inner.width) // 2, (height - inner.height) // 2))
    mask = mask.filter(ImageFilter.GaussianBlur(radius=min(width, height) // 10))

    darkened = ImageEnhance.Brightness(base).enhance(1.0 - strength)
    return Image.composite(base, darkened, ImageOps.invert(mask))


def add_noise(image: Image.Image, amount: int = 12) -> Image.Image:
    base = image.convert("RGB") if image.mode != "RGB" else image
    pixels = base.load()
    width, height = base.size
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            dr = random.randint(-amount, amount)
            dg = random.randint(-amount, amount)
            db = random.randint(-amount, amount)
            pixels[x, y] = (clamp(r + dr), clamp(g + dg), clamp(b + db))
    return base


def generate_variations(input_path: str, output_dir: str) -> None:
    ensure_dir(output_dir)
    img = Image.open(input_path)

    # 1) Contrast + Sharpness boost
    v1 = ImageEnhance.Contrast(img).enhance(1.3)
    v1 = ImageEnhance.Sharpness(v1).enhance(1.2)
    v1.save(os.path.join(output_dir, "variation_1_contrast_sharp.jpg"), quality=92)

    # 2) Warm color tint
    v2 = apply_color_tint(img, color=(255, 180, 120), intensity=0.20)
    v2 = ImageEnhance.Color(v2).enhance(1.05)
    v2.save(os.path.join(output_dir, "variation_2_warm_tint.jpg"), quality=92)

    # 3) Cool color tint + slight blur
    v3 = apply_color_tint(img, color=(140, 180, 255), intensity=0.18)
    v3 = v3.filter(ImageFilter.GaussianBlur(radius=0.8))
    v3.save(os.path.join(output_dir, "variation_3_cool_soft.jpg"), quality=92)

    # 4) Vignette + slight desaturation
    v4 = ImageEnhance.Color(img).enhance(0.85)
    v4 = add_vignette(v4, radius_scale=1.25, strength=0.35)
    v4.save(os.path.join(output_dir, "variation_4_vignette_matte.jpg"), quality=92)

    # 5) Film grain noise + faded contrast
    v5 = ImageEnhance.Contrast(img).enhance(0.92)
    v5 = add_noise(v5, amount=10)
    v5.save(os.path.join(output_dir, "variation_5_film_grain.jpg"), quality=92)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate 5 variations of an image using Pillow")
    parser.add_argument("input", help="Path to source image (jpg/png/webp)")
    parser.add_argument("--out", default="output", help="Directory to write variations")
    args = parser.parse_args()

    generate_variations(args.input, args.out)
    print(f"Saved variations in: {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
