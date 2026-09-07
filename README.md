# FantasyManager-Agent

Skill-Familie für einen **Sleeper**-NFL-Fantasy-Manager: sammelt Daten,
bewertet Spieler, baut die beste Wochenaufstellung und findet Waiver-/
Trade-Chancen — reproduzierbar, ohne Cache.

## Konfiguration (von dir editierbar)

Kader und Liga-Regeln sind **keine festen Werte im Code**, sondern zwei
Markdown-Dateien auf oberster Ebene, die du frei anpassen oder duplizieren
kannst:

- **`roster-<team>.md`** — dein Kader (Name — Position — NFL-Team, eine Zeile
  je Spieler). Beispiel: [roster-team-r4ph4.md](./roster-team-r4ph4.md).
- **`league-config-<team>.md`** — deine Liga-Einstellungen (Scoring, Slots,
  Waiver/Trade/Playoff-Regeln). Beispiel: [league-config-r4ph4.md](./league-config-r4ph4.md).

Für ein weiteres Team/eine weitere Liga legst du einfach ein neues Dateipaar
mit anderem `<team>`-Namen an (z. B. `roster-team-x.md` +
`league-config-team-x.md`) — der Rest der Pipeline funktioniert unverändert.

## Pipeline

Feste Reihenfolge, orchestriert vom [fantasy-manager-agent](./.github/agents/fantasy-manager-agent.agent.md):

```
Cleanup ─▶ Supporter ─▶ Evaluator ─▶ Scout ─▶ Coach
```

| Schritt | Skill | Aufgabe |
|---|---|---|
| 0. Cleanup | [fantasy-manager-cleanup](./.github/skills/fantasy-manager-cleanup/SKILL.md) | löscht alte `temp/`-Daten |
| 1. Supporter | [fantasy-manager-supporter](./.github/skills/fantasy-manager-supporter/SKILL.md) | sammelt Fakten je Spieler (Statistik, Verletzung, News, Team-Ausrichtung), holt Rohdaten über [fantasy-manager-supporter-sleeper](./.github/skills/fantasy-manager-supporter-sleeper/SKILL.md) |
| 2. Evaluator | [fantasy-effectiveness-evaluator](./.github/skills/fantasy-effectiveness-evaluator/SKILL.md) | macht aus jedem Report einen Effektivitätswert |
| 3. Scout | [fantasy-opportunity-scout](./.github/skills/fantasy-opportunity-scout/SKILL.md) | findet Waiver-/Buy-low-/Sell-high-/Trade-Kandidaten |
| 4. Coach | [fantasy-lineup-coach](./.github/skills/fantasy-lineup-coach/SKILL.md) | löst die Slot-Zuordnung und fasst alles zu **einem** Abschlussreport zusammen |

Regelbasis (Slots, Scoring, Waiver/FAAB, Trades):
[SleeperFantasyManager.md](./.github/skills/fantasy-lineup-coach/SleeperFantasyManager.md).

## Nutzung

Es gibt **keinen direkten Skript-Aufruf für dich als Nutzer** — die gesamte
Logik und der Ablauf laufen ausschließlich über den
[fantasy-manager-agent](./.github/agents/fantasy-manager-agent.agent.md). Du
stellst eine Anfrage (z. B. "stelle das beste Team für Woche 1 auf"); der
Agent routet sie durch die feste Pipeline (Cleanup → Supporter → Evaluator →
Scout → Coach) und liefert das Ergebnis. Die `tools/`-Skripte je Skill
(z. B. `coach_assign.py`) sind interne Implementierungsdetails, die der Agent
bzw. die Skills selbst aufrufen — nicht für manuelle Einzelaufrufe gedacht.

Ergebnis auf oberster Ebene: `lineup-<team>-w<n>.md` (finaler Report, mit
Scout-Zusammenfassung und Begründung je Spieler). Maschinenlesbare
Begleitdateien landen in `./temp/` — dieser Ordner ist in `.gitignore`
ausgeschlossen und wird vom Cleanup-Skill geleert.

## Grundsätze

- **Kein Cache:** jeder Lauf erzeugt frische Reports; nichts wird ungeprüft
  wiederverwendet.
- **Nur belegte Fakten:** offizielle NFL-/Team-/ESPN-/PFR-Quellen zuerst, jede
  Zahl mit Quelle und Datum, keine erfundenen Spieler/Statistiken/Annahmen.
  Kanonische Quellenliste: [sources.md](./.github/skills/fantasy-manager-supporter/sources.md).
- **Tools direkt beim Skill:** jeder ausführende Skill bringt seine
  Python-Tools als eigenen `tools/`-Unterordner mit (nur Standardbibliothek);
  Owner der gemeinsamen Engine ist `fantasy-lineup-coach`.
