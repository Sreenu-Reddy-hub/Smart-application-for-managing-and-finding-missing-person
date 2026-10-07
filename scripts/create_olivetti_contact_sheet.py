"""Create one labelled contact sheet from the exported Olivetti PNG images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IMAGE_ROOT = PROJECT_ROOT / "data" / "benchmark" / "olivetti_images"
OUTPUT_PATH = IMAGE_ROOT / "olivetti_400_images_contact_sheet.png"
CELL_SIZE = 72
COLUMNS = 20


def main() -> None:
    files = sorted(IMAGE_ROOT.glob("person_*/*.png"))
    if len(files) != 400:
        raise RuntimeError(f"Expected 400 PNG images, found {len(files)}. Run the PNG conversion first.")

    rows = (len(files) + COLUMNS - 1) // COLUMNS
    sheet = Image.new("RGB", (COLUMNS * CELL_SIZE, rows * CELL_SIZE), "white")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(files):
        image = Image.open(path).convert("L").resize((64, 64))
        x, y = (index % COLUMNS) * CELL_SIZE, (index // COLUMNS) * CELL_SIZE
        sheet.paste(image.convert("RGB"), (x + 4, y + 4))
        draw.text((x + 4, y + 67), f"{path.parent.name[-2:]}-{path.stem[-2:]}", fill="black")

    sheet.save(OUTPUT_PATH)
    print(f"Created contact sheet: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
