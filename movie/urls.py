from django.urls import path
from movie import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('charts/year/', views.chart_movies_by_year, name='chart_by_year'),
    path('charts/genre/', views.chart_movies_by_genre, name='chart_by_genre'),
    path('charts/', views.charts_page, name='charts'),
]
