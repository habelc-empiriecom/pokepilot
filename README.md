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
  docker-compose.yaml   # Container-Definitionen
  init.sql              # Schema + CSV-Import
  pokemon.csv           # Pokémon-Datensatz (801 Zeilen, 13 Spalten)
  mcp_pokeapi/          # MCP-Server (PokeAPI-Proxy)
  webapp/               # Web-App (FastAPI + HTML/CSS/JS)
  README.md             # Diese Datei
```

## Lokales LLM (Ollama)

Ein `ollama`-Service ist in der `docker-compose.yaml` vorkonfiguriert. Starten und ein Modell laden:

```sh
docker compose up -d ollama
docker exec ollama ollama pull phi3.5:3.8b
```

Das Modell ist dann via OpenAI-kompatibler API erreichbar:

```sh
curl http://localhost:11434/v1/chat/completions \
  -d '{
    "model": "phi3.5:3.8b",
    "messages": [{"role": "user", "content": "Build me a rain team for competitive battles."}],
    "stream": false
  }'
```

Empfohlene Modelle für schwache Maschinen:

| Modell | RAM | Bemerkung |
|--------|-----|-----------|
| `phi3.5:3.8b` | ~2.5 GB | Beste Reasoning-Qualität pro GB |
| `llama3.2:3b` | ~2 GB | Gute Allround-Leistung |
| `qwen2.5:1.5b` | ~1 GB | Für sehr knappe Ressourcen |

Alle Container (DB + LLM) können gemeinsam gestartet werden:

```sh
docker compose up -d
```

## Web-App

Die Web-App (`webapp/`) bietet ein Google-ähnliches Suchfeld für natürliche Sprachabfragen. Der Ablauf:

1. **LLM generiert Suchfilter** – Deine Frage wird an Ollama geschickt, das daraus PostgreSQL-WHERE-Bedingungen ableitet
2. **Datenbank-Abfrage** – Die Pokémon-Datenbank wird mit den generierten Filtern durchsucht
3. **PokeAPI-Details** – Zu jedem gefundenen Pokémon werden per [PokeAPI](https://pokeapi.co) aktuelle Daten (inkl. Artwork, Fähigkeiten, Größe/Gewicht) abgerufen
4. **Ergebnisanzeige** – Die gefundenen Pokémon werden als übersichtliche Karten mit Stats-Balken, Typen, Fähigkeiten und Bild unter dem Suchfeld angezeigt

Starten und aufrufen:

```sh
docker compose up -d
# Browser öffnen: http://localhost:8000
```

Beispiel-Abfragen:
- `"Build me a rain team for competitive battles."`
- `"Fast physical attackers from generation 3."`
- `"Tanky fire types with high defense."`
- `"All legendary Pokemon from gen 1."`

## Datenbestand

- **800 Pokémon** aus den Generationen 1–6
- Enthält Basisformen, Mega-Evolutions, regionale Varianten (z. B. Rotom, Deoxys, Kyurem)
- 73 legendäre/mysteriöse Pokémon (`legendary = True`)
- Datenquelle: [Kaggle Pokémon Dataset](https://www.kaggle.com/datasets/abcsds/pokemon)

## Aktueller Stand

### Implementiert

- [x] PostgreSQL-Datenbank mit Pokémon-Schema und 800+ Seed-Datensätzen
- [x] MCP-PokeAPI-Server (Proxy zur öffentlichen PokeAPI)
- [x] Ollama-Integration für lokale LLMs (phi3.5, llama3.2, qwen2.5)
- [x] Web-App mit Suchfeld und Ergebnisanzeige (Pokémon-Karten mit Stats, Typen, Bildern)
- [x] Pipeline: Frage → LLM-generierte Suchfilter → DB-Query → PokeAPI-Details → Anzeige

### Noch offen

- [ ] Tests
- [ ] CI/CD
- [ ] Umgebungsvariablen (`.env`) statt hartcodierter Credentials
- [ ] Fehlerbehandlung für Mega-Form-Namen (PokeAPI-Kompatibilität)
