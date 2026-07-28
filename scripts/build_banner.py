from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
OUTPUT_DARK = ROOT / "dark.svg"
OUTPUT_LIGHT = ROOT / "light.svg"


def read_text(name: str) -> str:
    return (ASSETS / name).read_text(encoding="utf-8")


def strip_svg(svg: str) -> str:
    return re.sub(r'^<\?xml[^>]*>\s*', '', svg).strip()


def build(theme: str) -> str:
    background = {
        "dark": "#0a101f",
        "light": "#edf2fb",
    }[theme]
    portrait = strip_svg(read_text("portrait.svg"))
    frames = strip_svg(read_text("frames.svg"))
    particles = strip_svg(read_text("particles.svg"))
    icons = strip_svg(read_text("icons.svg"))

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1180 610" role="img" aria-label="k4r0n22 cyber terminal banner {theme}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{background}"/>
      <stop offset="100%" stop-color="#0f172a"/>
    </linearGradient>
  </defs>
  <rect width="1180" height="610" fill="url(#bg)"/>
  {frames}
  {particles}
  <g opacity="0.95">
    <g transform="translate(438 78)">
      <circle cx="0" cy="0" r="4" fill="#10b981"/>
      <circle cx="16" cy="0" r="4" fill="#22d3ee"/>
      <circle cx="32" cy="0" r="4" fill="#a78bfa"/>
    </g>
  </g>
  <g transform="translate(94 100)">{portrait}</g>
  <g transform="translate(490 118)">
    <rect x="0" y="0" width="508" height="116" rx="20" fill="{('#0b1322' if theme == 'dark' else '#f8fbff')}" fill-opacity="{0.78 if theme == 'dark' else 0.92}" stroke="{('#22314d' if theme == 'dark' else '#c4cfdf')}"/>
    <text x="24" y="32" fill="{('#94a3b8' if theme == 'dark' else '#64748b')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" letter-spacing="2">IDENTITY</text>
    <text x="24" y="58" fill="{('#f8fafc' if theme == 'dark' else '#0f172a')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="18" font-weight="700">k4r0n22</text>
    <text x="24" y="84" fill="{('#22d3ee' if theme == 'dark' else '#0891b2')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">Cybersecurity Engineering / Pentester</text>
  </g>
  <g transform="translate(490 248)">
    <rect x="0" y="0" width="508" height="132" rx="20" fill="{('#0a1322' if theme == 'dark' else '#f3f7fc')}" fill-opacity="{0.82 if theme == 'dark' else 0.98}" stroke="{('#22314d' if theme == 'dark' else '#d4deee')}"/>
    <text x="24" y="32" fill="{('#94a3b8' if theme == 'dark' else '#64748b')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" letter-spacing="2">FOCUS &amp; STACK</text>
    <text x="24" y="58" fill="{('#f8fafc' if theme == 'dark' else '#0f172a')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">web security / offensive security / malware analysis</text>
    <text x="24" y="84" fill="{('#22d3ee' if theme == 'dark' else '#0891b2')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">Python, Bash, PowerShell, JavaScript</text>
    <text x="24" y="110" fill="{('#a78bfa' if theme == 'dark' else '#7c3aed')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">Kali, Burp Suite, Linux, Docker, Git, OWASP</text>
  </g>
  <g transform="translate(490 394)">
    <rect x="0" y="0" width="508" height="84" rx="20" fill="{('#0a1424' if theme == 'dark' else '#eef4fb')}" fill-opacity="{0.82 if theme == 'dark' else 0.98}" stroke="{('#22314d' if theme == 'dark' else '#d4deee')}"/>
    <text x="24" y="32" fill="{('#94a3b8' if theme == 'dark' else '#64748b')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" letter-spacing="2">CONTACT</text>
    <text x="24" y="58" fill="{('#f8fafc' if theme == 'dark' else '#0f172a')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="13">LinkedIn and email fields align here</text>
  </g>
  <g transform="translate(56 492)">
    <rect x="0" y="0" width="508" height="52" rx="18" fill="{('#091220' if theme == 'dark' else '#f8fbff')}" fill-opacity="{0.9 if theme == 'dark' else 0.98}" stroke="{('#22314d' if theme == 'dark' else '#c4cfdf')}"/>
    <g transform="translate(44 26)">
      <use href="#kali" transform="translate(-100 0)"/>
      <use href="#burp" transform="translate(-66 0)"/>
      <use href="#python" transform="translate(-32 0)"/>
      <use href="#linux" transform="translate(2 0)"/>
      <use href="#git" transform="translate(36 0)"/>
      <use href="#docker" transform="translate(70 0)"/>
      <use href="#owasp" transform="translate(104 0)"/>
    </g>
    <text x="300" y="31" fill="{('#94a3b8' if theme == 'dark' else '#64748b')}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="12" letter-spacing="2">toolchain</text>
  </g>
  {icons}
</svg>'''


def main() -> None:
    portrait_script = ROOT / "scripts" / "build_portrait.py"
    if portrait_script.exists():
        import runpy
        runpy.run_path(str(portrait_script), run_name="__main__")

    OUTPUT_DARK.write_text(build("dark"), encoding="utf-8")
    OUTPUT_LIGHT.write_text(build("light"), encoding="utf-8")


if __name__ == "__main__":
    main()