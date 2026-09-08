---
name: journalist
description: >-
  Fach-Subskill des Analysts: trägt ausschließlich aktuelle News/Meldungen zu
  einem Spieler oder Team zusammen — primär aus dem Sleeper News Feed (NFL,
  FF News, NFL Community) sowie verifizierten NFL-Insidern, mit Quellen-Tiering
  und Bestätigungsstatus. Keine Statistik, keine Stärken/Schwächen-Bewertung,
  keine offizielle Verletzungsstatus-Feststellung (nur die Meldung darüber).
  Wird vom fantasy-manager orchestriert, kann aber auch einzeln für
  "aktuelle News zu Spieler X" genutzt werden.
---

# Journalist — News

## Quellen

Die verbindliche Online-Quellenbasis und Zitierregeln stehen in
[`sources.md`](./sources.md). Jede Meldung erhält Outlet,
Autor, Veröffentlichungszeitpunkt, URL und `retrieved_at`.

## Ziel

Nur **aktuelle, quellenbelegte News/Meldungen** zu einem Spieler oder Team
sammeln: Verletzungsmeldungen (als Meldung, nicht als offizielle Statusfest-
stellung), Rollen-/Depth-Chart-Änderungen, Transaktionen, Inactives,
Coaching-/Scheme-News. Kein Statistikwert, keine Stärken/Schwächen-Bewertung.

## Abgrenzung zu den Geschwister-Subskills

- Die **offizielle Statusfeststellung** (Injury Report, Practice-Status)
  gehört zu `doctor`; dieser Skill liefert nur die
  **Meldung darüber** (wer hat wann was gemeldet).
- Statistik/Team-Ausrichtung/Stärken-Schwächen: siehe
  `analyst-stats` bzw. `analyst-team-analysis`.

## Eingaben

```text
subject: Spielername oder Teamname (Pflicht)
as_of: ISO-8601-Zeitpunkt, optional; standardmäßig jetzt
lookback: Zeitraum, optional; Standard die letzten 7 Tage bis `as_of`
```

## Grundregeln

- **Nur News, keine Bewertung.** Wiedergabe der Meldung; keine Einordnung, ob
  sie fantasy-relevant „gut" oder „schlecht" ist.
- **Immer mit Feed-Quelle/Autor + Zeitstempel.** Nie eine Meldung ohne Quelle
  übernehmen.
- **Aktualität vor Vollständigkeit.** Bei mehreren Meldungen zum selben Thema
  gilt die **neuere** Version; ältere/überholte Meldungen werden nicht separat
  aufgeführt (höchstens als „ursprünglich gemeldet, später aktualisiert").
- **Unbestätigtes klar kennzeichnen** (`confirmed: false`), niemals als Fakt
  ausgeben.

## Sleeper News Feed (Hauptquelle über Sub-Subskill)

`analyst-sleeper` liefert im Abschnitt „News und Verletzungs-/
Statusmeldungen" den auf Sleeper kuratierten Feed. Dieser hat drei
Feed-Quellen mit **unterschiedlicher Verlässlichkeit**:

- **NFL** — offizielle Meldungen/Announcements → nahe Primärquelle; für
  Verletzungsmeldungen trotzdem den Hinweis „gegen offiziellen Injury Report
  abzugleichen" mitgeben (das Abgleichen selbst macht der Injury-Subskill).
- **FF News** — redaktionell/Experten-Kuratierung → Ursprungs-Outlet nennen,
  wenn ermittelbar zur Primärquelle zurückverfolgen.
- **NFL Community** — Crowdsourced/Gerücht → **nie alleiniger Beleg**;
  entweder durch eine andere Quelle bestätigt übernehmen oder ausdrücklich als
  „unbestätigt/Gerücht" markieren (`confirmed: false`).

## Weitere Quellen

- **Verifizierte NFL-Insider** (X/Twitter: Schefter, Rapoport, Pelissero,
  Garafolo, Yates, Fowler, Russini, Schultz, etablierte Team-Beat-Reporter) —
  immer mit Autor + Zeitstempel, nie als alleiniger Beleg, möglichst durch eine
  offizielle Quelle bestätigen.
- **Offizielle Team-/Liga-Announcements** (Transaktionen, Inactives) — höchste
  Verlässlichkeit, direkt übernehmbar.

Details/Tiers: [sources.md](../../sources.md).

## Ausgabe: JSON-Fragment

```json
{
  "news": [
    {
      "headline": "...",
      "feed_source": "NFL|FF News|NFL Community|Insider|Team",
      "outlet": "...",
      "date": "ISO-8601",
      "url": "...",
      "confirmed": true
    }
  ],
  "sources": [{"url": "...", "type": "news", "published": "...", "retrieved_at": "..."}]
}
```

Neueste Meldung zuerst; leeres Array + Hinweis „keine aktuellen News", wenn
nichts Relevantes vorliegt.

## Ausgabe: Markdown (Fragment)

```markdown
## News (Sleeper-Feed + Primärquellen)
| Datum | Meldung | Feed-Quelle (NFL/FF News/NFL Community) | Outlet/Autor | bestätigt? |
(aktuelle, relevante News; „NFL Community" nur mit Bestätigung, sonst „unbestätigt")
```

## Abnahmekriterien

1. Jede Meldung mit Feed-Quelle/Autor + Zeitstempel + Link (wenn verfügbar).
2. „NFL Community"-Meldungen ohne Zweitquelle klar als unbestätigt markiert.
3. Nur die neueste Version eines Themas, keine Redundanz.
4. Kein Statistikwert, keine Stärken/Schwächen-Bewertung, keine eigene
   Verletzungsdiagnose im Output.
