from django.urls import path
from . import views

app_name = 'tupac_amaru'

urlpatterns = [
    path('tupac_amaru/', views.tupac_amaru, name='tupac_amaru'),
    path('autopartes_diaz_1/', views.autopartes_diaz_1, name='autopartes_diaz_1'),
    path('autopartes_diaz_1a/', views.autopartes_diaz_1a, name='autopartes_diaz_1a'),
    path('parabrisas_willy_glass/', views.parabrisas_willy_glass, name='parabrisas_willy_glass'),
    path('autopartes_christian_local1/', views.autopartes_christian_local1, name='autopartes_christian_local1'),
    path('autopartes_christian_local2/', views.autopartes_christian_local2, name='autopartes_christian_local2'),
    path('autopartes_christian_local3/', views.autopartes_christian_local3, name='autopartes_christian_local3'),
    path('autopartes_accesorios_alcantara/', views.autopartes_accesorios_alcantara, name='autopartes_accesorios_alcantara'),
    path('autopartes_de_multimarcas_daniel_alcantara_monsefu/', views.autopartes_de_multimarcas_daniel_alcantara_monsefu, name='autopartes_de_multimarcas_daniel_alcantara_monsefu'),
    path('distribuidora_matizados_velsa_1/', views.distribuidora_matizados_velsa_1, name='distribuidora_matizados_velsa_1'),
    path('distribuidora_matizados_velsa_2/', views.distribuidora_matizados_velsa_2, name='distribuidora_matizados_velsa_2'),
    path('fierro_nancy_marlene/', views.fierro_nancy_marlene, name='fierro_nancy_marlene'),
    path('autopartes_alfredo_peluca/', views.autopartes_alfredo_peluca, name='autopartes_alfredo_peluca'),
    path('chino_juana_iris/', views.chino_juana_iris, name='chino_juana_iris'),
    path('domingo_saavedra_peluca/', views.domingo_saavedra_peluca, name='domingo_saavedra_peluca'),
    path('compra_y_venta_chatarra_laurie/', views.compra_y_venta_chatarra_laurie, name='compra_y_venta_chatarra_laurie'),
    path('arenado_jose_antonio_rodriguez_chafloque/', views.arenado_jose_antonio_rodriguez_chafloque, name='arenado_jose_antonio_rodriguez_chafloque'),
    path('arenado_miguel_carpio/', views.arenado_miguel_carpio, name='arenado_miguel_carpio'),
    path('pedro_estella/', views.pedro_estella, name='pedro_estella'),
    path('steev_anatoly_maquin_valladares/', views.steev_anatoly_maquin_valladares, name='steev_anatoly_maquin_valladares'),

    path("formulario_ingreso/", views.formulario_ingreso, name="formulario_ingreso"),
    path("guardar-ingreso/", views.guardar_ingreso, name="guardar_ingreso"),

    path('resumen/', views.resumen, name='resumen'),
]

