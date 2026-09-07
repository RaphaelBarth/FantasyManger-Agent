---
name: fantasy-manager-supporter-injuries
description: >-
  Fach-Subskill des Supporters: liefert ausschließlich den aktuell relevanten
  Verletzungs-/Statusstatus eines Spielers (Injury Report, Practice-Status,
  Datum, Quelle) — keine Verletzungshistorie, keine Statistik, keine
  Prognose. Nutzt den Sleeper NFL Data Skill als Kreuzcheck, bestätigt aber
  gegen den offiziellen NFL/Team-Injury-Report. Wird vom
  fantasy-manager-supporter orchestriert, kann aber auch einzeln für
  "Verletzungsstatus von Spieler X" genutzt werden.
---

# Fantasy Manager Supporter — Verletzungen

## Ziel

Nur das **aktuell relevante Verletzungsthema** eines Spielers liefern: Status
(z. B. active/questionable/doubtful/out/IR), Practice-Status der Woche
(DNP/LP/FP), kurze Meldung und Quelle/Datum. **Keine Historie** (keine
vergangenen Verletzungen, kein Verlauf über mehrere Wochen), keine
medizinische Einschätzung, keine Prognose zur Rückkehr.

## Abgrenzung zu den Geschwister-Subskills

Statistik, Team-Ausrichtung/Stärken-Schwächen und News sind **nicht** Teil
dieses Skills — dafür `fantasy-manager-supporter-stats`,
`fantasy-manager-supporter-team-analysis`, `fantasy-manager-supporter-news`.
Eine Verletzungs-**Meldung** (z. B. „laut Insider XY fraglich") gehört in den
News-Subskill; sobald sie **offiziell im Injury Report** steht, gehört der
aktuelle Status hierher.

## Eingaben

```text
subject: Spielername (Pflicht)
week: NFL-Woche, optional; Standard aktuelle Woche
as_of: ISO-8601-Zeitpunkt, optional; standardmäßig jetzt
```

## Grundregeln

- **Nur der aktuelle Status.** Ein Report enthält höchstens **eine** aktuelle
  Verletzungsmeldung; frühere/abgeschlossene Verletzungen werden nicht erwähnt.
- **Keine Diagnose, keine Prognose.** Nur den gemeldeten Status/die Meldung
  wiedergeben, keine Einschätzung zur Rückkehr oder Schwere ableiten.
- Kein Beleg vorhanden → `status: "active"` ohne Meldung (nicht „vermutlich
  gesund" behaupten, nur den fehlenden Beleg dokumentieren).
- Jede Meldung mit Quelle + Datum.

## Sleeper als Hilfsquelle (Sub-Subskill)

`fantasy-manager-supporter-sleeper` liefert im Abschnitt „Stammdaten und Status"
sowie „News und Verletzungs-/Statusmeldungen" den auf Sleeper angezeigten
Status/Practice-Status — als **schneller Kreuzcheck** nutzbar. Für die
Übernahme in den Report muss der Status gegen den **offiziellen NFL-/Team-
Injury-Report** bestätigt werden (Tier A); bei Abweichung gilt die offizielle
Quelle, die Sleeper-Angabe wird nicht ungeprüft übernommen.

## Quellenstrategie

1. **NFL.com Injury Report** (offiziell, primär)
2. **Offizielle Teamseite** (Practice-Status DNP/LP/FP, Pressekonferenzen)
3. ESPN (Status-Übersicht, sofern mit Quelle)
4. Sleeper NFL Data Skill (Kreuzcheck, keine alleinige Quelle)
5. Verifizierte NFL-Insider (X/Twitter, siehe
   [sources.md](../../sources.md))
   nur ergänzend, mit Autor + Zeitstempel, nie als alleiniger Beleg; möglichst
   durch offiziellen Report bestätigen.

## Ausgabe: JSON-Fragment

```json
{
  "injury": {
    "status": "active|questionable|doubtful|out|ir",
    "practice": "DNP|LP|FP",
    "note": "kurze Meldung",
    "date": "ISO-8601",
    "source": "URL/Quelle"
  },
  "sources": [{"url": "...", "type": "injury_report", "published": "...", "retrieved_at": "..."}]
}
```

## Ausgabe: Markdown (Fragment)

```markdown
## Aktuelle Verletzung
| Datum | Status/Meldung | Quelle |
(nur das aktuelle Thema; sonst "keine aktuelle Verletzungsmeldung")
```

## Abnahmekriterien

1. Höchstens eine aktuelle Meldung, keine Historie.
2. Status gegen den offiziellen Injury Report bestätigt (Sleeper allein reicht
   nicht als Beleg).
3. Kein medizinisches Urteil, keine Rückkehr-Prognose.
4. Ohne Beleg: `status: "active"`, keine Meldung, kein Kommentar.
