import os
import json
import re
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import psycopg2
import psycopg2.extras

app = FastAPI(title="Pokepilot")

DB_DSN = os.environ.get("DB_DSN", "host=localhost port=5432 dbname=pokedb user=pokedb password=AI_Th0ught_L3ad3r")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/v1/chat/completions")
MODEL = os.environ.get("MODEL", "phi3.5:3.8b")

POKEAPI_BASE = "https://pokeapi.co/api/v2"

ALLOWED_COLUMNS = {"id", "name", "type1", "type2", "total", "hp", "attack", "defense", "sp_atk", "sp_def", "speed", "generation", "legendary"}

TYPES = [
    "Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting",
    "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost",
    "Dragon", "Dark", "Steel", "Fairy"
]

class AskRequest(BaseModel):
    question: str


with open("templates/index.html") as f:
    INDEX_HTML = f.read()


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML


@app.post("/api/ask")
async def ask(req: AskRequest):
    filters = await generate_filters(req.question)

    conn = psycopg2.connect(DB_DSN)
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    query = f"SELECT * FROM pokemon WHERE {filters['where']} ORDER BY {filters['order_by']} LIMIT {filters['limit']}"
    try:
        cur.execute(query)
    except Exception as e:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Database query failed: {e}")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        return {"results": [], "reasoning": filters["reasoning"], "note": "No Pokemon found matching your criteria."}

    async with httpx.AsyncClient(timeout=10) as client:
        tasks = [fetch_pokemon_detail(client, row["name"]) for row in rows]
        details_list = await asyncio.gather(*tasks)

    results = []
    for row, detail in zip(rows, details_list):
        types = [row["type1"]]
        if row["type2"]:
            types.append(row["type2"])
        results.append({
            "id": row["id"],
            "name": row["name"],
            "types": types,
            "total": row["total"],
            "hp": row["hp"],
            "attack": row["attack"],
            "defense": row["defense"],
            "sp_atk": row["sp_atk"],
            "sp_def": row["sp_def"],
            "speed": row["speed"],
            "generation": row["generation"],
            "legendary": row["legendary"],
            "sprite": detail.get("sprite", ""),
            "abilities": detail.get("abilities", []),
            "height": detail.get("height", ""),
            "weight": detail.get("weight", ""),
            "highlights": extract_highlights(row),
        })

    return {
        "question": req.question,
        "sql_query": query,
        "reasoning": filters["reasoning"],
        "results": results,
        "sources": [
            {
                "name": "Pokemon Stats Database",
                "description": "PostgreSQL database seeded with the Kaggle Pokemon dataset (Generations 1–6, 800+ entries including base forms, Mega Evolutions, and alternate forms).",
                "url": "https://www.kaggle.com/datasets/abcsds/pokemon"
            },
            {
                "name": "PokeAPI",
                "description": "Official Pokemon sprite images, abilities, height, and weight data from the public RESTful Pokemon API.",
                "url": "https://pokeapi.co"
            },
            {
                "name": f"Ollama ({MODEL})",
                "description": "Local large language model used to translate natural language queries into database search filters.",
                "url": "https://ollama.ai"
            }
        ],
    }


def extract_highlights(row: dict) -> list:
    stats = [
        ("HP", row["hp"]), ("ATK", row["attack"]), ("DEF", row["defense"]),
        ("SpA", row["sp_atk"]), ("SpD", row["sp_def"]), ("SPD", row["speed"])
    ]
    max_stat = max(stats, key=lambda x: x[1])
    highlights = [f"Highest stat: {max_stat[0]} ({max_stat[1]})"]
    if row["speed"] >= 100:
        highlights.append(f"Fast ({row['speed']} Speed)")
    if row["attack"] >= 120:
        highlights.append(f"Strong physical attacker ({row['attack']} ATK)")
    elif row["attack"] >= 100:
        highlights.append(f"Decent physical attacker ({row['attack']} ATK)")
    if row["sp_atk"] >= 120:
        highlights.append(f"Strong special attacker ({row['sp_atk']} SpA)")
    elif row["sp_atk"] >= 100:
        highlights.append(f"Decent special attacker ({row['sp_atk']} SpA)")
    if row["defense"] >= 100 and row["sp_def"] >= 100:
        highlights.append("Bulky (100+ both defenses)")
    elif row["defense"] >= 100:
        highlights.append(f"Physically bulky ({row['defense']} DEF)")
    elif row["sp_def"] >= 100:
        highlights.append(f"Specially bulky ({row['sp_def']} SpD)")
    if row["total"] >= 600:
        highlights.append("Pseudo-legendary tier stats")
    if row["total"] >= 500 and row["total"] < 600:
        highlights.append("Strong base stats")
    return highlights


