from django.contrib import admin
from .models import Movie

class MovieAdmin(admin.ModelAdmin):
    list_display = ('title', 'genre', 'year', 'length', 'order')
    list_editable = ('genre', 'year', 'length', 'order')
    ordering = ('order',)

admin.site.register(Movie, MovieAdmin)