from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[2]
d=(root/'outputs/original_flash_256KiB_read1.bin').read_bytes()
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16)
tiles=[]
for base in [0x19c00,0x30e00,0x31000]:
 for mode,stride in [('interleaved',28),('planar_row',28),('interleaved',26),('single',16)]:
  im=Image.new('RGB',(104,212),'white'); px=im.load()
  for y in range(212):
   for x in range(104):
    col=x//8;bit=7-x%8
    a=base+y*stride+(col*2 if mode=='interleaved' else col)
    b=a+1 if mode=='interleaved' else a+13
    black=not(d[a]>>bit&1);red=False if mode=='single' else not(d[b]>>bit&1)
    px[x,y]=(210,0,0) if red else (0,0,0) if black else (255,255,255)
  im=im.transpose(Image.Transpose.ROTATE_90).resize((636,312),Image.Resampling.NEAREST)
  tile=Image.new('RGB',(660,350),'#dddddd');tile.paste(im,(12,30))
  ImageDraw.Draw(tile).text((10,6),f'{base:#x} {mode} stride={stride}',font=font,fill='black')
  tiles.append(tile)
sheet=Image.new('RGB',(1320,350*6),'white')
for i,tile in enumerate(tiles):sheet.paste(tile,((i%2)*660,(i//2)*350))
sheet.save(root/'work/diagnostics/image_layout_candidates.png')
im=Image.new('RGB',(104,212),'white')
colors={0:(0,0,0),1:(0,0,0),2:(210,0,0),3:(255,255,255)}
for y in range(212):
 for x in range(104):
  v=d[0x19c00+y*28+x//4]
  im.putpixel((x,y),colors[(v>>(6-2*(x%4)))&3])
im=im.transpose(Image.Transpose.ROTATE_90)
im.save(root/'work/diagnostics/original_image_2bpp_candidate.png')
im.resize((848,416),Image.Resampling.NEAREST).save(root/'work/diagnostics/original_image_2bpp_candidate_large.png')
im.save(root/'outputs/original_screen_recovered_212x104.png')
im.resize((848,416),Image.Resampling.NEAREST).save(root/'outputs/original_screen_recovered_4x.png')
(root/'outputs/original_screen_resource_2bpp.bin').write_bytes(d[0x19c00:0x19c00+28*212])
