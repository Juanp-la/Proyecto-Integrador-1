from django.db import models

# Create your models here.

class News(models.Model):
    title = models.CharField(max_length=150)
    summary = models.CharField(max_length=300)
    image = models.ImageField(upload_to='news/images/')
    published_at = models.DateField()

    class Meta:
        ordering = ['-published_at']

    def __str__(self):
        return self.title
