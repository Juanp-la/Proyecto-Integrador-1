from django.contrib import admin
from.models import Movie


# Register your models here.

from django.contrib import admin
from .models import Movie

class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)
    ordering = ('order',)

admin.site.register(Movie, MovieAdmin)