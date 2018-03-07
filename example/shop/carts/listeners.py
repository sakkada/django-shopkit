from shopkit.cart import signals


def cart_line_changed_listener(sender, cart=None, cart_line=None, **kwargs):
    # for order in cart.orders.filter(status=order.SC.CHECKOUT):
    #     order.groups.all().delete()
    pass


def start_listening():
    signals.cart_line_changed.connect(cart_line_changed_listener)
