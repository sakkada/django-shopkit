from django import template
from django.db import models

register = template.Library()

class PromoteNode(template.Node):
    def __init__(self, arg, var_name):
        self.arg = template.Variable(arg)
        self.var_name = var_name

    def render(self, context):
        obj = self.arg.resolve(context)
        if hasattr(obj, 'get_subtype_instance'):
            context[self.var_name] = obj.get_subtype_instance()
        else:
            context[self.var_name] = [o.get_subtype_instance() for o in obj]
        return ''

@register.tag(name='promote')
def do_promote(parser, token):
    args = token.split_contents() # ['promote', 'var', 'as', 'newvar',]
    assert all((len(args) == 4, args[0] == 'promote', args[-2] == 'as',))

    arg, var_name = args[1], args[-1]
    return PromoteNode(arg, var_name)
