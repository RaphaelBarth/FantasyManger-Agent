#!/usr/bin/env python3
"""run_week.py — End-to-End-Runner fuer eine Woche.

Kette: Kader/Eingabe -> pro Spieler frischer Report (kein Cache, jeder Lauf
zieht neu) -> Effektivitaet (Projektion x Verletzungs-Gate) -> optimale
Aufstellung (exaktes Max-Weight-Assignment) -> Scout-Schwaechen -> Wochen-Bundle
(JSON+MD).

Eingabe (JSON): { team, week, as_of, scoring, slots:[{name,eligible}],
                  players:[{name,pos,team,bye,status,practice,proj,opp}] }

Nur Python-Standardbibliothek (nutzt fmlib).
"""

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fmlib  # noqa: E402

DEFAULT_PROFILES_PATH = Path(__file__).resolve().parent / "team_profiles.default.json"
DEFAULT_SCHEDULE_PATH = Path(__file__).resolve().parent / "schedule.default.json"


def pid(name):
    return fmlib.slugify(name)


def load_default_team_profiles(path=None):
    """Laedt die mitgelieferte Team-Ausrichtungs-Wissensbasis (Scheme/Coordinators).
    Nur stabile Liga-Fakten (Ausrichtung); Meta-Schluessel mit '_' werden ignoriert.
    Fehlt die Datei, wird ein leeres Dict zurueckgegeben (kein harter Fehler)."""
    p = Path(path) if path else DEFAULT_PROFILES_PATH
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8-sig"))
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def load_default_schedule(path=None):
    """Laedt den gebuendelten Spielplan (Gegner je Team/Woche). Struktur:
    {"<season>": {"<week>": {"<team>": "@OPP" | "vsOPP"}}}. Meta-Schluessel mit
    '_' werden ignoriert. Fehlt die Datei, wird ein leeres Dict zurueckgegeben."""
    p = Path(path) if path else DEFAULT_SCHEDULE_PATH
    if not p.exists():
        return {}
    raw = json.loads(p.read_text(encoding="utf-8-sig"))
    return {k: v for k, v in raw.items() if not str(k).startswith("_")}


def merge_team_profiles(default, override):
    """Mergt Default-Profile mit Eingabe-Profilen je Team-Code. Eingabefelder
    gewinnen pro Team (flacher Merge auf Teamebene), sodass die Eingabe einzelne
    Felder (z. B. strengths/news) ergaenzt, ohne die Default-Ausrichtung zu verlieren."""
    merged = {code: dict(prof) for code, prof in (default or {}).items()}
    for code, prof in (override or {}).items():
        if code in merged and isinstance(prof, dict) and isinstance(merged[code], dict):
            base = dict(merged[code])
            base.update(prof)
            merged[code] = base
        else:
            merged[code] = prof
    return merged


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
    Bevorzugt das explizite Feld `unit` (aus der Wissensbasis), sonst Keyword-Heuristik."""
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
    Offense-Eigenschaften des Gegners werden daher ausgeblendet. Für DEF umgekehrt
    (die gegnerische Offense zählt). Neutraler Kontext bleibt für beide erhalten."""
    drop = "defense" if str(pos or "").upper() == "DEF" else "offense"
    return [c for c in (claims or []) if _claim_unit(c) != drop]


