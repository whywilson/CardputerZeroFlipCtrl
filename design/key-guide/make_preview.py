"""Render the 320x170 pixel guide previews and its embedded RGB565 header."""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
BG = '#101318'
PANEL = '#191e25'
DIM = '#64707e'
ORANGE = '#ff932f'
CREAM = '#ffedcf'
MINT = '#9fdfb0'
GLYPHS = {
 'A':'01110/10001/10001/11111/10001/10001/10001',
 'B':'11110/10001/10001/11110/10001/10001/11110',
 'C':'01111/10000/10000/10000/10000/10000/01111',
 'D':'11110/10001/10001/10001/10001/10001/11110',
 'E':'11111/10000/10000/11110/10000/10000/11111',
 'F':'11111/10000/10000/11110/10000/10000/10000',
 'G':'01111/10000/10000/10111/10001/10001/01111',
 'H':'10001/10001/10001/11111/10001/10001/10001',
 'I':'11111/00100/00100/00100/00100/00100/11111',
 'J':'00111/00010/00010/00010/10010/10010/01100',
 'K':'10001/10010/10100/11000/10100/10010/10001',
 'L':'10000/10000/10000/10000/10000/10000/11111',
 'M':'10001/11011/10101/10101/10001/10001/10001',
 'N':'10001/11001/10101/10011/10001/10001/10001',
 'O':'01110/10001/10001/10001/10001/10001/01110',
 'P':'11110/10001/10001/11110/10000/10000/10000',
 'Q':'01110/10001/10001/10001/10101/10010/01101',
 'R':'11110/10001/10001/11110/10100/10010/10001',
 'S':'01111/10000/10000/01110/00001/00001/11110',
 'T':'11111/00100/00100/00100/00100/00100/00100',
 'U':'10001/10001/10001/10001/10001/10001/01110',
 'V':'10001/10001/10001/10001/10001/01010/00100',
 'W':'10001/10001/10001/10101/10101/10101/01010',
 'X':'10001/10001/01010/00100/01010/10001/10001',
 'Y':'10001/10001/01010/00100/00100/00100/00100',
 'Z':'11111/00001/00010/00100/01000/10000/11111',
 '0':'01110/10001/10011/10101/11001/10001/01110',
 '1':'00100/01100/00100/00100/00100/00100/01110',
 '2':'01110/10001/00001/00010/00100/01000/11111',
 '3':'11110/00001/00001/01110/00001/00001/11110',
 '4':'00010/00110/01010/10010/11111/00010/00010',
 '5':'11111/10000/10000/11110/00001/00001/11110',
 '6':'01110/10000/10000/11110/10001/10001/01110',
 '7':'11111/00001/00010/00100/01000/01000/01000',
 '8':'01110/10001/10001/01110/10001/10001/01110',
 '9':'01110/10001/10001/01111/00001/00001/01110',
 '-':'00000/00000/00000/11111/00000/00000/00000',
 '/':'00001/00001/00010/00100/01000/10000/10000',
 '>':'00000/01000/00100/00010/00100/01000/00000',
 '+':'00000/00100/00100/11111/00100/00100/00000',
}
image = Image.new('RGB', (320, 170), BG)
draw = ImageDraw.Draw(image)

def width(text):
    return max(0, len(text) * 6 - 1)

def text(x, y, value, color=CREAM):
    assert x >= 0 and y >= 0 and x + width(value) <= 320 and y + 7 <= 170
    for char in value:
        if char != ' ':
            for dy, row in enumerate(GLYPHS[char].split('/')):
                for dx, bit in enumerate(row):
                    if bit == '1':
                        draw.point((x + dx, y + dy), fill=color)
        x += 6

