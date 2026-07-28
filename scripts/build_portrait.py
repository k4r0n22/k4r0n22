from __future__ import annotations

from pathlib import Path
import math
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "assets" / "profile.jpg"
OUTPUT = ROOT / "assets" / "portrait.svg"

PORTRAIT_W = 320
PORTRAIT_H = 398
ANALYSIS_W = 144
ANALYSIS_H = 180


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def luminance(rgb: tuple[int, int, int]) -> float:
    r, g, b = [channel / 255.0 for channel in rgb]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def gaussian(value: float, center: float, spread: float) -> float:
    if spread <= 0:
        return 0.0
    delta = (value - center) / spread
    return math.exp(-delta * delta)


def cover_crop(image: Image.Image, target_w: int, target_h: int, y_bias: float = 0.42) -> Image.Image:
    src_w, src_h = image.size
    scale = max(target_w / src_w, target_h / src_h)
    resized = image.resize((round(src_w * scale), round(src_h * scale)), Image.Resampling.LANCZOS)
    left = round((resized.width - target_w) / 2)
    top = round((resized.height - target_h) * y_bias)
    top = int(clamp(top, 0, resized.height - target_h))
    left = int(clamp(left, 0, resized.width - target_w))
    return resized.crop((left, top, left + target_w, top + target_h))


def sample_grid(image: Image.Image) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    luminance_img = image.convert("L")
    ycbcr_img = image.convert("YCbCr")

    lum = list(luminance_img.getdata())
    ycbcr = list(ycbcr_img.getdata())
    width, height = image.size

    contrast: list[float] = [0.0] * (width * height)
    edge: list[float] = [0.0] * (width * height)
    skin: list[float] = [0.0] * (width * height)
    saturation: list[float] = [0.0] * (width * height)

    for y in range(height):
        row_offset = y * width
        for x in range(width):
            idx = row_offset + x
            center = lum[idx]
            total_diff = 0.0
            total_edge = 0.0
            neighbor_count = 0

            left = lum[idx - 1] if x > 0 else center
            right = lum[idx + 1] if x < width - 1 else center
            up = lum[idx - width] if y > 0 else center
            down = lum[idx + width] if y < height - 1 else center
            gx = (right - left) * 0.5
            gy = (down - up) * 0.5
            edge[idx] = min(1.0, math.hypot(gx, gy) / 96.0)

            for oy in (-1, 0, 1):
                ny = y + oy
                if ny < 0 or ny >= height:
                    continue
                for ox in (-1, 0, 1):
                    nx = x + ox
                    if ox == 0 and oy == 0:
                        continue
                    if nx < 0 or nx >= width:
                        continue
                    neighbor = lum[ny * width + nx]
                    total_diff += abs(center - neighbor)
                    neighbor_count += 1
            contrast[idx] = min(1.0, (total_diff / max(1, neighbor_count)) / 72.0)

            y_val, cb, cr = ycbcr[idx]
            skin_cb = gaussian(cb, 111.0, 17.0)
            skin_cr = gaussian(cr, 152.0, 18.0)
            skin[idx] = min(1.0, skin_cb * 0.75 + skin_cr * 0.85)

            r, g, b = image.getpixel((x, y))
            chroma = max(r, g, b) - min(r, g, b)
            saturation[idx] = min(1.0, chroma / 128.0)

    return lum, contrast, edge, skin, saturation


def feature_weights(x: int, y: int, width: int, height: int) -> tuple[float, float, float, float, float]:
    nx = x / max(1, width - 1)
    ny = y / max(1, height - 1)
    center = gaussian(nx, 0.5, 0.29) * gaussian(ny, 0.48, 0.32)
    hair = gaussian(nx, 0.5, 0.33) * gaussian(ny, 0.26, 0.19)
    eyes = gaussian(nx, 0.5, 0.21) * gaussian(ny, 0.42, 0.07)
    jaw = gaussian(nx, 0.5, 0.24) * gaussian(ny, 0.66, 0.12)
    silhouette = max(center, hair, eyes, jaw)
    return nx, ny, center, hair, silhouette


def dot_color(lum: float, edge: float, skin: float, saturation: float) -> str:
    if edge > 0.56 and lum < 0.86:
        return "#22d3ee" if saturation > 0.12 else "#a78bfa"
    if skin > 0.55 and lum > 0.48:
        return "#f8fafc" if lum > 0.7 else "#cbd5e1"
    if lum < 0.25:
        return "#0f172a"
    if lum < 0.44:
        return "#1e293b"
    if lum < 0.62:
        return "#334155"
    if lum < 0.78:
        return "#64748b"
    return "#cbd5e1"


