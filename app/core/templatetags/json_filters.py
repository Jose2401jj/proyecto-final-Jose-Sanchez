from django import template
import json
from django.utils.safestring import mark_safe
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(is_safe=True)
def json_encode(value):
    """
    Safely converts a Python object to JSON string for use in JavaScript.
    """
    return mark_safe(json.dumps(value, cls=DjangoJSONEncoder))

@register.filter(name='abs_value')
def abs_value(value):
    """
    Returns the absolute value of a number
    """
    try:
        return abs(float(value))
    except (ValueError, TypeError):
        return value 