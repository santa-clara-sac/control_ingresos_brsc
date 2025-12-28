from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('ta/', include('tupac_amaru.urls')),
    path('cc/', include('canta_callao.urls')),
    path('sullana/', include('sullana.urls')),
    path('cordova/', include('cordova.urls')),
    # path('tupac_amaru/', views.tupac_amaru, name='tupac_amaru'),
    # path('autopartes_diaz_1/', views.autopartes_diaz_1, name='autopartes_diaz_1'),
    # path('autopartes_diaz_1a/', views.autopartes_diaz_1a, name='autopartes_diaz_1a'),

]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
