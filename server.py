import os
import json
import requests
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("GE_Oracle")

# API Configuration
API_BASE_URL = "https://prices.runescape.wiki/api/v1/osrs"
HEADERS = {'User-Agent': 'GE_Oracle_MCP_Server - YourName/GitHub'}
MAPPING_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "item_mapping.json")


def load_or_fetch_mapping() -> tuple[dict, dict]:
    """Loads or fetches item mapping, storing limits and bidirectional lookups."""
    if os.path.exists(MAPPING_FILE):
        with open(MAPPING_FILE, 'r') as f:
            data = json.load(f)
            return data['by_name'], data['by_id']
            
    print(f"[{mcp.name}] Fetching enriched mapping from OSRS Wiki...")
    response = requests.get(f"{API_BASE_URL}/mapping", headers=HEADERS)
    response.raise_for_status()
    raw_data = response.json()
    
    by_name = {}
    by_id = {}
    
    for item in raw_data:
        if 'name' in item and 'id' in item:
            item_data = {
                'id': item['id'],
                'name': item['name'],
                'limit': item.get('limit', 0) # Some items don't have limits
            }
            by_name[item['name'].lower()] = item_data
            by_id[str(item['id'])] = item_data
            
    # Save standard JSON format
    cache_data = {'by_name': by_name, 'by_id': by_id}
    with open(MAPPING_FILE, 'w') as f:
        json.dump(cache_data, f)
        
    print(f"[{mcp.name}] Cached {len(by_name)} items with GE limits.")
    return by_name, by_id

# Load mappings into memory
NAME_TO_DATA, ID_TO_DATA = load_or_fetch_mapping()

@mcp.tool()
def get_item_margin(item_name: str) -> str:
    """Calculates the current margin, ROI, and 4-hour profit potential for a specific item."""
    try:
        query_name = item_name.strip().lower()
        if query_name not in NAME_TO_DATA:
            return f"Error: Could not find '{item_name}'."
            
        item_data = NAME_TO_DATA[query_name]
        item_id = item_data['id']
        limit = item_data['limit']
        
        response = requests.get(f"{API_BASE_URL}/latest", headers=HEADERS, params={'id': item_id})
        response.raise_for_status()
        live_data = response.json()
        
        if str(item_id) not in live_data['data']:
            return f"No live pricing data for '{item_name}'."
            
        prices = live_data['data'][str(item_id)]
        high = prices.get('high') or 0
        low = prices.get('low') or 0
        
        if high == 0 or low == 0:
            return f"Incomplete trading data for '{item_name}'. (High or Low price is 0)"
            
        tax = min(int(high * 0.01), 5000000)
        profit = (high - tax) - low
        roi = (profit / low) * 100
        max_4h_profit = profit * limit if limit > 0 else "N/A (No Limit)"
        
        return (f"Live Data for {item_data['name']}:\n"
                f"- Buy (Low): {low:,} gp\n"
                f"- Sell (High): {high:,} gp\n"
                f"- Tax: {tax:,} gp\n"
                f"- Profit per item: {profit:,} gp\n"
                f"- ROI: {roi:.2f}%\n"
                f"- GE Limit (4h): {limit:,}\n"
                f"- Max 4h Profit Potential: {max_4h_profit:,} gp")
                
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def scan_market_for_flips(min_profit: int = 50000, min_roi_percent: float = 2.0, max_buy_price: int = 50000000, top_n: int = 5) -> str:
    """
    Scans the entire Grand Exchange for the best flips based on strict arbitrage parameters.
    Returns the top items sorted by highest total 4-hour profit potential.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/latest", headers=HEADERS)
        response.raise_for_status()
        live_data = response.json()['data']
        
        viable_flips = []
        
        for item_id_str, prices in live_data.items():
            if item_id_str not in ID_TO_DATA:
                continue
                
            high = prices.get('high') or 0
            low = prices.get('low') or 0
            
            # Filter out broken data and items above our budget
            if high <= 0 or low <= 0 or low > max_buy_price:
                continue
                
            tax = min(int(high * 0.01), 5000000)
            profit = (high - tax) - low
            
            # Filter by minimum profit
            if profit < min_profit:
                continue
                
            roi = (profit / low) * 100
            # Filter by ROI
            if roi < min_roi_percent:
                continue
                
            limit = ID_TO_DATA[item_id_str]['limit']
            
            # We want items with a known limit to calculate true potential
            if limit <= 0:
                continue
                
            max_4h_profit = profit * limit
            
            viable_flips.append({
                'name': ID_TO_DATA[item_id_str]['name'],
                'profit': profit,
                'roi': roi,
                'limit': limit,
                'max_4h': max_4h_profit,
                'buy_price': low
            })
            
        # Sort by maximum 4-hour profit descending
        viable_flips.sort(key=lambda x: x['max_4h'], reverse=True)
        
        # Format the output
        top_flips = viable_flips[:top_n]
        if not top_flips:
            return "No flips found matching those parameters. Try lowering your min_profit or min_roi."
            
        output = f"Top {len(top_flips)} Market Flips (Sorted by 4h Potential):\n" + ("-" * 50) + "\n"
        for rank, flip in enumerate(top_flips, 1):
            output += (f"{rank}. {flip['name']}\n"
                       f"   Buy at: {flip['buy_price']:,} gp\n"
                       f"   Profit/Item: {flip['profit']:,} gp (ROI: {flip['roi']:.2f}%)\n"
                       f"   Max 4h Profit: {flip['max_4h']:,} gp (Limit: {flip['limit']:,})\n\n")
                       
        return output.strip()
        
    except Exception as e:
        return f"Error scanning market: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')