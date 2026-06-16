#!/usr/bin/env python3
"""Re-tier flat ## headings into part/chapter/subhead, build book.md for pandoc.

Also converts inline citation blockquotes into real (bottom-of-page) footnotes:
each superscript body marker becomes a pandoc footnote reference [^fnN] and the
citation text (from footnotes.json, keyed by N) becomes its definition. The
citation text lives in the gitignored data file, not in this script.
"""
import json
import os
import re

src = open("Hizmetin_Esaslari_RU_clean.md", encoding="utf-8").read()

# Footnote citation map {N(int): text}; absent file -> keep markers as plain text.
FN = {}
if os.path.exists("footnotes.json"):
    FN = {int(k): v for k, v in json.load(open("footnotes.json", encoding="utf-8")).items()}

# Drop the hand-written front-matter block (title + source note + hr) — pandoc
# generates a proper title page and TOC instead.
src = re.sub(r"\A# .*?\n---\n", "", src, count=1, flags=re.S).lstrip()

PART = re.compile(r"\bРАЗДЕЛ\b")                  # whole word, NOT «РАЗДЕЛЕНИЕ»
NUM = re.compile(r"^\d+\.")                        # 1. ... 23. ...
LETTER = re.compile(r"^[A-ZА-Я]\.\s")             # A. ...  B. ...  H. ...
TOP = re.compile(r"^(ВВЕДЕНИЕ|ЗАКЛЮЧЕНИЕ|ПРЕДИСЛОВИЕ)\b")  # top-level sections

# Spelled-out ordinals -> digits, so part dividers read «РАЗДЕЛ 1: …»
ORD = {"ПЕРВЫЙ": 1, "ВТОРОЙ": 2, "ТРЕТИЙ": 3, "ЧЕТВЁРТЫЙ": 4, "ЧЕТВЕРТЫЙ": 4,
       "ПЯТЫЙ": 5, "ШЕСТОЙ": 6, "СЕДЬМОЙ": 7}
_ord_re = re.compile(r"^(" + "|".join(ORD) + r")\s+РАЗДЕЛ\b")


def renumber_part(t):
    m = _ord_re.match(t)
    if not m:
        return t
    return _ord_re.sub(f"РАЗДЕЛ {ORD[m.group(1)]}", t)


FN_BLOCKQUOTE = re.compile(r"^> *(Сноск[аи]|[⁰¹²³⁴⁵⁶⁷⁸⁹])")  # inline citation lines

out = []
for line in src.splitlines():
    if FN_BLOCKQUOTE.match(line):
        continue                      # drop inline citation; re-emitted as footnote
    m = re.match(r"^## (.+)$", line)
    if not m:
        out.append(line)
        continue
    t = m.group(1).strip()
    if PART.search(t) or TOP.match(t):
        out.append(f"# {renumber_part(t)}")   # h1 = part divider (own page)
    elif NUM.match(t) or LETTER.match(t):
        out.append(f"## {t}")         # h2 = chapter (new page)
    else:
        out.append(f"### {t}")        # h3 = inline subhead (no break)
out = "\n".join(out)

# Body superscript markers -> footnote references [^fnN] (real bottom-of-page
# footnotes). Fall back to a plain ^N^ superscript if N has no citation.
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
used = []


def _marker(m):
    n = int(m.group().translate(SUP))
    if n in FN:
        used.append(n)
        return f"[^fn{n}]"
    return "^" + m.group().translate(SUP) + "^"


out = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", _marker, out)

# Append footnote definitions for every referenced marker.
if used:
    defs = "\n\n" + "\n\n".join(f"[^fn{n}]: {FN[n]}" for n in sorted(set(used)))
    out = out.rstrip() + "\n" + defs + "\n"
missing = sorted(set(FN) - set(used))   # citations with no in-text marker (orphans)

# Arabic runs -> raw-LaTeX \AR{...} so they render in the Arabic fallback font
# (PT Serif has no Arabic block). Includes Arabic + supplement + diacritics.
out = re.sub(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+(?:\s+[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]+)*",
             lambda m: "\\AR{" + m.group() + "}", out)

with open("book.md", "w", encoding="utf-8") as f:
    f.write(out)

parts = out.count("\n# ") + out.startswith("# ")
chaps = out.count("\n## ")
subs = out.count("\n### ")
print(f"parts(h1)={parts}  chapters(h2)={chaps}  subheads(h3)={subs}")
print(f"footnotes: {len(set(used))} referenced; orphan citations (no marker): {missing}")
