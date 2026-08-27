from django.db import models

class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    length = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. 2h 34m")
    genre = models.CharField(max_length=100, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='movies/images', blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0, help_text="Lower numbers show first")