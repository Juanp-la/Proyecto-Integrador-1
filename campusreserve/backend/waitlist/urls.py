from django.urls import path

from .views import ConfirmWaitlistOfferView, JoinWaitlistView, MyWaitlistView

urlpatterns = [
    path("", JoinWaitlistView.as_view(), name="waitlist-join"),
    path("mine/", MyWaitlistView.as_view(), name="waitlist-mine"),
    path("<int:pk>/confirm/", ConfirmWaitlistOfferView.as_view(), name="waitlist-confirm"),
]
