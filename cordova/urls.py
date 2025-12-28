from django.urls import path
from . import views

app_name = 'cordova'

urlpatterns = [
    path('cordova/', views.cordova, name='cordova'),
]