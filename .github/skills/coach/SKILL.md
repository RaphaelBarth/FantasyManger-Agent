---
name: coach
description: >-
  Erstellt für genau einen NFL-Spieler eine faktenbasierte Prediction für den
  nächsten Spieltag. Verwendet ausschließlich den kanonischen Report des
  Assistant Coach, das Matchup-Cheat-Sheet und belegte Report-Signale zu
  Verfügbarkeit, Rolle, Scheme-Fit, Gegner-Matchup und Form. Liefert Prognose,
  Faktoren, Floor/Ceiling, Konfidenz, Quellen und Datenlücken. Keine Garantie,
  keine medizinische Diagnose und keine Wette.
---

# Fantasy Coach

## Aufgabe

Der Coach beantwortet für **einen gegebenen Spieler** die Frage, wie dieser im
nächsten Spiel voraussichtlich performen wird. Grundlage ist ausschließlich der
kanonische, deduplizierte Spieler-Report aus
[`assistant-coach`](../assistant-coach/SKILL.md).

Der Coach recherchiert keine neuen Fakten und erstellt keine Aufstellung. Er
wandelt belegte Report-Signale in eine transparente, reproduzierbare Prognose
um. Die bestehende Matchup-Referenz
[`cheat-sheet-matchups.md`](./cheat-sheet-matchups.md) muss für Scheme-Fit und
Matchup-Einordnung verwendet werden. Sie liefert nur Richtung, niemals eigene
Spielerwerte oder einen Ersatz für Report-Quellen.

## Eingaben

```text
player: Spielername — Pflicht
report: kanonischer Assistant-Coach-Report — Pflicht
as_of: ISO-8601-Zeitpunkt — Pflicht
scoring: standard|half-ppr|ppr|custom — optional
horizon: next_game — fest
```

Der Report muss den nächsten Gegner, die Saisonstatistik, Rolle, Team-/Scheme-
Signale, Verletzungsstatus, News und Quellen enthalten, soweit verfügbar. Fehlt
ein Bereich, wird er als Datenlücke ausgewiesen und nicht geschätzt.

## Bewertungsmodell

Bewertet werden nur belegte Faktoren. Nicht belegte Faktoren werden ausgelassen;
die Gewichte der übrigen Faktoren werden renormalisiert. Es gibt keine neutralen
Default-Werte.

| Faktor | Inhalt | Basisgewicht |
|---|---|---:|
| Verfügbarkeit | Status, Practice-Status, Inactive-/IR-Hinweise | Gate, Multiplikator |
| Rolle / Usage | Starts, Snaps, Routes, Targets, Carries, Red Zone, Depth Chart | 0,30 |
| Scheme-Fit | Team-Scheme und belegte Spielermerkmale | 0,25 |
| Matchup | Gegnerstatistik und relevante Stärken/Schwächen | 0,25 |
| Formtrend | aktuelle Saison, letzter Game Log, Sample-Größe | 0,20 |

Die Verfügbarkeit wirkt zusätzlich als Gate von 0 bis 1. Out/IR erhält Gate 0.
Questionable wird nur nach belegtem Status und Practice-Status eingestuft.
Fehlende Angaben senken die Konfidenz und werden nicht geschätzt.

### Cheat-Sheet-Anwendung

1. Report-Signale für Spieler-Stärke, Team-Scheme, Gegner-Stärke und
   Gegner-Schwäche identifizieren.
2. Für Offensiv-Spieler nur die gegnerische Defense verwenden; für DEF nur die
   gegnerische Offense verwenden.
3. Die passende Positionstabelle in
   [`cheat-sheet-matchups.md`](./cheat-sheet-matchups.md) anwenden.
4. Gegenläufige Signale ausgleichen und im Ergebnis erklären.
5. Ohne belegtes Signal den Faktor auslassen, nicht neutral annehmen.

## Prediction

Das Ergebnis ist eine Prognose für den nächsten Spieltag, keine Tatsache.
Erforderliche Kennzahlen:

- `projection`: erwartete Fantasy-Punkte, nur wenn Scoring und Reportdaten eine
  nachvollziehbare Projektion erlauben
- `effectiveness`: 0 bis 100 als qualitative Effektivität
- `floor`: konservative Untergrenze
- `ceiling`: realistisches positives Szenario
- `confidence`: 0 bis 1
- `gate`: Verfügbarkeitsfaktor 0 bis 1

Wenn keine belastbare Punkteprojektion möglich ist, werden `projection` und
entsprechende Zahlen nicht erfunden. Die qualitative Prediction bleibt möglich,
sofern mindestens Rolle, Verfügbarkeit oder Matchup belegt sind.

## Ausgabeformat

```markdown
# Coach-Prediction: <Spieler> — nächstes Spiel

Stand: <as_of> | Gegner: <Team> | Scoring: <...>

## Prediction
- Erwartete Leistung: niedrig | mittel | hoch
- Projektion: <Wert oder nicht belastbar>
- Effektivität: <0-100 oder nicht belastbar>
- Floor–Ceiling: <...>
- Verfügbarkeit: <Status> | Gate: <0-1>
- Konfidenz: <0-1> | Einstufung: niedrig | mittel | hoch

## Begründung
<Zusammenhängende Begründung auf Basis der belegten Report-Fakten.>

## Faktoren
| Faktor | Bewertung | Report-Signal | Auswirkung |
|---|---:|---|---|
| Rolle / Usage | ... | ... | ... |
| Scheme-Fit | ... | ... | ... |
| Matchup | ... | ... | ... |
| Formtrend | ... | ... | ... |
| Verfügbarkeit | ... | ... | ... |

## Quellen und Datenlücken
- Quellen: <URL, Veröffentlichungsdatum, retrieved_at>
- Datenlücken: <offene Bereiche oder "keine">
- Konflikte: <Konflikte oder "keine">
```

## Regeln

- Nur Fakten aus dem kanonischen Assistant-Coach-Report verwenden.
- Das Cheat-Sheet nur als erklärende Heuristik verwenden, nicht als Datenquelle.
- Keine Werte aus Suchmaschinen-Snippets oder unbestätigten Quellen übernehmen.
- Verletzungs-News nicht mit einem offiziellen Injury-Status verwechseln.
- `conflicts` aus dem kanonischen Report sichtbar halten.
- Prognose, Floor, Ceiling und Konfidenz klar als Einschätzung kennzeichnen.
- Keine Aufstellung, kein Add/Drop, kein Trade und keine medizinische Aussage.

## Referenz

Die einzige zusätzliche fachliche Referenz ist
[`cheat-sheet-matchups.md`](./cheat-sheet-matchups.md). Es ordnet belegte
Spieler-, Scheme- und Gegner-Signale ein, ersetzt aber keine Report-Quelle.
