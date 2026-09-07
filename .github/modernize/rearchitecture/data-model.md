# Datenmodell

## Zentrale Entitäten

- **Roster:** Team, Woche, Scoring, Slots und Spieler.
- **Player/Subject:** Name, Position, NFL-Team, Bye, Status und Training.
- **Supporter Report:** Identität, aktuelle Saisonstatistik, Spieler-Stärken,
  Verletzung, News, Team- und Gegnerkontext, Quellen, Datenlücken und Metadaten.
- **Evaluation:** Faktoren, Gate, Effektivität, Floor/Ceiling, Konfidenz und
  Begründung.
- **Lineup:** Startspieler je Slot, Bank, knappe Entscheidungen, Monitor und
  Scout-Zusammenfassung.
- **Scout Candidate:** Waiver-/FA- oder Trade-Kandidat mit Trigger,
  Effektivität, Bedarf und optionalem FAAB-Vorschlag.

## Beziehungen

Ein Roster enthält viele Player. Jeder Player erzeugt pro Lauf genau einen
frischen Report; ein Report erzeugt eine Evaluation. Viele Evaluationswerte
werden einer Lineup-Zuordnung unterworfen. Ein Lineup kann eine Scout-
Zusammenfassung auslösen. Reports und Bundles referenzieren Quellen und
Zeitstempel, nicht umgekehrt.
