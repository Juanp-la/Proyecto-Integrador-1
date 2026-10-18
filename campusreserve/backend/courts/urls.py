from django.urls import path

from .views import CourtDetailView, CourtListView

urlpatterns = [
    path("", CourtListView.as_view(), name="court-list"),
    path("<int:pk>/", CourtDetailView.as_view(), name="court-detail"),
]
