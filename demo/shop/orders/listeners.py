from django.conf import settings
from shopkit.order.signals import order_status_changed


def order_status_changed_listener(sender, instance, old_status=None, **kwargs):
    """
    checkout            (undergoing checkout)
    verification        (verification)
    payment-pending     (waiting for payment)
    payment-complete    (paid)
    payment-failed      (payment failed)
    delivery            (shipped)
    cancelled           (cancelled)
    refunded            (refunded)
    """
    context = {'order': instance, 'user': instance.user,}
    email_template = None

    # return if no changes
    if instance.status == old_status:
        return

    # order creation and sending to csv export
    if instance.status == 'verification' and old_status == 'checkout':
        email_template = 'verification'

        # clean other orders in checkout status
        if instance.user:
            instance._meta.model.objects.filter(user=instance.user,
                                                status='checkout').delete()

    if instance.status == 'payment-pending' and old_status == 'verification':
        email_template = 'payment-pending'

    if instance.status == 'payment-complete' \
        and old_status in ('payment-pending', 'payment-failed'):
        email_template = 'payment-complete'

    if instance.status in ('cancelled', 'refunded') \
        and not old_status in ('checkout', 'cancelled', 'refunded'):
        #instance.fake_stock_free()
        email_template = instance.status

    if instance.status == 'payment-failed' and old_status == 'payment-pending':
        email_template = 'payment-failed'

    if instance.status == 'delivery' and old_status == 'payment-complete':
        email_template = 'delivery'

    # send email message
    # topliga sending emails via internal Navision
    # if email_template:
    #     email_template = 'satchless/checkout/email/order_%s.txt' % email_template
    #     for to in ([instance.user.email], settings.SATCHLESS_EMAIL_ORDER_SPECTATORS):
    #         message = message_from_template(context, email_template, to)
    #         message.send()

def start_listening():
    order_status_changed.connect(order_status_changed_listener)
