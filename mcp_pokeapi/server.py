import httpx
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.sse import SseServerTransport
import mcp.types as types
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn


POKEAPI_BASE = "https://pokeapi.co/api/v2"

server = Server("pokeapi")


async def _get_json(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_pokemon",
            description="Get detailed information about a Pokémon by name or Pokédex ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon": {
                        "type": "string",
                        "description": "Pokémon name or Pokédex ID (e.g. 'pikachu' or 25)",
                    }
                },
                "required": ["pokemon"],
            },
        ),
        types.Tool(
            name="list_pokemon",
            description="List Pokémon with pagination (limit and offset)",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "number",
                        "description": "Number of results per page (default 20, max 100)",
                        "default": 20,
                    },
                    "offset": {
                        "type": "number",
                        "description": "Offset for pagination (default 0)",
                        "default": 0,
                    },
                },
            },
        ),
        types.Tool(
            name="get_ability",
            description="Get details about a Pokémon ability by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "ability": {
                        "type": "string",
                        "description": "Ability name or ID (e.g. 'overgrow' or 65)",
                    }
                },
                "required": ["ability"],
            },
        ),
        types.Tool(
            name="get_type",
            description="Get type info including damage relations (strengths/weaknesses)",
            inputSchema={
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "description": "Type name or ID (e.g. 'fire' or 10)",
                    }
                },
                "required": ["type"],
            },
        ),
        types.Tool(
            name="get_evolution_chain",
            description="Get the evolution chain for a given Pokémon name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "pokemon": {
                        "type": "string",
                        "description": "Pokémon name or ID to look up its evolution chain",
                    }
                },
                "required": ["pokemon"],
            },
        ),
        types.Tool(
            name="get_move",
            description="Get details about a Pokémon move by name or ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "move": {
                        "type": "string",
                        "description": "Move name or ID (e.g. 'thunderbolt' or 85)",
                    }
                },
                "required": ["move"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if not arguments:
        arguments = {}

    if name == "get_pokemon":
        pokemon = str(arguments["pokemon"]).lower()
        data = await _get_json(f"{POKEAPI_BASE}/pokemon/{pokemon}")
        return [types.TextContent(type="text", text=_format_pokemon(data))]

    elif name == "list_pokemon":
        limit = min(int(arguments.get("limit", 20)), 100)
        offset = int(arguments.get("offset", 0))
        data = await _get_json(
            f"{POKEAPI_BASE}/pokemon?limit={limit}&offset={offset}"
        )
        results = data.get("results", [])
        lines = [
            f"Pokémon ({data['count']} total, showing {offset+1}-{offset+len(results)}):"
        ]
        for i, r in enumerate(results, start=offset + 1):
            lines.append(f"  {i}. {r['name']}")
        return [types.TextContent(type="text", text="\n".join(lines))]

    elif name == "get_ability":
        ability = str(arguments["ability"]).lower()
        data = await _get_json(f"{POKEAPI_BASE}/ability/{ability}")
        return [types.TextContent(type="text", text=_format_ability(data))]

    elif name == "get_type":
        type_ = str(arguments["type"]).lower()
        data = await _get_json(f"{POKEAPI_BASE}/type/{type_}")
        return [types.TextContent(type="text", text=_format_type(data))]

    elif name == "get_evolution_chain":
        pokemon = str(arguments["pokemon"]).lower()
        species = await _get_json(f"{POKEAPI_BASE}/pokemon-species/{pokemon}")
        chain_url = species["evolution_chain"]["url"]
        chain = await _get_json(chain_url)
        return [
            types.TextContent(
                type="text", text=_format_evolution_chain(chain["chain"])
            )
        ]

    elif name == "get_move":
        move = str(arguments["move"]).lower()
        data = await _get_json(f"{POKEAPI_BASE}/move/{move}")
        return [types.TextContent(type="text", text=_format_move(data))]

    raise ValueError(f"Unknown tool: {name}")


def _format_pokemon(data: dict) -> str:
    name = data["name"]
    pok_id = data["id"]
    types_ = [t["type"]["name"] for t in data["types"]]
    stats = {s["stat"]["name"]: s["base_stat"] for s in data["stats"]}
    abilities = [
        a["ability"]["name"]
        for a in data["abilities"]
        if not a["is_hidden"]
    ]
    hidden = [
        a["ability"]["name"]
        for a in data["abilities"]
        if a["is_hidden"]
    ]
    height = data["height"] / 10
    weight = data["weight"] / 10

    lines = [
        f"#{pok_id} {name.upper()}",
        f"  Types: {', '.join(types_)}",
        f"  Height: {height}m  Weight: {weight}kg",
        f"  Base stats: HP {stats.get('hp', '?')} | "
        f"ATK {stats.get('attack', '?')} | "
        f"DEF {stats.get('defense', '?')} | "
        f"SP.ATK {stats.get('special-attack', '?')} | "
        f"SP.DEF {stats.get('special-defense', '?')} | "
        f"SPD {stats.get('speed', '?')}",
        f"  Abilities: {', '.join(abilities)}",
    ]
    if hidden:
        lines.append(f"  Hidden ability: {hidden[0]}")
    return "\n".join(lines)


def _format_ability(data: dict) -> str:
    name = data["name"]
    effect = ""
    for entry in data.get("effect_entries", []):
        if entry["language"]["name"] == "en":
            effect = entry["short_effect"] or entry["effect"]
            break
    pokemon_list = [p["pokemon"]["name"] for p in data.get("pokemon", [])[:20]]
    lines = [
        f"ABILITY: {name}",
        f"  Effect: {effect}" if effect else "",
        f"  Pokémon with this ability: {', '.join(pokemon_list)}" + 
        ("..." if len(data.get("pokemon", [])) > 20 else ""),
    ]
    return "\n".join(lines)


def _format_type(data: dict) -> str:
    name = data["name"]
    def extract(names: list[dict]) -> list[str]:
        return sorted(n["name"] for n in names)

    dmg = data.get("damage_relations", {})
    lines = [
        f"TYPE: {name.upper()}",
        f"  Strong against (2x): {', '.join(extract(dmg.get('double_damage_to', [])))}",
        f"  Weak to (2x): {', '.join(extract(dmg.get('double_damage_from', [])))}",
        f"  Resists (0.5x): {', '.join(extract(dmg.get('half_damage_from', [])))}",
        f"  Not very effective against (0.5x): {', '.join(extract(dmg.get('half_damage_to', [])))}",
        f"  Immune to: {', '.join(extract(dmg.get('no_damage_from', [])))}",
        f"  Does no damage to: {', '.join(extract(dmg.get('no_damage_to', [])))}",
    ]
    return "\n".join(lines)


def _format_evolution_chain(chain: dict, depth: int = 0) -> str:
    prefix = "  " * depth + ("└── " if depth > 0 else "")
    species_name = chain["species"]["name"]
    result = f"{prefix}{species_name}"
    for evo in chain.get("evolves_to", []):
        result += "\n" + _format_evolution_chain(evo, depth + 1)
    return result


def _format_move(data: dict) -> str:
    name = data["name"]
    effect = ""
    for entry in data.get("effect_entries", []):
        if entry["language"]["name"] == "en":
            effect = entry["short_effect"] or entry["effect"]
            break
    pp = data.get("pp", "?")
    power = data.get("power", "?")
    accuracy = data.get("accuracy", "?")
    move_type = data.get("type", {}).get("name", "?")
    damage_class = data.get("damage_class", {}).get("name", "?")
    return (
        f"MOVE: {name}\n"
        f"  Type: {move_type.upper()}  |  Class: {damage_class.upper()}\n"
        f"  Power: {power}  |  Accuracy: {accuracy}  |  PP: {pp}\n"
        f"  Effect: {effect}" if effect else ""
    )


sse = SseServerTransport("/messages/")


async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(
            streams[0],
            streams[1],
            InitializationOptions(
                server_name="pokeapi",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages/", endpoint=sse.handle_post_message, methods=["POST"]),
    ]
)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
