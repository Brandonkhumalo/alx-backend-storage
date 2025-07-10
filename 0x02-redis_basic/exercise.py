#!/usr/bin/env python3
"""
This module provides a Cache class that allows storing and
retrieving data from Redis, including method call counting.
"""

import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts the number of times a method is called.

    Stores the count in Redis under the method's qualified name.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        """Wrapper function to increment count and call the method."""
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


class Cache:
    """
    Cache class that interfaces with a Redis data store.
    """

    def __init__(self):
        """
        Initialize the Cache instance and flush the Redis database.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store the given data in Redis using a random UUID key.

        Args:
            data: The data to store. Can be str, bytes, int, or float.

        Returns:
            The key under which the data is stored, as a string.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieve data from Redis and optionally convert it using a callable.

        Args:
            key: The key to retrieve from Redis.
            fn: Optional function to convert the result to the desired format.

        Returns:
            The retrieved data, possibly transformed by fn, or None.
        """
        data = self._redis.get(key)
        if data is None:
            return None
        return fn(data) if fn else data

    def get_str(self, key: str) -> Optional[str]:
        """
        Retrieve a UTF-8 string from Redis using the provided key.

        Args:
            key: The key to retrieve from Redis.

        Returns:
            The decoded string or None if key doesn't exist.
        """
        return self.get(key, fn=lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> Optional[int]:
        """
        Retrieve an integer from Redis using the provided key.

        Args:
            key: The key to retrieve from Redis.

        Returns:
            The integer value or None if key doesn't exist.
        """
        return self.get(key, fn=int)
