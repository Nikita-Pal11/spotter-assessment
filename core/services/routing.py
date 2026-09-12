import os
import requests

GEOAPIFY_KEY = os.getenv("GEOAPIFY_KEY", "a0121d6c1eb34c91bc42b8698129a390")
def routeApi(latS,lngS,latF,lngF):
    url = f"https://api.geoapify.com/v1/routing?waypoints={latS},{lngS}|{latF},{lngF}&mode=medium_truck&apiKey={GEOAPIFY_KEY}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    print(response.text)
    return response

def geoCoding(text):
    if not text:
        return None, None
    url = "https://api.geoapify.com/v1/geocode/search"
    params = {
        "text": text,
        "format": "json",
        "apiKey": GEOAPIFY_KEY
    }
    try:
        resp = requests.get(url, params=params, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            if results:
                return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception:
        pass
    return None, None

def parse_geoapify_route(data):
    if not data or "features" not in data or not data["features"]:
        return None

    feature = data["features"][0]
    properties = feature.get("properties", {})
    geometry = feature.get("geometry", {})

    distance_meters = properties.get("distance", 0)
    distance_miles = round(distance_meters * 0.000621371, 2)


    time_seconds = properties.get("time", 0)
    duration_mins = round(time_seconds / 60, 1)


    raw_coords = geometry.get("coordinates", [])
    coords = []
    geom_type = geometry.get("type")

    if geom_type == "LineString":
        coords = raw_coords
    elif geom_type == "MultiLineString":
        for segment in raw_coords:
            coords.extend(segment)

    return {
        "distance_miles": distance_miles,
        "duration_mins": duration_mins,
        "coordinates": coords,
        "geojson": geometry
    }