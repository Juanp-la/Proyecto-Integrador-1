from django.shortcuts import render, get_object_or_404
from .models import News

def news(request):
    newss = News.objects.all().order_by('-date')
    return render(request, 'news.html', {'newss': newss, 'active_page': 'news'})

def news_detail(request, pk):
    article = get_object_or_404(News, pk=pk)
    return render(request, 'news_detail.html', {'article': article, 'active_page': 'news'})