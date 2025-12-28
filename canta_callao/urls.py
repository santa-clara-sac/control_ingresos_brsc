from django.urls import path
from . import views

app_name = 'canta_callao'

urlpatterns = [
    path('canta_callao/', views.canta_callao, name='canta_callao'),
]