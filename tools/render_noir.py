"""Render the profile's original motion graphics: python tools/render_noir.py.

Requires Pillow 12.3.0 and the DejaVu fonts shipped with Ubuntu.
These are illustrative animations, not live telemetry or sponsor counters.
"""

from pathlib import Path
import math

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/noir"
INK, PAPER, RED, MUTED, LINE = "#0a0a0a", "#f2efe9", "#b3001b", "#aaa59f", "#383532"
FONT = Path("/usr/share/fonts/truetype/dejavu")


def font(size, serif=False):
    return ImageFont.truetype(str(FONT / ("DejaVuSerif.ttf" if serif else "DejaVuSansMono.ttf")), size)


def text(draw, xy, value, size=16, fill=PAPER, center=False, serif=False):
    draw.text(xy, value, font=font(size, serif), fill=fill, anchor="mt" if center else "lt")


def canvas(width, height, label):
    im = Image.new("RGB", (width, height), INK)
    d = ImageDraw.Draw(im)
    d.rectangle((1, 1, width-2, height-2), outline=LINE)
    d.line((24, 48, width-24, 48), fill=LINE)
    text(d, (24, 18), label, 13, MUTED)
    for y in (68, height-30):
        d.rectangle((10, y, 15, y+10), fill=LINE)
        d.rectangle((width-16, y, width-11, y+10), fill=LINE)
    return im, d


def save(frames, name):
    frames[0].save(OUT / name, save_all=True, append_images=frames[1:],
                   duration=100, loop=0, optimize=True, disposal=1)


def signal(mobile=False):
    w, h = (600, 760) if mobile else (1200, 360)
    names = ["FIELD", "PLC / SCADA", "CLOUD", "INTERFACE", "OPERATOR"]
    descriptions = [("Sensors", "Relays"), ("Logic / PID", "Modbus"),
                    ("IoT", "WebSockets"), ("Android / POS", "Dashboards"), ("Read", "Decide / act")]
    frames = []
    for frame in range(60):
        im, d = canvas(w, h, "BRUNNODEV / SIGNAL STUDY 01")
        text(d, (30, 69), "From the field. Back to the field.", 25 if mobile else 32, serif=True)
        active = min(frame // 10, 4) if frame < 50 else -1
        positions = [(65, 130+i*105, 475, 83) for i in range(5)] if mobile else [(40+i*228, 140, 208, 112) for i in range(5)]
        for i, (x, y, bw, bh) in enumerate(positions):
            hot = i == active
            d.rectangle((x, y, x+bw, y+bh), fill=RED if hot else "#111110", outline=PAPER if hot else LINE, width=2)
            if mobile:
                text(d, (x+18, y+17), f"0{i+1}", 22, PAPER if hot else MUTED)
                text(d, (x+92, y+14), names[i], 24)
                text(d, (x+92, y+49), " / ".join(descriptions[i]), 17, PAPER if hot else MUTED)
            else:
                text(d, (x+16, y+12), f"0{i+1}", 13, PAPER if hot else MUTED)
                text(d, (x+bw/2, y+35), names[i], 21, center=True)
                for j, line in enumerate(descriptions[i]):
                    text(d, (x+bw/2, y+67+j*19), line, 15, PAPER if hot else MUTED, center=True)
            if i < 4:
                if mobile:
                    cx, cy = x+bw/2, y+bh
                    d.line((cx, cy, cx, cy+22), fill=RED, width=2)
                    p = cy+3+(frame % 10)*1.6
                    d.rectangle((cx-3, p, cx+3, p+4), fill=PAPER)
                else:
                    cx, cy = x+bw, y+bh/2
                    d.line((cx, cy, cx+20, cy), fill=RED, width=2)
                    p = cx+2+(frame % 10)*1.5
                    d.rectangle((p, cy-3, p+4, cy+3), fill=PAPER)
        if mobile:
            d.line([(65, 592), (36, 592), (36, 172), (65, 172)], fill=RED, width=2)
            d.polygon([(65, 172), (55, 167), (55, 177)], fill=RED)
            text(d, (65, 680), "FEEDBACK / close the loop", 20, MUTED)
            text(d, (65, 719), "Concept animation / explore the reels below", 13, MUTED)
        else:
            d.line([(1056, 252), (1056, 286), (144, 286), (144, 252)], fill=RED, width=2)
            d.polygon([(144, 252), (139, 262), (149, 262)], fill=RED)
            text(d, (600, 304), "FEEDBACK / close the loop", 16, MUTED, center=True)
            if frame >= 50:
                p = 1056-(frame-50)/10*912
                d.ellipse((p-4, 282, p+4, 290), fill=PAPER)
        frames.append(im)
    save(frames, "signal-path-mobile.gif" if mobile else "signal-path.gif")
    frames[0].save(OUT / ("signal-path-mobile.png" if mobile else "signal-path.png"))


def sponsors():
    frames = []
    for frame in range(48):
        im, d = canvas(1200, 248, "BRUNNODEV / THE PEOPLE BEHIND THE NEXT FRAME")
        text(d, (40, 76), "Keep the lab in motion.", 43, serif=True)
        text(d, (40, 143), "Open tools. Documented decisions. Working examples.", 19, MUTED)
        text(d, (40, 200), "GITHUB SPONSORS / BUY ME A COFFEE", 15)
        cx, cy, radius = 1082, 146, 65
        d.ellipse((cx-radius, cy-radius, cx+radius, cy+radius), outline=LINE, width=2)
        for i in range(5):
            a = frame/48*2*math.pi + i*2*math.pi/5
            x, y = cx+41*math.cos(a), cy+41*math.sin(a)
            d.ellipse((x-13, y-13, x+13, y+13), outline=MUTED, width=2)
        d.ellipse((cx-7, cy-7, cx+7, cy+7), fill=RED)
        frames.append(im)
    save(frames, "sponsors.gif")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    signal()
    signal(mobile=True)
    sponsors()
