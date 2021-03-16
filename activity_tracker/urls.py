from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('view_db', views.viewdb, name='view_db'),
    path('pub', views.pub, name='pub'),
    path('login', views.login, name='login'),
    path('check_token', views.check_token, name='check_token'),
    path('register', views.register, name='register'),
    path('get/now', views.get_now, name='get_now'),

    path('debug/process', views.proc_mil, name='proc_mil'),
]
