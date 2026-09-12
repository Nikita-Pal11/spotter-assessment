
import time
import requests
from django.core.management.base import BaseCommand
from core.models import FuelStop

GEOAPIFY_KEY = "a0121d6c1eb34c91bc42b8698129a390"

class Command(BaseCommand):
    help = "Geocode fuel stations missing lat/lng"

    def handle(self, *args, **options):
        cache = {}
        stations = FuelStop.objects.filter(lat__isnull=True)
        total = stations.count()
        self.stdout.write(f"Found {total} stations missing coordinates.")

        updated_count = 0
        for station in stations:
            key = (station.city, station.state)
            if key not in cache:
                lat, lng = self.geocode_geoapify(station.city, station.state)
                if lat is None:
                    lat, lng = self.geocode_nominatim(station.city, station.state)
                    time.sleep(1)
                cache[key] = (lat, lng)

            lat, lng = cache[key]
            if lat is not None and lng is not None:
                station.lat = lat
                station.lng = lng
                station.save(update_fields=["lat", "lng"])
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"Finished geocoding! Updated {updated_count} stations."))

    def geocode_geoapify(self, city, state):
        url = "https://api.geoapify.com/v1/geocode/search"
        params = {
            "text": f"{city}, {state}, USA",
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

    def geocode_nominatim(self, city, state):
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": f"{city}, {state}, USA", "format": "json", "limit": 1}
        headers = {"User-Agent": "SpotterFuelRouteApp/1.0 (contact@spotter.com)"}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            if resp.status_code == 200:
                results = resp.json()
                if results:
                    return float(results[0]["lat"]), float(results[0]["lon"])
        except Exception:
            pass
        return None, None