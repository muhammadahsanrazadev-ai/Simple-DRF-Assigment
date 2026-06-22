"""
Utility: safe_enqueue()

Wraps Celery's .delay() to safely fire background tasks.
If the broker (Redis) is down, the error is logged and the
main API request is NOT affected — only the email will be missed.
"""

import logging

logger = logging.getLogger(__name__)


def safe_enqueue(task, *args, **kwargs):
    """Enqueue a Celery task. Logs and swallows broker errors silently."""
    try:
        task.delay(*args, **kwargs)
    except Exception:
        logger.exception(
            "Failed to enqueue task %s — is Redis running? "
            "The API request succeeded; only the email was skipped.",
            getattr(task, "name", task),
        )
