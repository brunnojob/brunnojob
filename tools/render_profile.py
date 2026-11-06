"""Render the compact profile panel and its reduced-motion alternative."""
from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/profile'
W, H = 1200, 400
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
def font(n, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, n)

icons = {}
for name in ('offshore', 'wallmarket'):
    path = OUT / f'{name}-favicon.png'
    icon = Image.open(path).convert('RGBA')
    icon.thumbnail((64, 64), Image.Resampling.LANCZOS)
    icon.save(path, optimize=True)
    icons[name] = icon

frames = []
for frame in range(48):
    t = frame / 48 * math.tau
    im = Image.new('RGB', (W, H), '#0c1729')
    glow = Image.new('RGB', (W, H), '#000000')
    g = ImageDraw.Draw(glow)
    for x, y, r, color in [(180+60*math.sin(t), 350, 220, '#06486e'),
                            (990+45*math.cos(t), 50, 170, '#67401d')]:
        g.ellipse((x-r,y-r,x+r,y+r),fill=color)
    from PIL import ImageChops
    im = ImageChops.add(im, glow.filter(ImageFilter.GaussianBlur(75)))
    d = ImageDraw.Draw(im)
    for j in range(4):
        points = [(x, 300+j*22+9*math.sin(x/150+t+j/2)) for x in range(0,W+1,8)]
        d.line(points,fill=(15,62+j*4,88+j*5),width=1)
    for j in range(18):
        x = (j*79+14*math.sin(t+j))%W
        y = 28+(j*47)%340+6*math.cos(t+j)
        d.ellipse((x,y,x+2,y+2),fill='#63849b')
    d.rounded_rectangle((1,1,W-2,H-2),radius=18,outline='#30435b',width=2)
    d.rounded_rectangle((34,36,39,132),radius=2,fill='#dfae68')
    d.text((60,33),'BRUNNO DEV',font=font(49,True),fill='#faf7f0')
    d.text((63,96),'Software, systems & field operations',font=font(23),fill='#c6d5e7')
    d.text((950,49),'BRAZIL / GLOBAL',font=font(17,True),fill='#dfae68')
    d.text((950,83),'brunnodev.store',font=font(17),fill='#d5dfeb')
    d.line((60,151,1140,151),fill='#41536a',width=1)
    d.text((60,172),'Full-stack  /  Cybersecurity  /  Industrial automation  /  Low-code',font=font(26,True),fill='#f4f5f7')
    for y, line in [(220,'I turn operational requirements into usable software,'),
                    (256,'connecting field devices, APIs and interfaces.')]:
        d.text((60,y),line,font=font(26),fill='#d7e1ef')
    d.text((60,306),'C & Java foundation',font=font(22,True),fill='#dfae68')
    d.text((60,345),'Cambridge C2 English',font=font(20),fill='#cad5e3')
    offset = round(2*math.sin(t))
    for x,name,label in [(438,'offshore','RF Offshore'),(807,'wallmarket','RF WALLMARKET')]:
        y=310+offset
        d.rounded_rectangle((x,y,x+333,y+66),radius=10,fill='#14273c',outline='#44607a')
        icon=icons[name].copy();icon.thumbnail((40,40),Image.Resampling.LANCZOS)
        d.rounded_rectangle((x+8,y+8,x+58,y+58),radius=8,fill='#f4f0e8')
        im.paste(icon,(x+13,y+13),icon)
        d.text((x+65,y+8),'CEO',font=font(14,True),fill='#dfae68')
        d.text((x+65,y+28),label,font=font(21,True),fill='#f4f5f7')
    frames.append(im)

frames[0].save(OUT/'intro.png')
compact=[f.resize((960,320),Image.Resampling.LANCZOS) for f in frames[::2]]
palette=compact[0].quantize(colors=48)
indexed=[f.quantize(palette=palette,dither=Image.Dither.NONE) for f in compact]
indexed[0].save(OUT/'intro.gif',save_all=True,append_images=indexed[1:],duration=200,loop=0,optimize=True,disposal=1)
print(f'Rendered {len(frames)} frames; GIF: {(OUT/"intro.gif").stat().st_size:,} bytes')
