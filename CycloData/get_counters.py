import ijson
import json
import csv
import requests
import os

url = "https://api.golemio.cz/v2/bicyclecounters"
TOKEN = os.getenv("GOLEMIO_API_KEY")

params = {
    "latlng": "50.0805,14.467",  # souřadnice středu (Praha)
    "range": 18000,             # poloměr v metrech
    "limit": 250,
    "offset": 0
}

headers = {
    "accept": "application/json; charset=utf-8",
    "x-access-token": TOKEN
}

response = requests.get(url, headers=headers, params=params)

if response.status_code == 200:
    data = response.json()
    with open("CycloData/counters.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("✅ Data byla uložena do counters.json")
else:
    print(f"❌ Chyba {response.status_code}: {response.text}")

input_file = 'CycloData/counters.json'
output_file = 'CycloData/counters.csv'

def safe_get(obj, *keys, default=""):
    """Bezpečné získání hodnoty z vnořeného slovníku."""
    for key in keys:
        if isinstance(obj, dict) and key in obj:
            obj = obj[key]
        else:
            return default
    return obj if obj is not None else default

with open(input_file, 'r', encoding='utf-8') as json_file, open(output_file, 'w', newline='', encoding='utf-8') as csv_file:
    fieldnames = [
        'name', 'id', 'route', 'updated_at',
        'latitude', 'longitude',
        'direction_id', 'direction_name'
    ]
    writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
    writer.writeheader()

    features = ijson.items(json_file, 'features.item')
    for feature in features:
        props = safe_get(feature, 'properties', default={})
        coords = safe_get(feature, 'geometry', 'coordinates', default=[None, None])

        try:
            longitude, latitude = coords
        except (ValueError, TypeError):
            longitude, latitude = "", ""

        directions = safe_get(props, 'directions', default=[])
        if not isinstance(directions, list):
            directions = []

        for direction in directions:
            if safe_get(direction, 'id') == "": continue
            writer.writerow({
                'name': safe_get(props, 'name'),
                'id': safe_get(props, 'id'),
                'route': safe_get(props, 'route'),
                'updated_at': safe_get(props, 'updated_at'),
                'latitude': latitude,
                'longitude': longitude,
                'direction_id': safe_get(direction, 'id'),
                'direction_name': safe_get(direction, 'name')
            })

print("✅ Data byla uložena do counters.csv")
