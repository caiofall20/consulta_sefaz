# Generated by Django 5.1.1 on 2024-09-11 04:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NotaFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero_serie', models.CharField(max_length=50)),
                ('razao_social', models.CharField(max_length=255)),
                ('cnpj_emitente', models.CharField(max_length=50)),
                ('inscricao_estadual', models.CharField(max_length=50)),
                ('data_emissao', models.CharField(max_length=50)),
                ('data_autorizacao', models.CharField(max_length=50)),
                ('valor_total_produtos', models.DecimalField(decimal_places=2, max_digits=10)),
                ('forma_pagamento', models.CharField(max_length=100)),
                ('chave_acesso', models.CharField(max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.CharField(max_length=255)),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=10)),
                ('unidade', models.CharField(max_length=20)),
                ('valor_unid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('desconto', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('valor_total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('nota_fiscal', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='itens', to='nfce.notafiscal')),
            ],
        ),
    ]