async def generate_filters(question: str) -> dict:
    type_list = ", ".join(TYPES)
    prompt = f"""You are a Pokemon competitive team builder. The PostgreSQL table 'pokemon' has:
- id (INTEGER), name (TEXT)
- type1 (TEXT), type2 (TEXT) — valid types: {type_list}
- total, hp, attack, defense, sp_atk, sp_def, speed (INTEGER)
- generation (INTEGER 1-6), legendary (BOOLEAN)

The user asks: "{question}"

Return ONLY valid JSON (no markdown, no extra text):
{{"where": "SQL WHERE clause (safe column names + quoted string values)", "order_by": "column DESC/ASC", "limit": number (1-20), "reasoning": "detailed multi-sentence explanation covering the competitive strategy, why specific types/tiers/stats are chosen, and how the selection fulfills the user's request"}}

Examples:
- "fast electric types" -> {{"where": "(type1='Electric' OR type2='Electric') AND speed > 100", "order_by": "speed DESC", "limit": 10, "reasoning": "Electric-types with Speed over 100 make excellent fast offensive pivots. High Speed ensures they can outpace common threats and land critical hits before taking damage. Priority is given to Speed to maximize the revenge-killing potential of these Pokemon."}}
- "rain team" -> {{"where": "(type1='Water' OR type2='Water') AND speed > 80", "order_by": "speed DESC", "limit": 8, "reasoning": "Rain teams revolve around Swift Swim abusers and Water-type attackers that benefit from rain-boosted Water moves. Water-types with solid Speed stats are preferred to apply immediate offensive pressure under rain. Fast Pokemon like Floatzel and Ludicolo can sweep once rain is up."}}
- "tanky fire types" -> {{"where": "(type1='Fire' OR type2='Fire') AND defense >= 80 AND hp >= 80", "order_by": "defense DESC", "limit": 5, "reasoning": "Bulky Fire-types serve as defensive cores that can take hits and retaliate with STAB Fire moves. High Defense and HP ensure they can switch into physical attackers repeatedly. These Pokemon often pair well with rain or sand teams to cover their Water weakness."}}"""

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(OLLAMA_URL, json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "temperature": 0.1,
        })
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if not json_match:
        raise HTTPException(status_code=500, detail="LLM returned invalid response format")

    try:
        parsed = json.loads(json_match.group())
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse LLM response: {e}")

    where = parsed.get("where", "1=1")
    order_by = parsed.get("order_by", "total DESC")
    limit_val = max(1, min(parsed.get("limit", 10), 20))
    reasoning = parsed.get("reasoning", "")

    validate_where_clause(where)

    return {"where": where, "order_by": order_by, "limit": limit_val, "reasoning": reasoning}


def validate_where_clause(clause: str):
    lower = clause.lower()
    forbidden = ["drop", "delete", "insert", "update", "truncate", "alter", "create", "exec", "--", ";"]
    for word in forbidden:
        if word in lower:
            raise HTTPException(status_code=400, detail=f"Forbidden SQL keyword: {word}")


def to_pokeapi_slug(name: str) -> str:
    name = name.strip()
    mega_match = re.search(r'^(.+?)Mega\s+(.+)$', name)
    if mega_match:
        base = mega_match.group(1).strip().lower()
        return f"{base}-mega"
    slug = name.lower()
    slug = slug.replace('♀', '-f').replace('♂', '-m')
    slug = slug.replace(' ', '-')
    slug = slug.replace('.', '').replace("'", '').replace(':', '').replace('é', 'e')
    return slug


async def fetch_pokemon_detail(client: httpx.AsyncClient, name: str) -> dict:
    slug = to_pokeapi_slug(name)
    url = f"{POKEAPI_BASE}/pokemon/{slug}"
    try:
        resp = await client.get(url, follow_redirects=True)
        if resp.status_code != 200:
            base = slug.replace('-mega', '')
            resp = await client.get(f"{POKEAPI_BASE}/pokemon/{base}", follow_redirects=True)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "sprite": (
                    data.get("sprites", {}).get("other", {})
                    .get("official-artwork", {}).get("front_default", "")
                    or data.get("sprites", {}).get("front_default", "")
                ),
                "abilities": [
                    a["ability"]["name"].replace("-", " ").title()
                    for a in data.get("abilities", [])
                ],
                "height": data.get("height", 0) / 10,
                "weight": data.get("weight", 0) / 10,
            }
    except Exception:
        pass
    return {"sprite": "", "abilities": [], "height": "", "weight": ""}
