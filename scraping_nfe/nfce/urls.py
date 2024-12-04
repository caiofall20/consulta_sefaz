# nfce/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('nota_fiscal/<int:nota_fiscal_id>/', views.nota_fiscal_view, name='nota_fiscal'),
    path('nota_fiscal/<int:nota_fiscal_id>/editar/', views.editar_itens, name='editar_itens'),
    path('process_captcha/<str:qr_code_url>/', views.process_captcha, name='process_captcha'),
    path('editar_itens/<int:nota_fiscal_id>/', views.editar_itens, name='editar_itens'),
    path('conferir_itens/', views.conferir_itens, name='conferir_itens'),
    path('listar_notas_fiscais/', views.listar_notas_fiscais, name='listar_notas_fiscais'),
    path('adicionar_nota_fiscal/', views.adicionar_nota_fiscal, name='adicionar_nota_fiscal'),
    path('login/', auth_views.LoginView.as_view(template_name='nfce/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('cadastro/', views.cadastro_view, name='cadastro'),
    path('inicio/', views.inicio_view, name='inicio'),
    path('consultar_nfce/', views.consultar_nfce, name='consultar_nfce'),
]
