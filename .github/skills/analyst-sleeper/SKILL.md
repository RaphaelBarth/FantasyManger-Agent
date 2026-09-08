---
name: analyst-sleeper
description: >-
  Fach-Subskill des Analysts: sammelt die auf https://sleeper.com/nfl
  verfügbaren Rohdaten zu einem bestimmten NFL-Spieler oder Team und dient den
  übrigen Analyst-Subskills (Statistik, Verletzung, News, Team-Auswertung) als
  gemeinsame, zwingende Ausgangsbasis/Kreuzcheck. Der Skill ruft die passende
  Sleeper-Seite ab, folgt den dort verlinkten Detailansichten und liefert ein
  vollständiges, quellenbelegtes Datenpaket mit Abrufzeitpunkt. Verwende ihn bei
  Anfragen wie "alle Sleeper-Infos zu Spieler X", "durchsuche Sleeper für Team Y"
  oder "was steht bei Sleeper über X". Keine erfundenen Werte, keine Umgehung von
  Login-, Rate-Limit- oder Zugriffsschutz.
---

# Analyst Sleeper

## Quellen

Die verbindliche Online-Quellenbasis und Zitierregeln stehen in
[`sources.md`](./sources.md). Sleeper ist hier die primäre
Rohdatenquelle; geschützte oder nicht sichtbare Daten werden nicht ergänzt.

## Ziel

Für **genau einen Spieler oder ein Team** alle auf der öffentlichen Sleeper-NFL-
Oberfläche tatsächlich verfügbaren Informationen strukturiert erfassen. Der
Skill ist ein Datensammler, kein Prognose-, Start/Sit-, Trade- oder Wettberater.
Informationen, die Sleeper nicht ausliefert oder die nur nach Anmeldung sichtbar
sind, werden als nicht verfügbar dokumentiert und nicht ergänzt.

## Eingabe

```text
subject: Spielername, Spieler-URL, Teamname oder Team-URL (Pflicht)
season: NFL-Saison, optional; Standard ist die auf Sleeper ausgewählte Saison
week: Woche, optional; Standard ist die aktuell ausgewählte Woche
as_of: ISO-8601-Zeitpunkt, optional; Standard ist jetzt
format: markdown|json, optional; Standard markdown
```

Bei einem mehrdeutigen Namen zuerst nach Team, Position oder Sleeper-URL fragen.
Bei einer Team-Anfrage nur das Team selbst und seine auf Sleeper verknüpften
Spieler-/Teamdaten erfassen; nicht ungefragt die gesamte NFL crawlen.

## Abrufstrategie

1. `https://sleeper.com/nfl` öffnen und die öffentliche NFL-Navigation prüfen.
2. Den passenden Spieler- oder Team-Link aus der Seite bzw. ihrer Suche
   ermitteln. URLs nicht aus einem vermuteten Slug konstruieren, wenn ein
   kanonischer Link gefunden werden kann.
3. Die Zielseite vollständig laden. Bei clientseitig gerenderten Bereichen
   auf das Ende des Ladevorgangs warten und sichtbare Tabs/Akkordeons öffnen,
   sofern sie ohne Login zugänglich sind.
4. Alle öffentlich sichtbaren Detailbereiche und verlinkten, zum Ziel gehörenden
   Unterseiten erfassen: Profil/Kernangaben, Status, Verletzung, News, Statistiken,
   Spielprotokoll, Schedule, Rankings/Projektionen, Ownership/ADP, Depth Chart
   und Team-/Positionskontext — jeweils nur, wenn Sleeper diesen Bereich für das
   Ziel anzeigt.
5. Pagination, Saison- und Wochenfilter der Zielseite prüfen. Für jeden
   tatsächlich verfügbaren Filter eine eigene Datenzeile bzw. einen eigenen
   Abschnitt aufnehmen; den verwendeten Filter im Report festhalten.
6. Werte aus strukturierten Netzwerkantworten oder einer öffentlichen Sleeper-
   Schnittstelle dürfen verwendet werden, wenn sie von der Zielseite selbst
   geladen werden. Keine privaten, authentifizierten oder undokumentierten
   Endpunkte erraten oder gegen Nutzungsbedingungen verwenden.
7. Abrufzeitpunkt, URL, Seitentitel und relevante Filter speichern. Bei
   widersprüchlichen Angaben gilt die aktuellere Darstellung derselben
   Sleeper-Seite; der Widerspruch bleibt im Datenqualitätsabschnitt vermerkt.

## Vollständigkeitsregeln

- "Alle Informationen" bedeutet alle **öffentlich abrufbaren und zum Ziel
  gehörenden** Felder der Sleeper-Seite, nicht beliebige Daten aus dem Internet.
- Leere, nicht geladene oder nicht angebotene Felder als `nicht verfügbar`,
  `nicht veröffentlicht` oder `Login erforderlich` markieren; niemals schätzen.
- Zahlen unverändert mit Sleeper-Einheit übernehmen. Prozentwerte, Rankings,
  Punkte und Zeiträume nicht umrechnen, sofern es nicht ausdrücklich verlangt
  wird.
