#!/usr/bin/env python3
"""
This module provides a Cache class that allows storing and
retrieving data from Redis, tracking call counts and history.
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
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator that stores the history of inputs and outputs for a method.

    Inputs are stored in <method_name>:inputs and outputs in <method_name>:outputs.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"

        # Store input arguments as string
        self._redis.rpush(input_key, str(args))

        # Execute original method
        result = method(self, *args, **kwargs)

        # Store output
        self._redis.rpush(output_key, str(result))

        return result
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

    @call_history
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

def replay(method: Callable) -> None:
    """
    Display the history of calls of a particular function.

    It prints how many times the function was called,
    then lists all inputs and outputs from Redis.
    """
    redis_client = method.__self__._redis  # access redis instance from bound method
    method_name = method.__qualname__
    calls = redis_client.get(method_name)
    try:
        calls_int = int(calls) if calls else 0
    except Exception:
        calls_int = 0

    print(f"{method_name} was called {calls_int} times:")

    inputs = redis_client.lrange(f"{method_name}:inputs", 0, -1)
    outputs = redis_client.lrange(f"{method_name}:outputs", 0, -1)

    for inp, out in zip(inputs, outputs):
        print(f"{method_name}(*{inp.decode()}) -> {out.decode()}")
