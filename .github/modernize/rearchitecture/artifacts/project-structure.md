# Projektstruktur

## Projekttyp

Ein dateibasiertes Python-Agentenpaket ohne externes Framework. Die
Agentenlogik ist als GitHub-Copilot-Skill-Familie unter `.github/skills`
beschrieben. `tools/` enthält eine Standardbibliotheks-Implementierung für
Reports, Bewertung, Optimierung und Tests.

## Funktionale Domänen

1. **Datenerfassung:** öffentliche Sleeper-NFL-Daten und Quellenqualität.
2. **Faktenaufbereitung:** Statistik, Verletzungen, Team-/Gegnerkontext und News.
3. **Entscheidungsbewertung:** Verfügbarkeits-Gate, Rolle, Scheme-Fit, Matchup
   und Formtrend.
4. **Aufstellungsplanung:** Slot-Eignung und maximales gewichtetes Assignment.
5. **Kaderchancen:** Waiver-, Buy-low-, Sell-high- und Trade-Vorschläge.
6. **Persistenz/Ausgabe:** frische JSON-/Markdown-Reports und Wochen-Bundles.

## Schichten

- **Skill-Verträge:** YAML-Frontmatter und Markdown-SKILL-Dateien.
- **Orchestrierung:** Supporter, Coach und Scout.
- **Deterministische Kernlogik:** `tools/fmlib.py`.
- **Ausführungsadapter:** `tools/run_week.py` und `tools/report_cache.py`.
- **Verträge:** `tools/schemas/*.json`.
- **Regressionen:** `tools/tests/*.py`.
