#!/usr/bin/env python3
"""Translation work manager — resumable book translation.

Files (all in this dir):
  paragraphs.json  canonical source units [{id,type,text,page}]  (immutable)
  state.json       progress {next_id, completed_ids, ...}
  Hizmetin_Esaslari_RU.md   output, appended in id order
  batch_in.json    {id: "<russian text>"} written by the translator, consumed by `commit`

Usage:
  python tw.py next [N]      -> print next N untranslated source units as JSON
  python tw.py commit        -> append translations from batch_in.json, advance state
  python tw.py status        -> progress summary
"""
import json
import sys
import datetime
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda n: os.path.join(HERE, n)


def load(n):
    return json.load(open(P(n), encoding="utf-8"))


def save(n, obj):
    json.dump(obj, open(P(n), "w", encoding="utf-8"), ensure_ascii=False, indent=(1 if n == "paragraphs.json" else 2))


def cmd_next(n=8):
    paras = load("paragraphs.json")
    st = load("state.json")
    nxt = st["next_id"]
    batch = [p for p in paras if p["id"] >= nxt][:n]
    print(json.dumps(batch, ensure_ascii=False, indent=1))


def cmd_commit():
    paras = {p["id"]: p for p in load("paragraphs.json")}
    st = load("state.json")
    trans = load("batch_in.json")
    # Keys may be str; normalize to int and require a contiguous run from next_id
    items = sorted((int(k), v) for k, v in trans.items())
    expected = st["next_id"]
    out_lines = []
    committed = []
    for pid, ru in items:
        if pid != expected:
            raise SystemExit(f"Non-contiguous id {pid}, expected {expected}. Fix batch_in.json.")
        src = paras[pid]
        ru = ru.strip()
        if src["type"] == "heading":
            out_lines.append(f"<!-- #{pid} -->\n## {ru}\n")
        else:
            out_lines.append(f"<!-- #{pid} -->\n{ru}\n")
        committed.append(pid)
        expected += 1
    with open(P("Hizmetin_Esaslari_RU.md"), "a", encoding="utf-8") as f:
        f.write("\n".join(out_lines) + "\n")
    st["next_id"] = expected
    st["completed_ids"] = st.get("completed_ids", []) + committed
    st["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    save("state.json", st)
    os.remove(P("batch_in.json"))
    write_progress()
    print(f"Committed {len(committed)} units (#{committed[0]}..#{committed[-1]}). next_id={st['next_id']}/{st['total']}")


def write_progress():
    """Render a human-readable PROGRESS.md (watch this file while the loop runs)."""
    st = load("state.json")
    done, total = st["next_id"], st["total"]
    pct = 100 * done / total if total else 0
    filled = int(pct // 5)
    bar = "█" * filled + "░" * (20 - filled)
    out_chars = 0
    md = P("Hizmetin_Esaslari_RU.md")
    if os.path.exists(md):
        out_chars = len(open(md, encoding="utf-8").read())
    with open(P("PROGRESS.md"), "w", encoding="utf-8") as f:
        f.write("# Translation progress — Hizmetin Esasları → Russian\n\n")
        f.write(f"`{bar}` **{pct:.1f}%**\n\n")
        f.write(f"- Units translated: **{done} / {total}**\n")
        f.write(f"- Remaining: {total - done}\n")
        f.write(f"- Output size: {out_chars:,} chars\n")
        f.write(f"- Last update: {st['updated_at']}\n")
        f.write(f"- Status: {'DONE ✅' if done >= total else 'in progress…'}\n")


def cmd_status():
    st = load("state.json")
    done = st["next_id"]
    total = st["total"]
    pct = 100 * done / total if total else 0
    write_progress()
    print(f"{done}/{total} units ({pct:.1f}%) | next_id={done} | updated {st['updated_at']}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        cmd_status()
    elif a[0] == "next":
        cmd_next(int(a[1]) if len(a) > 1 else 8)
    elif a[0] == "commit":
        cmd_commit()
    elif a[0] == "status":
        cmd_status()
    else:
        raise SystemExit(__doc__)
