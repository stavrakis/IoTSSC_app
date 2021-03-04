from django.urls import path

from . import views

urlpatterns = [
    path('/', views.index, name='index'),
    path('/view_db/', views.viewdb, name='view_db'),
]
