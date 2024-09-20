# nfce/admin.py
from django.contrib import admin
from .models import NotaFiscal, Item

admin.site.register(NotaFiscal)
admin.site.register(Item)
