from django.urls import path
from .views import home, login_apoderado, login_conductor, registroConductor, registroApoderado, home_apoderado, home_conductor, informacionPersonal, informacionVehiculo, ingresaRuta, alumnos
from django.contrib.auth.views import LogoutView


from app import views

urlpatterns = [
    path('',home , name="home"),
    path('home_apoderado/', home_apoderado, name="home_apoderado"), 
    path('home_conductor/', home_conductor, name="home_conductor"), 
    path('registro_conductor/',registroConductor, name="registro_conductor"),
    path('registro_apoderado/',registroApoderado, name="registro_apoderado"),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('login/apoderado/', login_apoderado, name='login_apoderado'),  
    path('login/conductor/', login_conductor, name='login_conductor'),  
     #apoderado
    path('seguimiento/', views.seguimiento, name='seguimiento'),
    path('historial/', views.historial, name='historial'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('conductor/', views.conductor, name='conductor'),
    #conductor
    path('informacionPersonal/', views.informacionPersonal, name='informacionPersonal'),
    path('informacionVehiculo/', views.informacionVehiculo, name='informacionVehiculo'),
    path('ingresaRuta/', views.ingresaRuta, name='ingresaRuta'),
    path('apoderado/', views.apoderado, name='apoderado'),
    path('alumnos/', views.alumnos, name='alumnos'),
]

