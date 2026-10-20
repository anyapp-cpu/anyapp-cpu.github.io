"""Restore a Figma vector's per-region paints, omitted by the SVG exporter.

The JSON input is read-only Plugin API data for a source chart node.
The original document is never changed. Paths and colors remain the author's.
"""
from pathlib import Path
import json
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
data = json.loads(Path(sys.argv[1]).read_text())
filled = [r for r in data['vectorNetwork']['regions'] if r.get('fills')]
paths = data['vectorPaths'][:len(filled)]
assert len(filled) == 10 and len(paths) == 10
is_dashboard = data['id'] == '3158:19358'
group_id = 'dashboard-chart-repaired' if is_dashboard else 'skills-chart-repaired'
x, y = (data['x'], data['y']) if is_dashboard else (1384, 184)
group = ET.Element(f'{{{SVG}}}g', {'id': group_id, 'transform': f'translate({x} {y})'})
for path, region in zip(paths, filled):
    color = region['fills'][0]['color']
    rgb = '#'+''.join(f'{round(color[c]*255):02x}' for c in ('r', 'g', 'b'))
    ET.SubElement(group, f'{{{SVG}}}path', {'d': path['data'], 'fill': rgb,
                  'stroke': '#ffffff', 'stroke-width': str(data['strokeWeight']),
                  'fill-rule': 'nonzero'})
target = ROOT / 'assets/moscow/vectors' / ('dashboard.svg' if is_dashboard else 'skills.svg')
tree = ET.parse(target)
root = tree.getroot()
# The export includes its canvas grey behind the screen. Use the screen's own
# background beneath the blur so transparency at the edges does not darken it.
if len(root) and root[0].tag == f'{{{SVG}}}rect': root[0].set('fill', '#F2F2F2')
for element in list(root):
    if element.attrib.get('id') == group_id: root.remove(element)
root.append(group)
# Figma uses an HTML backdrop-filter inside foreignObject. Image-mode SVG does
# not render that backdrop. Keep its original 12px blur with a native SVG filter.
for parent in list(root.iter()):
    children = list(parent)
    foreign = next((c for c in children if c.tag.endswith('foreignObject')), None)
    if foreign is None: continue
    background = ET.Element(f'{{{SVG}}}g', {'filter': 'url(#skills-background-blur)'})
    for child in children[:children.index(foreign)]:
        parent.remove(child)
        background.append(child)
    parent.remove(foreign)
    parent.insert(0, background)
    defs = root.find(f'{{{SVG}}}defs')
    effect = ET.SubElement(defs, f'{{{SVG}}}filter', {'id': 'skills-background-blur',
        'x': '-5%', 'y': '-5%', 'width': '110%', 'height': '110%',
        'color-interpolation-filters': 'sRGB'})
    ET.SubElement(effect, f'{{{SVG}}}feGaussianBlur', {'stdDeviation': '12', 'edgeMode': 'duplicate'})
tree.write(target, encoding='unicode')
print('Restored all 10 original chart regions with their source colors.')
