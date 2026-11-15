"""Render the profile's original looping signal studies. Requires Pillow."""
from pathlib import Path
import base64
import io
import math
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/profile'
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'

def font(size, bold=False, mono=False):
    return ImageFont.truetype(MONO if mono else BOLD if bold else FONT, size)

def background(w, h, t):
    im = Image.new('RGB', (w, h), '#0b111b')
    light = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(light)
    for x,y,r,c in [(w*.8+30*math.cos(t),h*.1, h*.9, '#3d2113'),
                    (w*.75+35*math.sin(t),h*.85,h*.8,'#0c294b')]:
        d.ellipse((x-r,y-r,x+r,y+r), fill=c)
    im = ImageChops.add(im,light.filter(ImageFilter.GaussianBlur(h*.25)))
    return im

def save(frames, name):
    frames[0].save(OUT/f'{name}.png', optimize=True)
    # One palette keeps stationary lettering stable across the entire loop.
    palette = frames[0].quantize(colors=96)
    indexed = [im.quantize(palette=palette,dither=Image.Dither.NONE) for im in frames]
    indexed[0].save(OUT/f'{name}.gif',save_all=True,append_images=indexed[1:],
                    duration=125,loop=0,optimize=True,disposal=1)
    print(name, (OUT/f'{name}.gif').stat().st_size)

def trace(d, points, t, accent):
    d.line(points,fill='#30465b',width=2)
    lengths = [math.dist(a,b) for a,b in zip(points,points[1:])]
    target = (t/math.tau*sum(lengths))%sum(lengths)
    for a,b,length in zip(points,points[1:],lengths):
        if target <= length:
            x=a[0]+(b[0]-a[0])*target/length
            y=a[1]+(b[1]-a[1])*target/length
            d.ellipse((x-4,y-4,x+4,y+4),fill=accent)
            break
        target-=length

frames=[]
for n in range(40):
    t=n/40*math.tau
    im=background(1200,400,t); d=ImageDraw.Draw(im)
    # Technical field lives on the right; the reading surface stays quiet.
    for x in range(860,1200,40): d.line((x,0,x,400), fill='#23303b')
    for y in range(0,400,40): d.line((860,y,1200,y), fill='#23303b')
    for offset in range(3):
        y=145+offset*65
        trace(d,[(850,y+35),(905,y+35),(940,y),(1020,y),(1055,y-35),(1200,y-35)],t+offset*2,'#dfaa70' if offset%2==0 else '#60aede')
    d.rectangle((860,0,1199,399),outline='#273847')
    # Rings reference instrumentation without inventing live telemetry.
    d.ellipse((1010,230,1150,370),outline='#4b443a',width=1)
    d.arc((1020,240,1140,360),int(n/40*360),int(n/40*360)+90,fill='#dfaa70',width=2)
    d.text((1045,284),'LAB',font=font(21,mono=True),fill='#99b0c4')
    d.rounded_rectangle((1,1,1198,398),radius=16,outline='#374554',width=2)
    d.rectangle((38,39,43,62),fill='#dda66c')
    d.text((57,38),'BRUNNO / ENGINEERING LABORATORY',font=font(17,mono=True),fill='#c3b6a4')
    d.text((1070,39),'BR / EN',font=font(16,mono=True),fill='#b6c8d8')
    d.text((43,94),'brunnodev',font=font(91,True),fill='#f3f0e9')
    d.text((49,218),'SOFTWARE ENGINEER',font=font(25,True),fill='#f3f0e9')
    d.text((49,259),'ELECTRICAL / OFFSHORE DEVELOPER',font=font(20,mono=True),fill='#8ebfe0')
    d.line((49,314,799,314),fill='#354453')
    d.text((49,337),'Software. Industrial systems. Operational thinking.',font=font(22),fill='#c7c9cb')
    frames.append(im)
save(frames,'lab-hero')

for name,title,subtitle,accent in [('offshore','RF OFFSHORE','Industrial systems / field operations','#72bce6'),
                                  ('wallmarket','RF WALLMARKET','Retail systems / automation','#e1ad75')]:
    svg=(OUT/f'{name}-card.svg').read_text()
    encoded=re.search(r'data:image/png;base64,([^"\s]+)',svg).group(1)
    logo=Image.open(io.BytesIO(base64.b64decode(encoded))).convert('RGBA')
    logo.thumbnail((54,54),Image.Resampling.LANCZOS)
    frames=[]
    for n in range(40):
        t=n/40*math.tau
        im=background(590,166,t);d=ImageDraw.Draw(im)
        for y in [24,144]:
            trace(d,[(335,y),(420,y),(439,y-12 if y>40 else y+12),(588,y-12 if y>40 else y+12)],t,accent)
        d.rounded_rectangle((1,1,588,164),radius=14,outline='#384857',width=2)
        d.rounded_rectangle((22,48,91,117),radius=12,fill='#f3f0e9')
        im.paste(logo,(30,56),logo)
        d.text((110,28),'CEO / COMPANY',font=font(12,mono=True),fill=accent)
        d.text((108,52),title,font=font(27,True),fill='#f3f0e9')
        d.text((110,94),subtitle,font=font(15),fill='#bfc9d2')
        d.text((110,130),'VISIT COMPANY WEBSITE',font=font(11,mono=True),fill=accent)
        d.text((548,64),'↗',font=font(26),fill=accent)
        frames.append(im)
    save(frames,f'{name}-motion')
