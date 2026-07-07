from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.db.models import F
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import ChatGroup, GroupMessage, PrivateChatReadState
from apps.users.models import Profile
from .utils import get_other_private_member, get_seen_message_id
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
            self.other_member = get_other_private_member(self.chatroom, self.user)
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
        if event_type == 'chat.message_edit':
            self.edit_message(data)
            return
        if event_type == 'chat.message_delete':
            self.delete_message(data)
            return
        if event_type == 'chat.mark_read':
            self.mark_read()
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

    def get_owned_text_message(self, message_id):
        return GroupMessage.objects.filter(
            id=message_id,
            group=self.chatroom,
            sender=self.user,
            file__isnull=True,
            is_deleted=False,
        ).first()

    def edit_message(self, data):
        message_id = data.get('message_id')
        message_text = data.get('message', '').strip()
        if not message_id or not message_text:
            return

        chat = self.get_owned_text_message(message_id)
        if not chat:
            return

        chat.message = message_text
        chat.is_edited = True
        chat.save(update_fields=['message', 'is_edited'])
        self.broadcast_message_update(chat.id)

    def delete_message(self, data):
        message_id = data.get('message_id')
        if not message_id:
            return

        chat = self.get_owned_text_message(message_id)
        if not chat:
            return

        chat.message = ''
        chat.is_deleted = True
        chat.save(update_fields=['message', 'is_deleted'])
        self.broadcast_message_update(chat.id)

    def broadcast_message_update(self, message_id):
        event = {
            'type': 'message_update_handler',
            'message_id': message_id,
            'chatroom_id': str(self.chatroom.id),
            'other_member_id': self.other_member.id if self.other_member else None
        }
        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )

    def message_handler(self, event):
        chat = GroupMessage.objects.select_related('sender', 'sender__profile', 'group').get(id=event['message_id'])
        chatroom = ChatGroup.objects.get(id=event['chatroom_id'])
        other_member_id = event.get('other_member_id')
        other_member = User.objects.get(id=other_member_id) if other_member_id else None
        context = {
            'chat': chat,
            'user': self.user,
            'chatroom':chatroom,
            'other_member':other_member,
            'seen_message_id': get_seen_message_id(chatroom, self.user, other_member),

        }
        html = render_to_string('../templates/snippet/message_ws.html', context)
        self.send(text_data=html)

    def message_update_handler(self, event):
        chat = GroupMessage.objects.select_related('sender', 'sender__profile', 'group').get(id=event['message_id'])
        chatroom = ChatGroup.objects.get(id=event['chatroom_id'])
        other_member_id = event.get('other_member_id')
        other_member = User.objects.get(id=other_member_id) if other_member_id else None
        context = {
            'chat': chat,
            'user': self.user,
            'chatroom': chatroom,
            'other_member': other_member,
            'oob': True,
            'seen_message_id': get_seen_message_id(chatroom, self.user, other_member),
        }
        html = render_to_string('snippet/message.html', context)
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

    def private_presence_handler(self, event):
        if not self.chatroom.is_private or not self.other_member:
            return

        self.other_member.profile.refresh_from_db()
        context = {
            'other_member': self.other_member,
        }
        html = render_to_string('snippet/private_chat_presence.html', context)
        self.send(text_data=html)

    def mark_read(self):
        if not self.chatroom.is_private:
            return

        latest_message = (
            self.chatroom.messages
            .order_by('-created_at', '-id')
            .first()
        )
        if not latest_message:
            return

        read_state, _ = PrivateChatReadState.objects.get_or_create(
            group=self.chatroom,
            user=self.user,
        )
        previous_message_id = read_state.last_read_message_id
        if previous_message_id == latest_message.id:
            return

        read_state.last_read_message = latest_message
        read_state.save(update_fields=['last_read_message', 'updated_at'])

        event = {
            'type': 'read_receipt_handler',
            'reader_id': self.user.id,
            'previous_message_id': previous_message_id,
            'message_id': latest_message.id,
        }
        async_to_sync(self.channel_layer.group_send)(self.chatroom_name, event)

    def read_receipt_handler(self, event):
        if event['reader_id'] == self.user.id or not self.chatroom.is_private:
            return

        message_ids = [message_id for message_id in [
            event.get('previous_message_id'),
            event.get('message_id'),
        ] if message_id]
        if not message_ids:
            return

        seen_message_id = get_seen_message_id(self.chatroom, self.user, self.other_member)
        for message_id in dict.fromkeys(message_ids):
            chat = (
                GroupMessage.objects
                .select_related('sender', 'sender__profile', 'group')
                .filter(id=message_id, group=self.chatroom)
                .first()
            )
            if not chat:
                continue

            context = {
                'chat': chat,
                'user': self.user,
                'chatroom': self.chatroom,
                'other_member': self.other_member,
                'oob': True,
                'seen_message_id': seen_message_id,
            }
            html = render_to_string('snippet/message.html', context)
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
        self.is_connected = False
        if not self.user.is_authenticated:
            self.close()
            return

        Profile.objects.filter(user=self.user).update(
            online_connections=F('online_connections') + 1,
            online_status=True,
        )
        self.user.profile.refresh_from_db()
        self.is_connected = True
        async_to_sync(self.channel_layer.group_add)(
            f"user_{self.user.id}", self.channel_name
        )
        self.accept()
        self.broadcast_presence_update()

    def disconnect(self, code):
        self.user = self.scope['user']
        if not self.user.is_authenticated or not getattr(self, 'is_connected', False):
            return

        Profile.objects.filter(user=self.user, online_connections__gt=0).update(
            online_connections=F('online_connections') - 1
        )
        self.user.profile.refresh_from_db()
        if self.user.profile.online_connections == 0:
            self.user.profile.online_status = False
            self.user.profile.last_seen = timezone.now()
            self.user.profile.save(update_fields=['online_status', 'last_seen'])

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
            async_to_sync(channel_layer.group_send)(
                chatroom.name,
                {'type': 'private_presence_handler'}
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


