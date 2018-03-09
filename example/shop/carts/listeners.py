from django.contrib.auth.signals import user_logged_in
from shop.core.app import shop_app


def user_logged_in_listener(sender, user, request, **kwargs):
    """
    When user logged in, try to get his anonymous cart and try to merge it
    with his own cart or create new one if anonymous cart is exists to move
    all lines from anonymous cart to just created.
    """
    cart_new = user.carts.first() or shop_app.cart_app.Cart(user=user)
    cart_old = shop_app.cart_app.get_cart_for_request(request,
                                                      previous_for_merge=True)
    if not cart_old:
        return

    # merge cart lines from old and new cart
    for line_old in cart_old.lines.all():
        line_new = cart_new.get_line(line_old.variant, data=line_old.data)
        quantity = max(line_old.quantity,
                       line_new.quantity if line_new is not None else 0)
        cart_new.add(
            line_old.variant, quantity=quantity, data=line_old.data,
            replace=True, check_quantity=False)

    # clear all old cart lines
    for line in cart_old.lines.all():
        line.delete()


def start_listening():
    user_logged_in.connect(user_logged_in_listener)
