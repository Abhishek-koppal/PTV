import os
import hashlib
import hmac
import requests
import json
from dotenv import load_dotenv

load_dotenv()

DEV_ID = os.getenv("PTV_DEV_ID")
API_KEY = os.getenv("PTV_API_KEY")
BASE_URL = "https://timetableapi.ptv.vic.gov.au"


def build_signed_url(request_path: str) -> str:
    """
    request_path should include the leading slash and any query params,
    To fetch departures for a specific stop and route type, e.g. '/v3/departures/route_type/0/stop/1071'
    """
    separator = "&" if "?" in request_path else "?"
    raw = f"{request_path}{separator}devid={DEV_ID}"

    signature = hmac.new(
        API_KEY.encode("utf-8"),
        raw.encode("utf-8"),
        hashlib.sha1
    ).hexdigest().upper()

    return f"{BASE_URL}{raw}&signature={signature}"


def get_departures(stop_id, route_type=0):
    path = f"/v3/departures/route_type/{route_type}/stop/{stop_id}"
    url = build_signed_url(path)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# if __name__ == "__main__":
#     # Flinders Street Station, stop_id 1071, route_type 0 = train
#     #data = get_departures(stop_id=1071, route_type=0)
#     print(json.dumps(data, indent=2))

def get_tram_routes():
    """List all tram routes (route_type=1)."""
    path = "/v3/routes"
    # PTV API expects route_types as a repeated query param, e.g. ?route_types=1
    path += "?route_types=1"
    url = build_signed_url(path)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def get_tram_disruptions():
    """All current disruptions affecting trams."""
    path = "/v3/disruptions?route_types=1"
    url = build_signed_url(path)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def worst_tram_route():
    """Naive 'worst' = route with the most active disruptions right now."""
    routes = get_tram_routes()["routes"]
    disruptions_data = get_tram_disruptions()["disruptions"]

    # disruptions come back keyed by mode, e.g. {"metro_tram": [...], "general": [...]}
    all_disruptions = []
    for mode_disruptions in disruptions_data.values():
        all_disruptions.extend(mode_disruptions)

    counts = {}
    for d in all_disruptions:
        for route in d.get("routes", []):
            rid = route.get("route_id")
            if rid is not None:
                counts[rid] = counts.get(rid, 0) + 1

    if not counts:
        return None

    worst_id = max(counts, key=counts.get)
    route_name = next((r["route_name"] for r in routes if r["route_id"] == worst_id), "Unknown")
    return {"route_id": worst_id, "route_name": route_name, "disruption_count": counts[worst_id]}

def get_all_tram_disruptions(save_to_file=True, filepath="tram_disruptions.json"):
    """
    Fetch all current disruptions for trams (route_type=1), unmodified.
    Returns the full JSON response from PTV, optionally saved to disk.
    """
    data = get_tram_disruptions()

    if save_to_file:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {filepath}")

    return data

if __name__ == "__main__":
    data = get_all_tram_disruptions()
    print(json.dumps(worst_tram_route(), indent=2))
    print(json.dumps(data, indent=2))