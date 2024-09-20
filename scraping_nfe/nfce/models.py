# nfce/models.py
from django.db import models

class NotaFiscal(models.Model):
    numero_serie = models.CharField(max_length=50)
    razao_social = models.CharField(max_length=255)
    cnpj_emitente = models.CharField(max_length=50)
    inscricao_estadual = models.CharField(max_length=50)
    data_emissao = models.CharField(max_length=50)
    data_autorizacao = models.CharField(max_length=50)
    valor_total_produtos = models.DecimalField(max_digits=10, decimal_places=2)
    forma_pagamento = models.CharField(max_length=100)
    chave_acesso = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.numero_serie} - {self.razao_social}'


class Item(models.Model):
    nota_fiscal = models.ForeignKey(NotaFiscal, related_name='itens', on_delete=models.CASCADE)
    descricao = models.CharField(max_length=255)
    quantidade = models.DecimalField(max_digits=10, decimal_places=2)
    unidade = models.CharField(max_length=20)
    valor_unid = models.DecimalField(max_digits=10, decimal_places=2)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.descricao
