#!/usr/bin/env python3
"""Generate the note's SVG and vector PDF figures from one geometric scene.

SVG generation uses only the Python standard library. PDF output requires
ReportLab: ``python -m pip install -r requirements.txt``. Run with ``--svg-only``
when only the SVG files are needed. Every output is deterministic; no external
images, web fonts, or platform-specific drawing library is used.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from html import escape
from math import cos, pi, sin
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "paper" / "figures"
TYPES = {
    2: ((2, 1),),
    3: ((3, 1),),
    4: ((2, 2), (4, 1)),
    5: ((5, 1),),
    6: ((2, 3), (3, 2), (6, 1)),
}
UNIT = 44.0
INK = "#182d43"
MUTED = "#4e6072"
RULE = "#d5dfe8"
BLUE = "#235da8"
BLUE_FILL = "#edf4fd"
AMBER = "#966006"
AMBER_FILL = "#fff5e5"
WHITE = "#ffffff"


@dataclass
class Scene:
    width: float
    height: float
    title: str
    description: str
    marks: list[tuple[str, dict]] = field(default_factory=list)

    def add(self, kind: str, **values) -> None:
        self.marks.append((kind, values))

    def text(self, x: float, y: float, value: str, size: float = 20,
             color: str = INK, bold: bool = False, anchor: str = "start") -> None:
        self.add("text", x=x, y=y, value=value, size=size, color=color,
                 bold=bold, anchor=anchor)

    def line(self, x1: float, y1: float, x2: float, y2: float,
             color: str = RULE, width: float = 1) -> None:
        self.add("line", x1=x1, y1=y1, x2=x2, y2=y2,
                 color=color, width=width)


def number(value: float) -> str:
    """Stable compact coordinates, with more precision than display requires."""
    return f"{value:.4f}".rstrip("0").rstrip(".") or "0"


def description(numbers: tuple[int, ...]) -> str:
    details = []
    for n in numbers:
        kind = "prime" if len(TYPES[n]) == 1 else "composite"
        pairs = ", ".join(f"(k={k}, s={s})" for k, s in TYPES[n])
        details.append(f"N={n} is {kind}: {pairs}.")
    return (" ".join(details) +
            " All diagrams have the same length scale. Blue diagrams have unit"
            " steps; amber diagrams have non-unit steps. A digon is drawn as"
            " one segment with two opposite arrows on that segment: the route"
            " traverses the same segment twice, so its total length is 2s.")


def draw_route(scene: Scene, cx: float, cy: float, k: int, s: int) -> None:
    color, fill = (BLUE, BLUE_FILL) if s == 1 else (AMBER, AMBER_FILL)
    if k == 2:
        left, right = cx - s * UNIT / 2, cx + s * UNIT / 2
        scene.line(left, cy, right, cy, color, 3)
        # The arrows themselves lie on the segment; they do not suggest
        # distinct parallel sides or a positive-area Euclidean digon.
        for tip, direction in ((cx - s * UNIT * 0.18, -1),
                               (cx + s * UNIT * 0.18, 1)):
            tail = tip - direction * 6
            scene.add("polyline", points=((tail, cy - 4), (tip, cy),
                                           (tail, cy + 4)),
                      color=color, width=2.6)
        vertices = ((left, cy), (right, cy))
    else:
        radius = s * UNIT / (2 * sin(pi / k))
        start = -pi / 4 if k == 4 else -pi / 2
        vertices = tuple((cx + radius * cos(start + j * 2 * pi / k),
                          cy + radius * sin(start + j * 2 * pi / k))
                         for j in range(k))
        scene.add("polygon", points=vertices, color=color, fill=fill, width=3)
    for x, y in vertices:
        scene.add("circle", x=x, y=y, radius=3.3, fill=color)


def draw_card(scene: Scene, n: int, x: float, y: float,
              width: float, height: float = 212) -> None:
    scene.add("rect", x=x, y=y, width=width, height=height,
              fill=WHITE, stroke=RULE, radius=10)
    kind = "Prime" if len(TYPES[n]) == 1 else "Composite"
    count = len(TYPES[n])
    scene.text(x + 18, y + 30, f"N = {n}  |  {kind}", 23, bold=True)
    scene.text(x + 18, y + 55,
               f"{count} representation " + ("type" if count == 1 else "types"),
               18, MUTED)
    for index, (k, s) in enumerate(TYPES[n]):
        cx = x + width * (index + 0.5) / count
        draw_route(scene, cx, y + 112, k, s)
        scene.text(cx, y + 177, f"(k, s) = ({k}, {s})", 20,
                   anchor="middle")
        scene.text(cx, y + 200, "Unit steps" if s == 1 else "Non-unit steps",
                   18, BLUE if s == 1 else AMBER, anchor="middle")


def overview() -> Scene:
    scene = Scene(1000, 590, "Regular routes for total lengths 2 to 6",
                  description((2, 3, 4, 5, 6)))
    scene.text(22, 34, scene.title, 28, bold=True)
    scene.text(22, 64, "Primes have one representation type; composites have more.",
               20, MUTED)
    draw_card(scene, 2, 20, 86, 230)
    draw_card(scene, 3, 265, 86, 230)
    draw_card(scene, 4, 510, 86, 470)
    draw_card(scene, 5, 20, 311, 295)
    draw_card(scene, 6, 330, 311, 650)
    scene.text(22, 551,
               "Each (k, s) records k steps of length s. All routes use the same length scale.",
               18, MUTED)
    scene.text(22, 576,
               "The digon traverses one segment twice; its arrows lie on the coincident edges.",
               18, MUTED)
    return scene


def individual(n: int) -> Scene:
    width = 320 if len(TYPES[n]) == 1 else 255 * len(TYPES[n])
    scene = Scene(width, 272, f"All regular-route representation types for N={n}",
                  description((n,)))
    draw_card(scene, n, 1, 1, width - 2, 213)
    scene.text(width / 2, 239, "All diagrams share one length scale.",
               17, MUTED, anchor="middle")
    if any(k == 2 for k, _ in TYPES[n]):
        scene.text(width / 2, 262, "Digon: one segment, two traversals.",
                   17, MUTED, anchor="middle")
    return scene


def svg(scene: Scene) -> str:
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           f'<svg xmlns="http://www.w3.org/2000/svg" width="{number(scene.width)}" '
           f'height="{number(scene.height)}" viewBox="0 0 {number(scene.width)} '
           f'{number(scene.height)}" role="img" aria-labelledby="title description">',
           f'  <title id="title">{escape(scene.title)}</title>',
           f'  <desc id="description">{escape(scene.description)}</desc>',
           f'  <rect width="100%" height="100%" fill="{WHITE}"/>',
           '  <g font-family="Arial, Helvetica, sans-serif">']
    for kind, mark in scene.marks:
        v = {key: number(value) if isinstance(value, (int, float)) else value
             for key, value in mark.items()}
        if kind == "text":
            weight = "bold" if mark["bold"] else "normal"
            item = (f'<text x="{v["x"]}" y="{v["y"]}" font-size="{v["size"]}" '
                    f'font-weight="{weight}" text-anchor="{v["anchor"]}" '
                    f'fill="{v["color"]}">{escape(v["value"])}</text>')
        elif kind == "line":
            item = (f'<line x1="{v["x1"]}" y1="{v["y1"]}" x2="{v["x2"]}" '
                    f'y2="{v["y2"]}" stroke="{v["color"]}" '
                    f'stroke-width="{v["width"]}" stroke-linecap="round"/>')
        elif kind in ("polygon", "polyline"):
            points = " ".join(f"{number(x)},{number(y)}" for x, y in mark["points"])
            item = (f'<{kind} points="{points}" fill="{v.get("fill", "none")}" '
                    f'stroke="{v["color"]}" stroke-width="{v["width"]}" '
                    'stroke-linejoin="round" stroke-linecap="round"/>')
        elif kind == "circle":
            item = (f'<circle cx="{v["x"]}" cy="{v["y"]}" '
                    f'r="{v["radius"]}" fill="{v["fill"]}"/>')
        elif kind == "rect":
            item = (f'<rect x="{v["x"]}" y="{v["y"]}" width="{v["width"]}" '
                    f'height="{v["height"]}" rx="{v["radius"]}" '
                    f'fill="{v["fill"]}" stroke="{v["stroke"]}"/>')
        else:
            raise ValueError(kind)
        out.append("    " + item)
    out.extend(("  </g>", "</svg>", ""))
    return "\n".join(out)


def pdf(scene: Scene, target: Path) -> None:
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas

    # SVG CSS pixels are 1/96 inch. PDF points are 1/72 inch.
    factor = 0.75
    doc = canvas.Canvas(str(target), pagesize=(scene.width * factor,
                                               scene.height * factor),
                        invariant=1, pageCompression=1, pdfVersion=(1, 4))
    doc.setTitle(scene.title)
    doc.setSubject(scene.description)
    doc.setCreator("scripts/make_figures.py")
    doc.scale(factor, factor)
    doc.setFillColor(HexColor(WHITE))
    doc.rect(0, 0, scene.width, scene.height, fill=1, stroke=0)
    doc.setLineCap(1)
    doc.setLineJoin(1)
    for kind, mark in scene.marks:
        def y(value):
            return scene.height - value
        if kind == "text":
            doc.setFillColor(HexColor(mark["color"]))
            doc.setFont("Helvetica-Bold" if mark["bold"] else "Helvetica", mark["size"])
            draw = doc.drawCentredString if mark["anchor"] == "middle" else doc.drawString
            draw(mark["x"], y(mark["y"]), mark["value"])
        elif kind == "line":
            doc.setStrokeColor(HexColor(mark["color"]))
            doc.setLineWidth(mark["width"])
            doc.line(mark["x1"], y(mark["y1"]), mark["x2"], y(mark["y2"]))
        elif kind in ("polygon", "polyline"):
            doc.setStrokeColor(HexColor(mark["color"]))
            doc.setLineWidth(mark["width"])
            if "fill" in mark:
                doc.setFillColor(HexColor(mark["fill"]))
            path = doc.beginPath()
            for index, (px, py) in enumerate(mark["points"]):
                (path.moveTo if index == 0 else path.lineTo)(px, y(py))
            if kind == "polygon":
                path.close()
            doc.drawPath(path, stroke=1, fill=int("fill" in mark))
        elif kind == "circle":
            doc.setFillColor(HexColor(mark["fill"]))
            doc.circle(mark["x"], y(mark["y"]), mark["radius"], fill=1, stroke=0)
        elif kind == "rect":
            doc.setFillColor(HexColor(mark["fill"]))
            doc.setStrokeColor(HexColor(mark["stroke"]))
            doc.setLineWidth(1)
            doc.roundRect(mark["x"], y(mark["y"] + mark["height"]),
                          mark["width"], mark["height"], mark["radius"],
                          fill=1, stroke=1)
        else:
            raise ValueError(kind)
    doc.showPage()
    doc.save()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--svg-only", action="store_true",
                        help="generate SVG files using only the standard library")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    scenes = {f"n{n}": individual(n) for n in TYPES}
    scenes["overview"] = overview()
    for name, scene in scenes.items():
        source = OUTPUT / f"{name}.svg"
        source.write_text(svg(scene), encoding="utf-8", newline="\n")
        print(source.relative_to(ROOT))
        if not args.svg_only:
            target = source.with_suffix(".pdf")
            pdf(scene, target)
            print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
