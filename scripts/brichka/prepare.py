"""Prepare local Page 13 SVGs. Does not open or change the Figma document."""
from pathlib import Path
import json, re, sys, copy
from lxml import etree as E

sys.path.insert(0, '/private/tmp/gc-fonttools')
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'assets/brichka/vectors'
OUT.mkdir(parents=True, exist_ok=True)
NS = 'http://www.w3.org/2000/svg'
XL = 'http://www.w3.org/1999/xlink'
E.register_namespace('xlink', XL)
def tag(s): return '{' + NS + '}' + s
fonts = {w: TTFont(ROOT / 'assets/fonts' / ('onest-medium.ttf' if w == 500 else 'onest-regular.ttf')) for w in [400, 500]}

def outline_text(node):
    weight=node.get('font-weight','400')
    f=fonts[500 if weight in ['500','600','700','bold'] else 400]
    gs=f.getGlyphSet();cmap=f.getBestCmap();units=f['head'].unitsPerEm
    size=float(node.get('font-size','14'))
    raw=node.get('letter-spacing','0em')
    spacing=float(raw.replace('em',''))*size if 'em' in raw else float(raw.replace('px',''))
    g=E.Element(tag('g'),{k:v for k,v in node.attrib.items() if k in ['fill','transform','opacity','id']})
    spans=node.findall(tag('tspan')) or [node]
    for span in spans:
        x=float(span.get('x','0'));y=float(span.get('y','0'))
        line=E.SubElement(g,tag('g'),transform=f'translate({x:g} {y:g}) scale({size/units:g} {-size/units:g})')
        advance=0
        for char in ''.join(span.itertext()):
            gid=cmap.get(ord(char))
            if not gid:continue
            pen=SVGPathPen(gs);gs[gid].draw(pen)
            if pen.getCommands():E.SubElement(line,tag('path'),d=pen.getCommands(),transform=f'translate({advance:g} 0)')
            advance+=f['hmtx'][gid][0]+spacing*units/size
    return g

data=json.loads((HERE/'text-source.json').read_text())
audit=[]
for item in data:
    name=item['name']
    if name == 'referral-qr':
        continue
    tree=E.parse(str(HERE/'sources'/f'{name}.svg'))
    root=tree.getroot()
    # The device viewport differs slightly from the source artboard ratio.
    # Fill the viewport without SVG letterboxing above and below the UI.
    root.set('preserveAspectRatio', 'none')
    maps=root.xpath('//*[@id="map"]')
    # Preserve the source map's raster image, pattern matrix and layer position.
    source_map_transforms=[E.tostring(m) for m in maps]
    changes=[]
    for raw in item['texts']:
        t=E.fromstring(('<svg xmlns="'+NS+'">'+raw+'</svg>').encode())[0]
        value=''.join(t.itertext());new=None
        if value=='Иван Иванов':new='Андрей Волков'
        if value=='https://www.link.com/':new='brichka.app/r/m7k4'
        if name in ['trip','share','waiting']:
            if value=='320\u00a0₽':new='210\u00a0₽'
            if value=='150\u00a0₽':new='320\u00a0₽'
            if value=='50\u00a0₽':new='110\u00a0₽'
        if new is None:continue
        matching=root.xpath('//*[@id=$id]',id=t.get('id'))
        if len(matching)!=1:raise ValueError((name,value,len(matching)))
        spans=t.findall(tag('tspan'))
        spans[0].text=new
        for s in spans[1:]:s.text=''
        old=matching[0]
        # Preserve original positioning, including its parent transforms.
        old.getparent().replace(old,outline_text(t))
        changes.append({'from':value,'to':new})
    # Standalone payment sheet can be read without the map's surrounding chrome.
    if name == 'trip':
        assert len(changes)==3, (name,changes)
    E.SubElement(root,tag('title')).text='Бричка / '+name
    tree.write(str(OUT/f'{name}.svg'),encoding='utf-8',xml_declaration=False)
    images=[i for i in root.iter(tag('image'))]
    assert [E.tostring(m) for m in root.xpath('//*[@id="map"]')] == source_map_transforms
    if maps: assert any(i.get('width') == '2560' for i in images)
    audit.append({'name':name,'nodeId':item['id'],'changes':changes,'rasterImages':len(images),'mapPreserved':bool(maps),'bytes':(OUT/f'{name}.svg').stat().st_size})
(OUT/'layout-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print('Prepared',len(audit),'screens; original raster map and SVG pattern transforms preserved.')
