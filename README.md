# OSRS GE Oracle

A Grand Exchange flipping tool for Old School RuneScape, built as a dual-purpose system: an **MCP server** for AI assistant integration and a **REST API** for dashboard frontends. It pulls live pricing data from the [OSRS Wiki Prices API](https://prices.runescape.wiki/api/v1/osrs) to surface high-profit arbitrage opportunities in real time.

---

## Features

- **Market Scanner** — Scans the entire Grand Exchange and ranks items by 4-hour profit potential, filtered by minimum profit, ROI, and buy price caps.
- **Item Margin Calculator** — Looks up live buy/sell prices, GE tax, ROI, and max 4h profit for any specific item.
- **Historical Timeseries** — Fetches price history for charting (5m, 1h, 6h, 24h intervals).
- **Item Mapping Cache** — Fetches and caches item metadata (names, IDs, GE limits) locally to minimize redundant API calls.
- **MCP + REST API** — Exposes tools via the Model Context Protocol for AI assistants, and via FastAPI for web dashboards.

---

## Project Structure

```
.
├── server.py          # MCP server — exposes tools for AI assistant integration
├── api.py             # FastAPI REST server — exposes endpoints for dashboard frontends
├── item_mapping.json  # Auto-generated item cache (created on first run)
└── requirements.txt   # Python dependencies
```

---

## Getting Started

### Prerequisites

- Python 3.10+

### Installation

```bash
git clone https://github.com/Mzach55/osrs-ge-oracle.git
cd osrs-ge-oracle
pip install -r requirements.txt
```

### Running the MCP Server

```bash
python server.py
```

On first run, the server fetches and caches item mapping data from the OSRS Wiki. Subsequent starts load from `item_mapping.json`.

### Running the REST API

```bash
uvicorn api:app --reload
```

The API will be available at `http://localhost:8000`. Interactive docs are auto-generated at `http://localhost:8000/docs`.

---

## MCP Tools

### `get_item_margin(item_name)`

Returns live margin data for a specific item.

**Example output:**
```
Live Data for Dragon Bones:
- Buy (Low): 2,800 gp
- Sell (High): 3,100 gp
- Tax: 31 gp
- Profit per item: 269 gp
- ROI: 9.61%
- GE Limit (4h): 18,000
- Max 4h Profit Potential: 4,842,000 gp
```

### `scan_market_for_flips(min_profit, min_roi_percent, max_buy_price, top_n)`

Scans all tradeable items and returns the top flips sorted by 4-hour profit potential.

| Parameter | Default | Description |
|---|---|---|
| `min_profit` | `50000` | Minimum profit per item (gp) |
| `min_roi_percent` | `2.0` | Minimum return on investment (%) |
| `max_buy_price` | `50000000` | Maximum buy price per item (gp) |
| `top_n` | `5` | Number of results to return |

---

## REST API Endpoints

### `GET /api/flips`

Scans the market and returns the top flip opportunities as JSON.

**Query Parameters:**

| Parameter | Default | Description |
|---|---|---|
| `min_profit` | `50000` | Minimum profit per item (gp) |
| `min_roi` | `2.0` | Minimum ROI (%) |
| `max_buy` | `50000000` | Maximum buy price (gp) |
| `limit_n` | `50` | Number of results to return |

**Example:** `GET /api/flips?min_profit=100000&min_roi=5.0&limit_n=10`

### `GET /api/timeseries/{item_id}`

Returns historical price data for a given item, suitable for charting.

**Path Parameter:** `item_id` — the numeric OSRS item ID

**Query Parameter:** `timestep` — one of `5m`, `1h`, `6h`, `24h` (default: `5m`)

---

## Data Source

All pricing data is fetched from the [OSRS Wiki Real-Time Prices API](https://prices.runescape.wiki/api/v1/osrs). Please review their usage policy and set a descriptive `User-Agent` in `server.py` before deploying.

---

## License

MIT