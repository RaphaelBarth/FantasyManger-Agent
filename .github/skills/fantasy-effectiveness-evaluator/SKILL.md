---
name: fantasy-effectiveness-evaluator
description: >-
  Wertet auf Basis eines fertigen Statistik-Reports (aus dem Skill
  fantasy-manager-supporter) aus, wie effektiv ein NFL-Spieler in der nächsten
  Partie bzw. der aktuellen Saison sein wird. Nutzt ein reproduzierbares
  Faktormodell (Verfügbarkeit, Rolle, Scheme-Fit im eigenen Team, Matchup gegen
  den nächsten Gegner, Formtrend) und liefert einen Effektivitätswert, eine
  Faktoraufschlüsselung und eine Konfidenzangabe. Verwende den Skill bei Anfragen
  wie "wie effektiv wird Spieler X", "werte den Report aus" oder "Matchup-Rating".
  Erzeugt eine Prognose, keine Garantie; keine medizinische Diagnose, keine Wette.
---

# Fantasy Effectiveness Evaluator

## Ziel

Aus dem **fertigen Report** des Skills `fantasy-manager-supporter` ableiten, wie
effektiv ein Spieler voraussichtlich sein wird. Der Report ist die
**Datenquelle** – dieser Skill erfindet keine Zahlen dazu.

**Sleeper-Referenz:** Das verwendete Scoring/Ligaformat richtet sich nach der
Wissensbasis [SleeperFantasyManager.md](../fantasy-lineup-coordinator/SleeperFantasyManager.md);
die Scoring-abhängige Gewichtung nutzt diese Regeln statt Annahmen.

## Eingaben

```text
report: Pfad oder Inhalt des Statistik-Reports (Pflicht)
scoring: standard|half-ppr|ppr|custom, optional (verändert Gewichtung leicht)
horizon: next_game|season, optional; Standard next_game
```

Fehlt der Report, zuerst `fantasy-manager-supporter` ausführen. Es werden nur
Fakten aus dem Report verwendet; fehlende Werte werden nicht geschätzt, sondern
senken die Konfidenz.

## Grundregeln

- **Nur Report-Fakten.** Keine externen Annahmen; wenn eine Verifikation nötig
  ist, die Report-Quellen erneut prüfen, nichts hinzuerfinden.
- **Keine neutralen Defaults.** Ein Faktor ohne Report-Beleg wird **nicht** mit
  einem Mittelwert geschätzt, sondern **ausgeschlossen**; die Gewichte werden auf
  die belegten Faktoren renormalisiert. Fehlende Belege senken die Konfidenz.
- **Aktuelle Saison.** Wie im Report; Vorsaison zählt nicht.
- **Aktualität.** Vor der Auswertung `generated_at` des Reports prüfen: ist er
  älter als **eine Stunde** (relativ zu `as_of`), zuerst `fantasy-manager-supporter`
  einen frischen Report erstellen lassen und diesen verwenden.
- **Transparenz.** Jeder Faktor nennt die zugrunde liegende Report-Aussage.
- **Prognose ist gekennzeichnet.** Das Ergebnis ist eine Einschätzung mit
  Konfidenz und Floor/Ceiling-Band, keine Tatsache.

## Faktormodell

Fünf Faktoren, jeweils 0–100 bewertet. Verfügbarkeit wirkt zusätzlich als
Multiplikator (Gate), weil ein nicht spielender Spieler 0 Punkte bringt.

### 1. Verfügbarkeit (Gate, Multiplikator 0–1)
Formales Gate aus **Game-Status × Trainingsteilnahme** (letzte Einheit: DNP =
did not practice, LP = limited, FP = full). Umgesetzt in
[tools/fmlib.py](../../tools/fmlib.py) → `injury_gate(status, practice)`:

| Status \ Practice | DNP | LP | FP / unbekannt |
|---|---|---|---|
| Out / IR / PUP / Suspendiert | 0,00 | 0,00 | 0,00 |
| Doubtful | 0,20 | 0,20 | 0,20 |
| Questionable | 0,55 | 0,75 | 0,90 (unbek. 0,70) |
| Probable | – | – | 0,95 |
| keine Meldung / aktiv | 0,90 | 0,95 | 1,00 |

Ist nur der Status ohne Trainingsteilnahme bekannt, gilt für Questionable 0,70.
Werte sind konservativ und **reproduzierbar** (gleiche Eingabe → gleicher Gate).

### 2. Rolle / Usage
Aus Statistik (Starts, Snap-/Route-/Target-Anteil) und Team-Ausrichtung
(Depth-Chart-Stellung, interne Konkurrenz):
- Klarer Starter mit hohem Anteil, wenig Konkurrenz → 80–100
- Starter mit spürbarer Konkurrenz ums Volumen → 60–79
- Rotations-/Committee-Rolle → 40–59
- Nebenrolle / unklar → 0–39