def main() -> None:
    source = Image.open(SOURCE).convert("RGB")
    portrait = cover_crop(source, PORTRAIT_W, PORTRAIT_H)
    analysis = cover_crop(source, ANALYSIS_W, ANALYSIS_H)

    lum, contrast, edge, skin, saturation = sample_grid(analysis)
    aw, ah = analysis.size

    dots: list[tuple[float, str]] = []

    def collect(step: int, strength_scale: float, limit: int | None) -> None:
        candidates: list[tuple[float, str]] = []
        for y in range(0, PORTRAIT_H, step):
            for x in range(0, PORTRAIT_W, step):
                ax = int(round((x / PORTRAIT_W) * (aw - 1)))
                ay = int(round((y / PORTRAIT_H) * (ah - 1)))
                idx = ay * aw + ax
                l = lum[idx] / 255.0
                c = contrast[idx]
                e = edge[idx]
                s = skin[idx]
                sat = saturation[idx]
                _, _, center, hair, silhouette = feature_weights(ax, ay, aw, ah)

                face_score = 0.42 * center + 0.26 * hair + 0.18 * silhouette + 0.22 * s
                structure = 0.24 * c + 0.34 * e + 0.12 * sat
                depth = 0.40 * (1.0 - l) + face_score + structure
                depth += 0.08 * gaussian((y / PORTRAIT_H), 0.53, 0.33)

                if depth < 0.12 and step > 5:
                    continue

                jitter = (0.3 + c * 0.8 + e * 0.7) * 0.85
                xj = x + ((ax * 17 + ay * 11) % 7 - 3) * 0.06 * jitter
                yj = y + ((ax * 13 + ay * 19) % 7 - 3) * 0.05 * jitter

                radius = 0.22 + depth * 1.38 * strength_scale
                if step <= 5:
                    radius *= 0.82

                if e > 0.48 and l < 0.72:
                    color = "#22d3ee" if sat > 0.14 else "#a78bfa"
                else:
                    color = dot_color(l, e, s, sat)

                opacity = 0.15 + depth * 0.45 + e * 0.12
                candidates.append((depth, f'<circle cx="{xj:.2f}" cy="{yj:.2f}" r="{radius:.2f}" fill="{color}" fill-opacity="{clamp(opacity, 0.08, 0.86):.3f}"/>'))

        candidates.sort(key=lambda item: item[0], reverse=True)
        if limit is not None:
            candidates = candidates[:limit]
        dots.extend(candidates)

    collect(step=10, strength_scale=1.0, limit=440)
    collect(step=7, strength_scale=1.12, limit=620)
    collect(step=5, strength_scale=1.22, limit=700)

    dots.sort(key=lambda item: item[0])
    dot_markup = [dot for _, dot in dots]

    svg = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 320 398" role="img" aria-label="Generated portrait vector">',
        '  <defs>',
        '    <linearGradient id="portraitBg" x1="0" y1="0" x2="0" y2="1">',
        '      <stop offset="0%" stop-color="#0b1221"/>',
        '      <stop offset="100%" stop-color="#111c30"/>',
        '    </linearGradient>',
        '    <radialGradient id="portraitGlow" cx="50%" cy="38%" r="74%">',
        '      <stop offset="0%" stop-color="#22d3ee" stop-opacity="0.10"/>',
        '      <stop offset="42%" stop-color="#a78bfa" stop-opacity="0.05"/>',
        '      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.0"/>',
        '    </radialGradient>',
        '    <radialGradient id="portraitVignette" cx="50%" cy="48%" r="63%">',
        '      <stop offset="50%" stop-color="#0f172a" stop-opacity="0.0"/>',
        '      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.22"/>',
        '    </radialGradient>',
        '    <linearGradient id="portraitSheen" x1="0" y1="0" x2="1" y2="1">',
        '      <stop offset="0%" stop-color="#f8fafc" stop-opacity="0.16"/>',
        '      <stop offset="60%" stop-color="#22d3ee" stop-opacity="0.04"/>',
        '      <stop offset="100%" stop-color="#0f172a" stop-opacity="0.0"/>',
        '    </linearGradient>',
        '    <mask id="fadeMask">',
        '      <rect width="320" height="398" fill="url(#portraitBg)"/>',
        '      <rect x="7" y="7" width="306" height="384" rx="20" fill="#ffffff" fill-opacity="0.96"/>',
        '      <rect x="0" y="0" width="320" height="398" fill="url(#portraitVignette)"/>',
        '    </mask>',
        '    <clipPath id="portraitClip">',
        '      <rect width="320" height="398" rx="20"/>',
        '    </clipPath>',
        '  </defs>',
        '  <rect width="320" height="398" fill="url(#portraitBg)"/>',
        '  <rect width="320" height="398" fill="url(#portraitGlow)"/>',
        '  <g clip-path="url(#portraitClip)">',
        '    <ellipse cx="160" cy="178" rx="106" ry="126" fill="#0f172a" fill-opacity="0.22"/>',
        '    <ellipse cx="160" cy="178" rx="92" ry="118" fill="#111827" fill-opacity="0.12"/>',
        '    <path d="M118 315c14-21 33-31 42-31h0c9 0 28 10 42 31" fill="#0f172a" fill-opacity="0.16"/>',
        '    <g mask="url(#fadeMask)" opacity="0.98">',
        *dot_markup,
        '    </g>',
        '    <path d="M68 157c8-36 30-71 63-92 16-11 34-17 49-17 16 0 35 6 52 18 18 12 33 29 46 50 12 20 20 42 21 62-25-16-55-21-96-21-42 0-82 7-135 0Z" fill="#f8fafc" fill-opacity="0.04"/>',
        '    <path d="M67 234c23 23 44 39 61 45 14 6 31 9 54 9 23 0 39-3 53-9 17-7 37-23 60-47-4 40-21 70-44 87-21 16-43 23-69 23-27 0-49-7-69-23-23-18-39-48-46-85Z" fill="#22d3ee" fill-opacity="0.03"/>',
        '    <rect width="320" height="398" fill="url(#portraitSheen)" fill-opacity="0.22"/>',
        '    <rect width="320" height="398" fill="none" stroke="#22d3ee" stroke-opacity="0.10"/>',
        '  </g>',
        '</svg>',
    ]

    OUTPUT.write_text("\n".join(svg), encoding="utf-8")


if __name__ == "__main__":
    main()