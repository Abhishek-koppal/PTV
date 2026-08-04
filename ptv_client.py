import os
import hashlib
import hmac
import requests
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


def get_departures(stop_id: int, route_type: int = 0):
    path = f"/v3/departures/route_type/{route_type}/stop/{stop_id}"
    url = build_signed_url(path)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    # Flinders Street Station, stop_id 1071, route_type 0 = train
    data = get_departures(stop_id=1071, route_type=0)
    print(data)