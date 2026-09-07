# FantasyManagerSupport

Skill-Familie und Werkzeuge, um für eine **Sleeper**-NFL-Fantasy-Liga Daten zu
sammeln, Spieler zu bewerten, die beste Wochenaufstellung zu bauen und Waiver-/
Trade-Chancen zu finden — reproduzierbar und ohne Cache (jeder Lauf zieht
frische Daten).

## Skill-Hierarchie

```
 Fantasy Manager Agent (fantasy-manager-agent)   oberster Orchestrator
 ├─ Supporter (fantasy-manager-supporter)   orchestriert 4 Fach-Subskills + Sleeper-Collector
 │   ├─ Sleeper Collector (fantasy-manager-supporter-sleeper)   öffentliche Sleeper-Rohdaten (gemeinsame Basis)
 │   ├─ Statistiken (fantasy-manager-supporter-stats)          Saisonwerte, Game Log, Spieler-Stärken
 │   ├─ Verletzungen (fantasy-manager-supporter-injuries)      aktueller Status/Practice
 │   ├─ Team-Auswertung (fantasy-manager-supporter-team-analysis)  Ausrichtung + Stärken/Schwächen + Statistik (Team & Gegner)
 │   └─ News (fantasy-manager-supporter-news)                  Sleeper-News-Feed + Insider
 ├─ Evaluator (fantasy-effectiveness-evaluator)  Effektivitaet je Spieler
 ├─ Coach (fantasy-lineup-coordinator)      normale Aufstellungsplanung
 └─ Scout (fantasy-opportunity-scout)       Sleeper- & Trade-Kandidaten
                                             (nutzt Supporter + Evaluator)
Regelbasis: .github/skills/fantasy-lineup-coordinator/SleeperFantasyManager.md
```

- [fantasy-manager-supporter](./.github/skills/fantasy-manager-supporter/SKILL.md) —
  **Orchestrator**: ruft die vier Fach-Subskills unten **sowie zwingend den Sleeper-
  Collector als gemeinsame Rohdatenbasis** auf und fügt die Ergebnisse zu **einem**
  Report zusammen — **nur aktuelle Saison**: Statistiken, belegte **Spieler-
  Stärken** und **Gegner-Stärken/-Schwächen**, aktuelle Verletzung,
  Team-Ausrichtung (eigenes Team + Gegner), nächster Gegner. Kein Profil, keine
  Prognose, keine Annahmen. Quellenbasis:
  [sources.md](./.github/skills/fantasy-manager-supporter/sources.md).
  - [fantasy-manager-supporter-stats](./.github/skills/fantasy-manager-supporter-stats/SKILL.md)
    — nur Statistiken des Subjekts selbst (Saisonwerte, Game Log, metrik-belegte
    Spieler-Stärken; **keine** Gegner-Statistik).
  - [fantasy-manager-supporter-injuries](./.github/skills/fantasy-manager-supporter-injuries/SKILL.md)
    — nur aktueller Verletzungs-/Statusstatus, keine Historie.
  - [fantasy-manager-supporter-team-analysis](./.github/skills/fantasy-manager-supporter-team-analysis/SKILL.md)
    — nächster Gegner + Team-Ausrichtung/-Stärken/-Schwächen (eigenes Team & Gegner)
    **und Gegner-Statistik** (da der Gegner hier ohnehin aufgelöst wird).
  - [fantasy-manager-supporter-news](./.github/skills/fantasy-manager-supporter-news/SKILL.md)
    — nur News (Sleeper-Feed NFL/FF News/NFL Community + verifizierte Insider).
- [fantasy-manager-supporter-sleeper](./.github/skills/fantasy-manager-supporter-sleeper/SKILL.md) — erfasst alle öffentlich
  sichtbaren Sleeper-NFL-Daten zu genau einem Spieler oder Team, einschließlich
  Quellen, Filtern, Abrufzeit und expliziter Datenlücken. Dient dem Supporter und
  seinen Fach-Subskills als gemeinsame Rohdatenbasis/Kreuzcheck.
- [fantasy-effectiveness-evaluator](./.github/skills/fantasy-effectiveness-evaluator/SKILL.md) — macht
  aus einem Report einen Effektivitätswert (Faktoren: Rolle, Scheme-Fit, Matchup,
  Form; Verfügbarkeits-Gate; Konfidenz).
- [fantasy-opportunity-scout](./.github/skills/fantasy-opportunity-scout/SKILL.md) — findet Sleeper
  (Waiver/FA) und Buy-low/Sell-high/Trade-Paarungen.
- [fantasy-manager-agent](./.github/agents/fantasy-manager-agent.agent.md) —
  oberster Einstiegspunkt; routet und orchestriert alle Fachskills.
- [fantasy-lineup-coordinator](./.github/skills/fantasy-lineup-coordinator/SKILL.md) —
  normaler Aufstellungs-Skill; optimiert nur die Slot-Zuordnung.
- [SleeperFantasyManager.md](./.github/skills/fantasy-lineup-coordinator/SleeperFantasyManager.md)
  — Sleeper-Regelbasis (Slots, Scoring, Waiver/FAAB, Trades).

## Datenfluss

```
Anfrage ─▶ Fantasy Manager Agent
             ├─▶ Supporter (Report je Spieler, JSON, immer frisch – kein Cache)
             ├─▶ Evaluator (Effektivitaet E + Gate)
             ├─▶ Coach (exakte Slot-Zuordnung ─▶ beste Elf)
             └─▶ Scout (bei Schwaeche: Waiver/Trade)
```

## Werkzeuge (je Skill-Ordner unter `tools/`, nur Python-Standardbibliothek)

