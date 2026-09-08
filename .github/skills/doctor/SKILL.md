---
name: doctor
description: >-
  Recherchiert ausschließlich aktuelle, online belegte Verletzungen und
  gemeldete Ausfallzeiten eines NFL-Spielers. Verwendet die Quellenregeln aus
  sources.md, übernimmt keine eigenen Vermutungen und erstellt keine
  Diagnose oder Prognose.
---

# Doctor — Verletzungen

## Quellen

Die verbindliche Online-Quellenbasis und Zitierregeln stehen in
[`sources.md`](./sources.md). Diese Datei muss vor der Recherche verwendet
werden. Für Verletzungsstatus und Ausfallzeiten gelten NFL.com und offizielle
Team-Injury-Reports als primäre Quellen.

## Ziel

Für genau einen Spieler die **aktuell online belegte Verletzung** und, falls
eine Quelle sie ausdrücklich nennt, die **Ausfallzeit** recherchieren. Dazu
gehören der gemeldete Status (z. B. questionable/doubtful/out/IR), Practice-
Status, Verletzungsbezeichnung, erwartete oder bestätigte Ausfalldauer sowie
Quelle und Datum. **Keine Historie** und keine vergangenen oder erledigten
Verletzungen. Fehlt eine aktuelle Quelle, darf daraus nicht geschlossen
werden, dass der Spieler gesund oder verfügbar ist.

## Abgrenzung zu den Geschwister-Subskills

Statistik, Team-Ausrichtung/Stärken-Schwächen und News sind **nicht** Teil
dieses Skills — dafür `analyst-stats`,
`analyst-team-analysis`, `journalist`.
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

- **Nur aktuelle Quellen.** Berücksichtige nur Verletzungen und Ausfallzeiten,
  die zum Recherchezeitpunkt noch aktuell sind. Frühere oder erledigte
  Verletzungen werden nicht erwähnt.
- **Keine Vermutungen.** Keine Diagnose, keine eigene Einschätzung von Schwere,
  Verfügbarkeit oder Rückkehrdatum. Eine Ausfallzeit darf nur übernommen
  werden, wenn sie in einer Online-Quelle ausdrücklich genannt wird.
- **Quellenpflicht.** Jede Aussage benötigt eine URL, ein Veröffentlichungs-
  datum und `retrieved_at`. Suchmaschinen-Snippets ohne Originalquelle zählen
  nicht.
- **Kein Beleg, kein Fakt.** Wenn keine aktuelle Quelle gefunden wird, gib
  `status: "not_reported"` und eine offene Datenlücke aus; niemals
  `active` oder „gesund“ daraus ableiten.

## Sleeper als Hilfsquelle (Sub-Subskill)

`analyst-sleeper` kann als Kreuzcheck verwendet werden. Sleeper allein ist
kein ausreichender Beleg für eine Verletzung oder Ausfallzeit; bei
Abweichungen gilt die aktuellere belastbare Primärquelle aus `sources.md`.

## Quellenstrategie

1. **NFL.com Injury Report** (offiziell, primär)
2. **Offizielle Teamseite** (Practice-Status DNP/LP/FP, Pressekonferenzen)
3. ESPN (Status-Übersicht, sofern mit Quelle)
4. Sleeper NFL Data Skill (Kreuzcheck, keine alleinige Quelle)
5. Verifizierte NFL-Insider (X/Twitter, siehe
  [sources.md](./sources.md))
   nur ergänzend, mit Autor + Zeitstempel, nie als alleiniger Beleg; möglichst
   durch offiziellen Report bestätigen.

## Ausgabe: JSON-Fragment

```json
{
  "injury": {
    "status": "not_reported|questionable|doubtful|out|ir",
    "practice": "DNP|LP|FP|null",
    "injury_name": "nur wenn von der Quelle genannt",
    "absence_duration": "nur wenn von der Quelle ausdrücklich genannt",
    "note": "quellennahe Kurzfassung ohne eigene Einordnung",
    "date": "ISO-8601",
    "source": "URL"
  },
  "sources": [{"url": "...", "type": "injury_report", "published": "...", "retrieved_at": "..."}]
}
```

## Ausgabe: Markdown (Fragment)

```markdown
## Aktuelle Verletzung
| Datum | Verletzung | Status | Ausfallzeit | Quelle |
(nur aktuelle, ausdrücklich belegte Angaben; sonst "keine aktuelle
Verletzung oder Ausfallzeit online belegt")
```

## Abnahmekriterien

1. Nur aktuelle Verletzungen und Ausfallzeiten, keine Historie.
2. Jede Aussage stammt aus einer Online-Quelle aus `sources.md` und enthält
  URL, Veröffentlichungsdatum und Abrufzeitpunkt.
3. Ausfallzeiten werden nur übernommen, wenn sie ausdrücklich gemeldet sind.
4. Keine Diagnose, keine eigene Vermutung und keine selbst berechnete
  Rückkehr-Prognose.
5. Ohne aktuellen Beleg: `status: "not_reported"` und Datenlücke, nicht
  `active` oder „gesund“.
