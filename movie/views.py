import matplotlib.pyplot as plt
import matplotlib
import io
import urllib, base64
from django.shortcuts import render
from .models import Movie

def home(request):
    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm)
    else:
        movies = Movie.objects.all()
    return render(request, 'home.html', {'searchTerm': searchTerm, 'movies': movies})

def about(request):
    return render(request, 'about.html')

def signup(request):
    email = request.GET.get('email')
    return render(request, 'signup.html', {'email': email})

def statistics_view(request):
    matplotlib.use('Agg')
    all_movies = Movie.objects.all()

    # Gráfica 1: Por Año
    movie_counts_by_year = {}
    for movie in all_movies:
        year = movie.year if movie.year else "None"
        if year in movie_counts_by_year:
            movie_counts_by_year[year] += 1
        else:
            movie_counts_by_year[year] = 1

    bar_positions_year = range(len(movie_counts_by_year))
    plt.figure(figsize=(10, 5))
    plt.bar(bar_positions_year, movie_counts_by_year.values(), width=0.5, align='center')
    plt.title('Movies per year')
    plt.xlabel('Year')
    plt.ylabel('Number of movies')
    plt.xticks(bar_positions_year, movie_counts_by_year.keys(), rotation=90)
    plt.subplots_adjust(bottom=0.3)

    buffer_year = io.BytesIO()
    plt.savefig(buffer_year, format='png')
    buffer_year.seek(0)
    plt.close()
    graphic_year = base64.b64encode(buffer_year.getvalue()).decode('utf-8')
    buffer_year.close()

    # Gráfica 2: Por Género (Solo el primero)
    movie_counts_by_genre = {}
    for movie in all_movies:
        if movie.genre:
            genre = movie.genre.split(',')[0].strip()
            if genre in movie_counts_by_genre:
                movie_counts_by_genre[genre] += 1
            else:
                movie_counts_by_genre[genre] = 1

    bar_positions_genre = range(len(movie_counts_by_genre))
    plt.figure(figsize=(10, 5))
    plt.bar(bar_positions_genre, movie_counts_by_genre.values(), width=0.5, align='center', color='green')
    plt.title('Movies per genre (first only)')
    plt.xlabel('Genre')
    plt.ylabel('Number of movies')
    plt.xticks(bar_positions_genre, movie_counts_by_genre.keys(), rotation=90)
    plt.subplots_adjust(bottom=0.3)

    buffer_genre = io.BytesIO()
    plt.savefig(buffer_genre, format='png')
    buffer_genre.seek(0)
    plt.close()
    graphic_genre = base64.b64encode(buffer_genre.getvalue()).decode('utf-8')
    buffer_genre.close()

    return render(request, 'statistics.html', {'graphic_year': graphic_year, 'graphic_genre': graphic_genre})