def evaluation_rationale(report, ev, sel, week):
    """Sachliche 4–6-Satz-Begruendung aus Spieler-Report + Evaluation."""
    name, pos, team = report.get("subject"), report.get("position"), report.get("nfl_team")
    inj = report.get("injury", {})
    status, note = inj.get("status", "active"), inj.get("note")
    to = report.get("team_orientation", {})
    no = report.get("next_opponent", {})
    gate, tilt = sel.get("gate", 1.0), sel.get("tilt", 1.0)
    S = []
    if str(status).lower() in ("questionable", "ques", "q", "doubtful", "out", "ir"):
        S.append("{} ({}, {}) geht mit Status {} in Woche {} (Verfügbarkeits-Gate {:.2f}){}."
                 .format(name, pos, team, status, week, gate,
                         "" if not note else ": " + note))
    else:
        S.append("{} ({}, {}) ist für Woche {} ohne Verletzungsmeldung einsatzbereit (Gate {:.2f})."
                 .format(name, pos, team, week, gate))
    if to.get("offense"):
        S.append("Im eigenen Scheme spricht dafür: {}{}."
                 .format(to["offense"], "" if not to.get("preferred_player_types")
                         else "; bevorzugt " + to["preferred_player_types"]))
    else:
        S.append("Ein belegtes Offense-Profil des eigenen Teams liegt nicht vor.")
    if no.get("opponent"):
        parts = ["Nächster Gegner: {}{}".format(
            no["opponent"], "" if not no.get("home_away") else " ({})".format(no["home_away"]))]
        edge, risk = (_first_claim(_relevant_opp_claims(no.get("weaknesses", []), pos)),
                      _first_claim(_relevant_opp_claims(no.get("strengths", []), pos)))
        if edge:
            parts.append("nutzbare Gegner-Schwäche: " + edge)
        if risk:
            parts.append("Risiko durch Gegner-Stärke: " + risk)
        if not edge and not risk:
            parts.append("belastbare Gegner-Positionsstatistik der aktuellen Saison fehlt noch")
        S.append("; ".join(parts) + ".")
    if report.get("news"):
        n = report["news"][0]
        conf = "" if n.get("confirmed", True) else ", unbestätigt"
        S.append("Aktuelle News ({}{}{}): {}.".format(
            n.get("feed_source", "Feed"),
            "" if not n.get("outlet") else "/" + n["outlet"], conf, n.get("headline")))
    elif report.get("player_strengths"):
        S.append("Belegte Spieler-Stärke: {}.".format(_first_claim(report["player_strengths"])))
    elif report.get("additional_information"):
        S.append("Relevanter Kontext: {}.".format(report["additional_information"][0].get("note")))
    S.append("Bewertung: Effektivität {} (Floor {}, Ceiling {}), Projektions-Tilt {:.2f}, Konfidenz {}."
             .format(ev.get("effectiveness"), ev.get("floor"), ev.get("ceiling"),
                     tilt, ev.get("confidence_label")))
    preseason_used = sorted(k for k, v in (report.get("data_basis") or {}).items()
                            if v and "preseason" in v.lower())
    gaps = [g for g in report.get("data_gaps", []) if "Snapshot" not in g
            and "Woche-1-Ausnahme" not in g]
    if preseason_used and len(S) < 6:
        S.append("Woche-1-Ausnahme: teils Preseason-Daten ({}); ab Woche 2 nur aktuelle Saison."
                 .format(", ".join(preseason_used)))
    elif gaps and len(S) < 6:
        S.append("Einschränkung: {}.".format("; ".join(gaps[:2])))
    return " ".join(S[:6])


