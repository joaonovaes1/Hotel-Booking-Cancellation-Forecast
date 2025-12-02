import os
import pandas as pd
import requests
import json
import time
import numpy as np

ACCESS_TOKEN = "kJ9J52P5fkoZ9O0hcLNO"
TB_URL = "http://localhost:8081"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "..", "data", "hotel_bookings.csv")
CSV_PATH = os.path.normpath(CSV_PATH)

print("CSV_PATH usado:", CSV_PATH)

url = f"{TB_URL}/api/v1/{ACCESS_TOKEN}/telemetry"

df = pd.read_csv(CSV_PATH)

for i, (_, row) in enumerate(df.iterrows()):
    # converte a linha toda para dict
    payload = row.to_dict()

    # trata NaN para None, e garante tipos simples
    clean_payload = {}
    for k, v in payload.items():
        if isinstance(v, (np.floating, float)) and pd.isna(v):
            clean_payload[k] = None
        elif isinstance(v, (np.integer, int)):
            clean_payload[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            clean_payload[k] = float(v)
        else:
            clean_payload[k] = None if pd.isna(v) else str(v)

    resp = requests.post(
        url,
        data=json.dumps(clean_payload),
        headers={"Content-Type": "application/json"},
    )
    print(i, resp.status_code, resp.text)
    time.sleep(0.05)  # só pra não bombardear

    # opcional: limitar no começo pra testar
    if i >= 100:
        break
