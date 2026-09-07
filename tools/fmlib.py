#!/usr/bin/env python3
"""fmlib — gemeinsame, abhaengigkeitsfreie Bibliothek fuer die FantasyManager-Skills.

Enthaelt:
- IDs/Zeit:      slugify, make_report_id, parse_iso, now_iso
- Text-Hash:     normalize, strip_meta, content_hash_text  (Markdown-Reports)
- JSON:          canonical_json, content_hash_json         (strukturierte Reports)
- Verletzung:    injury_gate (formales Gate aus Game-Status + Trainingsteilnahme)
- Validierung:   validate (minimaler JSON-Schema-Validator: type/required/…)
- Optimierung:   hungarian, optimize_lineup (max. Gesamteffektivitaet)

Nur Python-Standardbibliothek.
"""

import datetime as _dt
import hashlib
import json
import re

META_PREFIX = "report_id:"
BOM = "\ufeff"


# =========================== Zeit ===========================

def parse_iso(value):
    """ISO-8601 -> timezone-aware datetime (UTC-normalisiert)."""
    if value is None:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = _dt.datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    return dt.astimezone(_dt.timezone.utc)


def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# =========================== IDs ===========================

def slugify(text):
    text = str(text).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def make_report_id(subject, season, week=None):
    rid = "{}-{}".format(slugify(subject), str(season).strip())
    if week not in (None, "", "0", 0):
        rid += "-w{}".format(str(week).strip())
    return rid


# =========================== Text-Hash ===========================

def normalize(text):
    """Deterministische Normalisierung fuer Markdown: fuehrendes BOM entfernen,
    pro Zeile rechts trimmen, \\n-Enden, genau ein abschliessender Umbruch."""
    if text.startswith(BOM):
        text = text[1:]
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    lines = [ln.rstrip() for ln in lines]
    return "\n".join(lines).rstrip("\n") + "\n"


def strip_meta(text):
    """Entfernt die Meta-Zeile (beginnt mit `report_id:`) vor dem Hashen."""
    out = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if ln.strip().startswith(META_PREFIX):
            continue
        out.append(ln)
    return "\n".join(out)


def content_hash_text(facts_text):
    norm = normalize(strip_meta(facts_text))
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


# =========================== JSON ===========================

def canonical_json(obj, exclude=("meta", "generated_at", "content_hash")):
    """Deterministische JSON-Serialisierung (sortierte Keys, feste Trenner).
    Volatile Felder (Default: das ganze `meta`-Objekt sowie generated_at/
    content_hash) werden vor dem Serialisieren rekursiv entfernt."""
    def clean(o):
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items() if k not in exclude}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    return json.dumps(clean(obj), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


def content_hash_json(obj, exclude=("meta", "generated_at", "content_hash")):
    return hashlib.sha256(canonical_json(obj, exclude).encode("utf-8")).hexdigest()


# =========================== Verletzungs-Gate (#7) ===========================

# Game-Status (offizielle NFL-Designation) und Trainingsteilnahme der letzten
# Einheit: DNP (did not practice), LP (limited), FP (full). Werte = erwartete
# effektive Verfuegbarkeit (0..1). Bewusst konservativ und dokumentiert.
_STATUS = {"out": 0.0, "ir": 0.0, "pup": 0.0, "sus": 0.0, "suspended": 0.0,
           "doubtful": 0.20, "questionable": None, "": 1.0, "active": 1.0,
           "probable": 0.95}
_QUES_BY_PRACTICE = {"fp": 0.90, "full": 0.90, "lp": 0.75, "limited": 0.75,
                     "dnp": 0.55, "none": 0.70, "": 0.70, None: 0.70}
_NOSTATUS_BY_PRACTICE = {"dnp": 0.90, "lp": 0.95, "limited": 0.95,
                         "fp": 1.0, "full": 1.0, "none": 1.0, "": 1.0, None: 1.0}


def injury_gate(status=None, practice=None):
    """Formales Gate 0..1 aus Game-Status + Trainingsteilnahme.
    Beispiele: injury_gate('Out') -> 0.0; injury_gate('Questionable','LP') -> 0.75;
    injury_gate('Questionable','FP') -> 0.90; injury_gate(None,'DNP') -> 0.90."""
    s = (status or "").strip().lower()
    p = (practice or "").strip().lower() if practice is not None else None
    if s in ("questionable", "ques", "q"):
        return _QUES_BY_PRACTICE.get(p, 0.70)
    if s in _STATUS and _STATUS[s] is not None:
        return _STATUS[s]
    if s in ("", "active", "none"):
        return _NOSTATUS_BY_PRACTICE.get(p, 1.0)
    # Unbekannter Status -> konservativ als questionable/unklar behandeln
    return _QUES_BY_PRACTICE.get(p, 0.70)


# =========================== Minimaler JSON-Schema-Validator ===========================

_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "number": (int, float), "integer": int, "null": type(None),
}


