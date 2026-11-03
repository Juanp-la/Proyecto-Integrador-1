from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .spa import frontend

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/accounts/", include("accounts.urls")),
    path("api/courts/", include("courts.urls")),
    path("api/reservations/", include("reservations.urls")),
    path("api/waitlist/", include("waitlist.urls")),
    path("api/ai/", include("ai.urls")),
    path("api/notifications/", include("notifications.urls")),
    # Everything that isn't the API or the admin -> React app (must be last).
    re_path(r"^(?!api(?:/|$)|admin(?:/|$)|static/)(?P<path>.*)$", frontend, name="frontend"),
]
