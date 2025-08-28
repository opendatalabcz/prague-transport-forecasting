import requests
import csv
import json
from datetime import datetime, timedelta
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6MzY4OSwiaWF0IjoxNzUwNzY5NzMxLCJleHAiOjExNzUwNzY5NzMxLCJpc3MiOiJnb2xlbWlvIiwianRpIjoiY2JkMDAyNmMtYmU1YS00ZDhhLWJkMWEtZDJkYTdiMzA2OTcyIn0.EBheHNy4j2GFQFGh-DX_Bye81lh9gBHOfj7_ganUVa8"  # tvůj Golemio token
BASE_URL = "https://api.golemio.cz/v2/bicyclecounters/detections"

# Seznam všech direction_id kamer
direction_ids = []
with open("cyclo-counters.csv", 'r') as csvfile:
    for line in csvfile.readlines()[1:]:
        array = line.split(',')
        direction_id = array[6]
        direction_ids.append(direction_id)
print(len(direction_ids))
print(direction_ids)

# Rozsah dnů, např. celý rok 2020
start_date = datetime(2020, 1, 1)
end_date = datetime(2025, 7, 25)

# Výstupní CSV
with open("detections.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ['date'] + direction_ids
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    current_date = start_date
    while current_date <= end_date:
        from_iso = current_date.replace(hour=0, minute=0, second=0).isoformat()
        to_iso = current_date.replace(hour=23, minute=59, second=59).isoformat()

        headers = {
            'accept': 'application/json; charset=utf-8',
            'x-access-token': TOKEN,
        }

        params = {
            'offset': '0',
            'from': from_iso,
            'to': to_iso,
            'aggregate': 'true'
        }

        # Retry loop
        attempts = 0
        while True:
            response = requests.get(
                BASE_URL, headers=headers, params=params
            )
            if response.status_code == 200:
                break
            attempts += 1
            if attempts > 5:
                print(f"❌ Chyba {response.status_code} dne {current_date.strftime('%Y-%m-%d')}")
                break
            print(f"⏳ Čekám, opakuji pokus ({attempts})...")
            time.sleep(5)

        if response.status_code != 200:
            current_date += timedelta(days=1)
            continue

        data = response.json()

        # Sestavení řádku podle dostupných hodnot
        row = {"date": current_date.strftime("%Y-%m-%d")}
        id_to_value = {entry["id"]: entry.get("value", '') for entry in data}

        for direction_id in direction_ids:
            row[direction_id] = id_to_value.get(direction_id, '')

        writer.writerow(row)
        time.sleep(0.1)  # šetrnost k API
        print(current_date)
        current_date += timedelta(days=1)
        
