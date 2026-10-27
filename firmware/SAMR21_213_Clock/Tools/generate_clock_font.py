"""Generate fixed-cell Oswald Regular clock digits, SIL OFL 1.1."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]
W,H,STRIDE,S=44,88,6,4
font=ImageFont.truetype(str(ROOT/'Assets/Oswald/Oswald.ttf'),120*S)
font.set_variation_by_axes([400])
raw=[]
for c in '0123456789':
    image=Image.new('L',(100*S,170*S),255)
    ImageDraw.Draw(image).text((8*S,-5*S),c,font=font,fill=0)
    box=image.point(lambda p:255 if p<150 else 0).getbbox()
    raw.append(image.crop(box))
factor=min(W*S/max(im.width for im in raw),H*S/max(im.height for im in raw))
digits=[]
for im in raw:
    im=im.resize((round(im.width*factor),round(im.height*factor)),Image.Resampling.LANCZOS)
    image=Image.new('L',(W*S,H*S),255)
    image.paste(im,((W*S-im.width)//2,(H*S-im.height)//2))
    digits.append(image.resize((W,H),Image.Resampling.LANCZOS).point(lambda p:0 if p<150 else 255,'1'))
rows=[]
for image in digits:
    packed=[]
    for y in range(H):
        for bx in range(STRIDE):
            v=0
            for bit in range(8):
                x=bx*8+bit
                if x<W and image.getpixel((x,y))==0:v|=128>>bit
            packed.append(v)
    rows.append(packed)
header='/* Generated from Oswald Regular (choice C); Assets/Oswald/OFL.txt. */\n'
header+='#ifndef CLOCK_FONT_H\n#define CLOCK_FONT_H\n'
header+='static const uint8_t clock_digits[10][528] = {\n'
for n,row in enumerate(rows):
    header+='    { /* '+str(n)+' */\n'
    header+='\n'.join('        '+','.join('0x%02x'%v for v in row[i:i+18])+',' for i in range(0,len(row),18))+'\n    },\n'
header+='};\n#endif\n'
(ROOT/'App/clock_font.h').write_text(header,encoding='utf-8',newline='\n')
for value in ['00:00','12:34','20:58','23:59']:
    image=Image.new('1',(212,104),1)
    for index,x in [(0,5),(1,53),(3,115),(4,163)]:image.paste(digits[int(value[index])],(x,8))
    d=ImageDraw.Draw(image)
    for y in [34,62]:d.ellipse((103,y,108,y+5),fill=0)
    image.convert('RGB').save(ROOT/('clock_'+value.replace(':','')+'_preview.png'))
print('Generated font C: Oswald Regular; 44x88 cells; aspect ratio preserved')