### 3. Scheme-Fit im eigenen Team
Aus „Team-Ausrichtung (eigenes Team)" **und** `team_strengths`/`team_weaknesses`:
Passt Schema, Lauf-/Pass-Tendenz, Personnel und **bevorzugter Spielertyp** zur
Position? Team-Stärken, die die Position speisen (z. B. „starke Pass-Protection"
für einen QB/WR), heben den Wert; Team-Schwächen, die sie bremsen, senken ihn.
- Schema und bevorzugter Typ begünstigen die Position deutlich → 80–100
- Überwiegend günstig → 60–79
- Neutral → 40–59
- Eher ungünstig (Schema/Tendenz arbeitet gegen die Position) → 0–39
Nur mit Beleg; sonst Faktor ausschließen (nicht neutral schätzen).

### 4. Matchup gegen nächsten Gegner
Zwei belegte Teilsignale, gemittelt zu einem Matchup-Wert:
- **M-Stat:** Gegner-Statistiken gegen die Position (`next_opponent.opponent_stats`,
  zugelassene Yards/Punkte/TDs, Sacks, INT).
- **M-Edge:** **Spieler-Stärken × Gegner-Schwächen (+)** und **Gegner-Stärken ×
  Spieler-Anfälligkeit (−)** aus `player_strengths`, `next_opponent.strengths`
  und `next_opponent.weaknesses`. Beispiel: Spieler-Stärke „hoher YAC-Anteil" trifft
  Gegner-Schwäche „schwache Tackling-/Coverage-Werte gegen die Position" → Edge hoch.
- **Einheiten-Relevanz (Pflicht):** Ein **Offensiv-Spieler (QB/RB/WR/TE, ebenso K)**
  trifft auf die **gegnerische Defense** – die **Offense-Eigenschaften des Gegners
  werden ignoriert** (eine gegnerische Elite-WR-Gruppe o. Ä. ist kein Dämpfer für
  den eigenen RB/WR). Nur die **Defense-Einheit** des Gegners (Pass-Rush, Secondary,
  Run-Defense, Coverage) und neutraler Kontext zählen. Für **DEF** gilt das
  Spiegelbild: relevant ist die **Offense** des Gegners, die Defense-Eigenschaften
  entfallen. In der Wissensbasis trägt jede `strengths`/`weaknesses` dazu ein Feld
  `unit` (`offense`/`defense`/`neutral`); fehlt es, klassifiziert eine Heuristik nach
  Schlüsselwörtern.
- Klar anfällig (Stat und/oder Edge deutlich positiv) → 80–100
- Leicht günstig → 60–79 · Ausgeglichen → 40–59 · Gegner stark → 0–39
Liegt **weder** eine Gegner-Statistik **noch** ein belegter (einheiten-relevanter)
Edge vor (nur Ausrichtung), gilt der Faktor als **unbelegt und wird ausgeschlossen**
– nicht neutral geschätzt.

Zur Einordnung von M-Edge und Scheme-Fit dient das **Cheat Sheet**
[cheat-sheet-matchups.md](./cheat-sheet-matchups.md): historisch/analytisch
fundierte Heuristiken, welche Spieler-Stärken zu Gegner-Schwächen und Team-Schemes
🟢 günstig / 🟡 neutral / 🔴 ungünstig passen. Es liefert nur die Richtung; die
Belege bleiben die Report-Signale, und gegenläufige Signale werden ausgewogen bewertet.

### 5. Formtrend (aktuelle Saison, Sample-gedämpft)
Aus dem Game Log der aktuellen Saison (letzte 1–3 Spiele):
- Steigend/stark → 70–100, stabil → 50–69, fallend/schwach → 0–49
- **Sample-Dämpfung:** Bei nur 1 gewerteten Spiel ist der Trend wenig aussagekräftig;
  den Faktor Richtung 50 dämpfen und die Konfidenz senken. Ab 3 Spielen voll.
- **Noch keine Saisondaten → Faktor entfällt** (Ausschluss + Renormalisierung).

### Zusatzinformationen als Modifikatoren
Belegte Einträge aus `additional_information` (z. B. „WR1 per Trade abgegeben →
Target-Share steigt", „neuer OC nutzt TE stärker") wirken als **gedeckelte
Anpassung ±10** auf den betroffenen Faktor (meist Rolle oder Scheme-Fit), nur mit
Quelle. Nie neue Faktoren erfinden; ohne Quelle kein Effekt.

## Gewichte und Berechnung

Deterministisch umgesetzt in [tools/fmlib.py](../../tools/fmlib.py) → `evaluate(...)`.
Basisgewichte:

| Faktor | Gewicht |
|---|---|
| Rolle / Usage | 0,30 |
| Scheme-Fit | 0,25 |
| Matchup | 0,25 |
| Formtrend | 0,20 |

`Effektivität = ( Σ_belegte Faktor × renorm_Gewicht ) × Verfügbarkeits-Gate`

**Unbelegte Faktoren werden ausgeschlossen**, die Gewichte auf die verbleibenden
renormalisiert (kein neutraler Default). Vor Saisonbeginn entfallen typischerweise
Form (kein Game Log) und – ohne Gegner-Statistik/Edge – auch Matchup; dann zählen
nur Rolle und Scheme-Fit.

