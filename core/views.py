from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.services.routing import geoCoding, routeApi, parse_geoapify_route
from core.services.fuel_optimizer import optimize_fuel_stops

# Create your views here.
class Route(APIView):
    def get(self, request):
        start = request.data.get("start") if request.data else None
        finish = request.data.get("finish") if request.data else None

        if not start or not finish:
            return Response(
                {"error": "Please provide both 'start' and 'finish' locations."},
                status=status.HTTP_400_BAD_REQUEST
            )

        latS, lngS = geoCoding(start)
        if latS is None or lngS is None:
            return Response(
                {"error": f"Could not geocode start location: '{start}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        latF, lngF = geoCoding(finish)
        if latF is None or lngF is None:
            return Response(
                {"error": f"Could not geocode finish location: '{finish}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        resp = routeApi(latS, lngS, latF, lngF)
        if resp.status_code != 200:
            return Response(
                {"error": "Failed to calculate route from Geoapify."},
                status=status.HTTP_502_BAD_GATEWAY
            )

        route_data = parse_geoapify_route(resp.json())
        if not route_data:
            return Response(
                {"error": "Could not parse route data."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        fuel_result = optimize_fuel_stops(route_data)

        response_payload = {
            "start": {
                "input": start,
                "latitude": latS,
                "longitude": lngS
            },
            "finish": {
                "input": finish,
                "latitude": latF,
                "longitude": lngF
            },
            "total_distance_miles": route_data["distance_miles"],
            "duration_mins": route_data["duration_mins"],
            "vehicle_specs": {
                "max_range_miles": 500,
                "fuel_efficiency_mpg": 10
            },
            "total_fuel_gallons": fuel_result["total_fuel_gallons"],
            "total_fuel_cost_usd": fuel_result["total_fuel_cost_usd"],
            "fuel_stops": fuel_result["fuel_stops"],
        }

        return Response(response_payload, status=status.HTTP_200_OK)
