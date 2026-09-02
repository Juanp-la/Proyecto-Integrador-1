import io
from collections import Counter

import matplotlib
matplotlib.use('Agg')  # backend sin interfaz gráfica, necesario para correr dentro de Django
import matplotlib.pyplot as plt

from django.shortcuts import render
from django.http import HttpResponse

from .models import Movie

# Create your views here.

def home(request):
    myName = 'Juan Diego Albanez'

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


def charts_page(request):
    return render(request, 'charts.html')


def chart_movies_by_year(request):
    movies = Movie.objects.exclude(year__isnull=True)
    counts = Counter(m.year for m in movies)
    years = sorted(counts.keys())
    values = [counts[y] for y in years]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([str(y) for y in years], values, color='#0d6efd')
    ax.set_title('Películas por año')
    ax.set_xlabel('Año')
    ax.set_ylabel('Cantidad de películas')
    plt.xticks(rotation=45)
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def chart_movies_by_genre(request):
    movies = Movie.objects.exclude(genre='')
    genre_counter = Counter()
    for m in movies:
        for g in m.genre.split(','):
            g = g.strip()
            if g:
                genre_counter[g] += 1

    genres = [g for g, _ in genre_counter.most_common()]
    values = [genre_counter[g] for g in genres]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(genres, values, color='#dc3545')
    ax.set_title('Películas por género')
    ax.set_xlabel('Género')
    ax.set_ylabel('Cantidad de películas')
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()

    buffer = io.BytesIO()
    fig.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    return HttpResponse(buffer.getvalue(), content_type='image/png')
