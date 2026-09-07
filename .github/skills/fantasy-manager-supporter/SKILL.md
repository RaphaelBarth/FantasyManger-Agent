---
name: fantasy-manager-supporter
description: >-
  Orchestriert die Fach-Subskills des Supporters — fantasy-manager-supporter-stats
  (Statistiken), fantasy-manager-supporter-injuries (Verletzungen),
  fantasy-manager-supporter-team-analysis (Team-Ausrichtung + Stärken/Schwächen
  eigenes Team & Gegner) und fantasy-manager-supporter-news (News) — sowie
  zwingend den fantasy-manager-supporter-sleeper-Skill als gemeinsame
  Rohdatenquelle, und fügt die Ergebnisse zu einem einzigen, vollständigen,
  quellenbelegten Report je Spieler/Team zusammen. Nur die aktuelle NFL-Saison
  (Woche-1-Ausnahme möglich). Kein Spielerprofil, keine Fantasy-Prognose, keine
  Empfehlung. Verwende den Skill bei Anfragen wie "Statistiken zu Spieler X",
  "Zahlen zu Team Y" oder "Werte zum nächsten Gegner".
  Nicht für medizinische Diagnosen, Prognosen oder Sportwetten.
---

# Fantasy Manager Supporter

## Ziel

Für einen Spieler oder ein Team einen **vollständigen, quellenbelegten Report**
der aktuellen Saison liefern — Statistik, aktuelle Verletzung, Team-/Gegner-
Ausrichtung samt Stärken/Schwächen und News. Dieser Skill selbst recherchiert
**nicht mehr direkt**: er **orchestriert vier Fach-Subskills**, die jeweils nur
für ihren Ausschnitt zuständig sind, und **fügt deren Ergebnisse zusammen** —
inkl. Reproduzierbarkeit und Vollständigkeitsprüfung. **Kein Cache:** bei
jeder Anfrage werden alle Subskills erneut aufgerufen und ein frischer Report
geschrieben, auch wenn bereits einer vorliegt.

**Sleeper-Referenz:** Ligamodell, Scoring und Roster-/Slot-Regeln folgen der
Wissensbasis [SleeperFantasyManager.md](../fantasy-lineup-coach/SleeperFantasyManager.md).
Bei Custom-/Sleeper-Scoring keine Standardwerte annehmen.

## Sub-Skills (Abhängigkeiten)

| Subskill | Liefert | Primär genutzt für |
|---|---|---|
| [fantasy-manager-supporter-sleeper](../fantasy-manager-supporter-sleeper/SKILL.md) | Rohdatenpaket von sleeper.com/nfl (Status, Game-Log/Stats, News-Feed, Team-/Schedule-Kontext) | Zwingende gemeinsame Ausgangsbasis/Kreuzcheck für alle vier Fach-Subskills |
| [fantasy-manager-supporter-team-analysis](../fantasy-manager-supporter-team-analysis/SKILL.md) | Nächster Gegner (Team/Datum/Heim-Auswärts/Bye), Team-Ausrichtung + Stärken/Schwächen (eigenes Team & Gegner) **und Gegner-Statistik** | `team_orientation`, `team_strengths`, `team_weaknesses`, `next_opponent.*` (inkl. `opponent_stats`) |
| [fantasy-manager-supporter-stats](../fantasy-manager-supporter-stats/SKILL.md) | Saisonstatistik, Game Log, metrik-belegte Spieler-Stärken des Subjekts selbst | `stats`, `player_strengths` |
| [fantasy-manager-supporter-injuries](../fantasy-manager-supporter-injuries/SKILL.md) | Aktueller Verletzungs-/Statusstatus | `injury` |
| [fantasy-manager-supporter-news](../fantasy-manager-supporter-news/SKILL.md) | Aktuelle News (Sleeper-Feed + Insider) | `news` |

