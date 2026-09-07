#!/usr/bin/env python3
"""coach_assign.py — Slot-Zuordnung + Abschlussreport (letzter Pipeline-Schritt).

Nimmt NUR bereits fertige Ergebnisse der vorgelagerten Skills entgegen (kein
eigenes Report-Fetching, keine eigene Effektivitäts-Bewertung, kein eigener
Scout-Scan):

- Supporter-Report je Spieler (Fakten: Verletzung, Team-/Gegner-Ausrichtung,
  Stärken, News, Vollständigkeit) unter `players[].report`.
- Evaluator-Ergebnis je Spieler (`proj`, `gate`, `tilt`, `evaluation`).
- Scout-Zusammenfassung (`scout_summary`) für den Kader.

Der Coach macht damit nur noch das, was wirklich seine Aufgabe ist: die
optimale, regelkonforme Slot-Zuordnung (Ungarischer Algorithmus aus fmlib.py)
und das Zusammenführen von Evaluator- + Scout-Ergebnissen zu einem
Abschlussreport (JSON + Markdown). Kein Netzwerkzugriff, kein Cache.

Eingabe (JSON): {
  team, week, as_of, scoring, slots:[{name,eligible}],
  players:[{name,pos,team,bye,proj,gate,tilt,evaluation:{...},report:{...}}],
  scout_summary: {lines:[...], future_risks:[...]}  # optional, vom Scout-Skill
}

Nur Python-Standardbibliothek (nutzt fmlib).
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmlib  # noqa: E402


def pid(name):
    return fmlib.slugify(name)


def _first_claim(items):
    return items[0].get("claim") if items else None


_OFFENSE_RE = re.compile(
    r"\b(qb|quarterback|o-?line|oline|ot|wr|wr1|receiver|rb|running back|backfield|te|"
    r"tight end|run-?game|rushing|laufspiel|red-?zone|passspiel|passing|offense|"
    r"offensiv\w*|explosiv\w*|playmaker|skill|waffen|weapon|under-center|play-action|"
    r"motion|yac|deep-?threat|completions|scoring|go-to-receiver|arm|mobil\w*|"
    r"dual-threat)\b", re.I)
_DEFENSE_RE = re.compile(
    r"\b(defense|defensiv\w*|defender|secondary|cb|cornerback|corner|pass-?rush|passrush|"
    r"front-?7|front-?four|front-?4|d-line|dline|d-front|linebacker|lb|safety|safeties|"
    r"run-defense|coverage|sack\w*|blitz\w*|takeaway\w*|turnover\w*|db|dbs|trenches|"
    r"interior-passrush)\b", re.I)


def _claim_unit(item):
    """Ordnet eine Stärke/Schwäche einer Einheit zu: 'offense' | 'defense' | 'neutral'.
    Bevorzugt das explizite Feld `unit` (aus dem Supporter-Report), sonst
    Keyword-Heuristik."""
    u = str((item or {}).get("unit") or "").strip().lower()
    if u.startswith("off"):
        return "offense"
    if u.startswith("def"):
        return "defense"
    if u in ("neutral", "special", "st", "coaching", "both"):
        return "neutral"
    text = (item or {}).get("claim") or ""
    off, dfn = bool(_OFFENSE_RE.search(text)), bool(_DEFENSE_RE.search(text))
    if off and not dfn:
        return "offense"
    if dfn and not off:
        return "defense"
    return "neutral"


def _relevant_opp_claims(claims, pos):
    """Matchup-relevante Gegner-Eigenschaften je nach Spielerposition:
    Offensiv-Spieler (QB/RB/WR/TE/K) treffen auf die gegnerische DEFENSE – die
    Offense-Eigenschaften des Gegners werden daher ausgeblendet. Für DEF umgekehrt."""
    drop = "defense" if str(pos or "").upper() == "DEF" else "offense"
    return [c for c in (claims or []) if _claim_unit(c) != drop]


def _is_ques(status):
    return (status or "").strip().lower() in ("questionable", "ques", "q")


def build_players(raw_players, week, force_all_active=False):
    """Baut die Optimierer-Spielerliste rein aus bereits gelieferten Werten:
    `E = proj x tilt x gate`. Keine eigene Bewertung, keine eigene Report-Erstellung."""
    out = []
    for p in raw_players:
        report = p.get("report") or {}
        status = report.get("injury", {}).get("status", "active")
        gate = 1.0 if force_all_active and _is_ques(status) else float(p.get("gate", 1.0))
        on_bye = p.get("bye") == week
        startable = gate > 0 and not on_bye
        proj = float(p.get("proj", 0.0))
        tilt = float(p.get("tilt", 1.0))
        e = round(proj * tilt * gate, 2) if startable else 0.0
        out.append({
            "id": pid(p["name"]), "name": p["name"], "pos": p["pos"], "team": p.get("team"),
            "E": e, "gate": gate, "startable": startable, "on_bye": on_bye, "status": status,
            "proj": proj, "tilt": round(tilt, 3),
            "evaluation": p.get("evaluation", {}), "report": report,
        })
    return out


def scout_notes(lineup, players_by_id, slots):
    """Erkennt lineup-spezifische Schwaechen: unbesetzte Slots, angeschlagene
    Starter ohne gesunden Ersatz. (Kader-weite Sleeper-/Trade-Analyse liefert
    der Scout-Skill selbst über `scout_summary`.)"""
    notes = []
    elig = {s["name"]: set(s["eligible"]) for s in slots}
    starter_ids = {s["player_id"] for s in lineup["starters"]}
    for slot in lineup.get("unfilled", []):
        notes.append("Slot '{}' unbesetzt – Waiver/Trade pruefen.".format(slot))
    for s in lineup["starters"]:
        pl = players_by_id[s["player_id"]]
        if pl["gate"] < 1.0:
            healthy = [q for q in players_by_id.values()
                       if q["id"] not in starter_ids and q["startable"]
                       and q["gate"] >= 1.0 and q["pos"] in elig[s["slot"]]]
            if not healthy:
                notes.append(
                    "'{}' ({}) ist angeschlagen (Gate {:.2f}) und hat KEINEN "
                    "gesunden Ersatz fuer Slot '{}' – Scout: Pickup gesucht."
                    .format(pl["name"], pl["pos"], pl["gate"], s["slot"]))
            else:
                notes.append(
                    "'{}' ({}) angeschlagen in Slot '{}' – Monitor; gesunder Pivot: {}."
                    .format(pl["name"], pl["pos"], s["slot"],
                            ", ".join(h["name"] for h in healthy[:2])))
    return notes


def cleared_diff(base, alt, players_by_id):
    """Vergleicht Basis- und All-Active-Aufstellung -> Wechsel, falls QUES aktiv."""
    base_map = {s["slot"]: s["player_id"] for s in base["starters"]}
    alt_map = {s["slot"]: s["player_id"] for s in alt["starters"]}
    diffs = []
    for slot, pidv in alt_map.items():
        if base_map.get(slot) != pidv:
            was = players_by_id.get(base_map.get(slot), {}).get("name", "—")
            now = players_by_id.get(pidv, {}).get("name", "—")
            diffs.append("Falls QUES aktiv: {} startet in '{}' statt {}."
                         .format(now, slot, was))
    return diffs


def _short(text, n=90):
    text = str(text)
    return text if len(text) <= n else text[:n - 1] + "…"


def _join_de(items):
    items = [i for i in items if i]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " und " + items[-1]


def _lead_phrase(eligible, pos):
    s = set(eligible)
    if len(s) == 1:
        return "als Stammplatz {}".format(pos)
    if "QB" in s and len(s) >= 4:
        return "als zweiter QB im Superflex" if pos == "QB" else "auf dem Superflex-Platz"
    if len(s) >= 3:
        return "im Flex"
    return "im Starter-Slot"


def report_reason(report, lead_phrase, is_starter):
    """Fließtext-Begründung der Coach-Entscheidung (Start/Bank), begründet mit den
    Daten aus dem Spieler-Report (Scheme, Matchup, Verletzung, News, Stärken) –
    OHNE die errechneten Werte E/Proj/Tilt."""
    name = report.get("subject") or "Der Spieler"
    pos = report.get("position")
    to = report.get("team_orientation", {})
    no = report.get("next_opponent", {})
    inj = report.get("injury", {})
    opp = no.get("opponent")
    ha = no.get("home_away")
    edge = _first_claim(_relevant_opp_claims(no.get("weaknesses", []), pos))
    risk = _first_claim(_relevant_opp_claims(no.get("strengths", []), pos))
    status = inj.get("status", "active")
    ques = str(status).lower() in ("questionable", "ques", "q", "doubtful", "out", "ir")
    news0 = (report.get("news") or [None])[0]
    strength = _first_claim(report.get("player_strengths", []))
    pref = to.get("preferred_player_types")
    offense = to.get("offense")

    sents = []
    if is_starter:
        s = "{} steht {} in der Aufstellung".format(name, lead_phrase)
        if pref:
            s += ", weil das Offense-Scheme {} bevorzugt".format(_short(pref, 130))
        elif offense:
            s += " im System {}".format(_short(offense, 130))
        sents.append(s + ".")
    else:
        s = "{} sitzt zunächst auf der Bank".format(name)
        if ques:
            note = inj.get("note")
            s += ", vor allem wegen des unsicheren Status ({}{})".format(
                status, "" if not note else ": " + _short(note, 70))
        else:
            s += ", da ihm im Positionsvergleich derzeit die belegten Vorteile der gesetzten Starter fehlen"
        sents.append(s + ".")

    if opp:
        loc = {"home": "zuhause gegen", "away": "auswärts bei"}.get(ha)
        prefix = "Im Matchup {} {}".format(loc, opp) if loc else "Gegen {}".format(opp)
        if edge and risk:
            sents.append("{} lässt sich die Gegner-Schwäche „{}“ nutzen, während die "
                         "Gegner-Stärke „{}“ der Hauptdämpfer bleibt.".format(
                             prefix, _short(edge, 100), _short(risk, 100)))
        elif edge:
            sents.append("{} lässt sich die belegte Gegner-Schwäche „{}“ nutzen.".format(
                prefix, _short(edge, 100)))
        elif risk:
            sents.append("{} ist die Gegner-Stärke „{}“ der wesentliche Dämpfer.".format(
                prefix, _short(risk, 100)))
        else:
            sents.append("{} liegen noch keine belegten Gegner-Stärken oder -Schwächen "
                         "vor.".format(prefix))

    frag = []
    if is_starter and ques:
        note = inj.get("note")
        frag.append("ist der Verfügbarkeitsstatus {}{}".format(
            status, "" if not note else " (" + _short(note, 70) + ")"))
    if news0:
        conf = "" if news0.get("confirmed", True) else ", noch unbestätigt"
        frag.append("meldet {}{} zuletzt „{}“".format(
            news0.get("feed_source", "Feed"), conf, _short(news0.get("headline", ""), 100)))
    if strength:
        frag.append("gilt als belegte Stärke {}".format(_short(strength, 100)))
    if frag:
        sents.append("Aktuell " + _join_de(frag) + ".")

    return " ".join(sents)


def reason_for_starter(s, players_by_id, slots):
    """Fließtext-Begründung, warum dieser Spieler in diesem Slot startet."""
    p = players_by_id[s["player_id"]]
    elig = next(set(sl["eligible"]) for sl in slots if sl["name"] == s["slot"])
    return report_reason(p["report"], _lead_phrase(elig, p["pos"]), is_starter=True)


def reason_for_bench(b_id, players_by_id):
    """Fließtext-Begründung, warum dieser Spieler auf der Bank sitzt."""
    p = players_by_id[b_id]
    report = p["report"]
    if p["on_bye"]:
        return "{} sitzt auf der Bank, weil das Team in dieser Woche Bye hat und er " \
               "nicht einsetzbar ist.".format(report.get("subject") or p["name"])
    if p["gate"] == 0:
        return "{} sitzt auf der Bank, weil er laut Status (Out/IR) nicht startfähig " \
               "ist.".format(report.get("subject") or p["name"])
    return report_reason(report, "auf der Bank", is_starter=False)


def _player_row(slot_label, p):
    ev = p.get("evaluation", {})
    return "| {} | {} | {} | {} | {} | {} | {:.2f} | {:.2f} | {} | {}–{} | {} |".format(
        slot_label, p["name"], p["pos"], p["team"], p["E"], p["proj"],
        p.get("tilt", 1.0), p["gate"], ev.get("effectiveness", "—"),
        ev.get("floor", "—"), ev.get("ceiling", "—"), ev.get("confidence_label", "—"))


_LEGEND = [
    "## Legende (Spaltenkürzel)",
    "- **E** – Auswahlwert des Coaches = Projektion × Tilt × Gate (Basis der Aufstellungswahl).",
    "- **Proj** – Plattform-Projektion: erwartete Fantasy-Punkte laut Eingabe.",
    "- **Tilt** – Evaluator-Qualitäts-Faktor (±20 %) aus Scheme-Fit/Matchup/Form (1.00 = neutral).",
    "- **Gate** – Verfügbarkeits-Gate 0–1 aus dem Verletzungsstatus (1.00 = fit, 0 = Out/IR).",
    "- **Eff** – Effektivität 0–100 des Evaluators (Qualität, positionsunabhängig).",
    "- **Floor–Ceil** – unteres/oberes Effektivitätsband (Sicherheit vs. Upside).",
    "- **Konf** – Konfidenz der Evaluation (niedrig/mittel/hoch) je nach Datenlage.",
]


def to_markdown(team, week, as_of, scoring, base, players_by_id, notes, diffs,
                starter_reasons, bench_reasons, scout, data_completeness=None):
    header = ["| Slot | Spieler | Pos | Team | E | Proj | Tilt | Gate | Eff | Floor–Ceil | Konf |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
    L = ["# Beste Aufstellung: {} — Woche {}".format(team, week),
         "Stand: {} | Scoring: {} | Auswahl-E (Evaluator-adjustierte Punkte): {}"
         .format(as_of, scoring, base["total_E"]),
         "", "## Startaufstellung"] + header
    for s in base["starters"]:
        L.append(_player_row(s["slot"], players_by_id[s["player_id"]]))
    if base.get("unfilled"):
        L += ["", "**Unbesetzt:** " + ", ".join(base["unfilled"])]
    L += ["", "## Bank"] + header
    for b in base["bench"]:
        L.append(_player_row("BN", players_by_id[b]))
    L += [""] + _LEGEND
    L += ["", "## Begründung je Starter (auf Basis des Spieler-Reports)"]
    for s in base["starters"]:
        p = players_by_id[s["player_id"]]
        L.append("- **{} ({})** – {}".format(p["name"], s["slot"],
                                             starter_reasons.get(s["player_id"], "")))
    L += ["", "## Bank (Begründung auf Basis des Spieler-Reports)"]
    for b in base["bench"]:
        L.append("- **{}** – {}".format(players_by_id[b]["name"], bench_reasons.get(b, "")))
    L += ["", "## Scout-Zusammenfassung"]
    L += ["- " + n for n in scout.get("lines", [])] or ["- (kein scout_summary in der Eingabe)"]
    if notes:
        L += ["", "**Erkannte Schwächen in der Startelf:**"]
        L += ["- " + n for n in notes]
    L += ["", "### Mögliche zukünftige Probleme"]
    future = scout.get("future_risks", [])
    L += (["- " + f for f in future] if future
          else ["- Keine strukturellen Zukunftsrisiken erkannt (Bye-Verteilung/Status unauffällig)."])
    L += ["", "## Datenvollständigkeit"]
    if data_completeness:
        L.append("Bei folgenden Spielern fehlen laut Supporter-Report noch Informationen "
                 "(noch nicht abgefragt/belegt):")
        for _, info in data_completeness.items():
            L.append("- **{}** – fehlt: {}".format(info["name"], ", ".join(info["missing"])))
    else:
        L.append("Alle Spieler-Reports vollständig – keine fehlenden Informationen.")
    L += ["", "## Falls QUES aufklart"]
    L += ["- " + d for d in (diffs or ["keine Aenderung"])]
    L += ["", "_Aufstellungswahl über E (= Projektion × Tilt × Gate, geliefert vom Evaluator). "
          "Die Begründungen je Spieler beruhen auf den Supporter-Report-Fakten (Scheme, "
          "Matchup, Verletzung, News, Stärken), nicht auf den Zahlen._"]
    return "\n".join(L) + "\n"


def run(args):
    data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    as_of = args.as_of or data.get("as_of") or fmlib.now_iso()
    week = int(data["week"])
    team = data.get("team", "Team")
    scoring = data.get("scoring", "half-ppr")
    slots = data["slots"]

    players = build_players(data["players"], week)
    players_by_id = {p["id"]: p for p in players}
    base = fmlib.optimize_lineup(players, slots)

    alt_players = build_players(data["players"], week, force_all_active=True)
    alt = fmlib.optimize_lineup(alt_players, slots)
    diffs = cleared_diff(base, alt, players_by_id)

    notes = scout_notes(base, players_by_id, slots)
    scout = data.get("scout_summary") or {"lines": [], "future_risks": []}

    data_completeness = {}
    for p in players:
        comp = (p.get("report") or {}).get("completeness", {})
        if comp.get("missing"):
            data_completeness[p["id"]] = {"name": p["name"], "missing": comp["missing"]}

    starter_reasons = {s["player_id"]: reason_for_starter(s, players_by_id, slots)
                       for s in base["starters"]}
    bench_reasons = {b: reason_for_bench(b, players_by_id) for b in base["bench"]}

    starters_rich = []
    for s in base["starters"]:
        p = players_by_id[s["player_id"]]
        ev = p.get("evaluation", {})
        starters_rich.append({
            "slot": s["slot"], "player_id": s["player_id"], "pos": s["pos"],
            "E": s["E"], "proj": p["proj"], "tilt": p.get("tilt", 1.0),
            "gate": p["gate"], "effectiveness": ev.get("effectiveness"),
            "floor": ev.get("floor"), "ceiling": ev.get("ceiling"),
            "confidence": ev.get("confidence"),
            "confidence_label": ev.get("confidence_label"),
            "reason": starter_reasons[s["player_id"]]})

    lineup_obj = {
        "team": team, "week": week, "as_of": as_of, "scoring": scoring,
        "total_E": base["total_E"],
        "selection_basis": "Projektion x Evaluator-Qualitaets-Tilt x Verfuegbarkeits-Gate",
        "starters": starters_rich, "bench": base["bench"],
        "bench_reasons": bench_reasons,
        "unfilled": base.get("unfilled", []),
        "monitors": diffs, "scout_notes": notes, "scout_summary": scout,
        "data_completeness": data_completeness,
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    json_dir = Path(args.json_dir)
    json_dir.mkdir(parents=True, exist_ok=True)
    stem = "lineup-{}-w{}".format(fmlib.slugify(team), week)
    (json_dir / (stem + ".json")).write_text(
        json.dumps(lineup_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / (stem + ".md")).write_text(
        to_markdown(team, week, as_of, scoring, base, players_by_id, notes, diffs,
                    starter_reasons, bench_reasons, scout, data_completeness),
        encoding="utf-8")

    print(json.dumps({
        "team": team, "week": week, "total_E": base["total_E"],
        "starters": ["{}={}".format(s["slot"], players_by_id[s["player_id"]]["name"])
                     for s in base["starters"]],
        "unfilled": base.get("unfilled", []),
        "incomplete": len(data_completeness),
        "out": str(out_dir / (stem + ".md")),
        "out_json": str(json_dir / (stem + ".json")),
    }, ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Coach: Slot-Zuordnung + Abschlussreport aus fertigen "
                    "Supporter-/Evaluator-/Scout-Ergebnissen.")
    p.add_argument("--input", required=True)
    p.add_argument("--out-dir", default=".")
    p.add_argument("--json-dir", default="./temp")
    p.add_argument("--as-of", default=None)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
