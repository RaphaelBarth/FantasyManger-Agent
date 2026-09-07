# SleeperFantasyManager — Sleeper-Wissensbasis

## Zweck

Diese Wissensbasis beschreibt, wie der NFL-Fantasy-Manager **Sleeper** funktioniert.
Sie ist die **kanonische Referenz** für die Skills `fantasy-lineup-coordinator`,
`fantasy-manager-supporter` und `fantasy-effectiveness-evaluator` (Ligamodell,
Slots, Scoring, Waiver/FAAB, Trades, Matchups, Roster-/Lineup-Regeln).

**Stand der Recherche:** 03.09.2026  
**Wichtig:** Sleeper erlaubt Commissioners, viele Werte pro Liga individuell zu
konfigurieren. Die konkrete Liga-Konfiguration ist daher immer wichtiger als
Standardwerte oder allgemeine Empfehlungen.

## 1. Grundmodell

- Eine Liga besteht aus mehreren Teams/Managern, einem Spielplan, Matchups,
  Rankings und optional Playoffs.
- **Redraft:** Team wird jedes Jahr neu gedraftet.
- **Keeper:** Ein definierter Teil des Teams wird in die nächste Saison übernommen.
- **Dynasty:** Spieler bleiben dauerhaft im Team; Draftpicks und Taxi-Squads sind
  besonders wichtig.
- Der Commissioner erstellt die Liga, lädt Manager ein und verwaltet Regeln,
  Zeitpläne, Kader und Streitfälle.
- Sleeper kombiniert Ligaaktivitäten mit Chat, Benachrichtigungen, News,
  Spielerstatus und Transaktionshistorie.

## 2. Kader und Aufstellung

Typische Slots sind `QB`, `RB`, `WR`, `TE`, `FLEX`, `SUPERFLEX`, `K`, `DEF`
und optional IDP-Positionen. Pro Liga können Startplätze, Bank, IR, Taxi Squad
und Positionslimits angepasst werden.

Vor jedem NFL-Spiel müssen Spieler in aktive Slots oder auf die Bank gesetzt
werden. Nach Beginn des jeweiligen Spieles ist ein Spieler in Sleeper
normalerweise nicht mehr frei verschiebbar. Ein `FLEX` akzeptiert nur die in
der Liga erlaubten Positionen; `SUPERFLEX` erlaubt üblicherweise auch einen QB.

Für den lokalen Manager bedeutet das:

- Slot-Regeln müssen aus der Liga-Konfiguration kommen, nicht aus dem UI.
- Ein Spieler braucht mindestens Status, Team, Position, Bye-Week und
  Spielbeginn.
- Lineup-Validierung muss Spielbeginn, Positionslimits und IR-Regeln prüfen.

## 3. Punktewertung

Sleeper unterstützt Standard-, PPR-, Half-PPR- und vollständig benutzerdefinierte
Scoring-Systeme. Relevante Kategorien:

### Offense

- Passing Yards, Passing TD, Completions, Attempts, First Downs
- Interceptions, Sacks, Pick-Six
- Rushing Yards, Rushing TD, Rush Attempts, First Downs
- Receptions, Receiving Yards, Receiving TD, First Downs
- 2-Point-Conversions
- Boni für lange Plays/TDs und Yard-Meilensteine
- Positionsabhängige Reception-Boni sind möglich

### Kicker

- Field Goals nach Entfernung oder Punkte pro Yard
- PAT made/missed
- Missed oder geblockte Kicks

### Team Defense / IDP

- Points/Yards Allowed mit Stufen oder pro Punkt/Yard
- Sacks, Interceptions, Fumble Recoveries, Forced Fumbles
- Safeties, Defensive TDs, Blocked Kicks, Tackles und Passes Defended
- Return-Yards und 2-Point-Returns

Werte können positiv oder negativ sein. Die aktuelle Projekt-Engine verwendet
hingegen ein kleineres Ran-Schema (`assets/js/scoring.js`); eine Sleeper-Option
ist daher nicht automatisch mit der bestehenden Wertung kompatibel.

## 4. Draft

Sleeper unterstützt unter anderem:

- Snake Draft
- Linear Draft, vor allem für Dynasty/Rookie-Drafts
- Auction Draft
- Offline-, Mock-, Supplemental-, Rookie- und Dispersal-Drafts
- konfigurierbare Rundeanzahl, Pick-Timer, Draftdatum und Draftreihenfolge
- optionales Pick-Trading und 3rd-Round-Reversal

Der Draft erzeugt den initialen Kader. In Dynasty-Ligen sind zukünftige Picks
ein handelbares Asset. Für eine Sleeper-ähnliche Implementierung müssen Pick,
Runde, Saison, Uhr/Timeout, Drafttyp und Draftstatus persistent sein.

## 5. Free Agents und Waiver Wire

Sleeper kennt mehrere Waiver-Modelle:

- **FAAB:** Jeder Manager besitzt ein saisonales Budget; verdeckte Gebote werden
  zum Waiver-Zeitpunkt verarbeitet. Das höchste gültige Gebot gewinnt.
  $0-Gebote sind möglich. Bei Gleichstand entscheidet die konfigurierte
  Waiver-Priorität.
- **Rolling Waivers:** Erfolgreiche Claims verschieben das Team typischerweise
  ans Ende der Prioritätsliste.
