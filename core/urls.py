from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('materiales/', views.materiales, name='materiales'),
    path('modulo/<slug:slug>/', views.modulo, name='modulo'),
]