def scout_summary(data, players, slots, week):
    """Deterministische Scout-Zusammenfassung: Bedarf, Bye-Luecken, QUES-Risiken,
    optional konkrete Waiver-/Trade-Kandidaten (nur falls Pool geliefert)."""
    cnt = Counter(p["pos"] for p in players)
    req = Counter()
    for sl in slots:
        if len(sl["eligible"]) == 1:
            req[sl["eligible"][0]] += 1
    surplus = sorted([pos for pos in cnt if cnt[pos] - req.get(pos, 0) >= 3])
    thin = sorted([pos for pos in req if cnt.get(pos, 0) - req[pos] <= 0])
    ques = sorted([p["name"] for p in players
                   if str(p["status"]).lower() in ("questionable", "ques", "q")])
    byes = sorted([p["name"] for p in data["players"] if p.get("bye") == week])
    fa = data.get("free_agents")
    other = data.get("other_rosters")
    lines = ["Kadergröße {} · Positionen: {}".format(
        len(players), ", ".join("{} {}".format(k, cnt[k]) for k in sorted(cnt)))]
    if surplus:
        lines.append("Überschuss (Handelsmasse, grobe Heuristik): " + ", ".join(surplus))
    if thin:
        lines.append("Dünn besetzt (Upgrade-/Bye-Absicherung prüfen): " + ", ".join(thin))
    lines.append("Bye diese Woche: " + (", ".join(byes) if byes else "keine"))
    lines.append("Fraglich (QUES): " + (", ".join(ques) if ques else "keine"))
    if fa:
        lines.append("Free-Agent-Pool geliefert ({} Spieler) → Sleeper-Bewertung via Scout möglich."
                     .format(len(fa)))
    else:
        lines.append("Kein Free-Agent-Pool im Input → keine konkreten Sleeper (Pool bereitstellen).")
    if other:
        lines.append("Liga-Kader geliefert → Buy-low/Trade-Ziele via Scout möglich.")
    else:
        lines.append("Keine Liga-Kader im Input → keine konkreten Trade-Ziele (Kader bereitstellen).")

    # Mögliche zukünftige Probleme (Bye-Cluster, QB-Doppel-Byes, K/DEF-Byes,
    # Verletzungsrisiken) – aus den Bye-Weeks und QUES-Status abgeleitet.
    future = []
    bye_by_week = defaultdict(list)
    for p in data["players"]:
        b = p.get("bye")
        if b and int(b) > week:
            bye_by_week[int(b)].append((p["name"], p["pos"]))
    for w in sorted(bye_by_week):
        names = bye_by_week[w]
        if len(names) >= 3:
            future.append("Woche {}: {} Spieler zeitgleich auf Bye ({}) – enge Aufstellung."
                          .format(w, len(names), ", ".join(n for n, _ in names)))
    qb_bye = Counter(int(p["bye"]) for p in data["players"]
                     if p["pos"] == "QB" and p.get("bye") and int(p["bye"]) > week)
    for w, c in sorted(qb_bye.items()):
        if c >= 2:
            future.append("Woche {}: {} Quarterbacks gleichzeitig auf Bye – QB/Superflex-Loch."
                          .format(w, c))
    for pos, label in (("K", "einziger Kicker"), ("DEF", "einzige Defense")):
        pl = [p for p in data["players"] if p["pos"] == pos]
        if len(pl) == 1 and pl[0].get("bye") and int(pl[0]["bye"]) > week:
            future.append("Woche {}: {} ({}) auf Bye – Streaming-Ersatz nötig."
                          .format(pl[0]["bye"], label, pl[0]["name"]))
    if ques:
        future.append("Verletzungsrisiko: {} aktuell fraglich – mögliche Ausfälle/Load-"
                      "Management in den Folgewochen beobachten.".format(", ".join(ques)))
    if thin:
        future.append("Dünne Positionen ({}) ohne Backup – bei Bye/Verletzung droht eine "
                      "Lücke; frühzeitig Tiefe aufbauen.".format(", ".join(thin)))

    return {"position_counts": dict(cnt), "surplus": surplus, "thin": thin,
            "bye_this_week": byes, "questionable": ques,
            "has_free_agents": bool(fa), "has_other_rosters": bool(other),
            "lines": lines, "future_risks": future}


def _parse_opp(opp):
    """'@ CIN' -> ('away','CIN'); 'vs NO' -> ('home','NO'); 'BYE' -> ('bye',None)."""
    if not opp:
        return None, None
    s = str(opp).strip()
    low = s.lower()
    if low in ("bye", "bye week", "bye-week"):
        return "bye", None
    if s.startswith("@"):
        return "away", s[1:].strip() or None
    if low.startswith("vs"):
        return "home", s[2:].lstrip(". ").strip() or None
    return None, s or None


def _season_field(current, preseason, is_week1):
    """Season-abhaengiges Feld mit Woche-1-Preseason-Fallback.
    Rueckgabe: (wert, basis, present). Ab Woche 2 zaehlt nur die aktuelle Saison;
    Preseason wird dann ignoriert."""
    if current:
        return current, "aktuelle Saison", True
    if is_week1 and preseason:
        return preseason, "preseason (Woche 1)", True
    return (current if current is not None else []), None, False


