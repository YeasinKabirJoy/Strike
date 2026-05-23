import mimetypes
import os

from django.db import models
import uuid
from django.contrib.auth import get_user_model
from functools import partial
import shortuuid
# Create your models here.

User = get_user_model()


def short_uuid(length):
    return shortuuid.ShortUUID().random(length=length)



class ChatGroup(models.Model):
    name = models.CharField(max_length=100,unique=True,blank=True,default=partial(short_uuid, length=10))
    online_users = models.ManyToManyField(User,related_name='online_in_groups',blank=True)
    groupchat_name = models.CharField(max_length=100,blank=True,null=True)
    admin = models.ForeignKey(User,on_delete=models.SET_NULL,blank=True,null=True,related_name='groupchat_admin')
    members = models.ManyToManyField(User,related_name='chat_groups',blank=True)
    is_private = models.BooleanField(default=False)
    id = models.UUIDField(default=uuid.uuid4,primary_key=True,editable=False,unique=True)

    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)

    class Meta:
        ordering = ['-updated_at']
    def __str__(self):
        return self.name


# def generate_short_uuid():
#     return uuid.uuid4().hex[:18]
#

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup,on_delete=models.CASCADE,related_name='messages')
    sender = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    message = models.TextField(blank=True,null=True)
    file = models.FileField(upload_to='files/',blank=True,null=True)
    id = models.CharField(default=partial(short_uuid, length=18), max_length=18,primary_key=True, editable=False, unique=True)

    # def __str__(self):
    #     if len(self.message)>20:
    #         return f'{self.sender.username} - {self.message[:20]}. . . . .'
    #     else:
    #         return f'{self.sender.username} - {self.message}'

    def file_type(self):
        if not self.file:
            return None
        mime_type, _ = mimetypes.guess_type(self.file.url)
        if mime_type:
            return mime_type.split('/')[0]  # Returns 'image', 'video', etc.
        return 'unknown'

    def get_file_name(self):
        """Returns the file name without extension."""
        if self.file:
            return os.path.splitext(os.path.basename(self.file.name))[0]
        return None

class GroupChatRequest(models.Model):
    group = models.OneToOneField(ChatGroup,on_delete=models.CASCADE)
    request = models.ManyToManyField(User,related_name='requested_group',blank=True)