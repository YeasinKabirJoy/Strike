from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatGroup,GroupMessage
from .forms import GroupChatInputForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http.response import Http404
# Create your views here.

User = get_user_model()

def home(request):
    return render(request,'home.html')


@login_required
def chatroom(request,chatroom_name='public-chat'):
    group = ChatGroup.objects.get(name=chatroom_name)
    chats = group.messages.all()
    form = GroupChatInputForm()


    is_private = group.is_private
    other_member = None

    if is_private:
        if request.user not in group.members.all():
            raise Http404()
        for member in group.members.all():
            if member!=request.user:
                other_member = member

    context = {
        'chats': chats,
        'form':form,
        'chatroom_name': chatroom_name,
        'private':is_private,
        'other_member':other_member

    }
    return render(request, 'rtchat/chat.html', context)

@login_required
def send_chat(request):
    chatroom_name = 'public-chat'
    if request.method == "POST":
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

@login_required
def create_chatroom(request,username):
    user = request.user
    other_user = User.objects.get(username=username)
    if user.username == username:
        redirect('home')

    private_chatrooms = user.chat_groups.filter(is_private=True)

    chatroom = None

    if private_chatrooms.exists():
        for room in private_chatrooms:
            if other_user in room.members.all():
                chatroom= room
                break

    if not chatroom:
        chatroom = ChatGroup.objects.create(is_private=True)
        chatroom.members.add(user,other_user)

    return redirect('chatroom',chatroom.name)


