---
name: fantasy-manager-supporter-stats
description: >-
  Fach-Subskill des Supporters: trägt ausschließlich reine Statistiken der
  aktuellen NFL-Saison des Subjekts selbst zusammen — Spieler-Saisonwerte,
  Game Log und metrik-belegte Spieler-Stärken (bzw. Team-Record/-Werte).
  Woche-1-Preseason-Ausnahme möglich. Kein Profil, keine Verletzung, keine
  News, keine Team-Ausrichtung/Stärken-Schwächen-Bewertung und keine
  Gegner-Statistik — dafür siehe die Geschwister-Subskills (Gegner-Statistik
  gehört zu fantasy-manager-supporter-team-analysis, da dieser den Gegner
  ohnehin auflöst). Wird vom fantasy-manager-supporter orchestriert, kann aber
  auch einzeln für "Statistik zu Spieler X" genutzt werden.
---

# Fantasy Manager Supporter — Statistiken

## Ziel

Nur die **Zahlen** der aktuellen Saison des Subjekts selbst liefern:
Volumen-/Produktionswerte, Game Log, Pro-Spiel-Schnitte und — wenn vorhanden —
metrik-belegte Stärken des Spielers. Für ein Team: Record, erzielte/
zugelassene Werte. Keine Bewertung, kein Schema/Scheme, keine Verletzung,
keine News, **keine Gegner-Statistik** (die gehört zur Team-Auswertung).

## Abgrenzung zu den Geschwister-Subskills

| Nicht Teil dieses Skills | Zuständig |
|---|---|
| Team-/Gegner-Ausrichtung (Scheme), Stärken/Schwächen von Teams | `fantasy-manager-supporter-team-analysis` |
| **Gegner-Statistik** (Werte der gegnerischen Defense/Offense gegen die Position/Team) | `fantasy-manager-supporter-team-analysis` — der Skill löst den Gegner ohnehin auf und liefert Ausrichtung + Stärken/Schwächen + Statistik in einem Zug |
| Verletzungsstatus | `fantasy-manager-supporter-injuries` |
| News/Meldungen | `fantasy-manager-supporter-news` |
| Wer der nächste Gegner ist (Team, Datum, Heim/Auswärts, Bye) | `fantasy-manager-supporter-team-analysis` |

## Eingaben

```text
subject: Spielername oder Teamname (Pflicht)
season: Saison, optional; standardmäßig aktuelle NFL-Saison
week: NFL-Woche, optional
as_of: ISO-8601-Zeitpunkt, optional; standardmäßig jetzt
```

Dieser Skill braucht **keinen aufgelösten Gegner** — er befasst sich
ausschließlich mit dem Subjekt selbst.

## Grundregeln

- **Nur die aktuelle Saison – mit Woche-1-Ausnahme.** Preseason-Daten sind
  **ausschließlich in Woche 1** und nur als klar gekennzeichneter Fallback
  erlaubt (`data_basis: "preseason (Woche 1)"`), wenn noch kein Saisonspiel
  vorliegt. Ab Woche 2 zählen ausschließlich aktuelle Saisondaten.
- **Keine Annahmen/Schätzungen.** Liegt kein Spiel vor: „noch keine
  Saisondaten" statt Vorjahres-/Karrierewerte einzusetzen.
- **Stärken nur metrik-belegt.** Eine „Stärke" ist nur zulässig mit konkreter
  Metrik + Wert/Rang + Quelle + Datum der aktuellen Saison (z. B. Target-Share,
  Snap-/Route-Anteil, YAC/Air Yards, Red-Zone-Nutzung, Separation, Yards nach
  Kontakt, Completion-/Pressure-Werte). Ohne Beleg weglassen, nie werten.
- **Kein Spielerprofil.** Keine Biografie (Größe, Gewicht, College, Draft, Alter).
- Jede Zahl mit Quelle + Datum; keine Scheinpräzision (konsistente
  Nachkommastellen).

