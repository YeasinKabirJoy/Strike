from django.urls import path
from .views import home,chatroom,send_chat,create_chatroom
urlpatterns = [
    path('',home,name='home'),
    path('chatroom/<str:chatroom_name>/',chatroom,name='chatroom'),
    path('chat/',send_chat,name='chat'),
    path('startchat/<str:username>/',create_chatroom,name='chatroom-create'),
]
