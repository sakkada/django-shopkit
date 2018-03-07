from django.contrib import admin
from . import models


admin.site.register(models.Order)
admin.site.register(models.DeliveryGroup)
admin.site.register(models.OrderLine)
