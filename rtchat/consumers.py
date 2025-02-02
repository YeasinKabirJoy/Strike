from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.shortcuts import get_object_or_404
from .models import ChatGroup, GroupMessage
import json
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync


class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, name=self.chatroom_name)
        self.other_member = None
        if self.chatroom.is_private:
            for member in self.chatroom.members.all():
                if member != self.user:
                    self.other_member = member
        async_to_sync(self.channel_layer.group_add)(self.chatroom_name, self.channel_name)


        if self.user not in self.chatroom.online_users.all():
            self.chatroom.online_users.add(self.user)
            self.update_online_count()

        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.chatroom_name, self.channel_name)
        if self.user in self.chatroom.online_users.all():
            self.chatroom.online_users.remove(self.user)
            self.update_online_count()

    def receive(self, text_data=None, bytes_data=None):
        text_data = json.loads(text_data)
        message = text_data['message']

        chat = GroupMessage.objects.create(
            sender=self.user,
            group=self.chatroom,
            message=message
        )
        event = {
            'type': 'message_handler',
            'chat': chat,
            'chatroom':self.chatroom,
            'other_member':self.other_member
        }

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )
        update_data = {
            'private': self.chatroom.is_private,
            'chatroom_name': self.chatroom.name,
            'members': self.chatroom.members,
        }

        for member in self.chatroom.members.all():
            if member.profile.online_status:
                self.broadcast_sidebar_update(member.id, update_data)

    def message_handler(self, event):
        print('handler')
        chat = event['chat']
        chatroom = event['chatroom']
        other_member = event['other_member']
        context = {
            'chat': chat,
            'user': self.user,
            'chatroom':chatroom,
            'other_member':other_member

        }
        html = render_to_string('../templates/snippet/message_ws.html', context)
        self.send(text_data=html)

    def update_online_count(self):
        online_count = self.chatroom.online_users.count()-1
        event = {
            'type':'online_count_handler',
            'online_count': online_count
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def online_count_handler(self,event):
        online_count = event['online_count']
        context = {
            'online_count': online_count
        }

        html = render_to_string('../templates/snippet/online_count.html', context)
        self.send(text_data=html)

    def broadcast_sidebar_update(self, user_id, update_data):
        channel_layer = get_channel_layer()
        event = {
            'type': 'update_sidebar_handler',
            'chatroom_name': update_data['chatroom_name'],
            'private': update_data['private'],
            'members': update_data['members']  # Convert QuerySet to list
        }
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}", event)


class OnlineStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.user.profile.online_status = True
        self.user.profile.save()  # Save the change to the database
        async_to_sync(self.channel_layer.group_add)(
            f"user_{self.user.id}", self.channel_name
        )
        self.accept()

    def disconnect(self, code):
        self.user = self.scope['user']
        self.user.profile.online_status = False
        self.user.profile.save()  # Save the change to the database

        async_to_sync(self.channel_layer.group_discard)(
            f"user_{self.user.id}", self.channel_name
        )

    def update_sidebar_handler(self, event):
        chatroom_name = event['chatroom_name']
        private = event['private']
        members = event['members']
        context = {
            'chatroom_name': chatroom_name,
            'members': members,
            'user':self.user
        }

        if private:
            html = render_to_string('../templates/snippet/chat-members-ws.html', context)
        else:
            html = render_to_string('../templates/snippet/groupchat_members-ws.html', context)
        self.send(text_data=html)


