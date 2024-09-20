# nfce/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('nota_fiscal/<int:nota_fiscal_id>/', views.nota_fiscal_view, name='nota_fiscal'),
    path('nota_fiscal/<int:nota_fiscal_id>/editar/', views.editar_itens, name='editar_itens'),
    path('process_captcha/<str:qr_code_url>/', views.process_captcha, name='process_captcha'),
    path('editar_itens/<int:nota_fiscal_id>/', views.editar_itens, name='editar_itens'),
    path('nota_fiscal/<int:nota_fiscal_id>/editar/', views.editar_itens, name='editar_itens'),
    path('conferir_itens/', views.conferir_itens, name='conferir_itens'),
    path('listar_notas_fiscais/', views.listar_notas_fiscais, name='listar_notas_fiscais'),  # URL para listar notas fiscais




]
