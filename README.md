# pokepilot

Provisions eine PostgreSQL 16-Datenbank, gefüllt mit umfassenden Pokémon-Daten (Generationen 1–6, 800+ Einträge inkl. Mega-Entwicklungen und alternativer Formen).

## Voraussetzungen

- [Docker](https://docs.docker.com/get-docker/) inkl. `docker compose`

## Quick Start

```sh
docker compose up
```

Dadurch wird ein PostgreSQL-Container (`pokemon-db`) gestartet und automatisch das Schema sowie die Seed-Daten geladen.

### Verbindungsdaten

| Parameter     | Wert                  |
|---------------|-----------------------|
| Host          | `localhost`           |
| Port          | `5432`                |
| Datenbank     | `pokedb`              |
| Benutzer      | `pokedb`              |
| Passwort      | `AI_Th0ught_L3ad3r`   |

Der Container verwendet `network_mode: host`, sodass PostgreSQL direkt auf dem Host-Netzwerk läuft.

## Datenbankschema

```sql
CREATE TABLE pokemon (
    id          INTEGER,
    name        TEXT,
    type1       TEXT,
    type2       TEXT,
    total       INTEGER,
    hp          INTEGER,
    attack      INTEGER,
    defense     INTEGER,
    sp_atk      INTEGER,
    sp_def      INTEGER,
    speed       INTEGER,
    generation  INTEGER,
    legendary   BOOLEAN
);
```

## Projektstruktur

```
pokepilot/
  docker-compose.yaml   # Container-Definition (PostgreSQL 16)
  init.sql              # Schema + CSV-Import
  pokemon.csv           # Pokémon-Datensatz (801 Zeilen, 13 Spalten)
  README.md             # Diese Datei
```

## Datenbestand

- **800 Pokémon** aus den Generationen 1–6
- Enthält Basisformen, Mega-Evolutions, regionale Varianten (z. B. Rotom, Deoxys, Kyurem)
- 73 legendäre/mysteriöse Pokémon (`legendary = True`)
- Datenquelle: [Kaggle Pokémon Dataset](https://www.kaggle.com/datasets/abcsds/pokemon)

## Aktueller Stand

Dies ist das initiale Scaffolding für den Hackathon. Das Projekt besteht derzeit ausschließlich aus der Datenbank-Infrastruktur. Folgende Bereiche sind noch zu implementieren:

- [ ] API-Schicht (Backend)
- [ ] Frontend / UI
- [ ] Tests
- [ ] CI/CD
- [ ] Umgebungsvariablen (`.env`) statt hartcodierter Credentials
