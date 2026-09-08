---
name: assistant-coach
description: >-
  Führt die von den spezialisierten Analyst-Skills gefundenen Reports pro
  Spieler zu genau einem einheitlichen und sauberen kanonischen Report zusammen.
  Entfernt doppelte Aussagen, bewahrt Quellen und Provenienz, kennzeichnet
  Widersprüche und erstellt keine neuen Fakten, Prognosen oder Empfehlungen.
  Verwende den Skill nach
  analyst-sleeper, analyst-team-analysis, analyst-stats, doctor und journalist
  sowie vor coach oder scout.
---

# Assistant Coach

## Ziel

Aus allen von den Analysten erhaltenen Reports pro Spieler einen einzigen,
vollständigen, einheitlichen und sauberen Report erzeugen. Der Skill
recherchiert nicht selbst und
bewertet nicht fantasy-spezifisch. Er normalisiert, dedupliziert und verbindet
nur bereits belegte Ergebnisse.

## Eingaben

```text
subject: Spielername oder Teamname — Pflicht
season: Saison — Pflicht
week: NFL-Woche — optional
as_of: ISO-8601-Zeitpunkt — Pflicht
sleeper_report: Ergebnis von analyst-sleeper — Pflicht, sofern verfügbar
team_analysis: Ergebnis von analyst-team-analysis — Pflicht
stats: Ergebnis von analyst-stats — Pflicht
injury: Ergebnis von doctor — Pflicht
news: Ergebnis von journalist — Pflicht
report_dir: Ablageort des kanonischen Reports — optional
```

Fehlt ein Spezial-Report, wird sein Anteil als `not_available` mit Datenlücke
markiert. Der Synthesizer bricht wegen eines fehlenden Einzel-Reports nicht ab.

## Ablauf

1. Eingaben anhand von `subject`, Saison, Woche und `as_of` zuordnen.
2. Fakten in ein gemeinsames Schema normalisieren.
3. Exakte Duplikate entfernen: gleiche Aussage, gleiche Quelle und gleicher
   Beleg erscheinen nur einmal.
4. Inhaltliche Duplikate zusammenführen: gleiche Aussage aus mehreren Quellen
   wird zu einem Fakt mit allen relevanten Quellen und dem neuesten
   `retrieved_at` verbunden.
5. Gleiche Fakten mit unterschiedlichen Quellen nicht blind überschreiben.
   Primärquellen haben Vorrang; widersprüchliche Angaben bleiben als
   `conflict` mit Quellen, Zeitpunkten und Begründung sichtbar.
6. Den fachlichen Zuständigkeitsbereich respektieren. Statistik, Verletzung,
   News, Team-/Matchup-Daten und Sleeper-Rohdaten werden nicht zu Prognosen
   vermischt.
7. Datenlücken aus allen Eingaben vereinigen und doppelte Lücken entfernen.
8. Einen kanonischen Report mit stabiler `report_id`, `generated_at` und
   Provenienz schreiben. Ein vorhandener Report derselben ID wird ersetzt.

## Deduplizierungsregeln

- Gleiche Aussage nach Normalisierung von Groß-/Kleinschreibung, Leerzeichen
  und Formatierung nur einmal ausgeben.
- Zahlen, Einheiten, Wochen und Datumsangaben niemals stillschweigend runden
  oder vereinheitlichen, wenn dadurch der Fakt verändert würde.
- Quellen nicht verlieren: Beim Zusammenführen alle eindeutigen Quellen behalten.
- Eine News-Meldung ist kein offizieller Injury-Status.
- Sleeper-Werte bleiben als Sleeper-Daten gekennzeichnet und ersetzen keine
  Primärquelle, sofern der Fach-Analyst eine Primärquelle verlangt.
- Ältere Quellen werden nicht gelöscht; sie werden als ältere Provenienz oder
  bei Widerspruch als Konflikt dokumentiert.
- Keine Synthese aus fehlenden Werten, keine Schätzungen und keine erfundenen
  Spieler, Statistiken oder Statusangaben.

## Kanonisches Ausgabeformat

```json
{
  "meta": {
    "report_id": "slug-subject-season-week",
    "subject": "...",
    "season": 2026,
    "week": 1,
    "as_of": "...",
    "generated_at": "...",
    "content_hash": "..."
  },
  "facts": {
    "stats": {},
    "injury": {},
    "news": [],
    "team_analysis": {},
    "sleeper": {}
  },
  "conflicts": [],
  "data_gaps": [],
  "provenance": [
    {
      "claim": "...",
      "source": "...",
      "published_at": "...",
      "retrieved_at": "...",
      "tier": "A|B|C"
    }
  ],
  "source_reports": [
    "analyst-sleeper",
    "analyst-team-analysis",
    "analyst-stats",
    "doctor",
    "journalist"
  ]
}
```

`facts` enthält nur deduplizierte belegte Fakten. `conflicts` und `data_gaps`
bleiben auch dann vorhanden, wenn sie leer sind. Der Report ist die einzige
Faktenquelle, die nachfolgende Evaluator-, Scout- und Coach-Schritte verwenden.

## Abgrenzung

- `fantasy-manager` orchestriert die Skills und übergibt die Ergebnisse.
- `assistant-coach` dedupliziert und erstellt den kanonischen Report.
- `coach` erstellt daraus die Effektivitätsbewertung und Einzelspieler-Prediction.
- `scout` erstellt Waiver-/Trade-Empfehlungen.
- `coach` erstellt die Prediction für den nächsten Spieltag.

Keine Prognose, keine Start/Sit-Empfehlung, keine medizinische Diagnose und
keine Wettberatung in diesem Skill.
