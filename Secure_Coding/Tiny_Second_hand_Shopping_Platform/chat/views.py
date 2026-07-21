from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from audit.services import record_audit
from core.security import active_user_required, rate_limited
from wallets.services import transfer_points
from .forms import ChatTransferForm, DirectChatForm
from .models import ChatParticipant, ChatRoom, Message


def _get_or_create_direct_room(sender, other):
    key = ":".join(map(str, sorted([sender.pk, other.pk])))
    with transaction.atomic():
        room, _ = ChatRoom.objects.get_or_create(room_type=ChatRoom.RoomType.DIRECT, direct_key=key)
        ChatParticipant.objects.get_or_create(room=room, user=sender)
        ChatParticipant.objects.get_or_create(room=room, user=other)
    return room


@active_user_required
def global_chat(request):
    room, _ = ChatRoom.objects.get_or_create(room_type=ChatRoom.RoomType.GLOBAL, direct_key="GLOBAL")
    return render(request, "chat/room.html", {"room": room, "messages_list": room.messages.select_related("author")[:100]})


@active_user_required
def direct_create(request):
    form = DirectChatForm(request.POST or None, sender=request.user)
    if request.method == "POST" and form.is_valid():
        other = form.cleaned_data["username"]
        room = _get_or_create_direct_room(request.user, other)
        return redirect("chat:room", public_id=room.public_id)
    return render(request, "chat/direct_create.html", {"form": form})


@require_POST
@active_user_required
def direct_with_user(request, public_id):
    other = get_object_or_404(User, public_id=public_id, status=User.Status.ACTIVE)
    if other == request.user:
        return HttpResponseForbidden("자기 자신과 1:1 채팅을 만들 수 없습니다.")
    room = _get_or_create_direct_room(request.user, other)
    return redirect("chat:room", public_id=room.public_id)


@active_user_required
def room_detail(request, public_id):
    room = get_object_or_404(ChatRoom, public_id=public_id, room_type=ChatRoom.RoomType.DIRECT)
    if not room.user_can_access(request.user):
        return HttpResponseForbidden("채팅방 접근 권한이 없습니다.")
    other_user = room.participants.exclude(pk=request.user.pk).first()
    return render(request, "chat/room.html", {
        "room": room,
        "messages_list": room.messages.select_related("author")[:100],
        "other_user": other_user,
        "transfer_form": ChatTransferForm(),
    })


@require_POST
@active_user_required
def room_transfer(request, public_id):
    room = get_object_or_404(ChatRoom, public_id=public_id, room_type=ChatRoom.RoomType.DIRECT)
    if not room.participants.filter(pk=request.user.pk).exists():
        return HttpResponseForbidden("채팅 참여자만 송금할 수 있습니다.")
    receiver = room.participants.exclude(pk=request.user.pk).first()
    if receiver is None:
        return HttpResponseForbidden("송금 받을 사용자를 확인할 수 없습니다.")
    if rate_limited("transfer", request.user.pk):
        messages.error(request, "송금 요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.")
        return redirect("chat:room", public_id=room.public_id)

    form = ChatTransferForm(request.POST)
    if not form.is_valid():
        messages.error(request, "송금 금액을 올바르게 입력해 주세요.")
        return redirect("chat:room", public_id=room.public_id)

    try:
        with transaction.atomic():
            point_transaction, created = transfer_points(
                sender=request.user,
                receiver=receiver,
                amount=form.cleaned_data["amount"],
                idempotency_key=form.cleaned_data["idempotency_key"],
            )
            chat_message = None
            if created:
                chat_message = Message.objects.create(
                    room=room,
                    author=request.user,
                    content=f"💸 {receiver.username}님에게 {point_transaction.amount:,} P를 송금했습니다.",
                )
                record_audit(
                    actor=request.user,
                    action="CHAT_POINT_TRANSFER",
                    target=point_transaction,
                    request=request,
                    detail={"room": str(room.public_id), "receiver": receiver.username, "amount": point_transaction.amount},
                )
                transaction.on_commit(lambda: _broadcast_transfer_message(room, chat_message))
    except ValidationError as exc:
        messages.error(request, " ".join(exc.messages))
        return redirect("chat:room", public_id=room.public_id)

    messages.success(request, "송금이 완료되었습니다." if created else "이미 처리된 송금 요청입니다.")
    return redirect("chat:room", public_id=room.public_id)


def _broadcast_transfer_message(room, message):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"chat_{room.public_id.hex}",
        {
            "type": "chat.message",
            "message": message.content,
            "author": message.author.username,
            "author_id": message.author_id,
            "created_at": message.created_at.isoformat(),
        },
    )
