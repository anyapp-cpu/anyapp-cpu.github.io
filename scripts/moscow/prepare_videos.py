"""Prepare the thirteen author-supplied Moscow videos for the case page.

Run: python3 scripts/moscow/prepare_videos.py /absolute/path/to/ffmpeg
Originals stay in «видео ПМ». The manifest records the exact source for each demo.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = sys.argv[1]
OUT = ROOT / 'assets/moscow'
TRIM_ENDS = {'bot': 14.0}
MAPPING = [
    ('home', 'главная финал.mp4', 'Главная страница'),
    ('test', 'тест.mp4', 'Тест «Путь мечты»'),
    ('favorites', 'корзина.mp4', 'Избранные вакансии и подбор'),
    ('atlas', 'Запись экрана 2025-08-05 в 18.46.59.mov', 'Атлас направлений'),
    ('residency', 'резидентство.mp4', 'Резидентство'),
    ('dashboard', '1 уровень.mp4', 'Личный кабинет первого уровня'),
    ('calendar', 'адвент.mp4', 'Адвент-календарь'),
    ('offline', 'Запись экрана 2025-08-05 в 19.10.20.mov', 'Офлайн-задание'),
    ('achievements', 'ачивки и активность.mp4', 'Достижения и активность'),
    ('level-three', '3 уровень.mp4', 'Подготовка к стажировке'),
    ('bot', 'чат-бот.mov', 'Telegram-бот'),
    ('resume', 'резюме2.mp4', 'Конструктор резюме'),
    ('return', 'фора (online-video-cutter.com).mp4', 'Фора для следующего набора'),
]
for folder in ('videos', 'posters'):
    (OUT / folder).mkdir(parents=True, exist_ok=True)


def run(args):
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', *args], check=True)


def prepare(item):
    name, filename, section = item
    source = ROOT / 'видео ПМ' / filename
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    trim_end = TRIM_ENDS.get(name)
    stem = f'{name}-{digest[:8]}' + (f'-trim{trim_end:g}' if trim_end else '')
    mp4 = OUT / 'videos' / f'{stem}.mp4'
    webm = OUT / 'videos' / f'{stem}.webm'
    poster = OUT / 'posters' / f'{stem}.webp'
    info = subprocess.run([FFMPEG, '-hide_banner', '-i', str(source)], capture_output=True, text=True).stderr
    w, h = map(int, re.search(r'Video:.*? (\d{3,5})x(\d{3,5})', info).groups())
    duration = re.search(r'Duration: (\d+):(\d+):([\d.]+)', info)
    source_seconds = sum(float(v) * m for v, m in zip(duration.groups(), [3600, 60, 1]))
    seconds = min(source_seconds, trim_end) if trim_end else source_seconds
    common = ['-i', str(source), *(['-t', str(trim_end)] if trim_end else []), '-an', '-map_metadata', '-1',
              '-vf', 'scale=min(1600\\,iw):-2,fps=30', '-pix_fmt', 'yuv420p']
    if not mp4.exists():
        run([*common, '-c:v', 'libx264', '-profile:v', 'baseline', '-level:v', '4.0',
             '-preset', 'medium', '-crf', '22', '-tag:v', 'avc1', '-movflags', '+faststart', str(mp4)])
    if not webm.exists():
        run([*common, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32',
             '-deadline', 'realtime', '-cpu-used', '6', '-row-mt', '1', str(webm)])
    # Choose a useful frame for demos that begin with a transition.
    poster_time = {'calendar': 7, 'atlas': 20, 'offline': 5}.get(name, 0.5)
    run(['-ss', str(poster_time), '-i', str(mp4), '-frames:v', '1', '-q:v', '85', str(poster)])
    for video in (mp4, webm):
        run(['-i', str(video), '-f', 'null', '-'])
    print(f'{name}: encoded and decoded', flush=True)
    return {'name': name, 'section': section, 'original': str(source.relative_to(ROOT)),
            'sourceSha256': digest, 'duration': seconds, 'sourceWidth': w, 'sourceHeight': h,
            **({'sourceDuration': source_seconds, 'trimEnd': trim_end} if trim_end else {}),
            'video': f'videos/{mp4.name}', 'webm': f'videos/{webm.name}',
            'poster': f'posters/{poster.name}', 'bytes': mp4.stat().st_size, 'webmBytes': webm.stat().st_size}


selected = set(sys.argv[2:])
assert selected <= {item[0] for item in MAPPING}, 'Unknown video name'
mapping = [item for item in MAPPING if not selected or item[0] in selected]
with ThreadPoolExecutor(max_workers=2) as pool:
    prepared = list(pool.map(prepare, mapping))
if selected:
    previous = json.loads((OUT / 'video-manifest.json').read_text())
    updated = {v['name']: v for v in [*previous, *prepared]}
    videos = [updated[item[0]] for item in MAPPING]
else:
    videos = prepared
(OUT / 'video-manifest.json').write_text(json.dumps(videos, ensure_ascii=False, indent=2) + '\n')
print(f'Prepared {len(prepared)} videos; manifest contains {len(videos)}.', flush=True)
