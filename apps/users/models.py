from django.db import models
from django.contrib.auth import get_user_model
from django.templatetags.static import static
from django.utils import timezone
from datetime import timedelta

# Create your models here.
User = get_user_model()


class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    image = models.ImageField(upload_to='avatars/',blank=True,null=True)
    name = models.CharField(max_length=50,blank=True,null=True)
    email = models.EmailField(unique=True,blank=True,null=True)
    location = models.CharField(max_length=100,blank=True,null=True)
    bio = models.TextField(blank=True,null=True)
    created = models.DateTimeField(auto_now_add=True)
    online_status = models.BooleanField(default=False)
    online_connections = models.PositiveIntegerField(default=0)
    last_seen = models.DateTimeField(blank=True, null=True)
    def __str__(self):
        return str(self.user)

    @property
    def avatar(self):
        try:
            avatar = self.image.url
        except:
            avatar = static('images/default_user.png')
        return avatar

    @property
    def get_name(self):

        if self.name:
            user_name = self.name
        else:
            user_name = self.user.username

        return user_name

    @property
    def presence_label(self):
        if self.online_status:
            return 'Online'

        if not self.last_seen:
            return 'Offline'

        local_last_seen = timezone.localtime(self.last_seen)
        local_now = timezone.localtime()

        if local_last_seen.date() == local_now.date():
            return f'Last seen today at {local_last_seen.strftime("%I:%M %p").lstrip("0")}'

        if local_last_seen.date() == (local_now - timedelta(days=1)).date():
            return f'Last seen yesterday at {local_last_seen.strftime("%I:%M %p").lstrip("0")}'

        return f'Last seen {local_last_seen.strftime("%b %d at %I:%M %p").replace(" 0", " ")}'


# class Connections(models.Model):
#     user = models.ForeignKey(User,on_delete=models.CASCADE,related_name='connections')
#     group = models.ForeignKey()
#     is_group = models.BooleanField(default=False)
#     is_private = models.BooleanField(default=False)
