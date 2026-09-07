# Tech-Stack

- **Sprache:** Python 3, ausschließlich Standardbibliothek in `tools/`.
- **Agent-Integration:** GitHub-Copilot-Skills unter `.github/skills`.
- **Externe Daten:** öffentliche Sleeper-NFL-Seiten/Feeds; ergänzend offizielle
  NFL-/Team-/ESPN-/PFR-Quellen nach Quellenregeln.
- **Persistenz:** JSON und Markdown im Dateisystem; kein Cache im fachlichen
  Ablauf. Gleiche Report-ID wird frisch überschrieben.
- **Schemas:** eigener Minimalvalidator in `fmlib.py` plus JSON-Schemas.
- **Optimierung:** Ungarischer Algorithmus für das maximale
  Spieler-zu-Slot-Assignment.
- **Konfiguration:** gebündelte Teamprofile und Spielplan; Eingabeprofile
  überschreiben Defaults.

## Relevante Grenzen

Zugriffsschutz, Login, Rate Limits und nicht veröffentlichte Sleeper-Daten dürfen
nicht umgangen werden. Fehlende Saisonwerte werden nicht geschätzt; sie senken
Vollständigkeit bzw. Konfidenz.