- **Reverse Standings:** Priorität folgt der umgekehrten Tabellenreihenfolge.

Commissioners können Budget, Priorität, Verarbeitungstage/-zeiten,
Post-Game-Waivers, Playoff- und Offseason-Regeln anpassen. FAAB kann je nach
Liga auch gehandelt werden. Claims haben Priorität und werden in einem Lauf
atomar verarbeitet; ein Spieler darf nicht von zwei Teams gewonnen werden.

## 6. Trades

Manager können je nach Liga Spieler, aktuelle und zukünftige Draftpicks sowie
FAAB anbieten; Multi-Team-Trades werden unterstützt. Nach Annahme kann ein Trade
eine konfigurierbare Review-/Wartezeit durchlaufen oder sofort verarbeitet werden.

Der Commissioner kann Trades prüfen, ablehnen, sofort durchsetzen oder in
bestimmten Situationen rückgängig machen. Eine Liga kann zusätzlich eine
Abstimmung per Chat-Poll organisieren. Trade-Deadline, Pick-Trading,
Offseason-Trading und Trade-Review sind Ligaeinstellungen und keine globalen
Annahmen.

## 7. Spieltag, Matchups und Playoffs

- Das Matchup vergleicht die aufgestellten Spieler beider Teams anhand der
  tatsächlich erzielten Fantasy-Punkte.
- Live-Punkte können sich durch offizielle Stat-Korrekturen ändern.
- Ergebnisse, Tabellenplatz und Tiebreaker müssen nach der offiziellen
  Auswertung aktualisiert werden.
- Playoff-Anzahl, Bracket, Seeding, Byes, Tiebreaker und Spielwochen sind
  konfigurierbar.
- Sleeper unterstützt je nach Konfiguration zusätzliche Regular-Season-Spiele,
  etwa Doubleheaders oder Median Games.

## 8. Commissioner- und Sicherheitsfunktionen

Für eine Manager-Unterstützung sollten folgende Aktionen als privilegiert
modelliert werden:

- Liga- und Scoring-Einstellungen ändern
- Spieler/Kader/Lineups manuell korrigieren
- Scores und Ergebnisse korrigieren
- Waiver-Priorität und FAAB anpassen
- Trade durchsetzen, ablehnen oder rückgängig machen
- Spielplan, Playoffs und Einladungen verwalten

Jede manuelle Änderung sollte Audit-Log, Zeitstempel, ausführenden Manager und
Begründung speichern. Keine Commissioner-Aktion darf ohne sichtbare Bestätigung
und Berechtigungsprüfung ausgeführt werden.

## 9. Abbildung auf FantasyManager

| Sleeper-Konzept | Aktueller Projektbezug | Nächster sinnvoller Schritt |
|---|---|---|
| Kader/Lineup | `state.lineup`, `FM.config.slots` | Ligaabhängige Slot- und Positionsregeln |
| Scoring | `assets/js/scoring.js` | Scoring-Profil statt nur Ran-Defaults |
| Spielwoche/Ergebnisse | `state.week`, `state.history` | Offizielle Stat-Korrekturen und Live-Status |
| Liga | `state.league` | Mitglieder, Format, Settings und Rollen ergänzen |
| Spielerpool | `state.realPlayers`, `state.realData` | Spielerstatus, Free-Agent- und Waiver-Status |
| Persistenz | IndexedDB/LocalStorage in `assets/js/db.js` | Transaktionen und Audit-Log |
| Online-Modus | Supabase-Schicht | Serverautorisierung für Commissioner-Aktionen |

`state.captain` und die bisherige Ran-Punkteformel sind projektspezifisch und
kein Sleeper-Standard. Bei einer späteren Sleeper-Annäherung dürfen sie nur als
optionale Liga-Features behandelt werden.

## 10. Quellen

Primärquellen (Sleeper Support Center):

- [Fantasy Football Support](https://support.sleeper.com/en/collections/410900-fantasy-football)
- [Scoring-Optionen](https://support.sleeper.com/en/articles/3998131-what-scoring-options-are-available)
- [Waiver-Typen](https://support.sleeper.com/en/articles/9656662-what-types-of-waivers-do-you-support)
- [FAAB und Waiver](https://support.sleeper.com/en/articles/9657110-how-do-faab-and-waivers-work)
- [FAAB-Gebote](https://support.sleeper.com/en/articles/1876040-how-does-faab-bidding-work)
- [Waiver für Regular Season und Playoffs](https://support.sleeper.com/en/articles/3978868-waivers-for-regular-season-playoffs)
- [Draft-Typen](https://support.sleeper.com/en/articles/2408256-what-draft-types-are-supported)
- [Trading](https://support.sleeper.com/en/articles/3188802-how-to-trade)
- [Trade erzwingen](https://support.sleeper.com/en/articles/4033467-how-do-i-force-a-trade-through)
- [Playoff-Seeding](https://support.sleeper.com/en/articles/2408257-can-i-customize-my-league-s-playoff-seeding)
- [Sleeper Fantasy Football](https://sleeper.com/fantasy-football)

Diese Datei ist eine zusammengefasste Arbeitsreferenz und keine vollständige
Wiedergabe der Sleeper-Dokumentation. Links und konkrete UI-Abläufe können sich
ändern; bei Implementierungsentscheidungen ist die aktuelle offizielle
Sleeper-Dokumentation zu prüfen.
