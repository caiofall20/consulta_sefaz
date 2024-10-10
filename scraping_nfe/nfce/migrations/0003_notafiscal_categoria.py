# Generated by Django 5.1.1 on 2024-10-10 17:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfce', '0002_alter_item_desconto_alter_item_descricao_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='notafiscal',
            name='categoria',
            field=models.CharField(choices=[('alimentacao', 'Alimentação'), ('transporte', 'Transporte'), ('lazer', 'Lazer'), ('saude', 'Saúde'), ('educacao', 'Educação')], default='alimentacao', max_length=50),
        ),
    ]
