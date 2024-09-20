# nfce/forms.py
from django import forms
from .models import Item

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['descricao', 'quantidade', 'unidade', 'valor_unid', 'desconto', 'valor_total']
