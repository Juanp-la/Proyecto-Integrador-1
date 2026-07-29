from django.db import models

# Create your models here.
class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    details = models.CharField(max_length=200, blank=True, null=True, help_text="e.g. Family/Fantasy · 2001 · 2h 32m")
    image = models.ImageField(upload_to='movies/images', blank=True, null=True)
    url = models.URLField(blank=True, null=True)