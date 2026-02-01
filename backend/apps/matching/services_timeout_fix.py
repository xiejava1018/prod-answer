import threading
from contextlib import contextmanager

class TimeoutError(Exception):
    """Timeout exception for context manager."""
    pass

@contextmanager
def time_limit(seconds):
    """
    Context manager to limit execution time (thread-safe).
    Uses threading.Timer instead of signal for compatibility with Django.

    Args:
        seconds: Timeout in seconds

    Yields:
        None (context)

    Raises:
        TimeoutError: If timeout is reached
    """
    timer = None
    timed_out = [False]

    def timeout_handler():
        timed_out[0] = True
        raise TimeoutError(f"Timeout after {seconds} seconds")

    timer = threading.Timer(seconds, timeout_handler)
    timer.start()

    try:
        yield
    except TimeoutError:
        raise
    finally:
        timer.cancel()
        # Wait a bit for timer thread to finish
        if timer.is_alive():
            timer.join(timeout=0.1)
