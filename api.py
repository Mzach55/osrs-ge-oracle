from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

from server import ID_TO_DATA, API_BASE_URL, HEADERS, fetch_volume_data

app = FastAPI(title="OSRS GE Oracle Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/flips")
def get_flips(
    min_profit: int = Query(50000, description="Minimum profit per item"),
    min_roi: float = Query(2.0, description="Minimum Return on Investment %"),
    max_buy: int = Query(50000000, description="Max buy price per item"),
    max_trade_age: int = Query(600, description="Max seconds since last trade on either side"),
    min_5m_volume: int = Query(5, description="Minimum trades on each side in the last 5 minutes"),
    limit_n: int = Query(50, description="Number of results to return")
):
    """
    Scans the market and returns an array of JSON objects representing the best flips.
    Filters by trade recency and 5-minute volume to exclude illiquid or manipulated items.
    """
    now = time.time()

    response = requests.get(f"{API_BASE_URL}/latest", headers=HEADERS)
    response.raise_for_status()
    live_data = response.json()['data']

    vol_data = fetch_volume_data()
    
    viable_flips = []
    
    for item_id_str, prices in live_data.items():
        if item_id_str not in ID_TO_DATA:
            continue
            
        high = prices.get('high') or 0
        low = prices.get('low') or 0
        high_time = prices.get('highTime') or 0
        low_time = prices.get('lowTime') or 0

        # Filter incomplete data and budget caps
        if high <= 0 or low <= 0 or low > max_buy:
            continue

        # --- LIQUIDITY FILTER 1: Trade recency ---
        if (now - high_time) > max_trade_age or (now - low_time) > max_trade_age:
            continue

        # --- LIQUIDITY FILTER 2: 5-minute volume ---
        vol = vol_data.get(item_id_str, {})
        high_vol = vol.get('highPriceVolume', 0)
        low_vol = vol.get('lowPriceVolume', 0)
        if high_vol < min_5m_volume or low_vol < min_5m_volume:
            continue
            
        tax = min(int(high * 0.01), 5000000)
        profit = (high - tax) - low
        
        if profit < min_profit:
            continue
            
        roi = (profit / low) * 100
        if roi < min_roi:
            continue
            
        limit = ID_TO_DATA[item_id_str]['limit']
        if limit <= 0:
            continue
            
        max_4h_profit = profit * limit
        
        viable_flips.append({
            'id': int(item_id_str),
            'name': ID_TO_DATA[item_id_str]['name'],
            'buy_price': low,
            'sell_price': high,
            'tax': tax,
            'profit': profit,
            'roi': round(roi, 2),
            'limit': limit,
            'max_4h': max_4h_profit,
            'high_vol_5m': high_vol,
            'low_vol_5m': low_vol,
            'high_time': high_time,
            'low_time': low_time,
        })
        
    viable_flips.sort(key=lambda x: x['max_4h'], reverse=True)
    
    return {"flips": viable_flips[:limit_n]}

@app.get("/api/timeseries/{item_id}")
def get_timeseries(item_id: int, timestep: str = "5m"):
    """
    Fetches the historical pricing data required for the D3.js line charts.
    Timestep options: '5m', '1h', '6h', '24h'
    """
    response = requests.get(
        f"{API_BASE_URL}/timeseries", 
        headers=HEADERS, 
        params={'id': item_id, 'timestep': timestep}
    )
    response.raise_for_status()
    return response.json()