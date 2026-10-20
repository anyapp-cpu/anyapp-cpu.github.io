from pathlib import Path
import sys, re, base64, copy, json
import xml.etree.ElementTree as E
sys.path.insert(0,'/private/tmp/gc-fonttools')
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from fontTools.pens.svgPathPen import SVGPathPen

ROOT=Path(__file__).resolve().parents[2]
SRC=Path(__file__).resolve().parent/'sources'
OUT=ROOT/'assets/gocomment/vectors'
OUT.mkdir(exist_ok=True)
NS='http://www.w3.org/2000/svg'
XL='http://www.w3.org/1999/xlink'
E.register_namespace('',NS);E.register_namespace('xlink',XL)
def tag(s):return '{'+NS+'}'+s
def data(svg):return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()
PHOTO='data:image/jpeg;base64,'+base64.b64encode((ROOT/'assets/gocomment/interior.jpg').read_bytes()).decode()

def website(w=1440,h=900,variant=0):
    if variant==1:
        return f'''<svg xmlns="{NS}" width="1440" height="900" viewBox="0 0 1440 900"><rect width="1440" height="900" fill="#e8ede9"/><text x="70" y="100" font-family="Arial" font-size="48" fill="#29413c">northline.</text><text x="70" y="270" font-family="Arial" font-size="94" fill="#29413c">A journal for</text><text x="70" y="375" font-family="Arial" font-size="94" fill="#29413c">slower days.</text><rect x="70" y="450" width="600" height="370" fill="#b8c4a9"/><circle cx="1040" cy="570" r="230" fill="#d4c5aa"/><path d="M750 800 Q1100 350 1370 800" fill="#849c88"/><text x="90" y="510" font-family="Arial" font-size="24" fill="#29413c">Stories · People · Places</text></svg>'''
    return f'''<svg xmlns="{NS}" xmlns:xlink="{XL}" width="1440" height="900" viewBox="0 0 1440 900"><rect width="1440" height="900" fill="#f6f4ee"/><text x="58" y="88" font-family="Georgia" font-size="58" fill="#242620">forma®</text><text x="1050" y="72" font-family="Arial" font-size="18" fill="#55584e">Projects　Studio　Contact ↗</text><text x="58" y="204" font-family="Arial" font-size="69" fill="#242620">Thoughtful spaces.</text><text x="58" y="280" font-family="Arial" font-size="69" fill="#242620">Everyday living.</text><text x="1040" y="229" font-family="Arial" font-size="18" fill="#72746c">Interiors that feel like you.</text><text x="1040" y="257" font-family="Arial" font-size="18" fill="#72746c">Designed to be lived in.</text><image x="58" y="330" width="1324" height="500" preserveAspectRatio="xMidYMid slice" xlink:href="{PHOTO}"/><text x="58" y="868" font-family="Arial" font-size="16" fill="#73766b">01　A quiet place, Copenhagen</text></svg>'''

HAND='data:image/png;base64,'+base64.b64encode((ROOT/'assets/gocomment/waving-hand.png').read_bytes()).decode()

BROWSER_ICONS=[
 f'<svg xmlns="{NS}" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="#ea4335"/><path d="M7 17L32 32 18 57A29 29 0 015 21Z" fill="#34a853"/><path d="M32 17H58A29 29 0 0133 61H18L32 32Z" fill="#fbbc05"/><circle cx="32" cy="32" r="14" fill="#4285f4" stroke="white" stroke-width="3"/></svg>',
 f'<svg xmlns="{NS}" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="32" r="29" fill="#f2f4f7" stroke="#c5cad1" stroke-width="2"/><circle cx="32" cy="32" r="25" fill="#27a8ef"/><path d="M23 23L43 12 37 37Z" fill="#ed4556"/><path d="M23 23L37 37 20 52Z" fill="white"/><circle cx="32" cy="32" r="2" fill="#ddd"/></svg>',
 f'<svg xmlns="{NS}" width="64" height="64" viewBox="0 0 64 64"><ellipse cx="32" cy="32" rx="21" ry="26" fill="none" stroke="#ed263d" stroke-width="12"/><path d="M42 10C60 23 57 46 42 54" fill="none" stroke="#c81836" stroke-width="8"/></svg>',
 f'<svg xmlns="{NS}" width="64" height="64" viewBox="0 0 64 64"><circle cx="32" cy="34" r="24" fill="#7345cf"/><path d="M50 7C61 23 64 41 48 55 27 69 4 50 6 31L15 16 16 28 26 20 23 34C29 43 42 42 46 32 51 22 45 19 50 7Z" fill="#ff8a24"/><path d="M9 42C25 58 48 51 51 32 60 56 23 72 9 42Z" fill="#ffb135"/></svg>'
]

