from math import radians, sin, cos, sqrt, atan2
from core.models import FuelStop

VEHICLE_RANGE_MILES = 500.0
MPG = 10.0
MAX_STATION_OFF_ROUTE_MILES = 15.0

def haversine(lat1, lng1, lat2, lng2):
    R = 3958.8
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * R * atan2(sqrt(a), sqrt(1 - a))

def compute_cumulative_distances(coords):
    cumulative = [0.0]
    for i in range(1, len(coords)):
        lng1, lat1 = coords[i - 1]
        lng2, lat2 = coords[i]
        d = haversine(lat1, lng1, lat2, lng2)
        cumulative.append(cumulative[-1] + d)
    return cumulative

def optimize_fuel_stops(route_info):
    coords = route_info.get("coordinates", [])
    total_distance = route_info.get("distance_miles", 0.0)

    if not coords or total_distance <= 0:
        return {
            "fuel_stops": [],
            "total_fuel_gallons": 0.0,
            "total_fuel_cost_usd": 0.0
        }

    cumulative = compute_cumulative_distances(coords)

    lats = [c[1] for c in coords]
    lngs = [c[0] for c in coords]
    min_lat, max_lat = min(lats) - 0.4, max(lats) + 0.4
    min_lng, max_lng = min(lngs) - 0.4, max(lngs) + 0.4

    stops = FuelStop.objects.filter(
        lat__gte=min_lat, lat__lte=max_lat,
        lng__gte=min_lng, lng__lte=max_lng
    )

    route_stops = []
    step = max(1, len(coords) // 500)
    for stop in stops:
        if stop.lat is None or stop.lng is None:
            continue

        min_dist_to_route = float("inf")
        best_mile_marker = 0.0

        for i in range(0, len(coords), step):
            lng, lat = coords[i]
            d = haversine(stop.lat, stop.lng, lat, lng)
            if d < min_dist_to_route:
                min_dist_to_route = d
                best_mile_marker = cumulative[i]

        if min_dist_to_route <= MAX_STATION_OFF_ROUTE_MILES:
            route_stops.append({
                "id": stop.truckstop_id,
                "name": stop.name,
                "address": stop.address,
                "city": stop.city,
                "state": stop.state,
                "price": stop.price,
                "lat": stop.lat,
                "lng": stop.lng,
                "mile_marker": round(best_mile_marker, 2),
                "dist_off_route": round(min_dist_to_route, 2)
            })


    route_stops.sort(key=lambda x: x["mile_marker"])


    total_gallons_needed = total_distance / MPG
    chosen_stops = []
    curr_pos = 0.0
    curr_fuel_range = VEHICLE_RANGE_MILES

    while curr_pos + curr_fuel_range < total_distance:
        max_reachable_mile = curr_pos + curr_fuel_range


        reachable = [s for s in route_stops if curr_pos < s["mile_marker"] <= max_reachable_mile]

        if not reachable:
            future_stops = [s for s in route_stops if s["mile_marker"] > curr_pos]
            if future_stops:
                best_stop = future_stops[0]
            else:
                break
        else:
            best_stop = min(reachable, key=lambda s: s["price"])

        distance_traveled = best_stop["mile_marker"] - curr_pos
        gallons_refueled = distance_traveled / MPG
        cost = gallons_refueled * best_stop["price"]

        chosen_stops.append({
            "name": best_stop["name"],
            "city": best_stop["city"],
            "state": best_stop["state"],
            "mile_marker": best_stop["mile_marker"],
            "price_per_gallon": best_stop["price"],
            "gallons_refueled": round(gallons_refueled, 2),
            "cost_usd": round(cost, 2),
            "latitude": best_stop["lat"],
            "longitude": best_stop["lng"]
        })

        curr_pos = best_stop["mile_marker"]
        curr_fuel_range = VEHICLE_RANGE_MILES

    total_cost = sum(s["cost_usd"] for s in chosen_stops)

    return {
        "fuel_stops": chosen_stops,
        "total_fuel_gallons": round(total_gallons_needed, 2),
        "total_fuel_cost_usd": round(total_cost, 2)
    }
