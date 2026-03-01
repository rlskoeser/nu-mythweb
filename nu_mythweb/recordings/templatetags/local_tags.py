from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """Retrieve a value from a dictionary using a variable key."""
    if key.isnumeric():
        return dictionary.get(int(key))
    return dictionary.get(str(key))
