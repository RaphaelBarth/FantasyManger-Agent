---
name: fantasy-manager-supporter-team-analysis
description: >-
  Fach-Subskill des Supporters: bestimmt den nächsten Gegner (Team, Datum,
  Heim/Auswärts, Bye) und trägt die Team-Ausrichtung (Offense-/Defense-Schema,
  Coordinators, bevorzugte Spielertypen), metrik-belegte Team-Stärken/
  -Schwächen UND die Gegner-Statistik (Werte des Gegners gegen die relevante
  Position/Team) zusammen — jeweils für das eigene Team UND den nächsten
  Gegner. Keine Statistik des Subjekts selbst, keine Verletzung, keine News,
  keine Fantasy-Bewertung. Wird vom fantasy-manager-supporter orchestriert,
  kann aber auch einzeln für "Ausrichtung von Team X" oder "wie steht Y gegen
  den nächsten Gegner da" genutzt werden.
---

# Fantasy Manager Supporter — Team-Auswertung

## Ziel

Für das **eigene Team** eines Spielers (bzw. ein direkt abgefragtes Team) und
für dessen **nächsten Gegner** die faktische Ausrichtung (Scheme), metrik-
belegte Stärken/Schwächen **und die Gegner-Statistik** zusammentragen — als
Fakten mit Quelle, ohne Bewertung oder Prognose. Dieser Skill **identifiziert
auch den nächsten Gegner** (Team, Datum, Heim/Auswärts/Bye); da er den Gegner
ohnehin auflöst, liefert er auch dessen **Statistik gegen die relevante
Position/Team** gleich mit — die Geschwister-Subskills (Statistik, News)
müssen den Gegner nicht erneut auflösen.

## Abgrenzung zu den Geschwister-Subskills

| Nicht Teil dieses Skills | Zuständig |
|---|---|
| Statistikwerte des Subjekts selbst (Zahlen, Game Log) | `fantasy-manager-supporter-stats` |
| Verletzungsstatus | `fantasy-manager-supporter-injuries` |
| News/Meldungen | `fantasy-manager-supporter-news` |

Die **Gegner-Statistik** (`next_opponent.opponent_stats`) ist Teil **dieses**
Skills, nicht von `fantasy-manager-supporter-stats` — sie gehört fachlich zur
Gegner-Auswertung, nicht zur Eigenstatistik des Subjekts.

## Eingaben

```text
subject: Spielername oder Teamname (Pflicht)
season: Saison, optional
week: NFL-Woche, optional
as_of: ISO-8601-Zeitpunkt, optional; standardmäßig jetzt
```

## Grundregeln

