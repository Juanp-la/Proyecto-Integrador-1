from django.shortcuts import render
from .models import Movie

def home(request):
    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    
    return render(request, 'home.html', {'name': 'Tomás Vera', 'searchTerm': searchTerm, 'movies': movies})

def about(request):
    return render(request, 'about.html')
