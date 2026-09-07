---
name: fantasy-lineup-coordinator
description: >-
  Normaler Fachskill für die aktuelle NFL-Woche. Erstellt aus bereits
  vorbereiteten Reports und Effektivitätswerten die beste regelkonforme
  Aufstellung eines Fantasy-Kaders und löst die Slot-Zuordnung. Der oberste
  fantasy-manager-agent orchestriert Supporter, Evaluator, diesen Skill und
  optional den Opportunity-Scout.
  Verwende den Skill bei Anfragen wie "stelle das beste Team für diese Woche auf",
  "optimiere meine Lineup" oder "wen soll ich starten".
  Erzeugt eine Empfehlung mit Konfidenz, keine Garantie; keine Wette.
---

# Fantasy Lineup Coordinator

Dieser Skill ist **kein Top-Level-Orchestrator**. Er ist ausschließlich für die
Aufstellungsplanung zuständig und wird normalerweise vom
`fantasy-manager-agent` aufgerufen.

## Ziel

Für die **aktuelle Woche** aus einem Kader die **beste Startaufstellung**
bestimmen – datenbasiert über vorbereitete Reports und eine transparente
Optimierung der Slot-Zuordnung.

## Eingangsartefakte (vom Top-Level-Agenten)

1. Kader und konkrete Liga-Regeln.
2. Ein frischer Supporter-Report je Kaderspieler.
3. Eine Evaluation je Kaderspieler mit Effektivität, Gate und Konfidenz.
4. Optional eine separate Scout-Empfehlung für erkannte Schwächen.

Der Coach recherchiert und orchestriert diese Skills nicht selbst. Er erfindet
keine Werte oder Spieler; fehlende Daten senken die Konfidenz.

## Referenz: Sleeper-Regeln

Ligamodell, **Slots** (inkl. FLEX/SUPERFLEX-Eignung), **Scoring**, Bye, IR und der
**Lineup-Lock bei Spielbeginn** folgen der Sleeper-Wissensbasis:
[SleeperFantasyManager.md](./SleeperFantasyManager.md). Die konkrete
Liga-Konfiguration hat immer Vorrang vor Standardwerten. `scoring` und `slots`
dieses Skills werden aus dieser Referenz bzw. der Ligakonfiguration abgeleitet.

## Eingaben

```text
roster: Datei/Liste der Kaderspieler (Name, Pos, Team) — Pflicht
slots: Liga-Startplätze inkl. Flex-/Superflex-Regeln — Pflicht
week: aktuelle NFL-Woche — Pflicht
scoring: standard|half-ppr|ppr|custom — optional (an Sub-Skill 2 durchreichen)
as_of: ISO-8601-Zeitpunkt — optional; Standard jetzt
```

Fehlen `slots`, aus der Ligakonfiguration bzw. dem Kader-Screenshot übernehmen
(z. B. QB, RB×2, WR×3, TE×2, W/R/T-Flex, W/R/T/Q-Superflex, K, DEF); Slot-,
Scoring- und Roster-Regeln (Bye, IR, Lineup-Lock bei Spielbeginn) folgen der
[Sleeper-Referenz](./SleeperFantasyManager.md).

## Slot-Eignung (Standard)

| Slot | Erlaubte Positionen |
|---|---|
| QB | QB |
| RB | RB |
| WR | WR |
| TE | TE |
| W/R/T (Flex) | WR, RB, TE |
| W/R/T/Q (Superflex) | QB, WR, RB, TE |
| K | K |
| DEF | DEF |

Abweichende Liga-Slots (z. B. reine Team-Units wie Passing/Rushing Offense)
werden analog nach ihrer erlaubten Menge behandelt.

## Ablauf

1. **Kader lesen** und je Spieler Position, Team, Bye und Woche bestimmen.
2. **Startwert je Spieler** = **erwartete Punkte, evaluator-adjustiert**:
   `E = Projektion × Qualitäts-Tilt × Gate`. Der Qualitäts-Tilt (±20 %) kommt aus
   den Evaluator-Qualitätsfaktoren (Scheme/Matchup/Form), das Gate aus der
   Verfügbarkeit. So bleibt der Wert **positionsübergreifend punktvergleichbar**
   (ein 90er-Kicker schlägt keinen 80er-QB im Superflex), während die
   Evaluator-Einschätzung ihn kalibriert. Umgesetzt in
   [tools/run_week.py](../../tools/run_week.py) via `fmlib.evaluate` + `quality_tilt`.
   - Spieler mit Bye in dieser Woche oder Gate 0 (Out/IR) sind **nicht
     startbar** und werden ausgeschlossen.
3. **Optimierung** (siehe unten): Zuordnung Spieler → Slots, die die Summe der
   Startwerte maximiert und jede Slot-Eignung respektiert.
4. **Ausgabe**: empfohlene Startelf pro Slot, Bank, knappe Entscheidungen,
   Monitore (offene QUES-Fälle), optionale Scout-Empfehlungen und Konfidenz.

## Optimierung (maximale Gesamteffektivität)

Es handelt sich um ein **maximales gewichtetes Zuordnungsproblem** (Spieler ↔
eignungsfähige Slots). Es wird **exakt** über den Ungarischen Algorithmus
(Kuhn-Munkres) gelöst — implementiert in [tools/fmlib.py](../../tools/fmlib.py)
(`optimize_lineup`). Kein manueller Swap-Check nötig.

Ausführbar über den End-to-End-Runner:

```
python tools/run_week.py --input woche.json --report-dir ./temp/reports --out-dir . --as-of <ISO>
```

