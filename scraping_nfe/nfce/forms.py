# nfce/forms.py
from django import forms
from .models import Item, NotaFiscal

class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['descricao', 'quantidade', 'unidade', 'valor_unid', 'desconto', 'valor_total']

class NotaFiscalForm(forms.ModelForm):
    class Meta:
        model = NotaFiscal
        fields = ['numero_serie', 'razao_social', 'data_emissao', 'categoria', 'subcategoria_transporte', 'valor_total_produtos']