from django.forms.models import modelform_factory
from django.conf.urls import url
from shopkit.order import forms
from shopkit.contrib.checkout.multistep import app
from shop.core.app import shop_app


class CheckoutApp(app.MultiStepCheckoutApp):
    Order = shop_app.order_app.Order

    BillingForm = modelform_factory(
        shop_app.order_app.Order, forms.BillingForm)

    PaymentMethodForm = modelform_factory(
        shop_app.order_app.Order, forms.PaymentMethodForm)

    DeliveryMethodForm = modelform_factory(
        shop_app.order_app.DeliveryGroup,
        form=forms.DeliveryMethodForm,
        fields=forms.DeliveryMethodForm._meta.fields)

    ShippingForm = modelform_factory(
        shop_app.order_app.DeliveryGroup,
        form=forms.ShippingForm, fields=forms.ShippingForm._meta.fields)

    # Views methods section
    # ---------------------
    def get_urls(self):
        return [
            url(r'^prepare-order/$',
                self.prepare_order, name='prepare-order'),
            url(r'^(?P<order_token>\w+)/$',
                self.checkout, name='checkout'),
            url(r'^(?P<order_token>\w+)/delivery-method/$',
                self.delivery_method, name='delivery-method'),
            url(r'^(?P<order_token>\w+)/delivery-details/$',
                self.delivery_details, name='delivery-details'),
            url(r'^(?P<order_token>\w+)/payment-method/$',
                self.payment_method, name='payment-method'),
            url(r'^(?P<order_token>\w+)/payment-details/$',
                self.payment_details, name='payment-details'),
            url(r'^(?P<order_token>\w+)/verification/$',
                self.verification, name='verification'),
            url(r'^(?P<order_token>\w+)/confirmation/$',
                self.confirmation, name='confirmation'),

            url(r'^(?P<order_token>\w+)/fixorder/$',
                self.fix_order_lines, name='fix-order-lines'),
            url(r'^(?P<order_token>\w+)/reactivate/$',
                self.reactivate_order, name='reactivate-order'),
        ]
