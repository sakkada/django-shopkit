from django.contrib import admin
from . import models


class TaxGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'id', 'rate', 'rate_name',)
