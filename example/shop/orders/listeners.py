from shopkit.cart import signals


def cart_line_changed_listener(sender, cart=None, cart_line=None, **kwargs):
    # clean all in-checkout stage orders on cart changed
    for order in cart.orders.filter(status=cart.orders.model.SC.CHECKOUT):
        order.groups.all().delete()


def start_listening():
    signals.cart_line_changed.connect(cart_line_changed_listener)
