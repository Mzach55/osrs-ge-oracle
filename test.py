import requests
HEADERS = {'User-Agent': 'GE_Oracle_MCP_Server - YourName/GitHub'}
r = requests.get("https://prices.runescape.wiki/api/v1/osrs/5m", headers=HEADERS)
data = r.json()['data']
# Print a sample entry
first_key = next(iter(data))
print(first_key, data[first_key])