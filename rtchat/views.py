from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatGroup,GroupMessage,GroupChatRequest
from .forms import GroupChatInputForm,GroupCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http.response import Http404, HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
# Create your views here.

User = get_user_model()
def test(request):
    return render(request,'rtchat/group-joining-request.html')


@login_required
def home(request):
    return render(request,'home.html')


@login_required
def chatroom(request,chatroom_name='public-chat'):
    group = get_object_or_404(ChatGroup,name=chatroom_name)
    chats = group.messages.all()
    form = GroupChatInputForm()
    is_private = group.is_private
    other_member = None
    groupchat_name = group.groupchat_name

    if is_private:
        if request.user not in group.members.all():
            raise Http404()
        for member in group.members.all():
            if member!=request.user:
                other_member = member

    if groupchat_name:
        if request.user not in group.members.all():
            if request.user not in group.groupchatrequest.request.all():
                group.groupchatrequest.request.add(request.user)
            context = {
                'groupchat_name':group.groupchat_name
            }
            return render(request,'rtchat/group-joining-request.html',context)


            # group.members.add(request.user)

    context = {
        'chats': chats,
        'form':form,
        'chatroom':group,
        'other_member':other_member,

    }
    return render(request, 'rtchat/chat.html', context)

# sending chat is now handled by ws consumers
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
def send_chat_files(request, chatroom_name='public-chat'):
    print('yooo')
    if request.method == "POST":
        group = get_object_or_404(ChatGroup, name=chatroom_name)
        other_member = None
        channel_layer = get_channel_layer()

        # Find the other member in a private chat
        if group.is_private:
            for member in group.members.all():
                if member != request.user:
                    other_member = member

        # Handle uploaded files
        files = request.FILES.getlist("files")  # Use `getlist` to retrieve multiple files
        for file in files:
            message = GroupMessage.objects.create(sender=request.user, group=group, file=file)
            event = {
                'type': 'message_handler',
                'chat': message,
                'chatroom': chatroom_name,
                'other_member': other_member
            }
            async_to_sync(channel_layer.group_send)(
                chatroom_name, event
            )

        return JsonResponse({"message": "File uploaded successfully."}, status=201)

    # If not POST, return an error
    return JsonResponse({"error": "Invalid request method."}, status=400)
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

@login_required
def create_group(request):
    form = GroupCreationForm()
    if request.method == 'POST':
        form = GroupCreationForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.admin = request.user
            group.save()
            group.members.add(request.user)
            GroupChatRequest.objects.create(group=group)
            return redirect('chatroom', group.name)
    context = {
        'form':form
    }
    return render(request,'rtchat/create_group.html',context)

@login_required
def edit_group(request,name):
    group = get_object_or_404(ChatGroup,name=name)
    if request.user != group.admin:
        raise Http404
    form = GroupCreationForm(instance=group)
    if request.method == 'POST':
        form = GroupCreationForm(data=request.POST,instance=group)
        if form.is_valid():
            form.save()

            remove_members_id = request.POST.getlist('remove-members')  # Get all selected member IDs
            for member_id in remove_members_id:
                member = User.objects.get(id=member_id)
                group.members.remove(member)

            request_members_id = request.POST.getlist('request-members')  # Get all selected member IDs
            for member_id in request_members_id:
                member = User.objects.get(id=member_id)
                group.members.add(member)
                group.groupchatrequest.request.remove(member)

        return redirect(request.META.get('HTTP_REFERER'))

    context = {
        'group':group,
        'form':form,
    }
    return render(request,'rtchat/edit-group.html',context)

@login_required
def leave_group(request,name):
    group = get_object_or_404(ChatGroup, name=name)

    if request.user not in group.members.all():
        raise Http404

    group.members.remove(request.user)

    return redirect('home')


@login_required
def delete_group(request, name):
    group = get_object_or_404(ChatGroup, name=name)
    if group.admin != request.user:
        raise Http404

    group.delete()

    return redirect('home')