## Sleeper als Hilfsquelle (Sub-Subskill)

Der Skill `fantasy-manager-sleeper-nfl-data` (Sleeper NFL Data Collector) darf
als **Ausgangspunkt/Kreuzcheck** aufgerufen werden — z. B. um schnell zu sehen,
welche Spiele/Wochen bereits existieren oder welchen Game-Log Sleeper zeigt.
**Sleeper-Werte allein sind kein hinreichender Beleg** für Statistik oder
Stärken; sie müssen gegen eine Tier-A/B-Primärquelle (siehe unten) bestätigt
werden, bevor sie in den Report übernommen werden. Bei Abweichung gilt die
Primärquelle.

## Quellenstrategie

Kanonisch: [sources.md](../../sources.md),
nur **Tier A/B** (nicht die News-Tiers):
1. `nfl.com` (Spieler-/Team-Statistik, Gamebooks)
2. Offizielle Teamseite
3. ESPN (Stats, Game Logs, Schedule)
4. NFL Next Gen Stats (Tracking-Metriken)
5. Pro-Football-Reference (Splits, Team-Defense vs. Position)
6. Ergänzend: PFF, FTN/DVOA, Sharp Football, rbsdm.com/Sumer Sports

Aggregatoren (FantasyPros, Rotowire, PlayerProfiler, StatMuse) nur als
Rückverweis, nie als alleiniger Beleg. Suchmaschinen-Snippets zählen nicht.

## Zu sammelnde Werte

### Spieler
- Spiele, Starts
- Passing: Attempts, Completions, Yards, TD, INT, Sacks
- Rushing: Carries, Yards, TD, Fumbles
- Receiving: Targets, Receptions, Yards, TD
- Pro-Spiel-Werte, wenn offiziell verfügbar Snap-/Route-/Target-Anteile
- Game Log der bisherigen Spiele (Woche, Gegner, relevante Spalten)
- Metrik-belegte Stärken (siehe oben)

### Team
- Record, erzielte/zugelassene Punkte
- Offense: Pass-/Laufyards, Yards gesamt
- Defense: zugelassene Pass-/Laufyards, Sacks, Turnover

## Ausgabe: JSON-Fragment

Deckt genau den Statistik-Teil des Supporter-Gesamtschemas ab
(`tools/schemas/report.schema.json`), damit der Orchestrator es 1:1 einfügen kann:

```json
{
  "stats": {
    "games": 0, "starts": 0, "season_data_available": false,
    "basis": "aktuelle Saison | preseason (Woche 1)",
    "totals": {}, "game_log": [{"week": 1, "opponent": "..."}]
  },
  "player_strengths": [
    {"claim": "...", "metric": "...", "value": "...", "rank": 0,
     "source": "...", "date": "..."}
  ],
  "data_basis": {"saison_statistik": "..."},
  "sources": [{"url": "...", "type": "...", "published": "...", "retrieved_at": "..."}],
  "notes": ["noch keine Saisondaten", "..."]
}
```

## Ausgabe: Markdown (Fragment)

```markdown
## Statistik (aktuelle Saison)
### Übersicht
| G | Start | <positions-/teamrelevante Spalten> |
### Game Log
| Woche | Gegner | <relevante Spalten> |

## Stärken (Spieler, belegt)
| Stärke | Metrik/Wert (Rang) | Quelle | Datum |
```

## Abnahmekriterien

1. Nur aktuelle Saison (Woche-1-Ausnahme klar gekennzeichnet).
2. Jede Zahl/Stärke mit Tier-A/B-Quelle + Datum; Sleeper-Werte nur als
   Kreuzcheck, nie alleiniger Beleg.
3. Keine Team-Ausrichtung, keine Verletzung, keine News, **keine
   Gegner-Statistik** im Output.
4. Fehlende Werte klar als „noch keine Saisondaten"/„nicht belegt" markiert.
