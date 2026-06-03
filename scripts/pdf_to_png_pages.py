from __future__ import annotations

import sys
from pathlib import Path

import pypdfium2 as pdfium


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: pdf_to_png_pages.py input.pdf output_dir")

    pdf_path = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    pdf = pdfium.PdfDocument(str(pdf_path))
    scale = 150 / 72
    for index in range(len(pdf)):
        page = pdf[index]
        bitmap = page.render(scale=scale)
        image = bitmap.to_pil()
        image.save(out_dir / f"page-{index + 1}.png")
    print(f"rendered {len(pdf)} pages")


if __name__ == "__main__":
    main()
