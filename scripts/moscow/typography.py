# -*- coding: utf-8 -*-
"""Apply Russian nonbreaking spaces and hyphens to human-readable case text.

HTML structure, asset filenames, IDs and URLs are kept byte-for-byte intact.
Run again after editing copy: python3 scripts/moscow/typography.py
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / 'moscow.html'
WORDS = '''в во на с со из изо к ко о об обо у по от ото до за для при
над надо под подо перед передо про без безо через между около после вместо
кроме вокруг вдоль мимо ради сквозь среди благодаря вопреки согласно
относительно насчёт вследствие посредством путём навстречу вне внутри возле
против помимо посреди вблизи ввиду насчет наподобие вслед наперекор и а но не ни'''.split()
WORDS += ['из‑за', 'из‑под']
PREPOSITION = re.compile(r'(?<![\w‑])(' + '|'.join(sorted(WORDS, key=len, reverse=True)) + r')[ \t\u00a0]+(?=\S)', re.I)
HYPHEN = re.compile(r'(?<=\w)-(?=\w)')
ATTR = re.compile(r'\b(alt|aria-label|data-caption|data-label)="([^"]*)"')
COMPOUND_WORDS = ['на протяжении', 'в течение', 'в качестве', 'в рамках',
                  'за счёт', 'за счет', 'по поводу', 'по мере', 'по отношению к',
                  'в зависимости от', 'несмотря на', 'в соответствии с']
COMPOUND = re.compile(r'(?<![\w‑])(' + '|'.join(
    r'[ \t\u00a0]+'.join(phrase.split()) for phrase in COMPOUND_WORDS
) + r')[ \t\u00a0]+(?=\S)', re.I)


def typography(text):
    text = HYPHEN.sub('‑', text)
    text = COMPOUND.sub(lambda m: re.sub(r'[ \t\u00a0]+', '\u00a0', m[0]), text)
    text = PREPOSITION.sub(lambda m: m[1] + '\u00a0', text)
    return text


parts = re.split(r'(<[^>]+>)', TARGET.read_text())
for index, part in enumerate(parts):
    if part.startswith('<'):
        parts[index] = ATTR.sub(lambda m: f'{m[1]}="{typography(m[2])}"', part)
    else:
        parts[index] = typography(part)
TARGET.write_text(''.join(parts))
print('Updated visible copy and accessible captions; paths and HTML attributes preserved.')
