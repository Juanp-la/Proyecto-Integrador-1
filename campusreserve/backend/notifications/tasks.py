from celery import shared_task


@shared_task
def check_weather_alerts():
    """Periodic task (Celery beat, see CELERY_BEAT_SCHEDULE): weather alerts for everyone."""
    from .services import refresh_all_weather_alerts

    return refresh_all_weather_alerts()
