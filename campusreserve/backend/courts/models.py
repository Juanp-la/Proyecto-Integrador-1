from django.db import models


class Court(models.Model):
    """
    A bookable court. When a physical space is shared between two sports
    (e.g. basketball/volleyball), it is modeled as ONE Court row covering
    both — this is what makes the shared-court constraint (HU5) automatic:
    any confirmed reservation on this court blocks it for every sport,
    because there is only one row to check for overlaps.
    """

    SPORT_CHOICES = [
        ("soccer", "Soccer"),
        ("basketball_volleyball", "Basketball / Volleyball"),
        ("basketball", "Basketball"),
        ("volleyball", "Volleyball"),
    ]

    name = models.CharField(max_length=120)
    sport = models.CharField(max_length=30, choices=SPORT_CHOICES)
    location = models.CharField(max_length=120)
    capacity = models.CharField(max_length=60, blank=True)
    surface = models.CharField(max_length=60, blank=True)
    image_ref = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
