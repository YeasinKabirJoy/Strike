from django.urls import path
from .views import home,chatroom,send_chat,create_chatroom,create_group,edit_group,test,leave_group,delete_group
urlpatterns = [
    path('',home,name='home'),
    path('test/',test,name='test'),
    path('chatroom/<str:chatroom_name>/',chatroom,name='chatroom'),
    path('chat/',send_chat,name='chat'),
    path('startchat/<str:username>/',create_chatroom,name='chatroom-create'),
    path('group/create/',create_group,name='group-create'),
    path('group/edit/<str:name>',edit_group,name='group-edit'),
    path('group/leave/<str:name>',leave_group,name='group-leave'),
    path('group/delete/<str:name>',delete_group,name='group-delete'),
]
