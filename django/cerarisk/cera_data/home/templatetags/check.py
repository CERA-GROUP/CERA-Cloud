# handle layer_check tags in html (look if key is on URL and if so return true (=checked))
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def check(values, key):
    if key in values:
        return 'true'
    return 'false'
