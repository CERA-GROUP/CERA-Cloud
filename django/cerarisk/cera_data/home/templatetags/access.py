# handle timestep in layer_check tags in html (header) - (look if (timestep)key 
# is on URL and if so return value, if not on URL return '[key]')

from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def access(urldata, key):
    return urldata.get(key, '[%s]' % key)