NAMES=['Olivia Bennett','Daniel Kim','Sofia Rossi','Emma Davis','Alex Morgan']
INITIALS=['O','D','S','E','A']
TIMES=['10:24','11:06','16:42','09:18','14:35']
DATES=['12 Mar','12 Mar','11 Mar','10 Mar','9 Mar']
MESSAGES=['Could we make this button stand out?','Heading wraps on iPhone. Checking it.','Updated spacing in the project gallery.','Please shorten the introduction.','The new image looks much better.']
IDS=['GC-147','GC-148','GC-139','GC-143','GC-145']

COMMON={
 'John Doe’s workspace':'North Studio','Working space':'North Studio','John Doe':'Alex Morgan','Name Surname':'Alex Morgan',
 'johndoe@gmail.com':'alex@north.studio','usermail@gmail.com':'alex@north.studio','Project Name':'Forma Living',
 'CompanyName':'Forma Living','Название проекта':'Форма / сайт','Иван Иванов':'Анна Смирнова',
 'https://www.asos.com/women/':'https://forma.studio','website.com':'forma.studio','Page Name':'Living room',
 'A-999':'GC-147','Image.png':'living-room.jpg','1 Mb':'284 KB','BestSite.com/1223-2...':'forma.studio/living',
 'Jun 23, 2023 at 12:14':'Mar 12, 2025 at 10:24','Chrome 98.0.4575.19':'Chrome 133.0.6943',
 '1920 × 1080':'1440 × 900','1920x1031':'1512 × 982','Windows 10':'macOS 15.3',
 'Nov 18 2022':'Mar 7, 2025','May 13, 12:43':'Mar 12, 11:06',
 '15 days of Free Trial left.':'5 days of Free Trial left.',
 'Label':'Website URL','Placeholder':'https://forma.studio','Button':'Button',
 'Your reply':'Thanks, I’ll check this.','Type keywords or names':'Search comments or people',
}

def set_text(node,value):
    spans=list(node.iter(tag('tspan')))
    if not spans:node.text=value;return
    if len(spans)==1:spans[0].text=value;return
    original=[(s.text or '') for s in spans]
    if len(spans)==2 and len(value)>35:
        words=value.split();half=len(value)//2;line=''
        while words and len(line)<half:line+=((' ' if line else '')+words.pop(0))
        spans[0].text=line;spans[1].text=' '.join(words)
        for s in spans[2:]:s.text=''
    else:
        spans[0].text=value
        for s in spans[1:]:s.text=''

