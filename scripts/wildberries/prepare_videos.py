"""Make self-hosted H.264 demos and first-frame posters from the Buildin originals.

Run with Python, passing the path to an ffmpeg executable as the first argument.
Original recordings stay in sources/wildberries/originals (excluded from Git).
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
FFMPEG = sys.argv[1]
ORIGINALS = ROOT / 'sources/wildberries/originals'
OUT = ROOT / 'assets/wildberries'


def prepare(source):
    label = source.stem
    destination = OUT / 'videos' / f'{label}.mp4'
    subprocess.run([
        FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(source),
        '-an', '-map_metadata', '-1', '-vf', 'scale=min(1600\\,iw):-2,fps=30',
        '-c:v', 'libx264', '-preset', 'medium', '-crf', '23',
        '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(destination)
    ], check=True)
    poster = OUT / 'posters' / f'{label}.webp'
    subprocess.run([
        FFMPEG, '-hide_banner', '-loglevel', 'error', '-y', '-ss', '0.2',
        '-i', str(destination), '-frames:v', '1', '-q:v', '85', str(poster)
    ], check=True)
    print(label, destination.stat().st_size, flush=True)
    return {'name': label, 'bytes': destination.stat().st_size,
            'original': source.name, 'poster': f'posters/{label}.webp',
            'video': f'videos/{label}.mp4'}


with ThreadPoolExecutor(max_workers=2) as executor:
    result = list(executor.map(prepare, sorted(ORIGINALS.iterdir())))
(OUT / 'video-manifest.json').write_text(
    json.dumps(result, ensure_ascii=False, indent=2) + '\n'
)