def centered(x, y, w, label, color=CREAM):
    text(x + (w - width(label)) // 2, y, label, color)

def box(x, y, w, h, border):
    # Stepped corners and a one-pixel bottom edge keep the design on the pixel grid.
    draw.rectangle((x+1, y, x+w-2, y+h-1), fill=PANEL)
    draw.line((x+2, y, x+w-3, y), fill=border)
    draw.line((x, y+2, x, y+h-3), fill=border)
    draw.line((x+w-1, y+2, x+w-1, y+h-3), fill=border)
    draw.line((x+2, y+h-1, x+w-3, y+h-1), fill=border)
    for px, py in [(x+1,y+1),(x+w-2,y+1),(x+1,y+h-2),(x+w-2,y+h-2)]:
        draw.point((px,py),fill=border)

def down(x, y):
    draw.line((x,y,x,y+3),fill=DIM)
    draw.line((x-2,y+2,x,y+4),fill=DIM)
    draw.line((x,y+4,x+2,y+2),fill=DIM)

def dpad(x,y):
    draw.line((x,y,x,y+12),fill=ORANGE,width=3)
    draw.line((x-6,y+6,x+6,y+6),fill=ORANGE,width=3)
    draw.rectangle((x-1,y+5,x+1,y+7),fill=PANEL)

def multitask(x,y):
    draw.rectangle((x+3,y,x+13,y+8),outline=ORANGE)
    draw.rectangle((x,y+3,x+10,y+11),fill=PANEL,outline=ORANGE)

def check(x,y):
    draw.line([(x,y+5),(x+4,y+9),(x+12,y+1)],fill=ORANGE,width=2)

def back(x,y):
    draw.line([(x+12,y+10),(x+12,y+4),(x,y+4)],fill=ORANGE,width=2)
    draw.line([(x+4,y),(x,y+4),(x+4,y+8)],fill=ORANGE,width=2)

# Title and the orange / green source-to-target legend.
draw.rectangle((7,7,9,15),fill=ORANGE)
text(15,8,'FLIPPER ONE',ORANGE)
text(254,8,'KEY GUIDE',CREAM)
draw.line((8,22,311,22),fill='#39414c')
text(8,27,'BOTTOM KEYS',DIM)
text(8,44,'ONE',ORANGE)
text(8,72,'ZERO',MINT)
for i, label in enumerate(('ESC','VIEW','POWER','EDIT','RUN')):
    x = 39 + i * 55
    box(x,39,50,19,ORANGE)
    centered(x,45,50,label)
    down(x+24,60)
    box(x,68,50,18,MINT)
    centered(x,73,50,str(i+4),MINT)

# Navigation and action keys are grouped by function.
draw.line((8,93,311,93),fill='#39414c')
text(8,98,'NAVIGATION / ACTION',DIM)
for i, (label, target, icon) in enumerate((
    ('D-PAD','ARROWS',dpad),('MULTI','TAB',multitask),
    ('OK','ENTER',check),('BACK','ESC',back))):
    x = 8 + i * 78
    box(x,109,70,21,ORANGE)
    text(x+5,116,label)
    icon(x+54 if i==0 else x+50,113)
    down(x+34,132)
    box(x,139,70,18,MINT)
    centered(x,144,70,target,MINT)

image.save(OUT / 'key-guide-320x170.png')
image.resize((960,510),Image.Resampling.NEAREST).save(OUT / 'key-guide-preview.png')
# Embed RGB565 runs so the help image needs neither PNG decoding nor data files.
from itertools import groupby
colors = [((r >> 3) << 11) | ((g >> 2) << 5) | (b >> 3)
          for r, g, b in image.getdata()]
runs = [(len(list(group)), color) for color, group in groupby(colors)]
assert sum(count for count, _ in runs) == 320 * 170
assert all(count <= 65535 for count, _ in runs)
encoded = [f'0x{((count << 16) | color):08x}u' for count, color in runs]
rows = [', '.join(encoded[i:i + 8]) for i in range(0, len(encoded), 8)]
header = '''// Generated by design/key-guide/make_preview.py. Do not edit by hand.
#pragma once
#include <algorithm>
#include <cstdint>
inline void render_key_guide(uint16_t* pixels) {
    static constexpr uint32_t runs[] = {
        ''' + ',\n        '.join(rows) + '''
    };
    for (uint32_t run : runs) {
        const unsigned count = run >> 16;
        std::fill_n(pixels, count, static_cast<uint16_t>(run));
        pixels += count;
    }
}
'''
(OUT.parents[1] / 'main' / 'key_guide_pixels.hpp').write_text(header)
print(f'Rendered previews and embedded {len(runs)} RGB565 runs')