def mock(root,name):
    counters={};current=0
    for node in root.iter(tag('text')):
        old=''.join(node.itertext());s=old.strip();count=counters.get(s,0);counters[s]=count+1
        new=COMMON.get(s)
        if s=='Name Name':new=NAMES[count%5]
        elif s in ['N','J']:new=INITIALS[count%5] if s=='N' else 'A'
        elif s=='A' and name not in ['comment','panel']:new='A'
        elif s=='И':new=['А','М','Д','Е'][count%4]
        elif s=='Имя Фамилия':new=['Анна Смирнова','Максим Орлов','Дарья Ким','Елена Волкова'][count%4]
        elif s=='Администратор':new='Комментатор' if count==0 else 'Менеджер'
        elif s=='5 дней назад':new=['12 марта','11 марта','10 марта','9 марта'][count%4]
        elif s=='Страница':new='Гостиная'
        elif s=='Все комме':new='Все'
        elif name.endswith('-ru') and s=='Иван Иванов':new='Север / студия' if count==0 else 'Анна Смирнова'
        elif name.endswith('-ru') and s=='usermail@gmail.com':new='anna@sever.studio'
        elif s=='@Иван':new='' if name=='panel-ru' else '@Дарья'
        elif s=='1 Мб':new='284 КБ'
        elif s.startswith('Давайте заменим это фото.'):
            new=['Давайте возьмём широкое фото. Дарья, посмотри референс.','На телефоне заголовок переносится. Проверяю сетку.','Обновила отступы в галерее. Можно посмотреть.'][count%3]
        elif s=='12:14':new=TIMES[count%5]
        elif s in ['today','5 days ago']:new=DATES[count%5]
        elif 'A-999' in s:new=IDS[count%5]+'  '
        elif 'Lorem ipsum' in s:new=MESSAGES[count%5]
        elif s.startswith("It's better to replace this photo."):new=['Could we use the wider photo here? Please check the attached reference.','The heading wraps on mobile. Could we adjust the spacing?','Updated the gallery spacing. Ready for another review.'][count%3]
        elif s=="I heard you. It will be done":new=['I’ll update it before the next review.','Done. Ready for another look.'][count%2]
        elif s=='@Name':new='' if name=='panel' else '@Sofia'
        elif name.startswith('mobile') and s=='Manager':
            new=['Commenter','Manager','Manager','Commenter'][count%4]
            for sp in node.iter(tag('tspan')):sp.set('x','192')
        elif name in ['comment','panel'] and s=='Admin':new='Commenter' if count==0 else 'Manager'
        elif s in ['To discuss','На обсуждении'] and name in ['panel','panel-ru']:
            new=(['На обсуждении','В работе','Решено'] if name=='panel-ru' else ['To discuss','In progress','Resolved'])[count%3]
            node.set('fill',(['#d93298','#8b80ef','#459b95'] if name=='panel-ru' else ['#c4882f','#8b80ef','#45a67b'])[count%3])
        elif s=='100' and name in ['panel','panel-ru']:new='12'
        elif s in ['Show 2 replies','Показать 2 ответа']:new=(['Показать 3 ответа','Показать 2 ответа'] if name=='panel-ru' else ['Show 3 replies','Show 2 replies'])[count%2]
        elif s=='999':new=['6','84','4','27'][count%4] if name=='projects' else ['3','2','1','4'][count%4]
        elif s=='99':new=str([2,1,0,1][count%4])
        elif name.startswith('mobile') and s=='7':new=str([3,2,1,4,3][count%5])
        elif name.startswith('mobile') and s=='1':new=str([2,1,0,1,3][count%5])
        elif name.startswith('mobile') and s=='8':new='12'
        elif name=='projects' and s=='Project Name':new=['Forma Living','Northline Journal'][count%2]
        elif name=='projects' and s=='Jan 11, 2023':new=['Mar 7, 2025','Mar 12, 2025'][count%2]
        elif name=='projects' and s=='15':new='18'
        elif name=='projects' and s=='/30':new='/23'
        elif name=='dashboard':
            new={'30':'31','/100':'/52','64':'9','25':'8','13':'4','50%':['62%','58%'][count%2],
                 '30%':'31%','20%':'7%','25%':'29%','15%':'4%','10%':'9%','165':'12','/1023':'/84','38':'4','28':'6'}.get(s,new)
        elif name in ['extension-en','extension-ru'] and s=='28':new='6'
        elif name=='kit-tag' and s=='Text':new='Open'
        elif name.startswith('kit') and s in ['Text','Text field']:new='forma.studio'
        elif name=='kit-select' and s in ['Select','Label']:new='Olivia Bennett' if s=='Select' or count>0 else 'Project members'
        if new is not None:set_text(node,new)
        if name in ['comment','comment-ru'] and s in ['1 Mb','1 Мб']:
            for sp in node.iter(tag('tspan')):sp.set('x','202')
        if name in ['comment','comment-ru','panel','panel-ru'] and s=='12:14':
            for sp in node.iter(tag('tspan')):sp.set('x','108' if name.startswith('comment') else '100')
        if name in ['comment','comment-ru','panel','panel-ru'] and s in ['today','5 days ago','5 дней назад']:
            for sp in node.iter(tag('tspan')):sp.set('x','148' if name.startswith('comment') else '142')
        if any(ord(c)>0xFFFF for c in s):
            # The source contains a private system-font lock glyph; preserve its meaning as a vector.
            spans=list(node.iter(tag('tspan')))
            if spans:
                x=float(spans[0].get('x','0'));y=float(spans[0].get('y','0'))
                for c in list(node):node.remove(c)
                node.tag=tag('g');node.attrib={'transform':f'translate({x} {y-12})'}
                E.SubElement(node,tag('rect'),{'x':'2','y':'5','width':'8','height':'7','rx':'1.5','fill':'#737373'})
                E.SubElement(node,tag('path'),{'d':'M4 5V3a2 2 0 014 0v2','fill':'none','stroke':'#737373','stroke-width':'1.4'})

    if name in ['panel','panel-ru']:
        dots=[c for c in root.iter(tag('circle')) if c.get('r')=='4' and c.get('fill') in ['#FFA944','#FF33B1']]
        for i,c in enumerate(dots):c.set('fill',(['#d93298','#8b80ef','#459b95'] if name=='panel-ru' else ['#d79731','#8b80ef','#45a67b'])[i%3])

