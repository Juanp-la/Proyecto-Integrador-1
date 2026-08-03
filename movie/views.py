from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie

# Create your views here.

# Búsqueda de películas por título
def home(request):
    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm': searchTerm, 'movies': movies, 'name': 'Samuel Rendón Pabón'})

def about(request):
    return render(request, 'about.html')