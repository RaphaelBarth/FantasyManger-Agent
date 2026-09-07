# Implementation Guide: FantasyManager-Agent

Diese Übersicht ist **nicht der vollständige Verhaltensvertrag**. Vor Änderungen
müssen die für die betroffene Einheit genannten Artefakte sowie die gefilterten
globalen Verträge gelesen werden.

## Systemzuschnitt

Der Agent ist eine NFL-Fantasy-Entscheidungskette:

`Roster + Liga-Regeln -> Sleeper-Rohdaten -> Supporter-Report -> Evaluator -> Coach`

Bei strukturellen Schwächen ergänzt der Scout Waiver-/Trade-Empfehlungen. Die
Berechnung ist lokal und deterministisch; Datenabrufe und News bleiben
quellen- und zeitabhängig.

## Einheiten

| Einheit | Artefakte | Abschlussnachweis |
|---|---|---|
| `manager_agent` | `units/manager_agent/*`, `wire_contracts.yaml` | Anfrage ist an die richtigen Fachskills geroutet und Ergebnisse sind getrennt ausgewiesen |
| `collector` | `units/collector/*`, `wire_contracts.yaml` | Ziel, Saison/Woche, Quellen, Abrufzeit und Lücken sind im Report nachvollziehbar |
| `supporter` | `units/supporter/*`, `shared_modules.yaml`, `cross_unit_state.yaml` | alle Pflichtfragmente sind im einheitlichen Report vorhanden oder explizit als Lücke markiert |
| `evaluator` | `units/evaluator/*`, `shared_modules.yaml` | Faktoren, Gewichte, Gate, Konfidenz und Datenbasis sind reproduzierbar |
| `coach` | `units/coach/*`, `wire_contracts.yaml` | jede Startposition ist regelkonform und die Zuordnung maximiert den Startwert |
| `scout` | `units/scout/*`, `wire_contracts.yaml` | Kandidaten stammen aus gelieferten Pools; Bedarf, Effektivität und Datenlücken sind getrennt |
| `runner` | `units/runner/*`, `wire_contracts.yaml` | JSON/Markdown-Bundle und Schema-Validierung sind erzeugt |

## Globale Filterregeln

- `unit_graph.yaml`: Abhängigkeiten und öffentliche Eingaben/Outputs prüfen.
- `wire_contracts.yaml`: Nur Verträge lesen, die den geänderten Ein-/Ausgabepfad
  berühren.
- `shared_modules.yaml`: `fmlib.py` und Report-Schreiblogik nicht duplizieren.
- `cross_unit_state.yaml`: Report-ID, `content_hash` und `generated_at` als
  zusammengehörigen Lebenszyklus behandeln.
- `migration_boundary.yaml`: `must_rewrite` ist der Änderungsumfang; reine
  `source_anchors` sind kein automatischer Rewrite-Auftrag.

## Navigationshinweis

Die `behavior.yaml`-Dateien enthalten zu erhaltende Seiteneffekte, Zweige und
Fehlerverträge. `bindings.yaml` enthält Eingabe-/Framework-Wiring und
Laufzeitkonfiguration. `unit_decomposition.yaml` enthält nur Kandidaten;
`commit: false` ist absichtlich.