base=TTFont(Path(__file__).with_name('Inter.ttf'))
fonts={}
def getfont(weight):
    weight=int(weight)
    if weight not in fonts:
        f=instantiateVariableFont(base,{'wght':weight,'opsz':14},inplace=False)
        fonts[weight]=(f,f.getGlyphSet(),f.getBestCmap(),f['head'].unitsPerEm)
    return fonts[weight]

def outline(root):
    defs=E.Element(tag('defs'));root.insert(0,defs);used={}
    parents={c:p for p in root.iter() for c in p}
    for text in list(root.iter(tag('text'))):
        if not list(text.iter(tag('tspan'))):
            value=text.text or '';text.text=None
            E.SubElement(text,tag('tspan'),{'x':text.get('x','0'),'y':text.get('y','0')}).text=value
        rawweight=text.get('font-weight','400');weight={'bold':700,'normal':400}.get(rawweight,int(rawweight) if rawweight.isdigit() else 400);f,gs,cmap,units=getfont(weight)
        size=float(text.get('font-size','14'));spacing=text.get('letter-spacing','0em')
        spacing=float(spacing.replace('em',''))*size if 'em' in spacing else float(spacing.replace('px',''))
        attrs={k:v for k,v in text.attrib.items() if k in ['fill','stroke','opacity','transform','clip-path','filter']}
        group=E.Element(tag('g'),attrs)
        for span in text.iter(tag('tspan')):
            content=span.text or '';x=float(span.get('x','0'));y=float(span.get('y','0'))
            line=E.SubElement(group,tag('g'),{'transform':f'translate({x:g} {y:g}) scale({size/units:g} {-size/units:g})'})
            advance=0
            for char in content:
                gid=cmap.get(ord(char))
                if gid is None:advance+=units*.25;continue
                key=(weight,gid)
                if key not in used:
                    pen=SVGPathPen(gs);gs[gid].draw(pen);path=pen.getCommands();uid=f'gcg-{weight}-{len(used)}';used[key]=uid
                    E.SubElement(defs,tag('path'),{'id':uid,'d':path})
                E.SubElement(line,tag('use'),{'href':'#'+used[key],'x':f'{advance:g}'})
                advance+=f['hmtx'][gid][0]+spacing*units/size
        parent=parents[text];i=list(parent).index(text);parent.remove(text);parent.insert(i,group)
    return root

def finish(root,path,title):
    E.SubElement(root,tag('title')).text=title
    outline(root)
    E.ElementTree(root).write(path,encoding='unicode',xml_declaration=False)

def measure(node, value=None):
    raw=node.get('font-weight','400');weight={'bold':700,'normal':400}.get(raw,int(raw) if raw.isdigit() else 400)
    f,gs,cmap,units=getfont(weight);size=float(node.get('font-size','14'))
    spacing=node.get('letter-spacing','0em');spacing=float(spacing.replace('em',''))*size if 'em' in spacing else float(spacing.replace('px',''))
    value=''.join(node.itertext()) if value is None else value
    return sum(f['hmtx'][cmap[c]][0]*size/units+spacing for c in map(ord,value) if c in cmap)

