from django.shortcuts import render
from .models import News

# Create your views here.

def news_list(request):
    news = News.objects.all()
    return render(request, 'news/news.html', {'news': news})
