from django.shortcuts import render
from django.http import HttpResponse
from.models import Movie
def home(request):
    #return HttpResponse ('<h1>Welcome to the home page</h1>')
    #return render (request,'home.html')
    #return render (request,'home.html',{'name':'Jp'})
    searchTerm = request.GET.get('searchMovie')
    if searchTerm:
        movies = Movie.objects.filter(title__icontains=searchTerm).order_by('order')
    else:
        movies = Movie.objects.all().order_by('order')
    return render(request, 'home.html', {'searchTerm': searchTerm, 'movies': movies})

def about(request):
    return render(request, "about.html")
        