def validate(instance, schema, path="$"):
    """Sehr kleiner JSON-Schema-Validator: type, required, properties, items,
    enum, additionalProperties(bool). Gibt eine Liste von Fehlertexten zurueck."""
    errors = []
    t = schema.get("type")
    if t:
        expected = _TYPES.get(t)
        # bool ist Subtyp von int -> number/integer duerfen kein bool sein
        ok = isinstance(instance, expected) and not (
            t in ("number", "integer") and isinstance(instance, bool))
        if not ok:
            errors.append("{}: erwartet {}, erhalten {}".format(
                path, t, type(instance).__name__))
            return errors
    if "enum" in schema and instance not in schema["enum"]:
        errors.append("{}: {!r} nicht in enum {}".format(path, instance, schema["enum"]))
    if t == "object" and isinstance(instance, dict):
        for req in schema.get("required", []):
            if req not in instance:
                errors.append("{}: Pflichtfeld '{}' fehlt".format(path, req))
        props = schema.get("properties", {})
        for key, val in instance.items():
            if key in props:
                errors += validate(val, props[key], "{}.{}".format(path, key))
            elif schema.get("additionalProperties") is False:
                errors.append("{}: unerlaubtes Feld '{}'".format(path, key))
    if t == "array" and isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            errors += validate(item, schema["items"], "{}[{}]".format(path, i))
    return errors


# =========================== Optimierung ===========================

_BIG = 10 ** 9