**Scoring-Anpassung:** PPR → Rolle +0,05 / Form −0,05 (Volumen zählt mehr);
Standard/TD → Matchup +0,05 / Form −0,05. Half-PPR unverändert. Die verwendete
Gewichtung wird immer ausgewiesen.

## Floor / Ceiling

Neben dem Punktwert wird ein **asymmetrisches Band** ausgegeben:
- **Floor** sinkt stärker bei Verletzungsrisiko (niedriges Gate) und niedriger
  Konfidenz — relevant für Start/Sit.
- **Ceiling** steigt mit Unsicherheit moderat — relevant für Upside/Turniere.

Formeln (in `fmlib.evaluate`): `downside = E·(0,10 + 0,30·(1−Konf) + 0,25·(1−Gate))`,
`upside = E·(0,10 + 0,25·(1−Konf))`; Floor/Ceiling auf 0..100 begrenzt.

## Konfidenz (quantitativ 0–1)

`Konfidenz = 0,35·Abdeckung + 0,30·Sample + 0,20·Verletzungs-Klarheit + 0,15·Quellen`
- **Abdeckung** = belegte Faktoren / 4
- **Sample** = min(Spiele, 3) / 3 (aktuelle Saison)
- **Verletzungs-Klarheit** = |2·Gate − 1| (klar bei Out=0 oder fit=1; unklar bei QUES)
- **Quellen** = min(Quellenanzahl, 3) / 3

Label: ≥ 0,66 hoch · ≥ 0,40 mittel · sonst niedrig.

## Effektivitätsstufen

| Wert | Stufe |
|---|---|
| 81–100 | sehr hoch |
| 61–80 | hoch |
| 41–60 | mittel |
| 21–40 | niedrig |
| 0–20 | sehr niedrig |

## Verbindliches Ausgabeformat

```markdown
# Effektivitäts-Auswertung: <Spieler>
Basierend auf: <Report-Quelle> | Stand: <as_of> | Horizon: <next_game|season>
Scoring: <...> | Gewichtung: <verwendete (renormalisierte) Gewichte>

## Ergebnis
- Effektivität: <0–100> → <Stufe>
- Floor / Ceiling: <floor> / <ceiling>
- Verfügbarkeits-Gate: <0–1>
- Konfidenz: <0–1> (<hoch|mittel|niedrig>)

## Faktoraufschlüsselung
| Faktor | Wert (0–100) | Gewicht | belegt? | Beleg aus Report |
(ausgeschlossene Faktoren mit "—" und Grund kennzeichnen)

## Sachliche Begründung (Pflicht, 4–6 Sätze)
Zusammenhängende, sachliche 4–6-Satz-Begründung, die **auf dem Spieler-Report und
der vorgenommenen Evaluation** beruht: Verfügbarkeit/Status, Scheme-Fit im eigenen
Team, Matchup (Gegner + Edge aus Stärken × Schwächen, ggf. mit Cheat-Sheet-
Einordnung), belegte Spieler-Stärke bzw. relevanter Kontext, die Kennzahlen
(Effektivität, Floor/Ceiling, Tilt, Konfidenz) und die wesentliche Einschränkung/
Datenlücke. Nur Report-Fakten, keine Erfindungen.

## Kurz-Treiber
- Stärkste positive Treiber (inkl. Matchup-Edge aus Stärken × Gegner-Schwächen):
- Stärkste Risiken/Dämpfer (inkl. Gegner-Stärken, Verletzungs-Gate):
- Wirksame Zusatzinformationen (belegte Modifikatoren):
- Was die Konfidenz begrenzt:

## Datenlücken
- Ausgeschlossene Faktoren und fehlende Report-Werte ("noch keine Saisondaten" …)
```

Keine Zusatzabschnitte; keine erfundenen Statistiken; keine Wett- oder
Gesundheitsaussagen. Der Runner erzeugt die 4–6-Satz-Begründung deterministisch
(`evaluation_rationale` in [tools/run_week.py](../../tools/run_week.py)) und legt sie
je Spieler in `evaluations-*.json` ab.

## Ablauf

1. Report laden (bevorzugt JSON) und die relevanten Abschnitte auslesen: Statistik,
   `player_strengths`, Verletzung, Team-Ausrichtung + `team_strengths`/`team_weaknesses`,
   nächster Gegner inkl. `strengths`/`weaknesses`, `additional_information`.
2. Je Faktor entscheiden, ob **belegt**; wenn ja 0–100 einordnen und Beleg notieren.
   Matchup aus M-Stat + M-Edge (Stärken × Schwächen); Zusatzinfos als ±10-Modifikator.
3. Verfügbarkeits-Gate über `injury_gate(status, practice)` bestimmen.
4. `fmlib.evaluate(factors, gate, games, sources, scoring, horizon)` aufrufen →
   Effektivität, Floor/Ceiling, Konfidenz, renormalisierte Gewichte.
5. Stufe, Begründung (inkl. Edge/Modifikatoren) und Datenlücken ausweisen.

Konfidenz ≈ 0,36 (niedrig); Matchup und Form ausgeschlossen.
