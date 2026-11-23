#!/usr/bin/env python3
"""WCAG 2.x contrast checker.

Usage: contrast.py "#FG:#BG" ["#FG:#BG" ...]
Accepts #RGB, #RRGGBB or #RRGGBBAA (alpha is composited over the background).
"""
import sys


def parse(hex_str):
    h = hex_str.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) not in (6, 8):
        raise ValueError(f"bad colour: {hex_str}")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
    return (r, g, b, a)


def composite(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3))


def luminance(rgb):
    def chan(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg_hex, bg_hex):
    bg = parse(bg_hex)
    fg = composite(parse(fg_hex), bg)
    l1, l2 = sorted((luminance(fg), luminance(bg[:3])), reverse=True)
    return (l1 + 0.05) / (l2 + 0.05)


def main(pairs):
    if not pairs:
        print(__doc__)
        return 1
    worst = 0
    for pair in pairs:
        fg, bg = pair.split(":")
        r = ratio(fg, bg)
        body = "PASS" if r >= 4.5 else "FAIL"
        large = "PASS" if r >= 3.0 else "FAIL"
        print(f"{fg} on {bg}: {r:5.2f}:1  body(4.5) {body}  large/UI(3.0) {large}")
        if r < 4.5:
            worst = 2
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
