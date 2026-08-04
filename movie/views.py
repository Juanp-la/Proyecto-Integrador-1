from django.shortcuts import render
from django.http import HttpResponse

from .models import Movie

# Create your views here.

def home(request):
    # NOTA: reemplaza 'Daniel Apellido' por tu nombre completo real
    myName = 'Daniel Muñeton'

    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()

    return render(request, 'home.html', {
        'name': myName,
        'searchTerm': searchTerm,
        'movies': movies,
    })


def about(request):
    return render(request, 'about.html')