from relayout import relayout
manifest={};geometry={}
for src in SRC.glob('*.svg'):
    if src.name.endswith('-raw.svg'):continue
    name=src.stem
    if name not in ['entry-en','entry-filled','entry-ru','extension-en','extension-ru','dashboard','projects','mobile-current','mobile-desktop','mobile-explanation','mobile-site','mobile-compose','mobile-thread','task-comment','task-form','tour-1','tour-2','tour-3','comment','environment','panel','panel-ru','comment-ru','kit-button','kit-button-hover','kit-input','kit-select','kit-reply','kit-avatar','kit-tag']:continue
    s=src.read_text();root=E.fromstring(s);mock(root,name);state_audit=[]
    if name.startswith('mobile'):
        # The physical display and the Figma canvas have slightly different
        # ratios. Fill the display viewport instead of letterboxing the SVG.
        root.set('preserveAspectRatio','none')
    if name in ['mobile-site','mobile-compose','mobile-thread']:
        # The native widget floats over a responsive furniture site, not a grey
        # placeholder. All interface and website lettering stays vector based.
        mobile=f'''<svg xmlns="{NS}" xmlns:xlink="{XL}" x="0" y="44" width="375" height="635" viewBox="0 0 375 635"><rect width="375" height="635" fill="#f6f4ee"/><text x="24" y="43" font-family="Inter" font-size="29" font-weight="500" fill="#242620">forma®</text><path d="M327 25h24m-24 7h24" stroke="#242620" stroke-width="1.5"/><text x="24" y="116" font-family="Inter" font-size="38" fill="#242620">Thoughtful spaces.</text><text x="24" y="161" font-family="Inter" font-size="38" fill="#242620">Everyday living.</text><text x="24" y="202" font-family="Inter" font-size="14" fill="#72746c">Interiors that feel like you.</text><image x="16" y="231" width="343" height="330" preserveAspectRatio="xMidYMid slice" xlink:href="{PHOTO}"/><text x="24" y="596" font-family="Inter" font-size="14" fill="#72746c">01 / A quiet place, Copenhagen</text></svg>'''
        background=next(n for n in root.iter(tag('rect')) if n.get('fill')=='#D0D5DD' and n.get('width')=='375')
        p=next(p for p in root.iter() if background in list(p));p.insert(list(p).index(background)+1,E.fromstring(mobile))
        background.set('fill','#f6f4ee')
        if name=='mobile-compose':
            reference=E.parse(SRC/'mobile-site.svg').getroot()
            bubble=next(n for n in reference.iter(tag('rect')) if n.get('x')=='245' and n.get('y')=='177')
            bubble_group=next(p for p in reference.iter() if bubble in list(p))
            filter_id=bubble_group.get('filter')[5:-1]
            shadow=copy.deepcopy(next(n for n in reference.iter(tag('filter')) if n.get('id')==filter_id))
            shadow.set('id','gc-cluster-shadow');next(root.iter(tag('defs'))).append(shadow)
            replacement=copy.deepcopy(bubble_group);replacement.set('filter','url(#gc-cluster-shadow)')
            old=next(n for n in root.iter(tag('rect')) if n.get('x')=='245' and n.get('y')=='177')
            parent=next(p for p in root.iter() if old in list(p));i=list(parent).index(old)
            label=list(parent)[i+1];parent.remove(old);parent.remove(label);parent.insert(i,replacement)
            state_audit.append({'kind':'comment-cluster','fill':'white','foreground':'#0F0E2B','shadow':True})
        if name=='mobile-thread':
            for parent in root.iter():
                for n in list(parent):
                    if n.get('stroke-dasharray'):parent.remove(n)
        pin_labels=[n for n in root.iter(tag('text')) if n.get('font-size') in ['18','20'] and ''.join(n.itertext()).strip() in INITIALS]
        for n,initial in zip(pin_labels,['D','S','O']):set_text(n,initial)
        for n in root.iter(tag('text')):
            if n.get('font-size')=='38':n.set('font-size','34')
        for n in root.iter(tag('text')):
            value=''.join(n.itertext()).strip()
            if name=='mobile-compose' and value=='Your comment':
                set_text(n,'Could we use a wider photo?');n.set('fill','#0F0E2B')
                parent=next(p for p in root.iter() if n in list(p))
                cursor=next(c for c in parent if c.tag==tag('rect') and c.get('x')=='28' and c.get('y')=='337')
                end=29+measure(n);cursor.set('x',f'{end+2:g}')
                state_audit.append({'kind':'caret','textEnd':end,'cursorX':end+2})
            if name=='mobile-compose' and value=='0/200':set_text(n,str(len('Could we use a wider photo?'))+'/200')
            if name=='mobile-thread' and value.startswith('Could we make'):
                set_text(n,'Could we use a wider photo?')
        for parent in root.iter():
            children=list(parent)
            for i,n in enumerate(children):
                if n.tag==tag('text') and ''.join(n.itertext()).strip()=='Olivia Bennett':
                    initials=[t for t in children[max(0,i-3):i] if t.tag==tag('text') and len(''.join(t.itertext()).strip())==1]
                    if initials:set_text(initials[-1],'O')
        if name=='mobile-compose':
            for parent in root.iter():
                children=list(parent)
                for i,n in enumerate(children):
                    if n.tag==tag('rect') and n.get('x')=='315' and n.get('y')=='421':
                        n.set('fill','#5E5CE6');children[i+1].set('fill','white')
                        state_audit.append({'kind':'send-button','state':'enabled','fill':'#5E5CE6','foreground':'white'})
    if name=='task-comment':
        # Open the relevant menu item without the unrelated status submenu.
        for n in list(root):
            if n.tag==tag('g') and any(''.join(t.itertext()).strip()=='Rejected' for t in n.iter(tag('text'))):root.remove(n)
        for n in root.iter(tag('text')):
            value=''.join(n.itertext()).strip()
            if value=='@Sofia':set_text(n,'')
            if value.startswith('Could we use'):
                for sp,line in zip(n.iter(tag('tspan')),['Could we use the wider photo here?','Please check the attached reference.']):sp.text=line
            if value=='Add task':n.set('fill','#5E5CE6');n.set('font-weight','600')
            if value=='Admin':set_text(n,'Commenter')
        for n in list(root):
            if n.tag==tag('path') and n.get('d','').startswith(('M250 73','M250 75')):root.remove(n)
    if name=='task-form':
        for n in root.iter(tag('text')):
            value=''.join(n.itertext()).strip()
            if value=='Name the task':set_text(n,'Use wider living room photo');n.set('fill','#0F0E2B')
            elif value=='Link' and n.get('font-size')=='14':set_text(n,'forma.studio/living')
            elif value.startswith('Set the task and'):
                for sp,line in zip(n.iter(tag('tspan')),['Send this comment to your connected task tracker.','The page, environment and files stay with the task.']):sp.text=line
            elif value.startswith('Could we make'):
                for sp,line in zip(n.iter(tag('tspan')),['Use the wider photo from the attached reference.','Source: forma.studio/living · Chrome 133 · macOS 15.3','Viewport: 1440 × 900 · Screen: 1512 × 982']):sp.text=line
            elif value=='100':set_text(n,'2')
            elif value=='100 Gb':set_text(n,'422 KB')
            elif value=='File.pdf':set_text(n,'brief.pdf')
        # Two genuine attachments are enough to tell the scenario.
        for group in root.iter(tag('g')):
            cs=list(group)
            if not any(n.tag==tag('text') and ''.join(n.itertext()).strip()=='PDF' for n in cs):continue
            for n in cs:
                if n.tag==tag('text'):
                    yy=float(next(n.iter(tag('tspan'))).get('y','0'))
                elif n.tag==tag('rect'):yy=float(n.get('y','0'))
                elif n.tag==tag('path'):
                    from relayout import path_bounds
                    bounds=path_bounds(n);yy=bounds[1] if bounds else 0
                else:continue
                if yy>561:group.remove(n)
        first_size=next((n for n in root.iter(tag('text')) if ''.join(n.itertext()).strip()=='284 KB'),None)
        if first_size is not None:set_text(first_size,'138 KB')
    geometry[name]=relayout(root,name,measure)+state_audit
    manifest[name]=[''.join(n.itertext()) for n in root.iter(tag('text'))]
    # Replace source raster fills with properly proportioned local vector artwork.
    images={im.get('id'):im for im in root.iter(tag('image')) if im.get('id')}
    for pattern in root.iter(tag('pattern')):
        ref=next(pattern.iter(tag('use')),None)
        if ref is None:continue
        image=images.get(ref.get('{'+XL+'}href','').lstrip('#'))
        if image is None:continue
        value=image.get('{'+XL+'}href',image.get('href',''))
        if not value.startswith('GC_MOCK_IMAGE'):continue
        index=int(value.rsplit('_',1)[-1])
        if name=='dashboard':
            fill=data(BROWSER_ICONS[index%4]);w,h=64,64
        elif name in ['comment','comment-ru','task-form']:
            fill=PHOTO;w,h=1440,960
        elif name.startswith('entry') and index==1:
            fill=HAND;w,h=641,634
        elif name.startswith('entry') or name.startswith('extension'):
            # Remove the puzzle entirely, keeping the extension card intact.
            parent_map={c:p for p in root.iter() for c in p}
            for element in list(root.iter()):
                if element.get('fill')=='url(#'+pattern.get('id')+')':parent_map[element].remove(element)
            for child in list(pattern):pattern.remove(child)
            continue
        else:
            fill=data(website(variant=1 if name=='projects' and index>=2 else 0));w,h=1440,900
        pattern.attrib.pop('patternContentUnits',None)
        pattern.set('viewBox',f'0 0 {w} {h}')
        pattern.set('preserveAspectRatio','xMidYMid slice')
        for c in list(pattern):pattern.remove(c)
        E.SubElement(pattern,tag('image'),{'width':str(w),'height':str(h),'preserveAspectRatio':'xMidYMid slice','{'+XL+'}href':fill})
        image.set('{'+XL+'}href',fill)
    if name.startswith('tour'):
        for rect in root.iter(tag('rect')):
            if rect.get('height')=='5889':rect.set('height','900')
    parents={c:p for p in root.iter() for c in p}
    for image in images.values():
        if image in parents:parents[image].remove(image)
    # Build sharp, self-contained images for normal rendering and full-size zoom.
    finish(root,OUT/(name+'.svg'),f'{name} · демонстрационные данные GoComment')
    print('Prepared',name)

