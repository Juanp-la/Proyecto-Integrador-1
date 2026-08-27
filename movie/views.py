from django.shortcuts import render
from django.http import HttpResponse
from .models import Movie
from django.db.models import Count
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
def home(request):
    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm).order_by('order')
    else:
        movies = Movie.objects.all().order_by('order')
    all_titles = Movie.objects.values_list('title', flat=True)
    return render(request, 'home.html', {
        'searchTerm': searchTerm,
        'movies': movies,
        'active_page': 'home',
        'all_titles': all_titles,
    })

def about(request):
    return render(request, 'about.html', {'active_page': 'about'})

def _generate_bar_chart(labels, values, title, xlabel, ylabel):
    width = max(8, len(labels) * 0.6)
    plt.figure(figsize=(width, 5.5))
    bar_positions = range(len(labels))
    plt.bar(bar_positions, values, width=0.5, align='center', color='#E7B10A')
    plt.title(title, color='white')
    plt.xlabel(xlabel, color='white')
    plt.ylabel(ylabel, color='white')
    plt.xticks(bar_positions, labels, rotation=90)
    fig = plt.gcf()
    fig.patch.set_facecolor('#15120F')
    ax = plt.gca()
    ax.set_facecolor('#15120F')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('#9C9284')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0.4, facecolor=fig.get_facecolor(), dpi=180)
    buffer.seek(0)
    plt.close()

    graphic = base64.b64encode(buffer.getvalue()).decode('utf-8')
    buffer.close()
    return graphic


def statistics_view(request):
    year_data = (
        Movie.objects.exclude(year__isnull=True)
        .values('year')
        .annotate(count=Count('id'))
        .order_by('year')
    )
    year_labels = [str(item['year']) for item in year_data]
    year_counts = [item['count'] for item in year_data]
    year_graphic = _generate_bar_chart(year_labels, year_counts, 'Movies per Year', 'Year', 'Number of movies')

    genre_data = (
        Movie.objects.exclude(genre__isnull=True).exclude(genre='')
        .values('genre')
        .annotate(count=Count('id'))
        .order_by('-count')
    )
    genre_labels = [item['genre'] for item in genre_data]
    genre_counts = [item['count'] for item in genre_data]
    genre_graphic = _generate_bar_chart(genre_labels, genre_counts, 'Movies per Genre', 'Genre', 'Number of movies')

    return render(request, 'statistics.html', {
        'year_graphic': year_graphic,
        'genre_graphic': genre_graphic,
        'active_page': 'statistics',
    })

def signup(request):
    email = request.GET.get('email')
    return render(request, 'signup.html', {'email': email, 'active_page': 'signup'})