from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('pub', views.pub, name='pub'),
    path('login', views.login, name='login'),
    path('check_token', views.check_token, name='check_token'),
    path('update_fbtoken', views.update_fb_token, name='update_fb_token'),
    path('register', views.register, name='register'),
    path('get/now', views.get_now, name='get_now'),
    path('get/history', views.get_history, name='get_history'),

]