(OUT/'mock-data.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(OUT/'layout-audit.json').write_text(json.dumps(geometry,ensure_ascii=False,indent=2))

# Original button sizing and colors; text width determines the container width.
for state,fill,foreground in [('default','#5E5CE6','#FFFFFF'),('hover','#514FE3','#FFFFFF'),('pressed','#403DE1','#FFFFFF'),('focused','#5E5CE6','#FFFFFF'),('disabled','#8B89FC','#D1D1FF')]:
    root=E.parse(SRC/'kit-button.svg').getroot()
    label=next(root.iter(tag('text')));set_text(label,'Button')
    width=round(measure(label)+24,3)
    root.set('width',str(width));root.set('viewBox',f'0 0 {width} 44')
    rect=next(root.iter(tag('rect')));rect.set('width',str(width));rect.set('fill',fill)
    if state=='focused':rect.set('stroke','#403DE1');rect.set('stroke-width','2');rect.set('x','1');rect.set('y','1');rect.set('height','42');rect.set('width',str(width-2))
    label.set('fill',foreground)
    finish(root,OUT/f'kit-button-{state}.svg','Button / '+state)

# A vector website replaces empty grey canvases in the source widget compositions.
web=E.fromstring(website());finish(web,OUT/'forma-site.svg','Демонстрационный сайт Forma Living')

# Figma variables editor, based on the real collection and mode names from the library.
for mode in ['theme','language']:
    colors=mode=='theme'
    rows=[('basics/Primary/09','#403DE1','#07383D'),('basics/Primary/08','#514FE3','#0D6A73'),('basics/Primary/07','#5E5CE6','#1294A1'),('basics/Primary/06','#8B89FC','#14A9B8'),('basics/Accent/07','#FF8A00','#FF009D')] if colors else [('buttons/Next','Next','Далее'),('buttons/Cancel','Cancel','Отменить'),('buttons/Back','Back','Назад'),('buttons/Save','Save','Сохранить'),('buttons/Leave a comment','Leave a comment','Оставить комментарий')]
    svg=f'<svg xmlns="{NS}" width="1120" height="560" viewBox="0 0 1120 560"><rect x="1" y="1" width="1118" height="558" rx="16" fill="#fff" stroke="#e2e2e5"/><path d="M1 61H1119M239 61V559" stroke="#e9e9eb"/><text x="28" y="38" font-family="Inter" font-size="17" font-weight="600" fill="#262626">Variables</text><text x="920" y="38" font-family="Inter" font-size="14" fill="#777">GoComment UI Kit</text><text x="26" y="104" font-family="Inter" font-size="14" fill="#777">Collections</text>'
    for i,label in enumerate(['theme','tokens','language']):
        y=142+i*50
        if label==mode:svg+=f'<rect x="12" y="{y-26}" width="214" height="40" rx="7" fill="#f0eaff"/>'
        svg+=f'<path d="M31 {y-13}l7-4 7 4-7 4Z M31 {y-6}l7 4 7-4" fill="none" stroke="{"#9747FF" if label==mode else "#777"}" stroke-width="1.4"/><text x="60" y="{y}" font-family="Inter" font-size="16" fill="#333">{label}</text>'
    svg+=f'<text x="270" y="108" font-family="Inter" font-size="18" font-weight="600" fill="#333">{mode}</text><rect x="970" y="82" width="112" height="34" rx="6" fill="#f3f3f5"/><text x="994" y="104" font-family="Inter" font-size="14" fill="#555">+ Variable</text><rect x="240" y="140" width="879" height="45" fill="#fafafa"/><text x="270" y="168" font-family="Inter" font-size="14" fill="#777">Name</text><text x="654" y="168" font-family="Inter" font-size="14" fill="#777">{ "pluto" if colors else "eng" }</text><text x="873" y="168" font-family="Inter" font-size="14" fill="#777">{ "venus" if colors else "ru" }</text>'
    for i,(key,a,b) in enumerate(rows):
        y=225+i*59
        svg+=f'<path d="M240 {y+22}H1119" stroke="#ededee"/><text x="270" y="{y}" font-family="Inter" font-size="15" fill="#444">{key}</text>'
        for x,value in [(650,a),(869,b)]:
            if colors:svg+=f'<rect x="{x}" y="{y-17}" width="20" height="20" rx="4" fill="{value}"/><text x="{x+30}" y="{y}" font-family="Inter" font-size="15" fill="#555">{value}</text>'
            else:svg+=f'<text x="{x}" y="{y}" font-family="Inter" font-size="15" fill="#555">{value}</text>'
    svg+='</svg>'
    finish(E.fromstring(svg),OUT/('variables-'+mode+'.svg'),'Переменные Figma: '+mode)
print('All vector assets prepared')

# Local initials on the original vector pin.
r=E.parse(ROOT/'assets/gocomment/comment-pin.svg').getroot()
for n in list(r):
 if n.tag==tag('path') and n.get('fill')=='white':r.remove(n)
t=E.SubElement(r,tag('text'),{'fill':'white','font-family':'Inter','font-size':'20'})
E.SubElement(t,tag('tspan'),{'x':'27','y':'40'}).text='O'
finish(r,OUT/'pin.svg','Комментарий Оливии')
# Full sources stay available for zoom; these crops bring the relevant controls closer.
for source,name,box in [('entry-en','entry-focus','535 285 640 365'),('entry-filled','entry-filled-focus','535 285 640 365'),('extension-en','extension-focus','295 130 1125 730'),('entry-ru','entry-ru-focus','535 285 640 365'),('tour-2','tour-2-focus','760 390 680 510'),('tour-3','tour-3-focus','760 390 680 510'),('mobile-desktop','mobile-switch','0 490 375 195')]:
 r=E.parse(OUT/(source+'.svg')).getroot();r.set('viewBox',box);nums=box.split();r.set('width',nums[2]);r.set('height',nums[3]);E.ElementTree(r).write(OUT/(name+'.svg'),encoding='unicode')
