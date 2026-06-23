---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #ffffff;
    color: #1a1a2e;
  }
  section.title {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 60%, #0f3460 100%);
    color: #ffffff;
    text-align: center;
    justify-content: center;
  }
  section.title h1 {
    font-size: 2.8rem;
    color: #e94560;
    margin-bottom: 0.3em;
  }
  section.title h2 {
    font-size: 1.1rem;
    color: #a8b2c8;
    font-weight: 400;
  }
  section.chapter {
    background: #0f3460;
    color: #ffffff;
    justify-content: center;
    text-align: center;
  }
  section.chapter h1 { font-size: 2.2rem; color: #e94560; }
  section.chapter p  { color: #a8b2c8; font-size: 1.1rem; }
  h1 { color: #0f3460; border-bottom: 3px solid #e94560; padding-bottom: 0.2em; }
  h2 { color: #16213e; }
  strong { color: #e94560; }
  code { background: #f0f4ff; padding: 0.1em 0.4em; border-radius: 4px; color: #0f3460; font-size: 0.85em; }
  table { width: 100%; border-collapse: collapse; }
  th { background: #0f3460; color: #ffffff; padding: 0.5em 0.8em; }
  td { padding: 0.4em 0.8em; border-bottom: 1px solid #e0e6f0; }
  tr:nth-child(even) td { background: #f0f4ff; }
  blockquote { border-left: 4px solid #e94560; padding-left: 1em; color: #555; background: #f8f9ff; margin: 0.5em 0; }
---

<!-- _class: title -->

# PokePilot

## Agentic AI in Practice

**Christoph · Maria · Heiko**

---

# The Problem

Our original idea: an **AI agent for automated product selection** in newsletter campaigns.

Then reality hit: **we come from three different companies.**

- Sensitive customer and product data — not shareable
- Different data privacy & governance policies
- No shared infrastructure

> We need a **neutral demo system** that demonstrates the same AI patterns — without real business data.

**Solution:** Pokémon — public, structured, multi-source. Same architecture, no compliance problem.

---

# PokePilot: The Transfer

| Newsletter Agent _(original idea)_ | PokePilot _(demo)_ |
|-------------------------------------|-------------------|
| Natural language → product filters | Natural language → Pokémon filters |
| ERP · Shop API · trend data | PostgreSQL · PokeAPI · Ollama |
| LLM generates SQL WHERE clause | LLM generates SQL WHERE clause |
| Product cards + campaign reasoning | Pokémon cards + strategy explanation |
| Local, privacy-compliant | Local, fully containerised |

> **Same idea. Same technology. Different data.**

---

# The Three Data Sources

| Source | What it provides | Real-world analogy |
|--------|-----------------|-------------------|
| **PostgreSQL** | 800+ Pokémon: stats, types, generations | ERP / data warehouse |
| **PokeAPI** | Sprites, abilities, height, weight | Online shop API / PIM |
| **Ollama (local)** | Natural language → SQL filters + reasoning | AI reasoning layer |

A single natural-language question links all three automatically.

---

# The Pipeline

```
"Build me a rain team for competitive battles."
          │
          ▼
  Ollama (phi3.5, running locally)
          │ generates structured JSON
          ▼
  { "where": "(type1='Water' OR type2='Water') AND speed > 80",
    "order_by": "speed DESC", "limit": 8,
    "reasoning": "Rain teams need fast Water-types..." }
          │
          ├──► PostgreSQL: SELECT * FROM pokemon WHERE … LIMIT 8
          │
          └──► PokeAPI: sprites + abilities in parallel for all 8 Pokémon
                    │
                    ▼
          Pokémon cards · stat bars · strategy text · source attribution
```

---

# From PokePilot to the Real Product

The transfer is direct — only the data sources change:

| PokePilot | Smart Promotion Copilot |
|-----------|------------------------|
| `"Build me a rain team"` | `"Top 20 women's fashion with > 30% discount"` |
| PostgreSQL (Pokémon stats) | BigQuery / ERP (margins, stock levels) |
| PokeAPI (artwork, abilities) | Shop API / PIM (product images, descriptions) |
| Ollama local | Ollama local — no data leaving the premises |
| Strategy explanation | Campaign reasoning + ranking |

**What stays the same:** LLM as reasoning layer · structured JSON output · local infrastructure · multi-source integration

---

<!-- _class: title -->

# Thank You

## PokePilot — Agentic AI, local, reproducible, transferable

`docker compose up` · `http://localhost:8000`

**Christoph · Maria · Heiko**
