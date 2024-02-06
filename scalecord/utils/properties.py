"""
* Utils: Properties
"""
from typing import Callable


def auto_prop_cached(func: Callable) -> property:
    """Property decorator wrapper which automatically creates a setter and caches the value."""
    attr_type = func.__annotations__.get('return', str) if (
        hasattr(func, '__annotations__')) else str
    cache_name = f"_{func.__name__}"

    def getter(self) -> attr_type:
        """Wrapper for getting cached value. If value doesn't exist, initialize it."""
        try:
            return getattr(self, cache_name)
        except AttributeError:
            value = func(self)
            setattr(self, cache_name, value)
            return value

    def setter(self, value: attr_type) -> None:
        """Setter for invalidating the property cache and caching a new value."""
        setattr(self, cache_name, value)

    def deleter(self) -> None:
        """Deleter for invalidating the property cache."""
        if hasattr(self, cache_name):
            delattr(self, cache_name)

    # Return complete property
    return property(getter, setter, deleter, getattr(func, '__doc__', ''))
