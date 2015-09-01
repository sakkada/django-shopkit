from django.contrib import messages
from django.utils.translation import ugettext as _
from shopkit.cart import signals


def cart_item_added_listener(sender, cart=None, cart_line=None,
                             request=None, **kwargs):
    real_variant = cart_line.product.get_subtype_instance()
    if cart_line.get_quantity() > 0:
        messages.success(request, _(u'<strong>Great success!</strong> %s was'
                                    u' added to your cart.') % real_variant)

def start_listening():
    signals.cart_item_added.connect(cart_item_added_listener)
