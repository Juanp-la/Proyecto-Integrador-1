from django.urls import path

from .views import AiStatusView, PopularCourtsView, QuietRecommendationsView, WeatherTodayView

urlpatterns = [
    path("status/", AiStatusView.as_view(), name="ai-status"),
    path("recommendations/popular/", PopularCourtsView.as_view(), name="ai-popular"),
    path("recommendations/quiet/", QuietRecommendationsView.as_view(), name="ai-quiet"),
    path("weather/today/", WeatherTodayView.as_view(), name="ai-weather-today"),
]
