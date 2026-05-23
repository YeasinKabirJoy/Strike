from django.contrib import admin
from .models import ChatGroup,GroupMessage,GroupChatRequest
# Register your models here.
admin.site.register([ChatGroup,GroupMessage,GroupChatRequest])