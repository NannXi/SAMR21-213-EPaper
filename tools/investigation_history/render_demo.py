"""Decode the framebuffer read from the running C application, not a mockup."""
from pathlib import Path
from PIL import Image
import collections, json
root=Path(__file__).resolve().parents[2]
project=root/'outputs/SAMR21_EPD_Keil'
run=sorted(project.glob('Runs/*/framebuffer.bin'))[-1]
raw=run.read_bytes()
assert len(raw)==5512
image=Image.new('RGB',(212,104))
counts=collections.Counter()
for y in range(104):
    for x in range(212):
        cx=y
        index=(211-x)*13+cx//8
        mask=0x80>>(cx%8)
        black=bool(raw[index]&mask)
        red=bool(raw[2756+index]&mask)
        color=(220,28,45) if not red else ((255,255,255) if black else (0,0,0))
        image.putpixel((x,y),color)
        counts[color]+=1
assert image.getpixel((0,0))==(255,255,255)
assert image.getpixel((0,51))==(255,255,255)
assert image.getpixel((0,52))==(220,28,45)
assert image.getpixel((211,103))==(220,28,45)
assert len(counts)==3
image.save(project/'demo_212x104.png')
image.resize((1060,520),Image.Resampling.NEAREST).save(project/'demo_preview.png')
print(json.dumps({'source':str(run.relative_to(project)),'pixels':{str(k):v for k,v in counts.items()},'verified':True}))
