from django.db import models

class News(models.Model):
    headline = models.CharField(max_length=200)
    body = models.TextField()
    date = models.DateField()

    class Meta:
        verbose_name_plural = "News"

    def __str__(self):
        return self.headline