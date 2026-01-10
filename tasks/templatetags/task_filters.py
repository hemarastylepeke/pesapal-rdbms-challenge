"""
Custom template filter to access dictionary keys.
"""
from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Template filter to look up dictionary values by key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
