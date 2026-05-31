# astro-mcp

An MCP server that gives Claude the ability to generate natal charts and solar returns (Revolución Solar), with full bilingual support in English and Spanish.

Built on [kerykeion](https://github.com/g-battaglia/kerykeion) and the Swiss Ephemeris. No external API needed.

---

## Tools

### `get_natal_chart`
Generates a full natal (birth) chart.

| Parameter | Required | Description |
|---|---|---|
| `name` | Yes | Person's name |
| `birth_date` | Yes | YYYY-MM-DD (e.g. `1973-07-25`) |
| `birth_time` | Yes | HH:MM 24h (e.g. `17:25`) |
| `city` | Yes | City of birth |
| `country_code` | No | ISO 2-letter code (e.g. `AR`, `ES`, `MX`) |
| `lat` | No | Latitude override (decimal degrees) |
| `lng` | No | Longitude override (decimal degrees) |
| `tz_str` | No | Timezone override (e.g. `America/Argentina/Buenos_Aires`) |
| `language` | No | `en` or `es` (default: `en`) |

### `get_solar_return`
Generates a Solar Return (Revolución Solar) chart for a given year.

| Parameter | Required | Description |
|---|---|---|
| `name` | Yes | Person's name |
| `birth_date` | Yes | YYYY-MM-DD |
| `birth_time` | Yes | HH:MM 24h |
| `birth_city` | Yes | City of birth |
| `return_year` | Yes | Year for the Solar Return (e.g. `2025`) |
| `birth_country_code` | No | ISO 2-letter code for birth city |
| `birth_lat/lng/tz_str` | No | Coordinate overrides for birth city |
| `return_city` | No | City where the SR is cast (defaults to birth city) |
| `return_country_code` | No | ISO 2-letter code for return city |
| `return_lat/lng/tz_str` | No | Coordinate overrides for return city |
| `language` | No | `en` or `es` (default: `en`) |

---

## Installation

### 1. Clone or download this project

```bash
git clone https://github.com/yourname/astro-mcp.git
cd astro-mcp
```

### 2. Install dependencies (recommended: uv or pip)

```bash
# With uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .
```

Verify it works:

```bash
python -m astro_mcp.server --help
```

---

## Connect to Claude Desktop

Add this to your Claude Desktop config file:

**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "astro-mcp": {
      "command": "python",
      "args": ["-m", "astro_mcp.server"],
      "cwd": "/absolute/path/to/astro-mcp"
    }
  }
}
```

Or if you installed the package (so `astro-mcp` is on your PATH):

```json
{
  "mcpServers": {
    "astro-mcp": {
      "command": "astro-mcp"
    }
  }
}
```

Restart Claude Desktop after saving. You should see a hammer icon with `astro-mcp` tools available.

---

## Connect to Claude.ai (remote MCP)

To expose it remotely (e.g. via ngrok or a VPS), run with HTTP transport:

```python
# In server.py, change the last line to:
mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)
```

Then add to Claude.ai Settings > Integrations > MCP:

```
https://your-server.com/mcp
```

---

## Example prompts

```
Give me Pablo's natal chart: born 25 July 1973, 17:25, Morón, Argentina. In Spanish.

Generate a Solar Return for Pablo for 2025. Born 1973-07-25 17:25 in Morón, AR.
Cast it in London, UK.

Carta natal de LorenaM: nacida el 19 de mayo de 1971 a las 14:15 en Córdoba, Argentina.
```

---

## Notes on geocoding

The server uses Nominatim (OpenStreetMap) for live geocoding and includes a
fallback table for common cities in Argentina, Spain, Mexico, and other
Spanish-speaking countries. If a city is not found, pass `lat`, `lng`, and
`tz_str` directly.

---

## License

MIT