def hungarian(cost):
    """Ungarischer Algorithmus (Kuhn-Munkres) fuer quadratische Kostenmatrix,
    minimiert die Summe. Gibt (total_cost, assignment) mit assignment[row]=col."""
    n = len(cost)
    if n == 0:
        return 0, []
    INF = float("inf")
    u = [0] * (n + 1)
    v = [0] * (n + 1)
    p = [0] * (n + 1)   # p[col] = row (1-indexiert)
    way = [0] * (n + 1)
    for i in range(1, n + 1):
        p[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        while True:
            used[j0] = True
            i0 = p[j0]
            delta = INF
            j1 = -1
            for j in range(1, n + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(0, n + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    assignment = [-1] * n
    for j in range(1, n + 1):
        if p[j] != 0:
            assignment[p[j] - 1] = j - 1
    total = sum(cost[i][assignment[i]] for i in range(n))
    return total, assignment


def optimize_lineup(players, slots):
    """Maximiert die Summe der Effektivitaet ueber eine gueltige Slot-Zuordnung.

    players: [{id, pos, E(float), startable(bool, default True)} ...]
    slots:   [{name, eligible:[Positionen]} ...]
    Rueckgabe: {starters:[{slot,player_id,pos,E}], bench:[player_id...],
                unfilled:[slot...], total_E:float}
    """
    slots = list(slots)
    elig = [set(s["eligible"]) for s in slots]
    ns = len(slots)
    real = [pl for pl in players]
    np_ = len(real)
    size = max(ns, np_, 1)
    # Kostenmatrix (Minimierung): cost = 100 - E fuer eignungsfaehige, startbare
    # Spieler; Dummy = 150 (nur wenn kein echter Spieler passt); ineligible = BIG.
    cost = [[_BIG] * size for _ in range(size)]
    for si in range(size):
        for pj in range(size):
            if si < ns and pj < np_:
                pl = real[pj]
                startable = pl.get("startable", True)
                if startable and pl.get("pos") in elig[si]:
                    e = float(pl.get("E", 0.0))
                    cost[si][pj] = 100.0 - e
                else:
                    cost[si][pj] = _BIG
            elif si < ns and pj >= np_:
                cost[si][pj] = 150.0        # Dummy-Spieler -> Slot bleibt leer
            else:
                cost[si][pj] = 0.0          # Dummy-Slot -> Bank
    _, assign = hungarian(cost)
    starters, unfilled, used = [], [], set()
    for si in range(ns):
        pj = assign[si]
        if pj < np_ and cost[si][pj] < _BIG:
            pl = real[pj]
            starters.append({"slot": slots[si]["name"], "player_id": pl.get("id"),
                             "pos": pl.get("pos"), "E": float(pl.get("E", 0.0))})
            used.add(pj)
        else:
            unfilled.append(slots[si]["name"])
    bench = [real[j].get("id") for j in range(np_) if j not in used]
    total_e = sum(s["E"] for s in starters)
    return {"starters": starters, "bench": bench, "unfilled": unfilled,
            "total_E": round(total_e, 2)}


# =========================== Effektivitaets-Evaluator (v2) ===========================

_BASE_WEIGHTS = {"role": 0.30, "scheme": 0.25, "matchup": 0.25, "form": 0.20}
_TIERS = [(81, "sehr hoch"), (61, "hoch"), (41, "mittel"), (21, "niedrig"), (0, "sehr niedrig")]


def effectiveness_tier(value):
    for lo, name in _TIERS:
        if value >= lo:
            return name
    return "sehr niedrig"


# Positions-Referenz (starke Starter, half-ppr) fuer den Projektions->Rolle-Proxy.
_POS_ELITE = {"QB": 25.0, "RB": 20.0, "WR": 20.0, "TE": 16.0, "K": 10.0, "DEF": 10.0}


def role_from_projection(pos, proj):
    """Grober, dokumentierter Proxy: skaliert eine Projektion auf 0..100 relativ zu
    einer positionsspezifischen Elite-Referenz. Nur als Anzeige-/Fallback-Signal,
    NICHT fuer positionsuebergreifende Punktauswahl (dafuer zaehlen echte Punkte)."""
    ref = _POS_ELITE.get((pos or "").upper(), 15.0)
    return max(0.0, min(100.0, 100.0 * float(proj) / ref)) if ref else 0.0


def quality_tilt(quality, swing=0.20):
    """Wandelt eine Evaluator-Qualitaet (0..100, 50=neutral) in einen
    Projektions-Tilt-Faktor um: 50 -> 1.0, 100 -> 1+swing, 0 -> 1-swing.
    quality None -> 1.0 (kein Tilt)."""
    if quality is None:
        return 1.0
    t = 1.0 + swing * ((float(quality) - 50.0) / 50.0)
    return max(1.0 - swing, min(1.0 + swing, t))


def _weights_for(scoring):
    """Scoring-abhaengige Gewichte (dokumentiert im Skill)."""
    w = dict(_BASE_WEIGHTS)
    s = (scoring or "").strip().lower()
    if s == "ppr":
        w["role"] += 0.05
        w["form"] -= 0.05
    elif s in ("standard", "td", "standard-td", "non-ppr", "0ppr"):
        w["matchup"] += 0.05
        w["form"] -= 0.05
    return w


def evaluate(factors, gate, games=0, sources=0, scoring="half-ppr", horizon="next_game"):
    """Deterministische, reproduzierbare Effektivitaets-Auswertung.

    factors: dict name -> {"value": 0..100 | None, "backed": bool, "evidence": str}
      erwartete Namen: role, scheme, matchup, form. **Unbelegte Faktoren
      (backed=False oder value=None) werden ausgeschlossen und die Gewichte auf
      die verbleibenden renormalisiert** – kein neutraler Default (keine Annahme).
    gate: 0..1 (aus injury_gate).
    games: Anzahl gewerteter Spiele der aktuellen Saison (Sample fuer Form/Konfidenz).
    sources: Anzahl belegter Quellen im Report.

    Rueckgabe: effectiveness, floor, ceiling, tier, gate, confidence(0..1) + label,
    weights_used (renormalisiert), backed/excluded, factors (Echo).
    """
    gate = max(0.0, min(1.0, float(gate)))
    base = _weights_for(scoring)

    backed, excluded = {}, []
    for name, w in base.items():
        f = factors.get(name) or {}
        val = f.get("value")
        is_backed = bool(f.get("backed", val is not None)) and val is not None
        if is_backed:
            backed[name] = (max(0.0, min(100.0, float(val))), w)
        else:
            excluded.append(name)

    total_w = sum(w for _, w in backed.values())
    weights_used = {n: round(w / total_w, 4) for n, (_, w) in backed.items()} if total_w else {}
    intermediate = sum(v * (w / total_w) for v, w in backed.values()) if total_w else 0.0
    effectiveness = round(intermediate * gate, 2)

    # Quantitative Konfidenz 0..1 aus Datenvollstaendigkeit/Sample/Klarheit/Quellen
    coverage = len(backed) / len(base)
    sample = min(max(int(games), 0), 3) / 3.0
    injury_clarity = abs(2.0 * gate - 1.0)         # 0 (unklar) .. 1 (klar out/fit)
    source_score = min(max(int(sources), 0), 3) / 3.0
    confidence = round(0.35 * coverage + 0.30 * sample +
                       0.20 * injury_clarity + 0.15 * source_score, 3)
    conf_label = "hoch" if confidence >= 0.66 else "mittel" if confidence >= 0.40 else "niedrig"

    # Asymmetrisches Floor/Ceiling-Band: Verletzungsrisiko weitet v. a. den Floor
    downside = effectiveness * (0.10 + 0.30 * (1 - confidence) + 0.25 * (1 - gate))
    upside = effectiveness * (0.10 + 0.25 * (1 - confidence))
    floor = round(max(0.0, effectiveness - downside), 2)
    ceiling = round(min(100.0, effectiveness + upside), 2)

    return {
        "effectiveness": effectiveness,
        "tier": effectiveness_tier(effectiveness),
        "floor": floor,
        "ceiling": ceiling,
        "gate": round(gate, 3),
        "confidence": confidence,
        "confidence_label": conf_label,
        "weights_used": weights_used,
        "backed_factors": sorted(backed.keys()),
        "excluded_factors": sorted(excluded),
        "scoring": scoring,
        "horizon": horizon,
        "factors": factors,
    }
