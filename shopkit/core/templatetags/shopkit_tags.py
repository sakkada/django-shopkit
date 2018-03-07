from django import template
from django.template.base import Node
from django.template.defaulttags import kwarg_re
from django.utils.encoding import smart_str


class BasePriceNode(Node):
    def __init__(self, item, kwargs, asvar):
        self.item = item
        self.kwargs = kwargs
        self.asvar = asvar

    def get_price(self, item, **kwargs):
        raise NotImplementedError

    def render(self, context):
        item = self.item.resolve(context)
        kwargs = {smart_str(k, 'ascii'): v.resolve(context)
                  for k, v in self.kwargs.items()}
        result = self.get_price(item, **kwargs)

        if self.asvar:
            context[self.asvar] = result
            result = ''
        return result


class ProductPriceRangeNode(BasePriceNode):
    def get_price(self, product, **kwargs):
        return product.get_price_range(**kwargs)


class VariantPriceNode(BasePriceNode):
    def get_price(self, product, **kwargs):
        return product.get_price(**kwargs)


class CartTotalPriceNode(BasePriceNode):
    def get_price(self, cart, **kwargs):
        return cart.get_total(**kwargs)


class CartItemPriceNode(BasePriceNode):
    def get_price(self, cartitem, **kwargs):
        return cartitem.get_total(**kwargs)


class CartItemUnitPriceNode(BasePriceNode):
    def get_price(self, cartitem, **kwargs):
        return cartitem.get_price_per_item(**kwargs)


def parse_price_tag(parser, token):
    bits = token.split_contents()
    tag_name = bits[0]
    if len(bits) < 3:
        raise template.TemplateSyntaxError(
            "'%s' syntax is {%% %s <instance> [currency='<iso-code>']"
            " as <variable-name> %%}" % (tag_name, tag_name)
        )

    item = parser.compile_filter(bits[1])
    kwargs = {}
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise template.TemplateSyntaxError(
                    "Malformed arguments to '%s' tag" % (tag_name,))
            name, value = match.groups()
            if not name:
                raise template.TemplateSyntaxError(
                    "'%s' takes only named arguments" % (tag_name,))
            kwargs[name] = parser.compile_filter(value)
    return item, kwargs, asvar


register = template.Library()


@register.tag
def product_price_range(parser, token):
    return ProductPriceRangeNode(*parse_price_tag(parser, token))


@register.tag
def variant_price(parser, token):
    return VariantPriceNode(*parse_price_tag(parser, token))


@register.tag
def cart_total_price(parser, token):
    return CartTotalPriceNode(*parse_price_tag(parser, token))


@register.tag
def cart_line_price(parser, token):
    return CartItemPriceNode(*parse_price_tag(parser, token))


@register.tag
def cart_line_unit_price(parser, token):
    return CartItemUnitPriceNode(*parse_price_tag(parser, token))