- Saison- und Wochenkontext bei jeder Statistik bewahren. Keine Vorjahres- oder
  Karrieredaten als aktuelle Daten ausgeben, wenn Sleeper sie nicht so
  kennzeichnet.
- News mit Datum/Uhrzeit, Überschrift, Outlet/Autor und Original-Link erfassen,
  sofern diese Felder sichtbar sind. News-Inhalte nicht über das auf der Seite
  nötige Maß hinaus vervielfältigen.
- Bei Teamdaten Spielerlisten, Record, Schedule, Teamstatistiken, Depth Chart,
  Injury-/Statusmeldungen und Sleeper-Fantasy-Kontext getrennt ausweisen.
- Bei Spielerdaten Identität/Team/Position, Status, Verletzung, Saisonwerte,
  Game Log, Fantasy-Werte, Rankings/Projektionen, Ownership/ADP, Schedule,
  News und angezeigten Kontext erfassen.
- Keine medizinische Diagnose, keine Leistungsprognose und keine Empfehlung aus
  den Rohdaten ableiten.

## Ausgabe: Markdown

```markdown
# Sleeper-NFL-Daten: <subject>

Stand: <as_of>
Quelle: <kanonische Sleeper-URL>
Saison/Woche: <season>/<week oder nicht gesetzt>
Abrufstatus: vollständig | teilweise | nicht zugänglich

## Zusammenfassung des gefundenen Ziels
...

## Stammdaten und Status
| Feld | Wert | Sleeper-Quelle |

## Statistiken und Spielprotokoll
| Saison/Woche/Spiel | Metrik | Wert | Quelle |

## Rankings, Projektionen, Ownership und ADP
| Kategorie | Zeitraum | Wert | Quelle |

## Schedule und Kontext
...

## News und Verletzungs-/Statusmeldungen
| Datum | Typ | Meldung/Überschrift | Outlet/Autor | Quelle |

## Teamdaten
Nur bei Team-Anfrage bzw. wenn Sleeper sie beim Ziel anzeigt.

## Nicht verfügbare oder geschützte Informationen
- <Feld/Bereich>: <Grund>

## Datenqualität
- Abgerufene URLs:
- Verwendete Filter:
- Abrufzeit:
- Pagination vollständig geprüft: ja/nein
- Bekannte Lücken/Widersprüche:
```

## Ausgabe: JSON

```json
{
  "subject": {"input": "...", "kind": "player|team", "canonical_url": "..."},
  "context": {"season": "...", "week": "...", "as_of": "..."},
  "access": {"status": "complete|partial|blocked", "retrieved_at": "..."},
  "identity": {},
  "status": {},
  "statistics": [],
  "game_log": [],
  "rankings_projections_ownership": [],
  "schedule": [],
  "news": [],
  "team_context": {},
  "unavailable": [],
  "sources": [],
  "quality": {"filters": [], "pagination_checked": false, "notes": []}
}
```

Jedes gefüllte Feld muss auf einen Eintrag in `sources` mit URL und
`retrieved_at` zurückführbar sein. Die JSON-Struktur bleibt auch bei fehlenden
Daten vollständig; leere Arrays und `unavailable` sind besser als ausgelassene
Felder.

## Wiederholbarkeit (kein Cache)

Bei **jeder** Anfrage werden die Daten frisch von den Quellen abgerufen — ein
vorhandenes Ergebnis wird nie ungeprüft wiederverwendet. Zeitstempel
(`retrieved_at`) und Quellen je Feld sind Pflicht, damit jeder Abruf
nachvollziehbar bleibt.

## Sicherheits- und Zugriffsregeln

- robots.txt, Nutzungsbedingungen, Rate Limits und HTTP-Fehler respektieren.
- Keine Umgehung von CAPTCHA, Login, Paywall, Bot-Schutz oder Geoblocking.
- Keine Zugangsdaten anfordern, speichern oder ausgeben.
- Bei 401/403/429/5xx den Status transparent melden und nicht aggressiv
  wiederholen; höchstens mit angemessenem Backoff gemäß aufrufendem Tool.
- Drittquellen nur ergänzend und klar getrennt verwenden. Der Auftrag dieses
  Skills ist Sleeper-Daten; externe Quellen dürfen fehlende Sleeper-Felder nicht
  als Sleeper-Daten ausgeben.

## Abnahmekriterien

Der Skill ist bestanden, wenn er:

1. das Ziel eindeutig als Spieler oder Team identifiziert,
2. die kanonische Sleeper-Seite und alle zugänglichen Ziel-Detailbereiche nutzt,
3. Saison-/Wochenfilter, Pagination, Quellen und Abrufzeit dokumentiert,
4. alle sichtbaren Datengruppen in ein stabiles Markdown- oder JSON-Schema bringt,
5. fehlende/geschützte Bereiche ausdrücklich meldet und nichts erfindet,
6. bei Zugriffsschutz sauber abbricht, statt ihn zu umgehen, und
7. keine Prognose, medizinische Aussage oder Fantasy-Empfehlung aus Rohdaten
   ableitet.