- **Nur belegte Fakten, keine Bewertung.** Stärken/Schwächen ausschließlich als
  **metrik-belegte Fakten mit Quelle** (z. B. „erlaubt die meisten Yards/Spiel
  an TE, Rang 32"), nie als Meinung.
- **Keine Annahmen.** Ohne konkrete Metrik der aktuellen Saison aus
  verlässlicher Quelle: weglassen, als „nicht belegt" markieren.
- **Erwartungen klar kennzeichnen.** Zu Saisonbeginn (Woche 1, noch keine
  Statistik) dürfen **erwartete** Scheme-Tendenzen (z. B. laut Beat-Reportern/
  Trainingslager-Berichten) verwendet werden, aber ausdrücklich als „Erwartung,
  noch nicht statistisch belegt" markiert — nicht als Fakt ausgeben.
- **Einheiten-Relevanz beachten:** Jede erfasste Stärke/Schwäche wird der
  richtigen Einheit zugeordnet (`unit: offense|defense|neutral`), damit der
  Evaluator sie später korrekt zuordnen kann (Offensiv-Spieler interessiert nur
  die gegnerische **Defense**, für DEF nur die gegnerische **Offense**).

## Sleeper als Hilfsquelle (Sub-Subskill)

`fantasy-manager-supporter-collector` liefert Team-Kontext (Depth Chart, Schedule,
Roster) — nutzbar, um den nächsten Gegner/Spielplan schnell zu verifizieren
und den Teamkontext eines Spielers zu bestätigen. Für **Scheme-Fakten** (HC/OC/
DC, Grundschema, Tendenzen) ist Sleeper keine Primärquelle; dafür gelten die
Quellen unten.

## Gebündelte Wissensbasis (Offline-Fallback)

Die Tools bringen eine recherchierte Basis-Ausrichtung + Stärken/Schwächen für
alle NFL-Teams mit: [tools/team_profiles.default.json](../fantasy-lineup-coordinator/tools/team_profiles.default.json)
und den Spielplan [tools/schedule.default.json](../fantasy-lineup-coordinator/tools/schedule.default.json).
Diese werden vom Offline-Runner der `fantasy-lineup-coordinator`-Tools
(`tools/run_week.py` im `fantasy-lineup-coordinator`-Skill) automatisch geladen, wenn keine Recherche stattfindet.
keine Recherche stattfindet. Dieser Skill soll bei einer **echten Recherche**
diese Basis nach Möglichkeit **verifizieren/aktualisieren** (Coordinators und
Schemes ändern sich) statt sie blind zu wiederholen; ein aktuell recherchierter
Fakt überschreibt immer den Default.

## Quellenstrategie

1. Offizielle Teamseite (HC/OC/DC, Pressekonferenzen, Scheme-Beschreibung)
2. `nfl.com`, ESPN (Team-Stats/-Rankings als Beleg für Stärken/Schwächen **und**
   für die Gegner-Statistik: zugelassene/erzielte Yards/Punkte, Sacks, INT)
3. Pro-Football-Reference (Team-Defense/-Offense vs. Position, Splits)
4. PFF/FTN-DVOA/Sharp Football/rbsdm.com/Sumer Sports (Unit-Rankings,
   Matchup-Schwächen)
5. Etablierte Beat-Reporter (nur für „Erwartung"-Kennzeichnung vor Saisonbeginn)

Details/Tiers: [sources.md](../../sources.md).
Für die Gegner-Statistik gelten dieselben Tier-A/B-Regeln wie im Statistik-
Subskill: Sleeper-Werte nur als Kreuzcheck, nie alleiniger Beleg.

## Zu ermittelnde Inhalte

### Nächster Gegner (Pflicht)
Nur **Gegner, Datum und Heim/Auswärts** (keine Uhrzeit, kein Sender); ist das
Team spielfrei, die **Bye-Week** vermerken.

### Team-Ausrichtung (eigenes Team UND Gegner)
- **Offense:** HC/OC, Grundschema (z. B. West Coast, Air Coryell, Zone-Run),
  Lauf-/Pass-Tendenz, Personnel-/Formations-Nutzung (11/12/13, Motion,
  Play-Action).
- **Defense:** DC, Grundfront (4-3/3-4/Nickel-Basis), Coverage-Tendenz
  (Mann/Zone), Pressure-/Blitz-Tendenz.
- **Bevorzugte Spielertypen:** z. B. Move-TE vs. Blocking-TE, Committee- vs.
  Bell-Cow-RB, Deep-Threat- vs. Slot-WR, penetrierende DTs, hybride DBs.

### Team-Stärken/-Schwächen (eigenes Team UND Gegner)
Metrik-belegte Stärken/Schwächen der aktuellen Saison, je mit Wert/Rang +
Quelle + Datum + `unit` (offense/defense/neutral), z. B. beste Pass-Protection,
schwache Run-Defense, gegen die relevante Position.

### Gegner-Statistik (Pflicht, sobald der Gegner feststeht)
Statistik des nächsten Gegners der aktuellen Saison, je mit Wert, Liga-Rang
(falls vorhanden) und Quelle — ohne Bewertung:
- **Für einen Spieler:** Werte der gegnerischen Defense gegen die relevante
  Position, z. B. zugelassene Yards/TDs gegen Pass bzw. Lauf, zugelassene
  Punkte an die Position, Sacks, Interceptions.
- **Für ein Team:** relevante Gegnerwerte, z. B. erzielte/zugelassene Punkte,
  Pass-/Laufabwehr und -offense.
Fehlt ein Wert (z. B. vor dem ersten Spieltag), als „noch keine Saisondaten"
kennzeichnen; **Woche-1-Ausnahme:** Preseason-Wert als Fallback zulässig, klar
als `data_basis: "preseason (Woche 1)"` markiert, ab Woche 2 nicht mehr.

## Ausgabe: JSON-Fragment

```json
{
  "team_orientation": {"offense": "...", "defense": "...", "preferred_player_types": "..."},
  "team_strengths": [{"claim": "...", "metric": "...", "value": "...", "rank": 0, "source": "...", "date": "...", "unit": "offense|defense|neutral"}],
  "team_weaknesses": [{"...": "...", "unit": "offense|defense|neutral"}],
  "next_opponent": {
    "opponent": "...", "home_away": "home|away|bye", "date": "...", "bye": false,
    "orientation": {"offense": "...", "defense": "...", "preferred_player_types": "..."},
    "strengths": [{"...": "...", "unit": "offense|defense|neutral"}],
    "weaknesses": [{"...": "...", "unit": "offense|defense|neutral"}],
    "opponent_stats": [{"metric": "...", "value": "...", "rank": 0, "source": "..."}]
  },
  "additional_information": [{"note": "...", "source": "...", "date": "..."}],
  "data_basis": {"gegner_statistik": "aktuelle Saison | preseason (Woche 1)"},
  "sources": [{"url": "...", "type": "...", "published": "...", "retrieved_at": "..."}]
}
```

`next_opponent.opponent`/`home_away`/`bye` wird an den News-Subskill
weitergereicht, falls relevant.

## Ausgabe: Markdown (Fragment)

```markdown
## Team-Ausrichtung (eigenes Team)
- Offense: HC/OC, Schema, Lauf/Pass-Tendenz, Personnel
- Defense: DC, Front, Coverage-/Pressure-Tendenz
- Bevorzugte Spielertypen:
- Stärken des eigenen Teams (belegt): | Stärke | Metrik/Wert (Rang) | Quelle | Einheit |
- Schwächen des eigenen Teams (belegt): | Schwäche | Metrik/Wert (Rang) | Quelle | Einheit |

## Nächster Gegner
- Gegner, Home/Away, Datum (keine Uhrzeit, kein Sender); ggf. Bye-Week
- Statistiken des Gegners (aktuelle Saison): | Metrik | Wert | Liga-Rang | Quelle |
- Stärken des Gegners (belegt): | Stärke | Metrik/Wert (Rang) | Quelle | Einheit |
- Schwächen des Gegners (belegt): | Schwäche | Metrik/Wert (Rang) | Quelle | Einheit |
- Ausrichtung des Gegners: Offense/Defense/Bevorzugte Spielertypen
```

## Abnahmekriterien

1. Nächster Gegner eindeutig (oder Bye) mit Datum + Heim/Auswärts.
2. Ausrichtung + Stärken/Schwächen für **beide** Seiten (eigenes Team, Gegner).
3. **Gegner-Statistik** vorhanden, sobald der Gegner feststeht (sonst „noch
   keine Saisondaten"/Woche-1-Preseason-Fallback klar gekennzeichnet).
4. Jede Stärke/Schwäche/Statistik mit Metrik + Quelle + Datum + `unit` (bei
   Stärken/Schwächen); sonst „nicht belegt".
5. Erwartungs-Tendenzen vor Saisonbeginn klar als Erwartung markiert.
6. Kein Statistikwert des Subjekts selbst, keine Verletzung, keine News im
   Output.
