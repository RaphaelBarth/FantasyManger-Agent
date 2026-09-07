---
name: fantasy-manager-cleanup
description: >-
  Entfernt erzeugte Laufzeit- und Reportausgaben des Fantasy-Manager-Agents.
  Der Skill löscht nur sicher erkannte Ausgabeordner wie out-*, reports-* und
  den gemeinsamen temp/-Ordner im Projektstamm. Skill-Definitionen, Tools,
  finale Reports auf oberster Ebene und Architekturartefakte werden niemals
  gelöscht.
---

# Fantasy Manager Cleanup

## Ziel

Diesen Skill verwenden, wenn erzeugte Reports, Lineup-Bundles oder
Evaluation-Ausgaben vollständig entfernt werden sollen.

## Sicherheitsgrenzen

Der Projektstamm muss explizit bekannt sein. Es dürfen nur direkte Unterordner
des Projektstamms gelöscht werden, deren Name einem dieser Muster entspricht:

- `out-*`
- `reports-*`
- `temp` (bzw. `temp-*`) — gemeinsamer Ablageort **aller** Skills/Agenten für
  temporäre/autogenerierte Dateien (Roh-Reports, Zwischen-Eingaben, Caches)

Nicht gelöscht werden:

- `.github/skills/**`
- `.github/modernize/**`
- Finale Reports/Bundles auf oberster Ebene (`lineup-*.md`, `lineup-*.json`,
  `evaluations-*.json`)
- `roster-*.md`, `league-config-*.md`
- README- und Konfigurationsdateien
- beliebige Ordner außerhalb des Projektstamms

## Ablauf

1. Projektstamm bestimmen und normalisieren.
2. Nur direkte Unterordner gegen die erlaubte Namensliste prüfen.
3. Einen Dry-Run mit allen gefundenen Zielpfaden erstellen.
4. Vor der Löschung eine Bestätigung einholen.
5. Nur nach Bestätigung mit `tools/cleanup_generated.py --apply` löschen
   (Skript liegt direkt in diesem Skill-Ordner: `./tools/cleanup_generated.py`).
6. Abschließend melden, welche Ordner gelöscht wurden und welche geschützt
   geblieben sind.

Ohne `--apply` wird niemals gelöscht. Der Skill darf keine Wildcard-Löschung
auf dem gesamten Projektstamm oder eine rekursive Löschung unbekannter Pfade
ausführen.

## Kommando

```text
python tools/cleanup_generated.py --root .       # Dry-Run
python tools/cleanup_generated.py --root . --apply
```

## Erfolgskriterium

Nach erfolgreicher Ausführung existieren im Projektstamm keine direkt
erkannten `out-*`-, `reports-*`- oder `temp`-Ausgabeordner mehr. Geschützte
Projektdateien, finale Reports auf oberster Ebene und Architekturartefakte
bleiben unverändert.
