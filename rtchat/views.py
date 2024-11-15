from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatGroup,GroupMessage
from .forms import GroupChatInputForm
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required
def home(request):
    chatroom_name = 'public-chat'
    chats = GroupMessage.objects.filter(group__name=chatroom_name)
    form = GroupChatInputForm()
    context = {
        'chats': chats,
        'form':form,
        'chatroom_name': chatroom_name
    }
    return render(request,'chat/chat.html',context)

@login_required
def chat(request):
    if request.method == "POST":
        chatroom_name = 'public-chat'
        group = get_object_or_404(ChatGroup,name=chatroom_name)
        form = GroupChatInputForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.group = group
            message.save()

            context = {
                'chat': message,

            }
            return render(request, 'snippet/message.html', context)