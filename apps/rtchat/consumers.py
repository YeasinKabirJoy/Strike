from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .models import ChatGroup, GroupMessage
import json
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync

User = get_user_model()


def can_access_chatroom(user, chatroom):
    if not user.is_authenticated:
        return False

    if chatroom.name == 'public-chat':
        return True

    return chatroom.members.filter(id=user.id).exists()


class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, name=self.chatroom_name)
        if not can_access_chatroom(self.user, self.chatroom):
            self.close()
            return

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
        if not can_access_chatroom(self.user, self.chatroom):
            self.close()
            return

        data = json.loads(text_data)
        event_type = data.get('type', 'chat.message')
        if event_type == 'chat.typing':
            self.broadcast_typing(bool(data.get('is_typing')))
            return

        message = data.get('message', '').strip()
        if not message:
            return

        chat = GroupMessage.objects.create(
            sender=self.user,
            group=self.chatroom,
            message=message
        )
        event = {
            'type': 'message_handler',
            'message_id': chat.id,
            'chatroom_id': str(self.chatroom.id),
            'other_member_id': self.other_member.id if self.other_member else None
        }

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )
        update_data = {
            'private': self.chatroom.is_private,
            'chatroom_name': self.chatroom.name,
            'member_ids': list(self.chatroom.members.values_list('id', flat=True)),
        }

        for member in self.chatroom.members.all():
            if member.profile.online_status:
                self.broadcast_sidebar_update(member.id, update_data)

    def broadcast_typing(self, is_typing):
        event = {
            'type': 'typing_handler',
            'user_id': self.user.id,
            'is_typing': is_typing,
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def message_handler(self, event):
        chat = GroupMessage.objects.select_related('sender', 'group').get(id=event['message_id'])
        chatroom = ChatGroup.objects.get(id=event['chatroom_id'])
        other_member_id = event.get('other_member_id')
        other_member = User.objects.get(id=other_member_id) if other_member_id else None
        context = {
            'chat': chat,
            'user': self.user,
            'chatroom':chatroom,
            'other_member':other_member

        }
        html = render_to_string('../templates/snippet/message_ws.html', context)
        self.send(text_data=html)

    def typing_handler(self, event):
        if event['user_id'] == self.user.id:
            return

        try:
            typing_user = User.objects.select_related('profile').get(id=event['user_id'])
        except User.DoesNotExist:
            return

        context = {
            'typing_user': typing_user,
            'is_typing': event['is_typing'],
        }
        html = render_to_string('snippet/typing_indicator.html', context)
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
            'member_ids': update_data['member_ids']
        }
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}", event)


class OnlineStatusConsumer(WebsocketConsumer):
    def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            self.close()
            return

        self.user.profile.online_status = True
        self.user.profile.save()  # Save the change to the database
        async_to_sync(self.channel_layer.group_add)(
            f"user_{self.user.id}", self.channel_name
        )
        self.accept()
        self.broadcast_presence_update()

    def disconnect(self, code):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            return

        self.user.profile.online_status = False
        self.user.profile.save()  # Save the change to the database

        async_to_sync(self.channel_layer.group_discard)(
            f"user_{self.user.id}", self.channel_name
        )
        self.broadcast_presence_update()

    def broadcast_presence_update(self):
        channel_layer = get_channel_layer()
        private_chatrooms = (
            self.user.chat_groups
            .filter(is_private=True, messages__isnull=False)
            .distinct()
            .prefetch_related('members')
        )
        for chatroom in private_chatrooms:
            member_ids = list(chatroom.members.values_list('id', flat=True))
            event = {
                'type': 'update_sidebar_handler',
                'chatroom_name': chatroom.name,
                'private': True,
                'member_ids': member_ids,
            }
            for member_id in member_ids:
                async_to_sync(channel_layer.group_send)(
                    f"user_{member_id}", event
                )

    def update_sidebar_handler(self, event):
        chatroom_name = event['chatroom_name']
        private = event['private']
        members = User.objects.filter(id__in=event['member_ids']).select_related('profile')
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


