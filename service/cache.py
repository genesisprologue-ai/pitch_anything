import os

import redis
import logging

redis_pool = None


def get_redis_pool():
    """
    Connect to Redis and return a Redis client object.
    """
    global redis_pool
    if redis_pool is None:
        if os.environ.get("REDIS_HOST"):
            host = os.environ.get("REDIS_HOST")
        else:
            host = "localhost"

        if os.environ.get("REDIS_PORT"):
            port = os.environ.get("REDIS_PORT")
        else:
            port = 6379

        redis_pool = redis.ConnectionPool(host=host, port=port, decode_responses=True)

    return redis_pool


def close_redis_pool():
    global redis_pool
    if redis_pool is not None:
        redis_pool.disconnect()
        redis_pool = None


def get_redis_client():
    """
    Connect to Redis using the connection pool and return a Redis client object.
    """
    pool = get_redis_pool()
    return redis.Redis(connection_pool=pool)


def del_cache(key):
    """
    Delete a cache value from Redis using the given key.
    """
    redis_client = get_redis_client()
    try:
        redis_client.delete(key)
    except Exception as e:
        print(f"Error deleting cache: {e}")


def set_cache(key, value, expiration_time=7200):
    """
    Set a cache value in Redis using the given key and value.
    """
    redis_client = get_redis_client()
    try:
        redis_client.set(key, value, ex=expiration_time)
    except Exception as e:
        print(f"Error setting cache: {e}")


def get_cache(key):
    """
    Get a cache value from Redis using the given key.
    """
    try:
        redis_client = get_redis_client()
        return redis_client.get(key)
    except Exception as e:
        print(f"Error getting cache: {e}")


def hset_cache(key, field, value, expiration_time=7200):
    """
    Set a cache value in Redis using the given key and value.
    """
    try:
        redis_client = get_redis_client()
        redis_client.hset(key, field, value)
        redis_client.expire(key, expiration_time)
    except Exception as e:
        print(f"Error setting cache: {e}")


def hgetall_cache(key):
    """
    Get a cache value from Redis using the given key.
    """
    try:
        redis_client = get_redis_client()
        return redis_client.hgetall(key)
    except Exception as e:
        print(f"Error getting cache: {e}")


def hget_cache(key, field):
    """
    Get a cache value from Redis using the given key.
    :param key:
    :return:
    """
    try:
        redis_client = get_redis_client()
        return redis_client.hget(key, field)
    except Exception as e:
        print(f"Error getting cache: {e}")


def acquire_lock(lock_id, lock_timeout=10):
    """
    Attempt to acquire a lock with the given lock_id for lock_timeout seconds.
    """
    try:
        redis_client = get_redis_client()
        # Use a unique value for the lock (e.g., a UUID or combination of hostname and PID)
        lock_value = f"lock:{lock_id}"
        # The `NX` argument only sets the key if it does not already exist (i.e., if the lock is not already held).
        # The `EX` argument sets the key to expire after lock_timeout seconds to avoid deadlocks if the lock is not released.
        return redis_client.set(lock_id, lock_value, ex=lock_timeout, nx=True)
    except Exception as e:
        print(f"Error acquiring lock: {e}")
        return False


def release_lock(lock_id):
    """
    Release a previously acquired lock with the given lock_id.
    """
    try:
        redis_client = get_redis_client()
        # Delete the lock key to release the lock
        redis_client.delete(lock_id)
    except Exception as e:
        print(f"Error releasing lock: {e}")


def delete_cache(key):
    """
    Delete a cache value from Redis using the given key.
    """
    try:
        redis_client = get_redis_client()
        redis_client.delete(key)
    except Exception as e:
        print(f"Error deleting cache: {e}")
