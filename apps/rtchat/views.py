from django.shortcuts import render, redirect, get_object_or_404
from .models import ChatGroup,GroupMessage,GroupChatRequest
from .forms import GroupChatInputForm,GroupCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.http.response import Http404, HttpResponse, JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .consumers import can_access_chatroom
from .utils import get_other_private_member, get_seen_message_id
from PIL import Image, UnidentifiedImageError
from django.utils.dateparse import parse_datetime
# Create your views here.

User = get_user_model()
CHAT_MESSAGES_PAGE_SIZE = 30

MAX_CHAT_IMAGE_SIZE = 5 * 1024 * 1024
ALLOWED_CHAT_IMAGE_TYPES = {
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
}


def validate_chat_image(file):
    if file.size > MAX_CHAT_IMAGE_SIZE:
        return f'{file.name} is larger than 5MB.'

    if file.content_type not in ALLOWED_CHAT_IMAGE_TYPES:
        return f'{file.name} must be a JPG, PNG, GIF, or WebP image.'

    try:
        Image.open(file).verify()
    except (UnidentifiedImageError, OSError):
        return f'{file.name} is not a valid image file.'
    finally:
        file.seek(0)

    return None


def get_chat_messages_queryset(group):
    return group.messages.select_related('sender', 'sender__profile').order_by('-created_at', '-id')


def get_chat_messages_context(group, *, query=''):
    chats_queryset = get_chat_messages_queryset(group)
    query = query.strip()

    if query:
        chats = list(
            chats_queryset.filter(message__icontains=query, is_deleted=False)[:CHAT_MESSAGES_PAGE_SIZE]
        )
        chats.reverse()
        return {
            'chats': chats,
            'has_more_messages': False,
            'search_mode': True,
            'search_query': query,
        }

    chats = list(chats_queryset[:CHAT_MESSAGES_PAGE_SIZE])
    chats.reverse()
    return {
        'chats': chats,
        'has_more_messages': chats_queryset.count() > CHAT_MESSAGES_PAGE_SIZE,
        'search_mode': False,
        'search_query': '',
    }


def test(request):
    return render(request,'users/search.html')


@login_required
def home(request):
    return render(request,'home.html')


@login_required
def chatroom(request,chatroom_name='public-chat'):
    group = get_object_or_404(ChatGroup,name=chatroom_name)
    form = GroupChatInputForm()
    is_private = group.is_private
    other_member = None
    groupchat_name = group.groupchat_name

    if is_private:
        if request.user not in group.members.all():
            raise Http404()
        other_member = get_other_private_member(group, request.user)

    if groupchat_name:
        if request.user not in group.members.all():
            if request.user not in group.groupchatrequest.request.all():
                group.groupchatrequest.request.add(request.user)
            context = {
                'groupchat_name':group.groupchat_name
            }
            return render(request,'rtchat/group-joining-request.html',context)


            # group.members.add(request.user)

    context = get_chat_messages_context(group)
    context.update({
        'form':form,
        'chatroom':group,
        'other_member':other_member,
        'seen_message_id': get_seen_message_id(group, request.user, other_member),
    })
    return render(request, 'rtchat/chat.html', context)


@login_required
def chatroom_messages(request, chatroom_name):
    group = get_object_or_404(ChatGroup, name=chatroom_name)
    if not can_access_chatroom(request.user, group):
        raise Http404()
    other_member = get_other_private_member(group, request.user)

    before_created_at = parse_datetime(request.GET.get('before_created_at', ''))
    before_id = request.GET.get('before_id', '')
    if not before_created_at or not before_id:
        return JsonResponse({"error": "Invalid pagination cursor."}, status=400)

    chats_queryset = (
        group.messages
        .select_related('sender', 'sender__profile')
        .filter(
            Q(created_at__lt=before_created_at) |
            Q(created_at=before_created_at, id__lt=before_id)
        )
        .order_by('-created_at', '-id')
    )
    chats = list(chats_queryset[:CHAT_MESSAGES_PAGE_SIZE + 1])
    has_more_messages = len(chats) > CHAT_MESSAGES_PAGE_SIZE
    chats = chats[:CHAT_MESSAGES_PAGE_SIZE]
    chats.reverse()

    context = {
        'chats': chats,
        'has_more_messages': has_more_messages,
        'search_mode': False,
        'search_query': '',
        'chatroom': group,
        'other_member': other_member,
        'seen_message_id': get_seen_message_id(group, request.user, other_member),
    }
    return render(request, 'snippet/older_messages.html', context)


@login_required
def chatroom_messages_list(request, chatroom_name):
    group = get_object_or_404(ChatGroup, name=chatroom_name)
    if not can_access_chatroom(request.user, group):
        raise Http404()

    context = get_chat_messages_context(group, query=request.GET.get('q', ''))
    other_member = get_other_private_member(group, request.user)
    context.update({
        'chatroom': group,
        'other_member': other_member,
        'seen_message_id': get_seen_message_id(group, request.user, other_member),
    })
    return render(request, 'snippet/chat_messages_list.html', context)

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
    if request.method == "POST":
        group = get_object_or_404(ChatGroup, name=chatroom_name)
        if not can_access_chatroom(request.user, group):
            raise Http404()

        other_member = None
        channel_layer = get_channel_layer()

        # Find the other member in a private chat
        if group.is_private:
            other_member = get_other_private_member(group, request.user)

        # Handle uploaded files
        files = request.FILES.getlist("files")  # Use `getlist` to retrieve multiple files
        if not files:
            return JsonResponse({"error": "No files were uploaded."}, status=400)

        for file in files:
            error = validate_chat_image(file)
            if error:
                return JsonResponse({"error": error}, status=400)

        for file in files:
            message = GroupMessage.objects.create(sender=request.user, group=group, file=file)
            event = {
                'type': 'message_handler',
                'message_id': message.id,
                'chatroom_id': str(group.id),
                'other_member_id': other_member.id if other_member else None
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
