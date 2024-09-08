# nfce/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('process_captcha/<str:qr_code_url>/', views.process_captcha, name='process_captcha'),

]
