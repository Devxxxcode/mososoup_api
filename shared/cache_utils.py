"""
Cache utility functions for Redis caching
"""
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import logging

logger = logging.getLogger('cache_operations')

# Cache key prefixes
CACHE_PREFIXES = {
    'PRODUCTS': 'products',
    'PACKAGES': 'packages', 
    'NOTIFICATIONS': 'notifications',
    'USER_NOTIFICATIONS': 'user_notifications',
    'ADMIN_NOTIFICATIONS': 'admin_notifications',
    'SETTINGS': 'settings',
    'EVENTS': 'events',
}

def get_cache_ttl(cache_type):
    """Get TTL for specific cache type"""
    return getattr(settings, 'CACHE_TTL', {}).get(cache_type, settings.CACHE_TTL.get('DEFAULT', 300))

def build_cache_key(prefix, *args):
    """Build cache key with prefix and arguments"""
    key_parts = [CACHE_PREFIXES.get(prefix, prefix)]
    key_parts.extend([str(arg) for arg in args])
    return ':'.join(key_parts)

def cache_result(cache_type, key_args=None, ttl=None):
    """
    Decorator to cache function results
    
    Args:
        cache_type: Type of cache (PRODUCTS, PACKAGES, etc.)
        key_args: Function arguments to use in cache key (by name or index)
                 Can also use nested access like 'user.id' (assumes args[1] is request)
        ttl: Time to live in seconds (overrides default)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_args:
                if isinstance(key_args, list):
                    # Use specific arguments
                    cache_key_parts = []
                    for arg in key_args:
                        if isinstance(arg, int):
                            # Index-based argument
                            if arg < len(args):
                                cache_key_parts.append(str(args[arg]))
                        elif isinstance(arg, str):
                            # Handle nested attribute access like 'user.id'
                            if '.' in arg:
                                # Split by dots and navigate the object
                                parts = arg.split('.')
                                try:
                                    # Start with args[1] (request is usually second argument)
                                    obj = args[1] if len(args) > 1 else None
                                    for part in parts:
                                        if obj is not None:
                                            obj = getattr(obj, part, None)
                                        else:
                                            break
                                    if obj is not None:
                                        cache_key_parts.append(str(obj))
                                except (AttributeError, IndexError):
                                    # If nested access fails, skip this part
                                    pass
                            # Regular keyword argument
                            elif arg in kwargs:
                                cache_key_parts.append(str(kwargs[arg]))
                    cache_key = build_cache_key(cache_type, *cache_key_parts)
                else:
                    # Single argument - handle nested access
                    if isinstance(key_args, str) and '.' in key_args:
                        # Handle nested attribute access
                        parts = key_args.split('.')
                        try:
                            obj = args[1] if len(args) > 1 else None
                            for part in parts:
                                if obj is not None:
                                    obj = getattr(obj, part, None)
                                else:
                                    break
                            if obj is not None:
                                cache_key = build_cache_key(cache_type, str(obj))
                            else:
                                cache_key = build_cache_key(cache_type, str(key_args))
                        except (AttributeError, IndexError):
                            cache_key = build_cache_key(cache_type, str(key_args))
                    else:
                        # Single argument
                        cache_key = build_cache_key(cache_type, str(key_args))
            else:
                # Use function name and all arguments
                all_args = [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
                cache_key = build_cache_key(cache_type, func.__name__, *all_args)
            
            # Try to get from cache
            try:
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    logger.info(f"Cache HIT: {cache_key}")
                    
                    # Handle cached DRF Response objects
                    if isinstance(cached_result, dict) and 'data' in cached_result and 'status_code' in cached_result:
                        # Reconstruct DRF Response object
                        from rest_framework.response import Response
                        response = Response(
                            data=cached_result['data'],
                            status=cached_result['status_code']
                        )
                        # Set headers if they exist
                        if 'headers' in cached_result and cached_result['headers']:
                            for key, value in cached_result['headers'].items():
                                response[key] = value
                        return response
                    else:
                        # Regular cached result
                        return cached_result
            except Exception as e:
                logger.warning(f"Cache GET error: {e}")
            
            # Execute function and cache result
            try:
                result = func(*args, **kwargs)
                cache_ttl = ttl or get_cache_ttl(cache_type)
                
                # Handle Django REST Framework Response objects
                if hasattr(result, 'data') and hasattr(result, 'status_code'):
                    # It's a DRF Response object, cache the data and status
                    cache_data = {
                        'data': result.data,
                        'status_code': result.status_code,
                        'headers': dict(result.items()) if hasattr(result, 'items') else {}
                    }
                    cache.set(cache_key, cache_data, cache_ttl)
                    logger.info(f"Cache SET: {cache_key} (TTL: {cache_ttl}s) - DRF Response")
                else:
                    # Regular result, cache as-is
                    cache.set(cache_key, result, cache_ttl)
                    logger.info(f"Cache SET: {cache_key} (TTL: {cache_ttl}s)")
                
                return result
            except Exception as e:
                logger.error(f"Function execution error: {e}")
                raise
                
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate all cache keys matching pattern"""
    try:
        # Get all keys matching pattern
        keys = cache.keys(pattern)
        if keys:
            cache.delete_many(keys)
            logger.info(f"Invalidated {len(keys)} cache keys matching: {pattern}")
        else:
            logger.debug(f"No cache keys found matching: {pattern}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

def invalidate_product_cache():
    """Invalidate all product-related cache"""
    invalidate_cache_pattern("products:*")

def invalidate_package_cache():
    """Invalidate all package-related cache"""
    invalidate_cache_pattern("packages:*")

def invalidate_user_notifications_cache(user_id=None):
    """Invalidate user notification cache"""
    if user_id:
        invalidate_cache_pattern(f"notifications:{user_id}*")
    else:
        invalidate_cache_pattern("notifications:*")

def invalidate_admin_notifications_cache():
    """Invalidate admin notification cache"""
    invalidate_cache_pattern("notifications:admin*")

def invalidate_all_notifications_cache():
    """Invalidate all notification cache"""
    invalidate_user_notifications_cache()
    invalidate_admin_notifications_cache()

def invalidate_settings_cache():
    """Invalidate all settings-related cache"""
    invalidate_cache_pattern("settings:*")

def invalidate_events_cache():
    """Invalidate all events-related cache"""
    invalidate_cache_pattern("events:*")

# Cache key builders
def get_products_cache_key():
    """Get cache key for all products"""
    return build_cache_key('PRODUCTS', 'all')

def get_product_cache_key(product_id):
    """Get cache key for specific product"""
    return build_cache_key('PRODUCTS', product_id)

def get_packages_cache_key():
    """Get cache key for all packages"""
    return build_cache_key('PACKAGES', 'all')

def get_user_notifications_cache_key(user_id):
    """Get cache key for user notifications"""
    return build_cache_key('USER_NOTIFICATIONS', user_id)

def get_admin_notifications_cache_key():
    """Get cache key for admin notifications"""
    return build_cache_key('ADMIN_NOTIFICATIONS', 'all')

def get_settings_cache_key():
    """Get cache key for global settings"""
    return build_cache_key('SETTINGS', 'global')

def get_events_cache_key():
    """Get cache key for all active events"""
    return build_cache_key('EVENTS', 'active')

def get_event_cache_key(event_id):
    """Get cache key for specific event"""
    return build_cache_key('EVENTS', event_id)
