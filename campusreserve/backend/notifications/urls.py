from django.urls import path

from .views import CancelReservationFromNotificationView, DismissNotificationView, MyNotificationsView

urlpatterns = [
    path("", MyNotificationsView.as_view(), name="notifications-mine"),
    path("<int:pk>/dismiss/", DismissNotificationView.as_view(), name="notification-dismiss"),
    path(
        "<int:pk>/cancel-reservation/",
        CancelReservationFromNotificationView.as_view(),
        name="notification-cancel-reservation",
    ),
]
