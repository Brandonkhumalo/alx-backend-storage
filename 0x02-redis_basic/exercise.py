#!/usr/bin/env python3
"""
This module provides a Cache class that allows storing data
in Redis using randomly generated keys.
"""

import redis
import uuid
from typing import Union


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
