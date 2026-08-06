import datetime, json, os

import requests

from ptv_client import build_signed_url

def save_bronze(endpoint: str, data: dict, out_dir="bronze_raw"):
    os.makedirs(out_dir, exist_ok=True)
    record = {
        "_ingested_at": datetime.datetime.utcnow().isoformat(),
        "_source_endpoint": endpoint,
        "data": data,
    }
    fname = endpoint.strip("/").replace("/", "_")
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%S")
    with open(f"{out_dir}/{fname}_{ts}.json", "w") as f:
        json.dump(record, f, indent=2)
        
def ptv_get(request_path: str) -> dict:
    url = build_signed_url(request_path)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

data = ptv_get("/v3/departures/route_type/0/stop/1071")
save_bronze("/v3/departures/route_type/0/stop/1071", data)