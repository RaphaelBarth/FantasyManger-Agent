---
name: fantasy-opportunity-scout
description: >-
  Scout-Agent, der für einen Fantasy-Kader potenzielle Sleeper (unterbewertete
  Waiver-/Free-Agent-Spieler mit steigender Rolle) sowie gute Trade-Kandidaten
  (Buy-low, Sell-high, Trade-Paarungen) findet. Nutzt die Sub-Skills
  fantasy-manager-supporter (Fakten) und fantasy-effectiveness-evaluator
  (Effektivität) und richtet sich nach den Sleeper-Regeln (Waiver/FAAB, Trades).
  Verwende den Skill bei Anfragen wie "finde Sleeper", "wer ist ein guter
  Waiver-Pickup", "Buy-low/Sell-high", "welche Trades lohnen sich".
  Erzeugt Empfehlungen mit Konfidenz, keine Garantie; keine Wette.
---

# Fantasy Opportunity Scout

## Ziel

Für einen Kader **Chancen** finden: (a) **Sleeper** – unterbewertete Waiver-/
Free-Agent-Spieler mit steigender Rolle/Gelegenheit; (b) **Trade-Kandidaten** –
Buy-low-Ziele, Sell-high aus dem eigenen Kader und faire Trade-Paarungen.

## Sub-Skills und Referenz

- **fantasy-manager-supporter** → Fakten je Spieler (Statistik aktuelle Saison,
  Verletzung, Team-Ausrichtung, nächster Gegner).
- **fantasy-effectiveness-evaluator** → Effektivitätswert je Spieler.
- **Sleeper-Regeln** (Waiver/FAAB, Trades, Roster/Slots) aus
  [SleeperFantasyManager.md](../fantasy-lineup-coordinator/SleeperFantasyManager.md);
  die konkrete Ligakonfiguration hat Vorrang.

Der Scout bewertet jeden Kandidaten über die beiden Sub-Skills und erfindet keine
Spieler oder Werte. Fehlt der Kandidatenpool, wird er angefordert/geladen.
Reports werden **ohne Cache** bei jeder Anfrage neu erstellt (siehe Supporter).

## Eingaben

```text
roster: eigener Kader (Name, Pos, Team) — Pflicht
free_agents: verfügbare Spieler (Waiver/FA) — für Sleeper-Suche nötig
other_rosters: Kader der Ligamitglieder — verbessert Trade-Ziele (optional)
mode: sleepers | trades | both — Standard both
week: aktuelle NFL-Woche — Pflicht
scoring: aus Sleeper-Referenz/Liga — optional
faab_budget: verbleibendes FAAB — optional (für Gebotsvorschlag)
as_of: ISO-8601 — optional; Standard jetzt
```

## Schritt 1 – Bedarfsanalyse (aus dem eigenen Kader)

Vor der Suche den Kader auswerten, damit Chancen zum Bedarf passen:

- **Positionstiefe:** Überschuss vs. Mangel je Position (inkl. Flex/Superflex).
- **Starter-Risiken:** QUES/Out-Häufungen, unsichere Rollen.
- **Bye-Weeks:** Wochen mit Lücken (v. a. Einzelbesetzungen wie K/DEF).
- **Handelsmasse:** Positionen mit verzichtbarem Überschuss.

### Mögliche zukünftige Probleme (Pflicht in der Zusammenfassung)
Die Scout-Zusammenfassung geht über die aktuelle Woche hinaus und benennt
absehbare Risiken der Folgewochen:
- **Bye-Cluster:** Wochen, in denen mehrere Kaderspieler zeitgleich Bye haben.
- **QB-/Superflex-Loch:** mehrere QBs mit demselben Bye.
- **K/DEF-Bye:** Bye des einzigen Kickers/der einzigen Defense (Streaming nötig).
- **Verletzungsrisiko:** aktuell fragliche Spieler mit möglichem Folgeausfall.
- **Dünne Positionen:** ohne Backup drohen Lücken bei Bye/Verletzung.

## Schritt 2 – Sleeper-Suche (Waiver/FA)

Kandidaten aus `free_agents` filtern nach **niedriger Verbreitung** (Rostered %)
**und** mindestens einem **Opportunity-Trigger** der aktuellen Saison:

- Rollenaufstieg (Verletzung/Ausfall eines Spielers davor, Depth-Chart-Aufstieg,
  Trade/Beförderung).
- Steigende Nutzung: Snaps, Routes, Targets, Carries, Red-Zone-Anteil.
- Scheme-Fit: Team-Ausrichtung/bevorzugter Spielertyp begünstigt den Spieler.
- Günstiger nächster Gegner (aus dem Report).

Jeden Kandidaten über Sub-Skill 1 → Sub-Skill 2 bewerten und ranken. Dann:

- **FAAB-Gebot** vorschlagen (Anteil des Budgets nach Upside × Bedarf ×
  erwarteter Konkurrenz; nach Sleeper-FAAB-Regeln, verdeckt, $0 möglich).
- **Add/Drop:** verzichtbarsten Bankspieler nennen (niedrigste Effektivität/kein
  Bye-/Positionsengpass).

## Schritt 3 – Trade-Kandidaten

**Wert-Signal** = Effektivität (Evaluator) **vs.** Marktwahrnehmung (Rostered %,
Start %, ADP, Projektion, Name-Value). Große Lücke = Handelschance.

- **Buy-low (fremde Spieler):** Marktwert temporär gedrückt (schwacher Start,
  schwere frühe Matchups, gefallener Name-Value), aber starke Rollen-/
  Effektivitätssignale → anvisieren.
- **Sell-high (eigene Spieler):** Marktwert über nachhaltiger Rolle (Namensglanz,
  kurzfristiger Ausreißer) oder Positionsüberschuss → als Handelsmasse abgeben.
- **Trade-Paarung:** eigenen Überschuss gegen Bedarf tauschen; Balance über
  Effektivität, nicht über Namen. Bei Bedarf Multi-Spieler-/Pick-/FAAB-Pakete
  gemäß Ligaregeln.

## Verbindliches Ausgabeformat

```markdown
# Scout-Report: <Team> — Woche <n>
Stand: <as_of> | Scoring: <...> | Basierend auf: supporter + evaluator (+ Sleeper-Regeln)

## Bedarfsanalyse
- Überschuss/Mangel je Position, Starter-Risiken, Bye-Lücken, Handelsmasse

## Sleeper-Watchlist (Waiver/FA)
| Spieler | Pos | Team | Rostered % | Trigger | Effektivität | FAAB-Gebot | Add/Drop |

## Trade-Board
### Buy-low Ziele (fremd)
| Spieler | Pos | Team | Marktwert-Signal | Effektivität | Warum unterbewertet |
### Sell-high (eigene)
| Spieler | Pos | Team | Marktwert-Signal | Effektivität | Warum abgeben |
### Vorgeschlagene Trades
- Geben ↔ Bekommen, Begründung über Bedarf/Effektivität

## Konfidenz & Datenlücken
- Gesamtkonfidenz; fehlende Pools (free_agents/other_rosters), "noch keine Saisondaten"
```

Keine erfundenen Spieler/Statistiken; keine Wett-/Gesundheitsaussagen;
Empfehlungen, keine Garantie.

## Konfidenz

- **hoch:** mehrere Spiele Saisondaten + vollständiger FA-/Roster-Pool.
- **mittel:** teils Daten oder unvollständiger Pool.
- **niedrig:** vor Saisonbeginn / kein FA-Pool → nur Rolle, Scheme-Fit, Bedarf.
