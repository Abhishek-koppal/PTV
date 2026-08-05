import json
from datetime import datetime, timezone
from collections import defaultdict

def load_disruptions(filepath="tram_disruptions.json"):
    with open(filepath) as f:
        data = json.load(f)

    # Flatten all modes into one list (metro_tram, general, etc.)
    all_disruptions = []
    for mode, items in data.get("disruptions", {}).items():
        for d in items:
            d["_mode"] = mode
            all_disruptions.append(d)
    return all_disruptions


def parse_date(date_str):
    """PTV dates look like '2026-08-01T00:00:00Z'."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def rank_tram_lines(filepath="tram_disruptions.json"):
    disruptions = load_disruptions(filepath)
    now = datetime.now(timezone.utc)

    # route_id -> stats
    stats = defaultdict(lambda: {
        "route_name": None,
        "disruption_count": 0,
        "total_days": 0.0,
        "titles": [],
    })

    for d in disruptions:
        routes = d.get("routes", [])
        if not routes:
            continue  # skip disruptions with no route attached (e.g. general/network-wide)

        from_date = parse_date(d.get("from_date"))
        to_date = parse_date(d.get("to_date")) or now  # ongoing disruptions: treat as "until now"
        duration_days = max((to_date - from_date).total_seconds() / 86400, 0) if from_date else 0

        for route in routes:
            # only count tram routes (route_type 1), in case 'general' disruptions leak other modes in
            if route.get("route_type") != 1:
                continue

            rid = route.get("route_id")
            if rid is None:
                continue

            s = stats[rid]
            s["route_name"] = route.get("route_name", s["route_name"])
            s["disruption_count"] += 1
            s["total_days"] += duration_days
            s["titles"].append(d.get("title", ""))

    # Convert to list and rank
    ranked = []
    for rid, s in stats.items():
        ranked.append({
            "route_id": rid,
            "route_name": s["route_name"],
            "disruption_count": s["disruption_count"],
            "total_disruption_days": round(s["total_days"], 1),
        })

    return ranked


def print_rankings(ranked, by="disruption_count", top_n=10):
    ranked_sorted = sorted(ranked, key=lambda x: x[by], reverse=True)
    print(f"\n{'Rank':<5}{'Route':<30}{'Count':<8}{'Total Days':<12}")
    print("-" * 55)
    for i, r in enumerate(ranked_sorted[:top_n], 1):
        print(f"{i:<5}{r['route_name']:<30}{r['disruption_count']:<8}{r['total_disruption_days']:<12}")


if __name__ == "__main__":
    ranked = rank_tram_lines("tram_disruptions.json")

    print("=== Ranked by number of disruptions ===")
    print_rankings(ranked, by="disruption_count")

    print("\n=== Ranked by total disruption-days ===")
    print_rankings(ranked, by="total_disruption_days")