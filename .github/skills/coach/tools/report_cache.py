#!/usr/bin/env python3
"""report_cache.py — Report-Schreib- und Reproduzierbarkeits-Werkzeug
(Markdown und JSON). Baut auf fmlib auf.

Kein Cache: jeder `write`/`writejson`-Aufruf erzeugt bzw. ueberschreibt den
Report sofort mit frisch uebergebenen Fakten (`--facts`); es wird nie ein
vorhandener Report unveraendert wiederverwendet.

Reproduzierbarkeit: stabile `report_id`, `content_hash` ueber den Faktenteil
(Markdown: ohne Meta-Zeile; JSON: ohne meta.generated_at/meta.content_hash).
Bei gleichen Fakten liefern zwei Laeufe denselben `content_hash`, auch wenn
`generated_at` sich unterscheidet.

Unterbefehle: id | path | write | writejson | hash | hashjson |
verify | validate
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmlib  # noqa: E402


def _ext(fmt):
    return ".json" if fmt == "json" else ".md"


def _read(src):
    if src and src != "-":
        return Path(src).read_text(encoding="utf-8-sig")
    return sys.stdin.read()


# --------------------------- Unterbefehle ---------------------------

def cmd_id(a):
    print(fmlib.make_report_id(a.subject, a.season, a.week)); return 0


def cmd_path(a):
    rid = fmlib.make_report_id(a.subject, a.season, a.week)
    print(str(Path(a.report_dir) / (rid + _ext(a.format)))); return 0


def cmd_write(a):
    rid = fmlib.make_report_id(a.subject, a.season, a.week)
    p = Path(a.report_dir) / (rid + ".md")
    facts = _read(a.facts)
    lines = facts.replace("\r\n", "\n").lstrip("\ufeff").split("\n")
    if not lines or not lines[0].strip():
        print("Fehler: erste Zeile muss der Titel sein.", file=sys.stderr); return 2
    chash = fmlib.content_hash_text(facts)
    generated_at = a.generated_at or a.as_of or fmlib.now_iso()
    meta = fmlib.META_PREFIX + " {} | generated_at: {} | content_hash: {}".format(
        rid, generated_at, chash)
    out = fmlib.normalize(lines[0] + "\n" + meta + "\n" + "\n".join(lines[1:]))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(out, encoding="utf-8")
    print(json.dumps({"report_id": rid, "path": str(p), "decision": "created",
                      "generated_at": generated_at, "content_hash": chash},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_writejson(a):
    rid = fmlib.make_report_id(a.subject, a.season, a.week)
    p = Path(a.report_dir) / (rid + ".json")
    obj = json.loads(_read(a.facts))
    if a.schema:
        schema = json.loads(Path(a.schema).read_text(encoding="utf-8-sig"))
        errs = fmlib.validate(obj, schema)
        if errs:
            print("Schema-Fehler:\n- " + "\n- ".join(errs), file=sys.stderr)
            return 3
    chash = fmlib.content_hash_json(obj)
    generated_at = a.generated_at or a.as_of or fmlib.now_iso()
    obj["meta"] = {"report_id": rid, "generated_at": generated_at, "content_hash": chash}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report_id": rid, "path": str(p), "decision": "created",
                      "generated_at": generated_at, "content_hash": chash},
                     ensure_ascii=False, indent=2))
    return 0


def cmd_hash(a):
    print(fmlib.content_hash_text(_read(a.facts))); return 0


def cmd_hashjson(a):
    print(fmlib.content_hash_json(json.loads(_read(a.facts)))); return 0


def cmd_verify(a):
    p = Path(a.path)
    if p.suffix == ".json":
        obj = json.loads(p.read_text(encoding="utf-8-sig"))
        stored = obj.get("meta", {}).get("content_hash")
        recomputed = fmlib.content_hash_json(obj)
    else:
        text = p.read_text(encoding="utf-8-sig")
        stored = None
        for line in text.splitlines():
            if line.strip().startswith(fmlib.META_PREFIX):
                for part in line.split("|"):
                    k, _, v = part.partition(":")
                    if k.strip() == "content_hash":
                        stored = v.strip()
        recomputed = fmlib.content_hash_text(text)
    match = stored == recomputed
    print(json.dumps({"path": str(p), "stored": stored, "recomputed": recomputed,
                      "match": match}, ensure_ascii=False, indent=2))
    return 0 if match else 1


def cmd_validate(a):
    obj = json.loads(_read(a.path if a.path != "-" else "-")) if a.path == "-" \
        else json.loads(Path(a.path).read_text(encoding="utf-8-sig"))
    schema = json.loads(Path(a.schema).read_text(encoding="utf-8-sig"))
    errs = fmlib.validate(obj, schema)
    if errs:
        print(json.dumps({"valid": False, "errors": errs}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps({"valid": True, "errors": []}, ensure_ascii=False, indent=2))
    return 0


def build_parser():
    p = argparse.ArgumentParser(description="Report schreiben (kein Cache) & Reproduzierbarkeit pruefen (md/json).")
    sub = p.add_subparsers(dest="cmd", required=True)

    def subj(sp):
        sp.add_argument("--subject", required=True)
        sp.add_argument("--season", required=True)
        sp.add_argument("--week", default=None)

    sp = sub.add_parser("id"); subj(sp); sp.set_defaults(func=cmd_id)

    sp = sub.add_parser("path"); subj(sp)
    sp.add_argument("--report-dir", default="./temp/reports")
    sp.add_argument("--format", choices=["md", "json"], default="md")
    sp.set_defaults(func=cmd_path)

    sp = sub.add_parser("write"); subj(sp)
    sp.add_argument("--report-dir", default="./temp/reports")
    sp.add_argument("--as-of", default=None); sp.add_argument("--generated-at", default=None)
    sp.add_argument("--facts", default="-")
    sp.set_defaults(func=cmd_write)

    sp = sub.add_parser("writejson"); subj(sp)
    sp.add_argument("--report-dir", default="./temp/reports")
    sp.add_argument("--as-of", default=None); sp.add_argument("--generated-at", default=None)
    sp.add_argument("--facts", default="-"); sp.add_argument("--schema", default=None)
    sp.set_defaults(func=cmd_writejson)

    sp = sub.add_parser("hash"); sp.add_argument("--facts", default="-")
    sp.set_defaults(func=cmd_hash)

    sp = sub.add_parser("hashjson"); sp.add_argument("--facts", default="-")
    sp.set_defaults(func=cmd_hashjson)

    sp = sub.add_parser("verify"); sp.add_argument("--path", required=True)
    sp.set_defaults(func=cmd_verify)

    sp = sub.add_parser("validate")
    sp.add_argument("--path", required=True); sp.add_argument("--schema", required=True)
    sp.set_defaults(func=cmd_validate)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))
