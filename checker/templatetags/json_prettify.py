import json
from django import template
register = template.Library()

@register.filter
def json_prettify(value):
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return value 