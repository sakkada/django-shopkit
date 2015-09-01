from django.forms.models import modelform_factory
from shopkit.order import forms
from shopkit.contrib.checkout.multistep import app
from shop.core.app import shop_app


class CheckoutApp(app.MultiStepCheckoutApp):
    Order = shop_app.order_app.Order

    BillingForm = modelform_factory(
        shop_app.order_app.Order,
        forms.BillingForm)

    ShippingForm = modelform_factory(
        shop_app.order_app.DeliveryGroup,
        form=forms.ShippingForm,
        fields=forms.ShippingForm._meta.fields)

    DeliveryMethodForm = modelform_factory(
        shop_app.order_app.DeliveryGroup,
        form=forms.DeliveryMethodForm,
        fields=forms.DeliveryMethodForm._meta.fields)
