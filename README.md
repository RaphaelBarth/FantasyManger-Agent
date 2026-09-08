# FantasyManager-Agent

Skill-Familie für einen **Sleeper**-NFL-Fantasy-Manager: sammelt Daten,
bewertet Spieler für den nächsten Spieltag, findet Waiver-/Trade-Chancen und
erstellt belegte Reports — reproduzierbar, ohne Cache.

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

Feste Reihenfolge, orchestriert vom [fantasy-manager](./.github/agents/fantasy-manager.agent.md):

```
Caretaker ─▶ Analyst ─▶ Evaluator ─▶ Scout ─▶ Coach
```

| Schritt | Skill | Aufgabe |
|---|---|---|
| 0. Caretaker | [caretaker](./.github/skills/caretaker/SKILL.md) | löscht alte `temp/`-Daten |
| 1. Analysts | [analyst-sleeper](./.github/skills/analyst-sleeper/SKILL.md), [analyst-team-analysis](./.github/skills/analyst-team-analysis/SKILL.md), [analyst-stats](./.github/skills/analyst-stats/SKILL.md), [doctor](./.github/skills/doctor/SKILL.md), [journalist](./.github/skills/journalist/SKILL.md) | spezialisierte Faktenrecherche; der `fantasy-manager` führt die Ergebnisse zusammen |
| 2. Assistant Coach | [assistant-coach](./.github/skills/assistant-coach/SKILL.md) | erstellt pro Spieler aus allen Analyst-Reports einen einheitlichen, sauberen Report |
| 3. Coach | [coach](./.github/skills/coach/SKILL.md) | erstellt aus einem Spielerreport eine Prediction für den nächsten Spieltag |
| 4. Scout | [scout](./.github/skills/scout/SKILL.md) | findet Waiver-/Buy-low-/Sell-high-/Trade-Kandidaten |

Regelbasis (Slots, Scoring, Waiver/FAAB, Trades):
[SleeperFantasyManager.md](./.github/agents/SleeperFantasyManager.md).

## Nutzung

Es gibt **keinen direkten Skript-Aufruf für dich als Nutzer** — die gesamte
Logik und der Ablauf laufen ausschließlich über den
[fantasy-manager](./.github/agents/fantasy-manager.agent.md). Du
stellst eine Anfrage (z. B. "stelle das beste Team für Woche 1 auf"); der
Agent routet sie durch die feste Pipeline (Caretaker → Analysts → Assistant Coach → Coach →
Scout) und liefert das Ergebnis. Die `tools/`-Skripte je Skill
(z. B. `coach_assign.py`) sind interne Implementierungsdetails, die der Agent
bzw. die Skills selbst aufrufen — nicht für manuelle Einzelaufrufe gedacht.

Ergebnis auf oberster Ebene: `lineup-<team>-w<n>.md` (finaler Report, mit
Scout-Zusammenfassung und Begründung je Spieler). Beim Start eines neuen
Report-Laufs löscht der Caretaker nach Bestätigung alte `lineup-*.md`-Reports
und generierte Begleitdaten; Kader- und Liga-Konfigurationen bleiben erhalten.
Maschinenlesbare Begleitdateien landen in `./temp/` — dieser Ordner ist in
`.gitignore` ausgeschlossen und wird vom Caretaker-Skill geleert.

## Grundsätze

- **Kein Cache:** jeder Lauf erzeugt frische Reports; nichts wird ungeprüft
  wiederverwendet.
- **Nur belegte Fakten:** offizielle NFL-/Team-/ESPN-/PFR-Quellen zuerst, jede
  Zahl mit Quelle und Datum, keine erfundenen Spieler/Statistiken/Annahmen.
  Kanonische Quellenliste: [sources.md](./.github/skills/sources/sources.md).
- **Tools direkt beim Skill:** jeder ausführende Skill bringt seine
  Python-Tools als eigenen `tools/`-Unterordner mit (nur Standardbibliothek);
  Owner der gemeinsamen Engine ist `coach`.
