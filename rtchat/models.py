from django.db import models
import uuid
from django.contrib.auth import get_user_model

# Create your models here.

User = get_user_model()

class ChatGroup(models.Model):
    name = models.CharField(max_length=100)
    online_users = models.ManyToManyField(User,related_name='online_in_groups',blank=True)
    id = models.UUIDField(default=uuid.uuid4,primary_key=True,editable=False,unique=True)
    slug = models.CharField(max_length=150)

    def __str__(self):
        return self.name


def generate_short_uuid():
    return uuid.uuid4().hex[:18]


class GroupMessage(models.Model):
    group = models.ForeignKey(ChatGroup,on_delete=models.CASCADE)
    sender = models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    message = models.TextField()
    id = models.CharField(default=generate_short_uuid, max_length=18,primary_key=True, editable=False, unique=True)

    def __str__(self):
        if len(self.message)>20:
            return f'{self.sender.username} - {self.message[:20]}. . . . .'
        else:
            return f'{self.sender.username} - {self.message}'

