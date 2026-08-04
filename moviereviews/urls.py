"""
URL configuration for moviereviews project.
"""
from django.contrib import admin
from django.urls import path
from movie import views as movieViews

from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', movieViews.home),
    path('about/', movieViews.about),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
