from django.urls import path

from .views import MyReservationsView, ReservationCancelView, ReservationCreateView

urlpatterns = [
    path("", ReservationCreateView.as_view(), name="reservation-create"),
    path("mine/", MyReservationsView.as_view(), name="reservation-mine"),
    path("<int:pk>/cancel/", ReservationCancelView.as_view(), name="reservation-cancel"),
]