Der Runner kettet: pro Spieler frischer Report (kein Cache, jeder Lauf zieht
neu) → Effektivität `E` (= Startwert, inkl. Verfügbarkeits-Gate) → exakte
Slot-Zuordnung → Scout-Schwächen → Bundle (`lineup-*.json` gegen `tools/schemas/lineup.schema.json`
validierbar, plus `lineup-*.md`). Zusätzlich wird die „falls QUES aktiv"-
Alternative berechnet und als Monitor ausgewiesen.

**Team-/Gegnerprofil in den Reports:** Der Runner lädt automatisch die **gebündelte
Liga-Wissensbasis** ([tools/team_profiles.default.json](../../tools/team_profiles.default.json):
Team-Ausrichtung + recherchierte Stärken/Schwächen je NFL-Team) und den
**Spielplan** ([tools/schedule.default.json](../../tools/schedule.default.json)). Damit
werden schon aus einem nackten Kader `team_orientation` (eigenes Team),
`team_strengths`/`team_weaknesses`, der nächste Gegner (via Spielplan, wenn kein
`opp` gesetzt ist) sowie `next_opponent.orientation`/`strengths`/`weaknesses`
befüllt. Enthält die Wocheneingabe einen `team_profiles`-Block bzw. ein `opp`-Feld,
**überschreibt die Eingabe die Defaults** pro Team (flacher Merge je Teamcode);
mit `--no-default-profiles` lassen sich die Defaults abschalten. Fehlt trotz allem
ein Profil, wird es **ehrlich als Datenlücke** vermerkt — nichts wird erfunden. Nur
`news` (Live-Sleeper-Feed) und die Saisonstatistik (ab Woche 1 erst nach Spielen,
Woche-1-Preseason-Fallback möglich) bleiben eingabe-/saisonabhängig. Diese
Snapshot-Reports (`report_kind: "snapshot"`) sind bewusst schlanker als die voll
recherchierten Supporter-Reports; jeder geschriebene Report wird gegen
`tools/schemas/report.schema.json` validiert (`reports.schema_invalid`).

Konzeptuell entspricht das:
1. Kandidatenmenge je Slot nach Eignung bilden; nicht startbare (Bye/Out) entfernen.
2. Zuordnung, die die Summe der Startwerte maximiert (Flex/Superflex inklusive;
   Superflex darf einen zweiten QB starten).

Bei Gleichstand entscheidet höhere Konfidenz, dann höherer Floor (geringeres
Verletzungs-/Rollenrisiko).

## Risiko und Konfidenz

- **Startwert** enthält bereits das Verfügbarkeits-Gate; ein QUES-Spieler mit
  hohem Rohwert kann dadurch hinter einen gesunden Spieler fallen.
- Ist ein QUES-Status noch offen, den betroffenen Slot als **Monitor** ausweisen
  und den besten gesunden Pivot nennen (Empfehlung „wechseln, falls bis Kickoff
  nicht aktiv").
- Gesamtkonfidenz = niedrigste relevante Einzelkonfidenz der Startelf
  (vor Saisonbeginn oder bei offenen Verletzungen typischerweise niedrig).

## Verbindliches Ausgabeformat

```markdown
# Beste Aufstellung: <Team> — Woche <n>
Stand: <as_of> | Scoring: <...> | Basierend auf: fantasy-manager-supporter + fantasy-effectiveness-evaluator (+ fantasy-opportunity-scout bei Schwachstelle)

## Startaufstellung (Tabelle)
| Slot | Spieler | Pos | Team | E | Proj | Tilt | Gate | Eff | Floor–Ceil | Konf |

## Bank (Tabelle, gleiche Spalten, Slot = BN)
| Slot | Spieler | Pos | Team | E | Proj | Tilt | Gate | Eff | Floor–Ceil | Konf |

## Legende (Spaltenkürzel)
- **E** = Auswahlwert = Projektion × Tilt × Gate · **Proj** = erwartete Fantasy-Punkte
- **Tilt** = Evaluator-Qualitäts-Faktor (±20 %) · **Gate** = Verfügbarkeit 0–1
- **Eff** = Effektivität 0–100 · **Floor–Ceil** = Effektivitätsband · **Konf** = Konfidenz

## Begründung je Spieler (Pflicht) — als Fließtext auf Basis des Spieler-Reports
- Für **jeden Starter und Bankspieler** eine zusammenhängende **Fließtext**-
  Erklärung (keine Stichpunkte): Sie nennt die **Coach-Entscheidung** (Start in
  Slot X / Bank) und begründet sie mit den **Report-Daten** (Scheme-Fit, Matchup
  mit Gegner-Stärken/-Schwächen, Verletzungsstatus, News, belegte Stärken) —
  **nicht** mit den errechneten Werten E/Proj/Tilt. Die Zahlen stehen in der Tabelle.

## Entscheidende Calls
- Knappe Slot-Duelle und warum der Sieger startet
- Monitore (offene QUES) + gesunder Pivot

## Scout-Empfehlungen (optional, bei Schwachstelle)
- Ausgelöste Schwäche (Slot/Bye/Konfidenz) und die vom Scout gelieferten
  Waiver-/Trade-Vorschläge (Kandidat/Typ, Aktion) — als Empfehlung, nicht Teil
  der aktuellen Startelf

## Konfidenz & Datenlücken
- Gesamtkonfidenz und was sie begrenzt ("noch keine Saisondaten" …)
```

Keine erfundenen Statistiken; keine Wett-/Gesundheitsaussagen; Empfehlung, keine
Garantie.
