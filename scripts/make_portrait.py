"""Encode the supplied photograph as an animated character portrait.

Run from the repository root: python scripts/make_portrait.py
Only Pillow is required; no model download, background removal, or API key.
"""
from pathlib import Path
import html
import sys
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets/source.jpg"
DESTINATION = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "assets/portrait.svg"
COLS, ROWS = 180, 96
ART_SIZE = 800
CELL_W, CELL_H = ART_SIZE / COLS, ART_SIZE / ROWS
RAMP = " .,:;+=xX#%@"


def character_rows(source):
    with Image.open(source) as original:
        photo = ImageOps.exif_transpose(original).convert("L")
        w, h = photo.size
        # Frame the head, torso and complete wings; retain the photographed silhouette.
        crop = photo.crop((round(w * .032), round(h * .251),
                           round(w * .968), round(h * .778)))
        pixels = crop.resize((COLS, ROWS), Image.Resampling.LANCZOS)
        rows = []
        for y in range(ROWS):
            line = []
            for x in range(COLS):
                luminance = pixels.getpixel((x, y)) / 255
                luminance = 0 if luminance < .035 else luminance ** .78
                line.append(RAMP[min(len(RAMP) - 1, round(luminance * (len(RAMP) - 1)))])
            rows.append("".join(line))
        return rows


def render(rows):
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="840" height="880" '
           'viewBox="0 0 840 880" role="img" aria-labelledby="title desc">',
           '<title id="title">Retrato em caracteres: silhueta com asas</title>',
           '<desc id="desc">Fotografia convertida em caracteres claros, em um terminal escuro.</desc>',
           '<style>@media(prefers-reduced-motion:reduce){.row{opacity:1!important}.cursor{display:none}}</style>',
           '<rect width="840" height="880" rx="14" fill="#0d1117"/>',
           '<rect x=".5" y=".5" width="839" height="879" rx="14" fill="none" stroke="#30363d"/>',
           '<path d="M0 32H840 M0 849H840" stroke="#30363d"/>']
    for x, color in [(23, "#ff5f56"), (39, "#ffbd2e"), (55, "#27c93f")]:
        svg.append(f'<circle cx="{x}" cy="16" r="5" fill="{color}"/>')
    svg.append('<text x="420" y="21" text-anchor="middle" font-family="monospace" '
               'font-size="12" fill="#8b949e">vitin@github: ~$ ./portrait.sh</text>')
    duration = 5.8 / ROWS
    for row, line in enumerate(rows):
        top = 42 + row * CELL_H
        begin = row * duration
        svg.append(f'<defs><clipPath id="line{row}"><rect x="20" y="{top:.2f}" width="800" height="{CELL_H:.3f}">'
                   f'<animate attributeName="width" from="0" to="800" begin="{begin:.3f}s" '
                   f'dur="{duration:.4f}s" fill="freeze"/></rect></clipPath></defs>')
        svg.append(f'<g class="row" clip-path="url(#line{row})"><set attributeName="opacity" to="0" begin="0s"/>'
                   f'<set attributeName="opacity" to="1" begin="{begin:.3f}s"/>'
                   f'<text x="20" y="{top + CELL_H * .79:.2f}" xml:space="preserve" '
                   f'font-family="DejaVu Sans Mono,Consolas,monospace" font-size="7.15" '
                   f'fill="#d5d9df" textLength="800" lengthAdjust="spacingAndGlyphs">{html.escape(line)}</text></g>')
    svg.append('<rect class="cursor" x="20" y="42" width="800" height="1.5" fill="#ffffff" opacity="0">'
               '<set attributeName="opacity" to=".5" begin="0s"/>'
               '<animate attributeName="y" from="42" to="842" dur="5.8s" fill="freeze"/>'
               '<set attributeName="opacity" to="0" begin="5.8s"/></rect>')
    svg.append('<text x="20" y="869" font-family="monospace" font-size="13" fill="#8b949e">'
               'vitin@github:~$ whoami <tspan fill="#d5d9df">Vitor Luan</tspan></text></svg>')
    return "".join(svg)


if __name__ == "__main__":
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(render(character_rows(SOURCE)), encoding="utf-8")
    print(f"Generated {DESTINATION.name}")
