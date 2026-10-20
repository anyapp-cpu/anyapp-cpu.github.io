# -*- coding: utf-8 -*-
"""Prepare website videos from the author's local «видео Wildberries» folder.

Run: python3 scripts/wildberries/prepare_videos.py /absolute/path/to/ffmpeg
The explicit mapping follows the seven demonstrations in the original case.
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
ORIGINALS = ROOT / 'видео Wildberries'
OUT = ROOT / 'assets/wildberries'
MAPPING = [
    ('quick-actions', 'Запись экрана 2025-08-05 в 15.05.42.mov', 'Быстрые действия на главной'),
    ('cabinet', 'Запись экрана 2025-08-05 в 15.34.14.mov', 'Первый визит в рекламный кабинет'),
    ('sandbox', 'Запись экрана 2025-08-05 в 15.40.32.mov', 'Знакомство с учебным режимом'),
    ('creation', 'Запись экрана 2025-08-05 в 16.16.35.mov', 'Создание кампании, товары и бюджет'),
    ('bid-calculator', 'Запись экрана 2025-08-05 в 16.19.55.mov', 'Калькулятор ставки'),
    ('campaign', 'Запись экрана 2025-08-05 в 16.43.35 (online-video-cutter.com).mp4', 'Внутренняя страница кампании'),
    ('time-skip', 'Запись экрана 2025-08-05 в 16.43.35 (online-video-cutter.com) (1).mp4', 'Прокрутка времени и статистика'),
]
for folder in ['videos', 'posters']:
    (OUT / folder).mkdir(exist_ok=True)


def run(args):
    subprocess.run([FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', *args], check=True)


def prepare(item):
    name, filename, section = item
    source = ORIGINALS / filename
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    stem = f'{name}-{digest[:8]}-compat'
    mp4 = OUT / 'videos' / f'{stem}.mp4'
    webm = OUT / 'videos' / f'{stem}.webm'
    poster = OUT / 'posters' / f'{stem}.webp'
    common = ['-i', str(source), '-an', '-map_metadata', '-1',
              '-vf', 'scale=min(1600\\,iw):-2,fps=30', '-pix_fmt', 'yuv420p']
    run([*common, '-c:v', 'libx264', '-profile:v', 'baseline', '-level:v', '4.0',
         '-preset', 'medium', '-crf', '22', '-tag:v', 'avc1',
         '-movflags', '+faststart', str(mp4)])
    run([*common, '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '32',
         '-deadline', 'realtime', '-cpu-used', '6', '-row-mt', '1', str(webm)])
    run(['-ss', '0.2', '-i', str(mp4), '-frames:v', '1', '-q:v', '85', str(poster)])
    # Decode every generated video, rather than accepting a non-empty file alone.
    for video in [mp4, webm]:
        run(['-i', str(video), '-f', 'null', '-'])
    info = subprocess.run([FFMPEG, '-hide_banner', '-i', str(mp4)], capture_output=True, text=True).stderr
    duration = re.search(r'Duration: (\d+):(\d+):([\d.]+)', info)
    h, m, sec = map(float, duration.groups())
    print(name, 'encoded and decoded', flush=True)
    return {
        'name': name, 'section': section,
        'original': str(source.relative_to(ROOT)), 'sourceSha256': digest,
        'duration': h * 3600 + m * 60 + sec,
        'video': f'videos/{mp4.name}', 'webm': f'videos/{webm.name}',
        'poster': f'posters/{poster.name}', 'bytes': mp4.stat().st_size,
        'webmBytes': webm.stat().st_size,
    }


with ThreadPoolExecutor(max_workers=2) as executor:
    result = list(executor.map(prepare, MAPPING))
(OUT / 'video-manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print('Prepared seven mapped videos with MP4 + WebM sources.', flush=True)
