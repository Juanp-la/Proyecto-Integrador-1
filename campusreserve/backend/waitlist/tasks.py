from celery import shared_task


@shared_task
def expire_waitlist_entry(entry_id):
    """
    Celery task scheduled by notify_next_in_queue() with a countdown equal
    to WAITLIST_CONFIRMATION_WINDOW_MINUTES. Implements HU8 (auto-advance
    the queue when a notified student doesn't respond in time).
    """
    from .services import expire_and_advance

    expire_and_advance(entry_id=entry_id)
