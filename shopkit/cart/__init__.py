from satchless import cart
from shopkit.cart import signals


class CartLine(cart.CartLine):
    # note: product in CartLine is Variant instance
    def __init__(self, product, quantity, data=None):
        super(CartLine, self).__init__(product, quantity, data=data)

    def get_price_per_item(self, **kwargs):
        return super(CartLine, self).get_price_per_item(**kwargs)

    def get_quantity(self, **kwargs):
        return self.quantity


class Cart(cart.Cart):
    """
    Cart object. Contains cart items. Serialized instance of cart
    is saved into django session.
    """
    loading_cart_from_storage = False
    session_key = 'cart'

    def __init__(self, request=None, shop_app=None):
        super(Cart, self).__init__()
        self.request = request
        self.shop_app = shop_app
        self.load_cart_from_storage()

    def __str__(self):
        return 'Your cart (%(cart_count)s)' % {'cart_count': self.count(),}

    def create_line(self, product, quantity, data):
        return CartLine(product, quantity, data=data)

    def save_cart_to_storage(self):
        data = [{'variant': item.product.pk,
                 'quantity': str(item.quantity), # to avoid not JSON serializable error
                 'data': item.data,} for item in self]
        self.request.session[self.session_key] = data

    def load_cart_from_storage(self):
        data = self.request.session.get(self.session_key, None)
        if not data:
            return
        self.loading_cart_from_storage = True

        variants = [i['variant'] for i in data]
        variants = self.shop_app.product_app.Variant.objects.filter(id__in=variants)
        variants = dict((i.id, i) for i in variants)
        for i in data:
            variant = variants[i['variant']].get_subtype_instance()
            self.add(variant, quantity=i['quantity'], check_quantity=False)

        self.loading_cart_from_storage = False

    def add(self, product, quantity=1, data=None, replace=False,
            check_quantity=True):
        quantity = product.product.quantize_quantity(quantity)
        super(Cart, self).add(product, quantity, data, replace, check_quantity)
        if not self.loading_cart_from_storage:
            self.save_cart_to_storage()
            signals.cart_content_changed.send(sender=type(self), cart=self)

    def clear(self):
        super(Cart, self).clear()
        if not self.loading_cart_from_storage:
            self.save_cart_to_storage()
            signals.cart_content_changed.send(sender=type(self), cart=self)
