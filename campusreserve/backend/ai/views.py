from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .llm import ai_enabled
from .services import daily_weather_report, popular_courts, quiet_recommendations


class PopularCourtsView(APIView):
    """GET /api/ai/recommendations/popular/ — canchas más usadas, explicadas por la IA."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(popular_courts())


class QuietRecommendationsView(APIView):
    """GET /api/ai/recommendations/quiet/ — canchas y horarios poco usados (y libres)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(quiet_recommendations())


class WeatherTodayView(APIView):
    """GET /api/ai/weather/today/ — reporte del clima del día generado con IA."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(daily_weather_report())


class AiStatusView(APIView):
    """GET /api/ai/status/ — tells the frontend whether an AI key is configured."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response({"ai_enabled": ai_enabled()})