Jeder Fach-Subskill ist **eigenständig aufrufbar** (z. B. „nur die Statistik zu
X"); dieser Skill wird nur gebraucht, wenn der **komplette** Report gefragt ist.

## Eingaben

```text
subject: Spielername oder Teamname
season: Saison, optional; standardmäßig aktuelle NFL-Saison
week: NFL-Woche, optional
as_of: ISO-8601-Zeitpunkt, optional; standardmäßig jetzt
report_dir: Ablageort der Reports, optional; Standard ./temp/reports
```

Ist der Name mehrdeutig, vor der Recherche nach Team/Position fragen.

## Ablauf (Orchestrierung)

Kein Cache: dieser Ablauf wird bei **jeder** Anfrage vollständig durchlaufen —
auch wenn bereits ein Report mit derselben `report_id` existiert.

1. **Gemeinsame Rohdatenbasis (Pflicht):** `fantasy-manager-supporter-sleeper` einmal für
   `subject` (und ggf. eigenes Team/absehbarer Gegner) aufrufen. Das Ergebnis
   wird den vier Fach-Subskills als **Ausgangspunkt/Kreuzcheck** mitgegeben,
   um doppelte Abrufe zu vermeiden — ersetzt aber nicht deren eigene
   Primärquellen-Pflicht (Sleeper-Werte sind für Statistik/Stärken/Schwächen
   nie alleiniger Beleg, siehe die jeweiligen Subskills).
2. **Team-Auswertung zuerst (Pflicht):** `fantasy-manager-supporter-team-analysis`
   aufrufen. Liefert den **nächsten Gegner** (Team, Datum, Heim/Auswärts/Bye),
   Ausrichtung + Stärken/Schwächen beider Seiten **und die Gegner-Statistik**
   (`next_opponent.opponent_stats`) — der Gegner wird hier ohnehin aufgelöst,
   daher liefert dieser Subskill alles, was den Gegner betrifft, in einem Zug.
3. **Statistik, Verletzung, News** (parallel/danach, alle drei Pflicht). Der Statistik-Subskill
   braucht keinen aufgelösten Gegner mehr — er befasst sich ausschließlich mit
   dem Subjekt selbst:
   - `fantasy-manager-supporter-stats`
   - `fantasy-manager-supporter-injuries`
   - `fantasy-manager-supporter-news`
4. **Zusammenführen** aller vier Fach-Ergebnisse und der Collector-Rohdaten in das einheitliche
   Report-Schema (siehe „Verbindliches Ausgabeformat"), `additional_information`
   aus allen Subskills zusammenführen (Duplikate anhand Quelle/Aussage
   vermeiden).
5. **Vollständigkeitsprüfung berechnen** (`completeness`, siehe unten) und
   `data_gaps` aus den von den Subskills gemeldeten Lücken bilden.
6. **Stempeln & schreiben:** `meta.report_id`, `generated_at`, `content_hash`
   (nur über den Faktenteil) setzen und über `tools/report_cache.py` (im
   `fantasy-lineup-coach`-Skill) bzw. dessen Runner ablegen — eine ggf.
   vorhandene Datei gleicher `report_id` wird dabei **überschrieben**.

Schlägt der Collector oder ein Fach-Subskill fehl oder liefert nichts, wird sein Anteil als
„nicht abgefragt/belegt" markiert — die anderen drei Anteile werden trotzdem
zusammengeführt (kein Total-Abbruch wegen eines einzelnen Subskills).

## Grundregeln (gelten für alle Subskills gemeinsam)

- **Nur die aktuelle Saison – mit Woche-1-Ausnahme.** Preseason-Daten nur in
  Woche 1, klar als `data_basis: "preseason (Woche 1)"` gekennzeichnet; ab
  Woche 2 ausschließlich aktuelle Saisondaten.
- **Nur belegte Fakten.** Keine Fantasy-Prognose, kein Ausblick, keine
  Start/Sit-Empfehlung. Stärken/Schwächen nur metrik-belegt mit Quelle.
- **Keine Annahmen.** Ohne Beleg: „nicht belegt"/„noch keine Saisondaten" statt
  zu schätzen oder herzuleiten.
- **Kein Spielerprofil.** Keine Biografie (Größe, Gewicht, College, Draft, Alter).
- **Verletzungen nur aktuell.** Keine Historie (siehe Injuries-Subskill).
- **Vollständige, einheitliche Struktur.** Jeder Report enthält **alle**
  Abschnitte/Felder — auch wenn ein Wert fehlt (dann leer + „nicht
  belegt/abgefragt"). Kein Feld wird bei einem Spieler weggelassen, bei einem
  anderen aber gesetzt.
- Ausführliche, subskill-spezifische Regeln (Quellen-Tiers, Formate) stehen in
  den jeweiligen Fach-Subskills, nicht doppelt hier.

## Vollständigkeitsprüfung (`completeness`)

Jeder zusammengeführte Report führt aus, welche Infos vorhanden (`present`)
und welche noch offen sind. Die Kategorien bilden 1:1 auf die vier Subskills ab:

| Kategorie | Subskill | Klasse |
|---|---|---|
| `saison_statistik`, `spieler_staerken` | Statistik | saisonabhängig (`season_dependent_missing`; Woche-1-Preseason-Fallback möglich) |
| `news` | News | recherchierbar jetzt (`missing`) |
| `team_ausrichtung`, `team_staerken`, `team_schwaechen`, `gegner_ausrichtung`, `gegner_staerken`, `gegner_schwaechen` | Team-Auswertung | recherchierbar jetzt (`missing`) |
| `gegner_statistik` | Team-Auswertung | saisonabhängig (`season_dependent_missing`; Woche-1-Preseason-Fallback möglich) |

`complete` bezieht sich nur auf die recherchierbaren Felder (`missing`), nicht
auf `season_dependent_missing`. Liefert ein Subskill kein Ergebnis, zählt sein
gesamter Anteil als offen in der jeweiligen Klasse.

## Aktualität (kein Cache)

Bei **jeder Anfrage** wird **pro Spieler ein neuer Report** erstellt — ganz
gleich, ob und wie alt ein vorhandener Report mit derselben `report_id` ist.

Ablauf je Spieler:
1. Alle fünf Subskills (Sleeper-Rohdaten + vier Fach-Subskills) frisch aufrufen;
   der Sleeper-Collector ist dabei nicht optional.
2. Ergebnisse zusammenführen und die Report-Datei über die stabile `report_id`
   (siehe unten) in `report_dir` **schreiben/überschreiben** — unabhängig
   davon, ob dort bereits eine Datei existiert oder wie alt sie ist.

## Reproduzierbarkeit (deterministische Erstellung)

Der Report muss bei gleichen Eingaben und gleichem Quellenstand **identisch**
sein. Regeln:

- **Stabile ID/Datei:** `report_id = slug(subject)-<season>[-w<week>]`; Dateiname
  daraus, **nicht** aus der Zeit. Re-Runs überschreiben dieselbe Datei mit
  frischen Daten.
- **Fester Aufruf-/Quellensatz & feste Reihenfolge:** je Subjekt immer dieselbe
  Subskill-Reihenfolge (Team-Auswertung → Statistik/Verletzung/News) und
  dieselben Primärquellen je Subskill; keine zufällige Auswahl.
- **Festes Template:** exakt die vorgegebene Abschnitts- und Spaltenreihenfolge;
  nur Fakten in Tabellen, keine frei variierende Prosa.
- **Feste Formate:** einheitliche Zahlenformate (z. B. eine Nachkommastelle),
  ISO-Daten, stabile Sortierung (Game Log nach Woche aufsteigend, Quellen in
  fester Reihenfolge, News neueste zuerst).
- **Provenienz:** jede Zahl mit URL + Veröffentlichungsdatum + Abrufzeit
  (`retrieved_at`).
- **`as_of` ist maßgeblich:** nur Daten bis `as_of`; dadurch ist der Faktenteil
  bei gegebenem `as_of` unabhängig von der realen Uhrzeit reproduzierbar.
- **Stempel & Prüfsumme:** Header trägt `report_id`, `generated_at` und
  `content_hash` (Hash nur über den Faktenteil **ohne** `generated_at`). Zwei
  Läufe mit gleichem Quellenstand ergeben denselben `content_hash`; ändert sich
  nichts an den Fakten, ändert sich nur `generated_at`.

### Werkzeug (schreibt Reports frisch, ohne Cache; prüft Reproduzierbarkeit)

Das Skript [tools/report_cache.py](../fantasy-lineup-coach/tools/report_cache.py)
(baut auf [tools/fmlib.py](../fantasy-lineup-coach/tools/fmlib.py) auf, nur
Python-Standardbibliothek; beide liegen im `fantasy-lineup-coach`-Skill,
dem alleinigen Ausführer dieser Tools) setzt beide Regeln deterministisch
um — für **Markdown- und JSON-Reports**:

```
# JSON-Report schreiben (ueberschreibt einen ggf. vorhandenen Report) + gegen Schema pruefen:
python ../fantasy-lineup-coach/tools/report_cache.py writejson --subject "Sam LaPorta" --season 2026 --week 1 \
    --report-dir ./temp/reports --as-of <ISO> --schema ../fantasy-lineup-coach/tools/schemas/report.schema.json --facts facts.json

# Markdown-Report schreiben/stempeln (Titelzeile + Abschnitte, ohne Meta-Zeile):
python ../fantasy-lineup-coach/tools/report_cache.py write --subject "Sam LaPorta" --season 2026 --week 1 \
    --report-dir ./temp/reports --as-of <ISO> --facts facts.md

# Reproduzierbarkeit pruefen:
python ../fantasy-lineup-coach/tools/report_cache.py hashjson --facts facts.json   # Hash zweier Laeufe vergleichen
python ../fantasy-lineup-coach/tools/report_cache.py verify --path ./temp/reports/<id>.json   # gespeicherten Hash nachrechnen
python ../fantasy-lineup-coach/tools/report_cache.py validate --path report.json --schema ../fantasy-lineup-coach/tools/schemas/report.schema.json
```

Bevorzugt wird das **JSON-Format** (maschinenlesbar, schema-validiert), das
Evaluator und Coach direkt konsumieren. Der `content_hash` deckt nur den
Faktenteil ab (ohne `meta`/`generated_at`), sodass identische
Subskill-Ergebnisse nachweisbar identische Reports liefern.

## Verbindliches Ausgabeformat

```markdown
# NFL Statistik: <subject>
report_id: <slug-season[-wWoche]> | generated_at: <ISO-8601> | content_hash: <hash>
Stand (as_of): <as_of> | Saison: <...> | Quelle der aktuellen Saison

## Statistik (aktuelle Saison)
### Übersicht
| G | Start | <positions-/teamrelevante Spalten> |
### Game Log
| Woche | Gegner | <relevante Spalten> |

## Stärken (Spieler, belegt)
| Stärke | Metrik/Wert (Rang) | Quelle | Datum |
(nur metrik-belegt; sonst "nicht belegt")

## Aktuelle Verletzung
| Datum | Status/Meldung | Quelle |
(nur das aktuelle Thema; sonst "keine aktuelle Verletzungsmeldung")

## News (Sleeper-Feed + Primärquellen)
| Datum | Meldung | Feed-Quelle (NFL/FF News/NFL Community) | Outlet/Autor | bestätigt? |
(aktuelle, relevante News; „NFL Community" nur mit Bestätigung, sonst „unbestätigt")

## Team-Ausrichtung (eigenes Team)
- Offense: HC/OC, Schema, Lauf/Pass-Tendenz, Personnel
- Defense: DC, Front, Coverage-/Pressure-Tendenz
- Bevorzugte Spielertypen:
- Stärken des eigenen Teams (belegt):
  | Stärke | Metrik/Wert (Rang) | Quelle |
- Schwächen des eigenen Teams (belegt):
  | Schwäche | Metrik/Wert (Rang) | Quelle |

## Nächster Gegner
- Gegner, Home/Away, Datum (keine Uhrzeit, kein Sender); ggf. Bye-Week
- Statistiken des Gegners (aktuelle Saison):
  | Metrik | Wert | Liga-Rang | Quelle |
- Stärken des Gegners (belegt):
  | Stärke | Metrik/Wert (Rang) | Quelle |
- Schwächen des Gegners (belegt):
  | Schwäche | Metrik/Wert (Rang) | Quelle |
- Ausrichtung des Gegners:
  - Offense: HC/OC, Schema, Lauf/Pass-Tendenz, Personnel
  - Defense: DC, Front, Coverage-/Pressure-Tendenz
  - Bevorzugte Spielertypen:

## Zusatzinformationen (optional)
| Info | Quelle | Datum |
(nur belegte Kontextinfos; sonst weglassen)

## Datenvollständigkeit
- present: [...] | missing: [...] | season_dependent_missing: [...]

## Quellen
1. [Quelle](URL) — Quellentyp, Datum
- Konflikte / fehlende Werte ("noch keine Saisondaten")
```

Keine weiteren Abschnitte (kein Profil, keine Einschätzung, keine Prognose).
Für die maschinenlesbare Form siehe `fantasy-lineup-coach/tools/schemas/report.schema.json`
(identische Feldnamen, vom Orchestrator aus den vier Subskill-Fragmenten
zusammengesetzt).
