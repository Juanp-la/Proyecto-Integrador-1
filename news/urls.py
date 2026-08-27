from django.urls import path
from . import views

urlpatterns = [
    path('', views.news, name='news'),
    path('<int:pk>/', views.news_detail, name='news_detail'),
]