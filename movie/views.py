from django.shortcuts import render
from django.http import HttpResponse

import matplotlib
import matplotlib.pyplot as plt
import io
import base64

from .models import Movie

# Create your views here.

def home(request):
    # NOTA: reemplaza 'Daniel Apellido' por tu nombre completo real
    myName = 'Daniel Apellido'

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


def signup(request):
    email = request.GET.get('email')
    return render(request, 'signup.html', {'email': email})


def statistics_view(request):
    matplotlib.use('Agg')

    all_movies = Movie.objects.all()

    # --- Gráfica: películas por año ---
    movie_counts_by_year = {}
    for movie in all_movies:
        year = movie.year if movie.year else "None"
        movie_counts_by_year[year] = movie_counts_by_year.get(year, 0) + 1

    # Ordenar por año (dejando "None" al final)
    sorted_years = sorted(
        movie_counts_by_year.keys(),
        key=lambda y: (y == "None", y)
    )
    year_counts = [movie_counts_by_year[y] for y in sorted_years]

    plt.figure()
    bar_positions = range(len(sorted_years))
    plt.bar(bar_positions, year_counts, width=0.5, align='center')
    plt.title('Movies per year')
    plt.xlabel('Year')
    plt.ylabel('Number of movies')
    plt.xticks(bar_positions, sorted_years, rotation=90)
    plt.subplots_adjust(bottom=0.3)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    graphic_year = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    # --- Gráfica: películas por género (solo el primer género listado) ---
    movie_counts_by_genre = {}
    for movie in all_movies:
        if movie.genre:
            first_genre = movie.genre.split(',')[0].strip()
        else:
            first_genre = "None"
        movie_counts_by_genre[first_genre] = movie_counts_by_genre.get(first_genre, 0) + 1

    genres = list(movie_counts_by_genre.keys())
    genre_counts = list(movie_counts_by_genre.values())

    plt.figure()
    bar_positions = range(len(genres))
    plt.bar(bar_positions, genre_counts, width=0.5, align='center', color='green')
    plt.title('Movies per genre (first only)')
    plt.xlabel('Genre')
    plt.ylabel('Number of movies')
    plt.xticks(bar_positions, genres, rotation=90)
    plt.subplots_adjust(bottom=0.3)

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plt.close()
    graphic_genre = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()

    return render(request, 'statistics.html', {
        'graphic_year': graphic_year,
        'graphic_genre': graphic_genre,
    })