def ensure_report(player, season, week, as_of, report_dir, team_profiles=None):
    """Erstellt bei jedem Aufruf einen frischen JSON-Report je Spieler (kein
    Cache – ein vorhandener Report wird immer ueberschrieben, nie unveraendert
    wiederverwendet). Reicht – falls in der Eingabe vorhanden – das Profil des
    eigenen Teams und des Gegners durch (team_profiles), ohne etwas zu
    erfinden. Fehlende Profile werden als Datenluecke vermerkt. Gibt den
    Dateipfad zurueck."""
    team_profiles = team_profiles or {}
    is_week1 = int(week) == 1
    rid = fmlib.make_report_id(player["name"], season, week)
    path = Path(report_dir) / (rid + ".json")

    # Profil des eigenen Teams (nur was in der Eingabe belegt ist)
    own = team_profiles.get(player.get("team"), {})
    team_orientation = own.get("orientation") or {}
    team_strengths = own.get("strengths", [])
    team_weaknesses = own.get("weaknesses", [])

    # Naechster Gegner + Gegnerprofil (Unterfelder IMMER vorhanden, ggf. leer).
    # Gegner-Saisonstatistik: Woche 1 darf Preseason als Fallback nutzen.
    home_away, opp_code = _parse_opp(player.get("opp"))
    opp = team_profiles.get(opp_code, {}) if opp_code else {}
    opp_stats, opp_stats_basis, opp_stats_present = _season_field(
        opp.get("opponent_stats", []), opp.get("preseason_stats", []), is_week1)
    next_opponent = {
        "bye": home_away == "bye",
        "orientation": opp.get("orientation") or {},
        "opponent_stats": opp_stats,
        "strengths": opp.get("strengths", []),
        "weaknesses": opp.get("weaknesses", []),
    }
    opponent_name = opp.get("name", opp_code) if opp_code else player.get("opp")
    if opponent_name:
        next_opponent["opponent"] = opponent_name
    if home_away:
        next_opponent["home_away"] = home_away

    # Spieler-Saisonstatistik + Staerken: Woche 1 darf Preseason als Fallback nutzen.
    game_log, stats_basis, stats_present = _season_field(
        player.get("game_log", []), player.get("preseason_stats", []), is_week1)
    player_strengths, ps_basis, ps_present = _season_field(
        player.get("strengths", []), player.get("preseason_strengths", []), is_week1)

    data_basis = {k: v for k, v in {
        "saison_statistik": stats_basis,
        "gegner_statistik": opp_stats_basis,
        "spieler_staerken": ps_basis}.items() if v}

    # Zusatzinformationen: Spieler-Ebene + eigenes Team + Gegner
    additional_information = list(player.get("additional_information", []))
    additional_information += list(own.get("additional_information", []))
    additional_information += list(opp.get("additional_information", []))

    # News (Sleeper-Feed): Spieler + eigenes Team + Gegner; neueste zuerst belassen
    news = list(player.get("news", []))
    news += list(own.get("news", []))
    news += list(opp.get("news", []))

    injury = {"status": player.get("status", "active")}
    if player.get("practice"):
        injury["practice"] = player["practice"]

    # Vollstaendigkeitspruefung. Zwei Klassen:
    #  - saisonabhaengig: braucht gespielte Spiele; Woche 1 darf Preseason nutzen
    #  - recherchierbar: sollte jetzt vorliegen (Scheme/Profile/News)
    season_dependent = {
        "saison_statistik": stats_present,
        "gegner_statistik": opp_stats_present or home_away == "bye",
        "spieler_staerken": ps_present,
    }
    researchable = {
        "news": bool(news),
        "team_ausrichtung": bool(team_orientation),
        "team_staerken": bool(team_strengths),
        "team_schwaechen": bool(team_weaknesses),
        "gegner_ausrichtung": bool(next_opponent["orientation"]) or home_away == "bye",
        "gegner_staerken": bool(next_opponent["strengths"]) or home_away == "bye",
        "gegner_schwaechen": bool(next_opponent["weaknesses"]) or home_away == "bye",
    }
    present = sorted(k for k, v in researchable.items() if v)
    missing = sorted(k for k, v in researchable.items() if not v)
    season_missing = sorted(k for k, v in season_dependent.items() if not v)
    completeness = {"complete": not missing, "present": present, "missing": missing,
                    "season_dependent_missing": season_missing}
    if is_week1:
        season_note = "{} (saisonabhängig; Woche-1-Preseason-Fallback möglich, sonst offen)"
    else:
        season_note = "{} (aktuelle Saisondaten erforderlich; ab Woche 2 keine Preseason)"
    gaps = (["Eingabe-Snapshot (run_week)"]
            + ["{} nicht abgefragt/belegt".format(m) for m in missing]
            + [season_note.format(m) for m in season_missing])
    preseason_used = sorted(k for k, v in data_basis.items()
                            if v and "preseason" in v.lower())
    if preseason_used:
        gaps.append("Woche-1-Ausnahme: Preseason-Daten für {} (ab Woche 2 nur aktuelle Saison)"
                    .format(", ".join(preseason_used)))

    stats = {"season_data_available": bool(player.get("game_log")), "game_log": game_log}
    if stats_basis:
        stats["basis"] = stats_basis

    obj = {
        "subject": player["name"], "kind": "player", "report_kind": "snapshot",
        "position": player.get("pos"), "nfl_team": player.get("team"),
        "season": season, "week": week, "as_of": as_of,
        "stats": stats,
        "player_strengths": player_strengths,
        "injury": injury,
        "news": news,
        "team_orientation": team_orientation,
        "team_strengths": team_strengths,
        "team_weaknesses": team_weaknesses,
        "next_opponent": next_opponent,
        "additional_information": additional_information,
        "data_basis": data_basis,
        "completeness": completeness,
        "sources": [], "data_gaps": gaps,
    }
    obj["meta"] = {"report_id": rid, "generated_at": as_of,
                   "content_hash": fmlib.content_hash_json(obj)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    return str(path)


def clear_report_dir(report_dir):
    """Entfernt vor einem Lauf alle vorhandenen Dateien aus dem Report-Ordner.

    Der Ordner selbst und Unterverzeichnisse bleiben erhalten. Fehler beim
    Löschen werden bewusst weitergereicht, damit kein Lauf mit alten Reports
    fortgesetzt wird.
    """
    path = Path(report_dir)
    if not path.exists():
        return 0
    if not path.is_dir():
        raise NotADirectoryError("Report-Pfad ist kein Ordner: {}".format(path))
    removed = 0
    for entry in path.iterdir():
        if entry.is_file():
            entry.unlink()
            removed += 1
    return removed


def _quality_factors(player):
    """Nur die vom Evaluator gelieferten Qualitaetsfaktoren (Scheme/Matchup/Form),
    die unabhaengig von der Projektion sind – Basis fuer den Projektions-Tilt."""
    prov = {}
    for k in ("scheme", "matchup", "form"):
        f = (player.get("factors") or {}).get(k)
        if f and f.get("value") is not None:
            prov[k] = {"value": f["value"], "backed": True,
                       "evidence": f.get("evidence", "Report")}
    return prov


def _display_factors(player):
    """Faktoren fuer die Anzeige-Evaluation: Rolle als Projektions-Proxy plus
    gelieferte Qualitaetsfaktoren."""
    factors = {"role": {"value": fmlib.role_from_projection(
        player["pos"], float(player.get("proj", 0.0))),
        "backed": True, "evidence": "Projektion (Proxy)"}}
    factors.update(_quality_factors(player))
    return factors


def build_players(raw_players, week, scoring="half-ppr", all_active=False):
    """Baut die Optimierer-Spielerliste. Nutzt pro Spieler `fmlib.evaluate`:
    - Anzeige-Evaluation (Effektivitaet/Floor/Ceiling/Konfidenz) je Spieler
    - Auswahlwert E = Projektion x Qualitaets-Tilt (aus Scheme/Matchup/Form) x Gate
      → positionsuebergreifend punktvergleichbar (Superflex korrekt)."""
    out = []
    for p in raw_players:
        status = p.get("status", "active")
        gate = 1.0 if all_active and _is_ques(status) \
            else fmlib.injury_gate(status, p.get("practice"))
        on_bye = p.get("bye") == week
        startable = gate > 0 and not on_bye
        games = int(p.get("games", 0))
        sources = int(p.get("sources", 0))
        proj = float(p.get("proj", 0.0))

        # Anzeige-Evaluation (mit Gate)
        ev = fmlib.evaluate(_display_factors(p), gate, games, sources, scoring)
        # Qualitaets-Tilt nur aus unabhaengigen Faktoren (kein Doppelzaehlen der Projektion)
        qf = _quality_factors(p)
        quality = fmlib.evaluate(qf, gate=1.0, games=games, sources=sources,
                                 scoring=scoring)["effectiveness"] if qf else None
        tilt = fmlib.quality_tilt(quality)
        e = round(proj * tilt * gate, 2)

        out.append({"id": pid(p["name"]), "name": p["name"], "pos": p["pos"],
                    "team": p.get("team"), "E": e, "gate": gate,
                    "startable": startable, "on_bye": on_bye,
                    "status": status, "proj": proj, "tilt": round(tilt, 3),
                    "quality": quality, "evaluation": {
                        "effectiveness": ev["effectiveness"], "floor": ev["floor"],
                        "ceiling": ev["ceiling"], "confidence": ev["confidence"],
                        "confidence_label": ev["confidence_label"]}})
    return out


def _is_ques(status):
    return (status or "").strip().lower() in ("questionable", "ques", "q")


def scout_notes(lineup, players_by_id, slots):
    """Erkennt Schwaechen: unbesetzte Slots, angeschlagene Starter ohne gesunden
    Ersatz, Bye-Loecher."""
    notes = []
    elig = {s["name"]: set(s["eligible"]) for s in slots}
    starter_ids = {s["player_id"] for s in lineup["starters"]}
    for slot in lineup.get("unfilled", []):
        notes.append("Slot '{}' unbesetzt – Waiver/Trade pruefen.".format(slot))
    for s in lineup["starters"]:
        pl = players_by_id[s["player_id"]]
        if pl["gate"] < 1.0:
            # gesunder, benchbarer Ersatz gleicher Eignung vorhanden?
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


def _slot_role_phrase(eligible, pos):
    s = set(eligible)
    if len(s) == 1:
        return "Stammplatz {}".format(pos)
    if "QB" in s and len(s) >= 4:
        return "zweiter QB im Superflex" if pos == "QB" else "Superflex-Platz"
    if len(s) >= 3:
        return "Flex-Platz"
    return "Startplatz"


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
    # 1) Coach-Entscheidung + Scheme-Begruendung
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

    # 2) Matchup aus dem Report
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

    # 3) Verfuegbarkeit / News / Staerke als Fliesstext
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


def reason_for_starter(s, players_by_id, slots, report):
    """Fließtext-Begründung, warum dieser Spieler in diesem Slot startet."""
    p = players_by_id[s["player_id"]]
    elig = next(set(sl["eligible"]) for sl in slots if sl["name"] == s["slot"])
    return report_reason(report, _lead_phrase(elig, p["pos"]), is_starter=True)


def reason_for_bench(b_id, players_by_id, report):
    """Fließtext-Begründung, warum dieser Spieler auf der Bank sitzt."""
    p = players_by_id[b_id]
    if p["on_bye"]:
        return "{} sitzt auf der Bank, weil das Team in dieser Woche Bye hat und er " \
               "nicht einsetzbar ist.".format(report.get("subject") or "Der Spieler")
    if p["gate"] == 0:
        return "{} sitzt auf der Bank, weil er laut Status (Out/IR) nicht startfähig " \
               "ist.".format(report.get("subject") or "Der Spieler")
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
    all_ids = [s["player_id"] for s in base["starters"]] + list(base["bench"])
    if all_ids and all(float(players_by_id[i].get("proj", 0) or 0) == 0 for i in all_ids):
        L.insert(2, "> Hinweis: Alle Projektionen in der Eingabe sind 0 → E/Eff sind neutral "
                    "und das Ranking ist noch nicht aussagekräftig. Trage Sleeper-Projektionen "
                    "(Feld `proj`) je Spieler ein, um eine belastbare Startelf zu erhalten.")
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
    L += ["- " + n for n in scout.get("lines", [])]
    if notes:
        L += ["", "**Erkannte Schwächen in der Startelf:**"]
        L += ["- " + n for n in notes]
    L += ["", "### Mögliche zukünftige Probleme"]
    future = scout.get("future_risks", [])
    L += (["- " + f for f in future] if future
          else ["- Keine strukturellen Zukunftsrisiken erkannt (Bye-Verteilung/Status unauffällig)."])
    L += ["", "## Datenvollständigkeit"]
    L.append("_Ausrichtung, Team-/Gegner-Stärken und -Schwächen werden aus der gebündelten "
             "Liga-Wissensbasis + dem Spielplan automatisch befüllt. `news` stammt aus dem "
             "Live-Sleeper-Feed (pro Lauf frisch); Saisonstatistik liegt ab Woche 1 erst nach "
             "gespielten Spielen vor (Woche-1-Preseason-Fallback möglich)._")
    if data_completeness:
        L.append("Bei folgenden Spielern fehlen noch Report-Informationen "
                 "(noch nicht abgefragt/belegt):")
        for pidk, info in data_completeness.items():
            L.append("- **{}** – fehlt: {}".format(info["name"], ", ".join(info["missing"])))
    else:
        L.append("Alle Spieler-Reports vollständig – keine fehlenden Informationen.")
    L += ["", "## Falls QUES aufklart"]
    L += ["- " + d for d in (diffs or ["keine Aenderung"])]
    L += ["", "_Aufstellungswahl über E (= Projektion × Tilt × Gate). Die Begründungen "
          "je Spieler beruhen auf den Report-Fakten (Scheme, Matchup, Verletzung, News, "
          "Stärken), nicht auf den Zahlen; ausführliche 4–6-Satz-Begründung in evaluations-*.json._"]
    return "\n".join(L) + "\n"


def run(args):
    data = json.loads(Path(args.input).read_text(encoding="utf-8-sig"))
    as_of = args.as_of or data.get("as_of") or fmlib.now_iso()
    week = int(data["week"])
    season = int(args.season) if args.season else int(str(as_of)[:4])
    team = data.get("team", "Team")
    scoring = data.get("scoring", "half-ppr")
    slots = data["slots"]
    team_profiles = merge_team_profiles(
        {} if getattr(args, "no_default_profiles", False) else load_default_team_profiles(),
        data.get("team_profiles", {}),
    )
    # Jeder Lauf startet ohne alte Spielerreports. So können veraltete Dateien
    # weder versehentlich weiterverwendet noch mit dem neuen Bundle verwechselt
    # werden.
    clear_report_dir(args.report_dir)
    # Naechsten Gegner je Spieler aus dem gebuendelten Spielplan ableiten, wenn die
    # Eingabe kein 'opp' liefert (Eingabe hat immer Vorrang).
    if not getattr(args, "no_default_profiles", False):
        wk_sched = load_default_schedule().get(str(season), {}).get(str(week), {})
        for p in data["players"]:
            if not p.get("opp") and p.get("team") in wk_sched:
                p["opp"] = wk_sched[p["team"]]

    # 1) Reports pro Spieler frisch erstellen (kein Cache) inkl. Profil-Durchreichung
    schema_path = Path(__file__).resolve().parent / "schemas" / "report.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
    invalid, reports_by_id = [], {}
    for p in data["players"]:
        rpath = ensure_report(p, season, week, as_of, args.report_dir, team_profiles)
        rep = json.loads(Path(rpath).read_text(encoding="utf-8-sig"))
        reports_by_id[pid(p["name"])] = rep
        errs = fmlib.validate(rep, schema)
        if errs:
            invalid.append({"player": p["name"], "errors": errs})

    # 2) Effektivitaet je Spieler via fmlib.evaluate + 3) Optimierung
    players = build_players(data["players"], week, scoring)
    players_by_id = {p["id"]: p for p in players}
    base = fmlib.optimize_lineup(players, slots)

    # 4) Alternative (QUES aktiv) + Diff
    alt = fmlib.optimize_lineup(build_players(data["players"], week, scoring, all_active=True), slots)
    diffs = cleared_diff(base, alt, players_by_id)

    # 5) Scout-Schwaechen + Zusammenfassung
    notes = scout_notes(base, players_by_id, slots)
    scout = scout_summary(data, players, slots, week)

    # Datenvollstaendigkeit je Spieler (welche Infos fehlen im Report)
    data_completeness = {}
    for p in players:
        rep = reports_by_id.get(p["id"], {})
        comp = rep.get("completeness", {})
        if comp.get("missing"):
            data_completeness[p["id"]] = {"name": p["name"], "missing": comp["missing"]}
    incomplete_count = len(data_completeness)

    # 4–6-Satz-Rationale je Spieler (aus Report + Evaluation)
    rationale_by_id = {}
    for p in players:
        rep = reports_by_id.get(p["id"], {})
        sel = {"gate": p["gate"], "tilt": p.get("tilt", 1.0), "quality": p.get("quality")}
        rationale_by_id[p["id"]] = evaluation_rationale(rep, p.get("evaluation", {}), sel, week)

    # Begründungen je Spieler (Starter + Bank) – auf Basis des Spieler-Reports
    starter_reasons = {s["player_id"]: reason_for_starter(
        s, players_by_id, slots, reports_by_id.get(s["player_id"], {}))
        for s in base["starters"]}
    bench_reasons = {b: reason_for_bench(b, players_by_id, reports_by_id.get(b, {}))
                     for b in base["bench"]}

    # Starter mit Evaluator-Werten + Begründung anreichern
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
            "reason": starter_reasons[s["player_id"]],
            "rationale": rationale_by_id.get(s["player_id"])})

    # Ausgabe-Bundle
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
    stem = "lineup-{}-w{}".format(fmlib.slugify(team), week)
    (out_dir / (stem + ".json")).write_text(
        json.dumps(lineup_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / (stem + ".md")).write_text(
        to_markdown(team, week, as_of, scoring, base, players_by_id, notes, diffs,
                    starter_reasons, bench_reasons, scout, data_completeness),
        encoding="utf-8")

    # Evaluations je Spieler (Transparenz) inkl. 4–6-Satz-Rationale
    evals = {p["id"]: {"name": p["name"], "pos": p["pos"], "team": p["team"],
                       "E": p["E"], "proj": p["proj"], "gate": p["gate"],
                       "tilt": p.get("tilt", 1.0), "quality": p.get("quality"),
                       "evaluation": p.get("evaluation", {}),
                       "rationale": rationale_by_id.get(p["id"])}
             for p in players}
    (out_dir / ("evaluations-{}-w{}.json".format(fmlib.slugify(team), week))).write_text(
        json.dumps(evals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "team": team, "week": week, "total_E": base["total_E"],
        "starters": ["{}={}".format(s["slot"], players_by_id[s["player_id"]]["name"])
                     for s in base["starters"]],
        "unfilled": base.get("unfilled", []),
        "reports": {"generated": len(data["players"]),
                    "schema_invalid": len(invalid),
                    "incomplete": incomplete_count},
        "out": str(out_dir / (stem + ".json")),
    }, ensure_ascii=False, indent=2))
    if invalid:
        print("WARN: schema-invalide Reports:\n" +
              json.dumps(invalid, ensure_ascii=False, indent=2), file=sys.stderr)
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description="End-to-End-Wochenrunner.")
    p.add_argument("--input", required=True)
    p.add_argument("--report-dir", default="./temp/reports")
    p.add_argument("--out-dir", default=".")
    p.add_argument("--as-of", default=None)
    p.add_argument("--season", default=None)
    p.add_argument("--no-default-profiles", dest="no_default_profiles",
                   action="store_true",
                   help="Mitgelieferte Team-Ausrichtungs-Wissensbasis nicht laden.")
    return run(p.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
