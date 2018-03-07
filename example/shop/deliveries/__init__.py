from django.utils.translation import ugettext_lazy as _
from shopkit.delivery import DeliveryProvider, DeliveryType


class SimpleDeliveryProvider(DeliveryProvider):
    DELIVERY_TYPES = [
        {
            'name': _('Simple download delivery.'),
            'type': 'simple_download',
            'price': 0,
        },
        {
            'name': _('Simple post delivery.'),
            'type': 'simple_post',
            'price': 100,
        }
    ]

    def __unicode__(self):
        return _('Simple delivery')

    def enum_types(self, customer=None, delivery_group=None):
        for typ in self.DELIVERY_TYPES:
            yield DeliveryType(provider=self, typ=typ['type'], name=typ['name'])

    def save(self, delivery_group, typ, form):
        delivery_type = {i['type']: i for i in self.DELIVERY_TYPES}
        delivery_type = delivery_type[typ or delivery_group.delivery_type]

        delivery_group.delivery_type_name = delivery_type['name']
        delivery_group.delivery_type_description = delivery_type['name']
        delivery_group.delivery_price = delivery_type['price']
        delivery_group.save()
