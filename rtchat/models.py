from django.db import models
import uuid
from django.contrib.auth import get_user_model
from functools import partial
import shortuuid
# Create your models here.

User = get_user_model()


def short_uuid(length=10):
    return shortuuid.ShortUUID().random(length=length)



class ChatGroup(models.Model):
    name = models.CharField(max_length=100,unique=True,blank=True,default=partial(shortuuid.ShortUUID().random, length=10))
    online_users = models.ManyToManyField(User,related_name='online_in_groups',blank=True)
    members = models.ManyToManyField(User,related_name='chat_groups',blank=True)
    is_private = models.BooleanField(default=False)
    id = models.UUIDField(default=uuid.uuid4,primary_key=True,editable=False,unique=True)

    def __str__(self):
        return self.name


# def generate_short_uuid():
#     return uuid.uuid4().hex[:18]
#

class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup,on_delete=models.CASCADE,related_name='messages')
    sender = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    message = models.TextField()
    id = models.CharField(default=partial(shortuuid.ShortUUID().random, length=18), max_length=18,primary_key=True, editable=False, unique=True)

    def __str__(self):
        if len(self.message)>20:
            return f'{self.sender.username} - {self.message[:20]}. . . . .'
        else:
            return f'{self.sender.username} - {self.message}'

