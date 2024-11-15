from django.urls import path
from .views import home,chat
urlpatterns = [
    path('',home,name='home'),
    path('chat/',chat,name='chat'),

]
