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
    nota_fiscal = models.ForeignKey('NotaFiscal', on_delete=models.CASCADE, related_name='itens')
    descricao = models.CharField(max_length=255, blank=True, default='Sem descrição')
    quantidade = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)  # Permite valores decimais e nulos
    unidade = models.CharField(max_length=50, blank=True, default='UN')
    valor_unid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    desconto = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.descricao

