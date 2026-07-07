from .models import GroupMessage, PrivateChatReadState


def get_other_private_member(chatroom, user):
    if not chatroom.is_private:
        return None

    return chatroom.members.select_related('profile').exclude(id=user.id).first()


def get_seen_message_id(chatroom, viewer, other_member=None):
    if not chatroom.is_private or not getattr(viewer, 'is_authenticated', False):
        return None

    other_member = other_member or get_other_private_member(chatroom, viewer)
    if not other_member:
        return None

    read_state = (
        PrivateChatReadState.objects
        .select_related('last_read_message')
        .filter(group=chatroom, user=other_member)
        .first()
    )
    if not read_state or not read_state.last_read_message:
        return None

    boundary_message = read_state.last_read_message
    seen_message = (
        GroupMessage.objects
        .filter(group=chatroom, sender=viewer)
        .filter(created_at__lte=boundary_message.created_at)
        .order_by('-created_at', '-id')
        .first()
    )
    return seen_message.id if seen_message else None