Jeder Skill, der Code ausführt, bringt seine Tools als direkten Unterordner
`tools/` mit — kein geteilter Top-Level-`tools/`-Ordner mehr.

| Datei | Skill (Owner) | Zweck |
|---|---|---|
| [fmlib.py](./.github/skills/fantasy-lineup-coordinator/tools/fmlib.py) | fantasy-lineup-coordinator | IDs, ISO-Zeit, `content_hash` (Text/JSON), `injury_gate`, Mini-Schema-Validator, Ungarischer Optimizer `optimize_lineup` |
| [report_cache.py](./.github/skills/fantasy-lineup-coordinator/tools/report_cache.py) | fantasy-lineup-coordinator | Reports schreiben (md/json, kein Cache — jeder Aufruf überschreibt frisch), `verify`, `validate` |
| [run_week.py](./.github/skills/fantasy-lineup-coordinator/tools/run_week.py) | fantasy-lineup-coordinator | End-to-End: Kader → frische Reports (kein Cache — jeder Lauf zieht neue Daten, **einheitliche Struktur + Vollständigkeitsprüfung**) → **Evaluator je Spieler** (`fmlib.evaluate`) → evaluator-adjustierte Punkte → optimale Elf → Scout-Zusammenfassung → Bundle (`lineup-*`, `evaluations-*`, inkl. `data_completeness`) |
| [schemas/](./.github/skills/fantasy-lineup-coordinator/tools/schemas) | fantasy-lineup-coordinator | JSON-Schemas: report, evaluation, lineup |
| [cleanup_generated.py](./.github/skills/fantasy-manager-cleanup/tools/cleanup_generated.py) | fantasy-manager-cleanup | Sicherer Cleanup für erzeugte `out-*`-, `reports-*`- und `temp`-Ausgabeordner; Dry-Run standardmäßig aktiv |

Andere Skills (Supporter, Evaluator, Team-Auswertung) **führen diese Tools nicht
selbst aus** — sie referenzieren nur den `fantasy-lineup-coordinator`-Skill als
alleinigen Ausführer, um Codeduplikate zu vermeiden.

**Auto-Befüllung ohne Recherche:** Schon aus einem nackten Kader (nur `team`/`pos`
je Spieler) füllt der Runner `team_ausrichtung`, `team_staerken`/`-schwaechen`,
den nächsten Gegner sowie `gegner_ausrichtung`/`-staerken`/`-schwaechen` aus der
gebündelten Wissensbasis + dem Spielplan. Eingabe-Profile/-`opp` überschreiben die
Defaults; mit `--no-default-profiles` lassen sich die Defaults abschalten. Nur
`news` (Live-Sleeper-Feed) und die Saisonstatistik (ab Woche 1 erst nach Spielen,
Woche-1-Preseason-Fallback möglich) bleiben eingabe-/saisonabhängig.

## Schnellstart

```bash
# Beste Aufstellung fuer eine Woche berechnen (End-to-End):
python .github/skills/fantasy-lineup-coordinator/tools/run_week.py \
    --input tools/examples/team-r4ph4.week1.input.json \
    --report-dir ./temp/reports --out-dir . --json-dir ./temp --as-of 2026-09-03T21:00:00+02:00

```

Ergebnis auf oberster Ebene (finaler Report): `lineup-<team>-w<n>.md` (mit
Scout-Zusammenfassung und Begründung je Spieler). Die maschinenlesbaren
Begleitdateien `lineup-<team>-w<n>.json` und `evaluations-<team>-w<n>.json`
(Effektivität, Floor/Ceiling, Konfidenz, 4–6-Satz-Rationale je Spieler) sowie
die temporären Spieler-Reports landen in `./temp/`.

## Ordner `temp/`

Alle Skills/Agenten legen temporäre bzw. autogenerierte Zwischendateien
(Roh-Reports, abgeleitete Eingabe-JSONs) unter `temp/` ab. Der Ordner ist in
`.gitignore` ausgeschlossen und wird von
[cleanup_generated.py](./.github/skills/fantasy-manager-cleanup/tools/cleanup_generated.py)
mitgeräumt. Finale Reports/Bundles bleiben auf oberster Ebene und werden nicht
angefasst.

## Reproduzierbarkeit (kein Cache)

- **Kein Cache:** jeder Lauf/jede Anfrage erzeugt für jeden Spieler einen neuen
  Report. Zu Beginn des Laufs werden vorhandene Dateien im angegebenen
  Report-Ordner gelöscht; anschließend werden die Reports frisch geschrieben.
  Es wird nie ungeprüft ein alter Report wiederverwendet.
- **`content_hash`:** Prüfsumme über den Faktenteil (ohne `meta`/`generated_at`).
  Gleiche Eingaben/Quellen → gleicher Hash; nur `generated_at` variiert.
- Prüfen: `python .github/skills/fantasy-lineup-coordinator/tools/report_cache.py verify --path <report>`.

## Datenquellen-Grundsätze

Offizielle NFL-/Team-/ESPN-/PFR-Quellen zuerst, jede Zahl mit Quelle und Datum,
nur aktuelle Saison, keine erfundenen Spieler/Statistiken, **keine Annahmen**.
Stärken/Schwächen nur metrik-belegt; Insider-Tweets und der **Sleeper-News-Feed**
(Feed-Quellen NFL / FF News / NFL Community) nur für News – mit Feed-Quelle,
Outlet/Autor und Zeitstempel, nie für Statistik; „NFL Community" nie als
alleiniger Beleg. Kanonische Liste:
[sources.md](./.github/skills/fantasy-manager-supporter/sources.md).
Eingaben ohne belegte Werte werden als „noch keine Saisondaten" gekennzeichnet.
