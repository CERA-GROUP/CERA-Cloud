from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def hindcast(value):
    if value == '999':
        return 'hindcast'
    # 991: OWI hindcast (Irma 2017)
    elif value == '991':
        return 'hindcast OWI'
    return value
