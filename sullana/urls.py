from django.urls import path
from . import views

app_name = 'sullana'

urlpatterns = [
    path('sullana/', views.sullana, name='sullana'),
]