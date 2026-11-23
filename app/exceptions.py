# app/exceptions.py
class CategoryRequired(Exception):
    """An expense must have a category."""

class CategoryNotFound(Exception):
    """Category doesn't exist or belongs to another user."""