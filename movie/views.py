from django.shortcuts import render
from django.http import HttpResponse 

def home(request):
    #return HttpResponse ('<h1>Welcome to the home page</h1>')
     #return render (request,'home.html')
     return render (request,'home.html',{'name':'Jp'})

# Create your views here.
def about(request):
     return HttpResponse('<h1>Class P1</h1>')
    