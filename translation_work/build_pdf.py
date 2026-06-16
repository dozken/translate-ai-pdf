#!/usr/bin/env python3
"""Re-tier flat ## headings into part/chapter/subhead, build book.md for pandoc."""
import re

src = open("Hizmetin_Esaslari_RU_clean.md", encoding="utf-8").read()

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


out = []
for line in src.splitlines():
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

# Unicode superscript digits (footnote markers ⁷¹/⁷²) -> pandoc ^N^ superscript,
# so the PDF font renders them (PT Serif lacks U+2070–2079 glyphs).
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
out = re.sub(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+", lambda m: "^" + m.group().translate(SUP) + "^", out)

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
