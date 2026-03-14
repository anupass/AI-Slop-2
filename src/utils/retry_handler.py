import time
from functools import wraps


def retry(exceptions, tries=4, delay=1, backoff=2):
    """
    Retry decorator with exponential backoff.

    :param exceptions: Exception class or tuple of exception classes to catch.
    :param tries: Number of attempts before giving up.
    :param delay: Initial delay between attempts in seconds.
    :param backoff: Backoff multiplier (e.g., 2 means double the delay every time).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f'Caught exception: {e}. Retrying...')
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            raise Exception(f'Failed after {tries} attempts')
        return wrapper
    return decorator
