"""Content-aware layout for local SVG exports. Never writes to Figma."""
import math
import re
import xml.etree.ElementTree as E
from fontTools.pens.boundsPen import BoundsPen
from fontTools.svgLib.path import parse_path

NS = '{http://www.w3.org/2000/svg}'


def text(node):
    return ''.join(node.itertext()).strip()


def position(node):
    span = next(node.iter(NS + 'tspan'))
    return float(span.get('x', '0')), float(span.get('y', '0'))


def set_x(node, x):
    for span in node.iter(NS + 'tspan'):
        span.set('x', f'{x:g}')


def shift(node, dx):
    if abs(dx) > .01:
        node.set('transform', f'translate({dx:g} 0) ' + node.get('transform', ''))


def path_bounds(node):
    pen = BoundsPen(None)
    parse_path(node.get('d', ''), pen)
    return pen.bounds


def relayout(root, name, measure):
    audit = []
    parents = {child: parent for parent in root.iter() for child in parent}

    # Remember badge membership before any neighboring tabs move. Text and its
    # background must then be laid out together, including translated statuses.
    text_badges = []
    for parent in root.iter():
        children = list(parent)
        for i, rect in enumerate(children):
            if rect.tag != NS+'rect' or rect.get('transform') or not rect.get('rx'):
                continue
            x, y = float(rect.get('x', 0)), float(rect.get('y', 0))
            w, h = float(rect.get('width', 0)), float(rect.get('height', 0))
            if not (15 <= h <= 28 and 24 <= w <= 200) or float(rect.get('rx')) >= h/2:
                continue
            for label in children[i+1:i+3]:
                if label.tag != NS+'text' or re.fullmatch(r'\d+', text(label)):
                    continue
                tx, ty = position(label)
                if x <= tx < x+w and y+7 <= ty <= y+h+1:
                    text_badges.append((parent, rect, label, max(4, min(8, tx-x))))
                    break

    # Headers are real inline rows: icon | identifier | time | date.
    handled_times = set()
    for node in root.iter(NS + 'text'):
        if not text(node).startswith('GC-'):
            continue
        for span in node.iter(NS + 'tspan'):
            span.text = (span.text or '').strip()
        parent = parents[node]
        children = list(parent)
        i = children.index(node)
        if i < 1 or len(children) <= i + 4:
            continue
        before = children[i-1]
        middle, time, after, date = children[i+1:i+5]
        if not (before.tag == middle.tag == after.tag == NS + 'rect'
                and time.tag == date.tag == NS + 'text'):
            continue
        x = float(before.get('x')) + 8
        set_x(node, x)
        middle.set('x', f'{x + measure(node) + 8:g}')
        set_x(time, float(middle.get('x')) + 8)
        after.set('x', f'{position(time)[0] + measure(time) + 8:g}')
        set_x(date, float(after.get('x')) + 8)
        handled_times.add(time)
        audit.append({'kind': 'header', 'id': text(node), 'end': position(date)[0] + measure(date),
                      'identifierGap': 8, 'timeGap': 8})

    # Mobile cards have time | date, and the separator must follow the actual time.
    for node in root.iter(NS + 'text'):
        if node in handled_times or not re.fullmatch(r'\d{2}:\d{2}', text(node)):
            continue
        parent = parents[node]
        children = list(parent)
        i = children.index(node)
        if len(children) < i + 3:
            continue
        separator, date = children[i+1:i+3]
        if separator.tag == NS + 'rect' and separator.get('width') == '1' and date.tag == NS + 'text':
            separator.set('x', f'{position(node)[0] + measure(node) + 8:g}')
            set_x(date, float(separator.get('x')) + 8)

    # Recompute every compact numeric badge from its text, including icon badges.
    badges = []
    for parent in list(root.iter()):
        children = list(parent)
        for i, rect in enumerate(children):
            if rect.tag != NS + 'rect' or rect.get('transform'):
                continue
            x, y = float(rect.get('x', 0)), float(rect.get('y', 0))
            width, height = float(rect.get('width', 0)), float(rect.get('height', 0))
            if not (15 <= height <= 24 and 10 <= width <= 50 and rect.get('rx')):
                continue
            candidates = []
            for j in range(i + 1, min(i + 5, len(children))):
                n = children[j]
                if n.tag != NS + 'text' or not re.fullmatch(r'\d+', text(n)):
                    continue
                tx, ty = position(n)
                if x - 1 <= tx < x + width + 2 and y + 7 <= ty <= y + height + 1:
                    candidates.append((j, n))
            if not candidates:
                continue
            j, node = candidates[0]
            # Step indicators are fixed circles, never content-sized pills.
            if abs(width-height)<.01 and float(rect.get('rx'))>=height/2:
                set_x(node, x+(width-measure(node))/2)
                audit.append({'kind':'step-indicator','text':text(node),'width':width,'height':height,'centerX':x+width/2})
                continue
            icons = [n for n in children[i+1:j] if n.tag in [NS+'g', NS+'path']]
            # Four pixels of padding, 16px icon, 2px icon/text gap.
            new_width = max(16, math.ceil(measure(node) + (26 if icons else 8)))
            badges.append({'parent': parent, 'rect': rect, 'node': node, 'icons': icons,
                           'x': x, 'y': y, 'oldWidth': width, 'width': new_width, 'newX': x})

    # Keep groups of mention/reply badges right-aligned while hugging both counts.
    paired = set()
    for a in badges:
        peers = [b for b in badges if b['parent'] is a['parent'] and abs(b['y']-a['y']) < .1]
        peers.sort(key=lambda b: b['x'])
        if len(peers) != 2:
            continue
        first, second = peers
        if not first['icons'] or second['x'] - first['x'] - first['oldWidth'] > 10:
            continue
        end = second['x'] + second['oldWidth']
        second['newX'] = end - second['width']
        first['newX'] = second['newX'] - 6 - first['width']
        paired.update([id(first), id(second)])

    for b in badges:
        rect, node, x, width = b['rect'], b['node'], b['newX'], b['width']
        rect.set('x', f'{x:g}'); rect.set('width', str(width))
        for icon in b['icons']:
            shift(icon, x - b['x'])
        set_x(node, x + 22 if b['icons'] else x + (width - measure(node)) / 2)
        audit.append({'kind': 'badge', 'text': text(node), 'width': width,
                      'leftPadding': position(node)[0]-x, 'rightPadding': x+width-position(node)[0]-measure(node),
                      'icon': bool(b['icons'])})

    # User-count tabs shrink as a group, including the tabs that follow them.
    for b in badges:
        if b['icons'] or b['rect'].get('fill') != '#A6ACB8':
            continue
        children = list(b['parent']); i = children.index(b['rect'])
        if not i or children[i-1].tag != NS+'text' or text(children[i-1]) not in ['Users', 'Пользователи']:
            continue
        label = children[i-1]
        x = position(label)[0] + measure(label) + 6
        b['rect'].set('x', f'{x:g}')
        set_x(b['node'], x+(b['width']-measure(b['node']))/2)
        old_end = b['x']+b['oldWidth']
        delta = x+b['width']-old_end
        baseline = position(label)[1]
        for n in children[children.index(b['node'])+1:]:
            if n.tag == NS+'text' and abs(position(n)[1]-baseline)<2:
                set_x(n, position(n)[0]+delta)
            elif n.tag == NS+'rect' and n.get('height')=='2' and float(n.get('width',0))<250 and float(n.get('x',0))>old_end and baseline+4<float(n.get('y',0))<baseline+20:
                n.set('x', f'{float(n.get("x"))+delta:g}')

    # Fit mobile filter tabs, their counts and the active underline as one row.
    for parent in list(root.iter()):
        labels = [n for n in parent if n.tag == NS+'text' and text(n) in ['All', 'Mentions', 'Hidden content'] and position(n)[1] < 160]
        if len(labels) != 3:
            continue
        labels.sort(key=lambda n: position(n)[0])
        row_badges = [b for b in badges if b['parent'] is parent and abs(position(b['node'])[1] - position(labels[0])[1]) < 2]
        row_badges.sort(key=lambda b: b['x'])
        if len(row_badges) != 3:
            continue
        cursor = position(labels[0])[0]
        for label, b in zip(labels, row_badges):
            set_x(label, cursor)
            x = cursor + measure(label) + 6
            b['rect'].set('x', f'{x:g}')
            set_x(b['node'], x + (b['width']-measure(b['node']))/2)
            end = x + b['width']
            if text(label) == 'All':
                for n in parent:
                    if n.tag == NS+'rect' and n.get('height') == '2' and abs(float(n.get('x', 0))-cursor) < 1:
                        n.set('width', f'{end-cursor:g}')
            cursor = end + 16

    # A workspace title and its edit icon are also a single content-sized row.
    for node in root.iter(NS+'text'):
        if text(node) not in ['North Studio', 'Север / студия']:
            continue
        x, y = position(node)
        if not (300 <= x <= 320 and y < 45):
            continue
        children = list(parents[node]); i = children.index(node)
        icon = children[i+1] if len(children) > i+1 else None
        if icon is not None and icon.tag == NS+'path':
            bounds = path_bounds(icon)
            if bounds:
                shift(icon, x + measure(node) + 8 - bounds[0])
                audit.append({'kind': 'workspace', 'text': text(node), 'gap': 8})

    # Names, roles and initials must fit their actual content too.
    for node in root.iter(NS+'text'):
        parent = parents[node]
        if name.startswith('mobile') and text(node) in ['Commenter', 'Manager']:
            children = list(parent); i = children.index(node)
            if i and children[i-1].tag == NS+'text':
                author = children[i-1]
                set_x(node, position(author)[0] + measure(author) + 8)
        if len(text(node)) == 1 and text(node).isalpha():
            x, y = position(node)
            for background in parent:
                if background.tag != NS+'rect' or not background.get('rx'):
                    continue
                bx, by = float(background.get('x', 0)), float(background.get('y', 0))
                bw, bh = float(background.get('width', 0)), float(background.get('height', 0))
                if abs(bw-bh) < 1 and 20 <= bw <= 40 and bx <= x <= bx+bw and by <= y <= by+bh:
                    set_x(node, bx + (bw-measure(node))/2)
                    break

    # The complete account control is right-aligned, rather than placing the
    # chevron at a coordinate chosen for the original placeholder name.
    for node in root.iter(NS+'text'):
        if '@' not in text(node) or position(node)[1] > 55:
            continue
        children = list(parents[node]); i = children.index(node)
        if i < 4:
            continue
        avatar, initial, author, chevron = children[i-4:i]
        if not (avatar.tag == NS+'rect' and initial.tag == author.tag == NS+'text' and chevron.tag == NS+'path'):
            continue
        bounds = path_bounds(chevron)
        if not bounds:
            continue
        right = float(root.get('width', 1440))-24
        icon_x = right-(bounds[2]-bounds[0])
        shift(chevron, icon_x-bounds[0])
        tx = icon_x-12-max(measure(author), measure(node))
        set_x(author, tx); set_x(node, tx)
        ax = tx-44
        avatar.set('x', f'{ax:g}');set_x(initial, ax+(36-measure(initial))/2)
        assert icon_x-position(author)[0]-measure(author) >= 11.9
        audit.append({'kind':'profile', 'text':text(author), 'chevronGap':icon_x-position(author)[0]-measure(author), 'right':right})

    # Text badges hug the rendered wording too. Some are inline with a tab or
    # card heading; pack that whole row and extend its underline accordingly.
    badge_backgrounds = {label:rect for parent,rect,label,padding in text_badges}
    for parent, rect, label, padding in text_badges:
        children = list(parent); i = children.index(rect)
        preceding = children[i-1] if i else None
        x, y = position(label)
        if preceding is not None and preceding.tag == NS+'text':
            px, py = position(preceding)
            if abs(py-y) < 4:
                previous_badge=badge_backgrounds.get(preceding)
                end = float(previous_badge.get('x'))+float(previous_badge.get('width')) if previous_badge is not None else px+measure(preceding)
                x = end+8+padding
                set_x(label, x)
        width = math.ceil(measure(label)+padding*2)
        rect.set('x', f'{x-padding:g}');rect.set('width', str(width))
        end = x-padding+width
        if preceding is not None and preceding.tag == NS+'text' and text(preceding) in ['Widget','Виджет']:
            for following in children[children.index(label)+1:]:
                if following.tag == NS+'rect' and following.get('height') == '2':
                    following.set('x', f'{position(preceding)[0]:g}')
                    following.set('width', f'{end-position(preceding)[0]:g}')
                elif following.tag == NS+'text' and abs(position(following)[1]-y)<4:
                    set_x(following, end+24)
                    break
        assert end-position(label)[0]-measure(label) >= padding-.01
        audit.append({'kind':'text-badge','text':text(label),'width':width,'padding':padding})

    # The trial banner is centered as a full sentence, including its link.
    for node in root.iter(NS+'text'):
        if not ('days of Free Trial left.' in text(node) or text(node).startswith(('Осталось 10 дней','Мы выпустили браузерное','GoComment browser extension is now'))):
            continue
        children = list(parents[node]); i = children.index(node)
        row = children[i:i+3]
        if len(row) != 3 or any(n.tag != NS+'text' for n in row):
            continue
        width = sum(measure(n) for n in row) + 8
        cursor = (float(root.get('width', 1440))-width)/2
        for n in row:
            set_x(n, cursor)
            cursor += measure(n) + 4

    # The project-card statistics are compact groups, not three-digit text slots.
    if name == 'projects':
        for parent in root.iter(NS+'g'):
            children = list(parent)
            for i, label in enumerate(children):
                if label.tag != NS+'text' or text(label) != 'users' or i < 2 or len(children) <= i+4:
                    continue
                user_icon, count = children[i-2:i]
                divider, comment_icon, comment_count, comment_label = children[i+1:i+5]
                if user_icon.tag != NS+'path' or comment_icon.tag != NS+'path':
                    continue
                set_x(count, path_bounds(user_icon)[2] + 8)
                set_x(label, position(count)[0] + measure(count) + 6)
                dx = position(label)[0] + measure(label) + 12
                divider.set('x', f'{dx:g}')
                bounds = path_bounds(comment_icon)
                new_icon_x = dx + 13
                shift(comment_icon, new_icon_x - bounds[0])
                set_x(comment_count, new_icon_x + bounds[2]-bounds[0] + 8)
                set_x(comment_label, position(comment_count)[0] + measure(comment_count) + 6)
                audit.append({'kind': 'project-statistics', 'userGap': 6, 'commentGap': 6})
        for label in root.iter(NS+'text'):
            if text(label) not in ['Created', 'Last action']:
                continue
            children = list(parents[label]); i = children.index(label)
            if i == 0 or len(children) <= i+1:
                continue
            background, date = children[i-1], children[i+1]
            if background.tag != NS+'path' or background.get('fill') != 'white' or date.tag != NS+'text':
                continue
            x, y, right, bottom = path_bounds(background)
            set_x(date, position(label)[0] + measure(label) + 8)
            right = position(date)[0] + measure(date) + 8
            background.set('d', f'M{x+8:g} {y:g}H{right-8:g}Q{right:g} {y:g} {right:g} {y+8:g}V{bottom:g}H{x:g}V{y+8:g}Q{x:g} {y:g} {x+8:g} {y:g}Z')

    # Numerator / denominator pairs grow from the width of the numerator.
    for parent in root.iter():
        children = list(parent)
        for i, node in enumerate(children):
            if node.tag != NS+'text' or not re.fullmatch(r'/\d+', text(node)) or i == 0:
                continue
            before = children[i-1]
            if before.tag == NS+'text' and re.fullmatch(r'\d+', text(before)):
                gap = 8 if float(before.get('font-size', 14)) >= 20 else 4
                set_x(node, position(before)[0] + measure(before) + gap)
                audit.append({'kind': 'fraction', 'text': text(before)+text(node), 'gap': gap})

    # Attachment size follows the actual filename, with the same compact gap.
    for node in root.iter(NS+'text'):
        if text(node) not in ['284 KB', '284 КБ', '138 KB']:
            continue
        children = list(parents[node]); i = children.index(node)
        if i and children[i-1].tag == NS+'text':
            filename = children[i-1]
            set_x(node, position(filename)[0]+measure(filename)+8)
            audit.append({'kind': 'attachment', 'filename': text(filename), 'gap': 8})

    # Normalize status typography and use the original theme token for each dot.
    palettes = ['#FF33B1', '#14A9B8', '#5EB084'] if name.endswith('-ru') else ['#FFA944', '#8B89FC', '#5EB084']
    labels = ['На обсуждении', 'В работе', 'Решено'] if name.endswith('-ru') else ['To discuss', 'In progress', 'Resolved']
    for node in root.iter(NS+'text'):
        if text(node) not in labels:
            continue
        x, y = position(node)
        for dot in parents[node].iter(NS+'circle'):
            if dot.get('r') == '4' and abs(float(dot.get('cy')) - (y-4.364)) < 2:
                node.set('fill', '#667085')
                dot.set('fill', palettes[labels.index(text(node))])
                audit.append({'kind': 'status', 'text': text(node), 'color': palettes[labels.index(text(node))]})

    # Every badge must have balanced padding and fit its number after layout.
    for b in badges:
        x = float(b['rect'].get('x')); w = float(b['rect'].get('width'))
        right = x+w-position(b['node'])[0]-measure(b['node'])
        assert 3.4 <= right <= 6.5, (name, text(b['node']), right)
    return audit
