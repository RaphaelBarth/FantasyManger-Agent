# Cheat Sheet: Matchup-Kompatibilität (Stärken × Schwächen × Scheme)

**Zweck:** Referenz für den Evaluator, um die Faktoren **Matchup** und
**Scheme-Fit** qualitativ einzuordnen — welche Spieler-Stärken zu Gegner-Schwächen
(und welche Team-Schemes zu Spielertypen) **gut** oder **schlecht** passen.

**Charakter der Angaben (Ehrlichkeit):** Dies sind etablierte, öffentlich breit
belegte **Analytics-Heuristiken** (Konzepte aus NFL Next Gen Stats, PFF-Coverage/
-Pass-Rush-Grades, DVOA/„Points Allowed by Position", Snap-/Route-/Target-Anteile).
Es sind **Richtungsregeln, keine Garantien** und keine erfundenen Einzelstatistiken.
Sie ersetzen nicht die belegten Saison-Metriken im Report; sie helfen nur, ein
belegtes Signal als günstig/ungünstig einzuordnen. Ohne belegtes Report-Signal →
kein Faktor (keine Annahme).

**Einheiten-Relevanz:** Alle folgenden Tabellen für Offensiv-Positionen (QB/RB/WR/TE)
beziehen sich ausschließlich auf die **gegnerische Defense** (Pass-Rush, Coverage,
Secondary, Run-Defense). Die **Offense** des Gegners ist für Offensiv-Spieler
**irrelevant** und wird ignoriert; sie zählt nur bei der Bewertung einer **DEF**
(dann umgekehrt: Offense des Gegners relevant, Defense irrelevant).

Skala: 🟢 günstig (Faktor hoch) · 🟡 neutral/kontextabhängig · 🔴 ungünstig (Faktor niedrig).

## 1. Quarterback (QB)
| Spieler-Stärke | Gegner-Konstellation | Bewertung | Begründung |
|---|---|---|---|
| Mobiler QB, gut off-structure | hohe Blitz-Rate, aggressive Man-Coverage | 🟢 | Scramble-Yards & Big Plays gegen Man/Blitz; Pressure wird zu Chancen |
| Pocket-Passer, schnelle Release | starke Interior-Pressure, wenig Zeit | 🔴 | Interior-Push kollabiert die Pocket, kein Ausweichen |
| Deep-Ball-QB | Cover-0/Cover-1, wenig Safety-Hilfe | 🟢 | einzelabgedeckte WR außen, 1-on-1 downfield |
| jeder QB | Elite-Coverage-Secondary, wenig Pressure erlaubt | 🔴 | dichte Fenster, niedrige aDOT erzwungen |
| QB mit starker O-Line | schwacher Pass-Rush | 🟢 | Zeit → höhere Completion/Big-Play-Rate |

## 2. Running Back (RB)
| Spieler-Stärke | Gegner-Konstellation | Bewertung | Begründung |
|---|---|---|---|
| Pass-fangender RB (Routes/Targets) | schwache RB-/LB-Coverage, viel Zone | 🟢 | Check-downs & Mismatches gegen langsame LBs |
| Power-/Zwischen-den-Tackles-RB | aufgerüstete/stoute Interior-DL (Run-Stop) | 🔴 | wenig Raum inside, negative Runs |
| Zone-/One-Cut-RB, Explosivität | schwache Edge-Contain / schlechte Run-Fits | 🟢 | Outside-Zone bricht groß an |
| Bell-Cow (hoher Snap-/Touch-Anteil) | schwache Run-Defense insgesamt | 🟢 | Volumen × günstige Front = hohe Deckenwerte |
| Committee-RB (geteilte Touches) | jede Front | 🟡 | Volumen deckelt Deckenwert unabhängig vom Matchup |

## 3. Wide Receiver (WR)
| Spieler-Stärke | Gegner-Konstellation | Bewertung | Begründung |
|---|---|---|---|
| Elite Separation / Route-Running | zonenlastige, „weiche" Coverage | 🟢 | findet Löcher in der Zone, sichere Targets |
| Kontested-Catch / große Boundary-WR | Press-Man mit kleineren CBs | 🟢 | 50/50-Bälle & Back-Shoulder gewinnen |
| Slot-WR (hoher Slot-Route-Anteil) | schwache Slot-/Nickel-Coverage | 🟢 | Mismatch im Slot, hohe Target-Rate |
| WR gegen Shadow-CB (Elite-Boundary-Corner) | Press-Man-Shadow | 🔴 | Volumen/Effizienz gedrückt durch Top-Corner |
| Deep-Threat (hohe aDOT/Air Yards) | Two-High-Safety-Shell (Cover 2/4) | 🔴 | Deckung nimmt den Deep-Shot weg |
| YAC-WR | aggressive Man-Coverage, schlechte Tackler | 🟢 | Raum nach dem Catch, Big-Play-Potenzial |

## 4. Tight End (TE)
| Spieler-Stärke | Gegner-Konstellation | Bewertung | Begründung |
|---|---|---|---|
| Receiving-/Move-TE, hohe Route-Rate | Defense erlaubt viele Punkte/Yards an TE (Rang schlecht) | 🟢 | direkte Positions-Schwäche, hohe Ziele |
| Move-TE (Mismatch-Alignment) | langsame LBs / schwache Coverage-Safeties | 🟢 | Geschwindigkeitsvorteil im Seam |
| Blocking-/Inline-TE | jede Coverage | 🟡 | geringes Passvolumen deckelt den Wert |
| TE | Defense mit starker Seam-/Middle-Coverage (guter Cover-LB/Safety) | 🔴 | Middle zu, wenig Separation |

## 5. Defense/Special Teams (DEF)
| DEF-Stärke | Gegner-Offense | Bewertung | Begründung |
|---|---|---|---|
| starker Pass-Rush | schwache O-Line / Backup-QB / hohe Sack-Rate erlaubt | 🟢 | Sacks & Turnovers (Sack-Fumbles, erzwungene INTs) |
| ballräuberische Secondary | turnover-anfälliger QB | 🟢 | INTs/Defensive-Scores |
| DEF | Elite-Offense, hohe erzielte Punkte | 🔴 | wenig Sacks/Turnover, viele zugelassene Punkte |
| DEF | Backup-/Rookie-QB, konservative Offense | 🟢 | Punkte-gegen niedrig, Turnover-Chancen |

## 6. Team-Scheme × Spielertyp (eigenes Team)
| Scheme / Tendenz | Begünstigt | Deckelt |
|---|---|---|
| West Coast, viel 12-Personnel, TE-freundlich | Receiving-/Move-TE, Slot-WR | reine Deep-Threat-WR |
| Air-Coryell / vertikal, hohe aDOT | Deep-Threat-WR, Big-Play-RB | Possession-/Dink-Receiver |
| Pass-lastig (hohe Pass-Rate, Pace) | WR/TE-Volumen, Pass-Catching-RB | reine Early-Down-Grinder-RB |
| Lauflastig / Ball-Control, niedrige Pace | Bell-Cow-RB, Blocking-TE | Boom-or-Bust-WR |
| Spread / 11-Personnel, hohe Neutral-Pass-Rate | WR1/WR2, Slot | TE2/FB |
| Committee-Backfield (geteilte Touches) | keiner klar (Volumen verteilt) | jeden RB einzeln (Deckelung) |

## Anwendung im Evaluator
1. Nimm ausschließlich **belegte** Report-Signale (Spieler-Stärke, Gegner-Stärke/
   -Schwäche, Team-Ausrichtung).
2. Ordne jedes Paar über die Tabellen als 🟢/🟡/🔴 ein → das prägt die 0–100-Werte
   von **Matchup** (M-Edge) und **Scheme-Fit**.
3. Gegenläufige Signale (z. B. RB: Gegner-LB-Schwäche 🟢 **und** starke Interior-DL 🔴)
   werden **ausgewogen** bewertet und in der Begründung benannt (nicht einseitig).
4. Kein belegtes Signal → Faktor **ausschließen**, nicht neutral schätzen.
5. Die Einordnung ist eine **Prognose-Heuristik**; sie senkt/hebt den Faktor, aber
   die Konfidenz bleibt an die Datenlage (Sample/Quellen) gebunden.
