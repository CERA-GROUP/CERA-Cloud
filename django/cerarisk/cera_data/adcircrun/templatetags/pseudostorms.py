from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def pseudostorms(value):
    if value == '92222':
        return 'hypothetical'
    if value.startswith('9'):
        return 'pseudo ' + value[1:5]
    return value
