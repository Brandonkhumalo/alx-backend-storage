#!/usr/bin/env python3
"""
Web cache module: fetch pages, cache results with expiration,
and track URL access counts using Redis.
"""

import redis
import requests
from functools import wraps
from typing import Callable


redis_client = redis.Redis()


def count_calls(method: Callable) -> Callable:
    """
    Decorator to count how many times a URL is accessed.
    The URL is expected as the first argument of the function.
    """
    @wraps(method)
    def wrapper(url: str, *args, **kwargs):
        redis_client.incr(f"count:{url}")
        return method(url, *args, **kwargs)
    return wrapper


def cache_page(expiration: int = 10) -> Callable:
    """
    Decorator to cache the page content of a URL in Redis for a given expiration time.
    The URL is expected as the first argument of the function.
    """
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(url: str, *args, **kwargs):
            cached = redis_client.get(f"cached:{url}")
            if cached:
                return cached.decode('utf-8')
            result = method(url, *args, **kwargs)
            # Cache the result with expiration
            redis_client.setex(f"cached:{url}", expiration, result)
            return result
        return wrapper
    return decorator


@cache_page(expiration=10)
@count_calls
def get_page(url: str) -> str:
    """
    Fetch HTML content of the given URL using requests.

    Args:
        url: URL to fetch.

    Returns:
        The HTML content as a string.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text
