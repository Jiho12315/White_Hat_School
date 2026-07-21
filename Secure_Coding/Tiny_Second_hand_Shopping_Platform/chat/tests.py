import uuid

from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from .models import ChatParticipant, ChatRoom, Message
from wallets.models import PointTransaction


class ChatBubbleLayoutTests(TestCase):
    def test_current_user_and_other_user_messages_have_different_sides(self):
        password = "Strong-test-pass-2026"
        me = User.objects.create_user(username="me", password=password)
        other = User.objects.create_user(username="other", password=password)
        room = ChatRoom.objects.create(room_type=ChatRoom.RoomType.DIRECT, direct_key=f"{me.pk}:{other.pk}")
        ChatParticipant.objects.create(room=room, user=me)
        ChatParticipant.objects.create(room=room, user=other)
        Message.objects.create(room=room, author=other, content="상대방 메시지")
        Message.objects.create(room=room, author=me, content="내 메시지")

        self.client.force_login(me)
        response = self.client.get(reverse("chat:room", args=[room.public_id]))

        self.assertContains(response, 'class="message-row message-other"')
        self.assertContains(response, 'class="message-row message-mine"')
        self.assertContains(response, "상대방 메시지")
        self.assertContains(response, "내 메시지")


class ChatTransferTests(TestCase):
    def setUp(self):
        cache.clear()
        password = "Strong-test-pass-2026"
        self.sender = User.objects.create_user(username="sender", password=password)
        self.receiver = User.objects.create_user(username="receiver", password=password)
        self.outsider = User.objects.create_user(username="outsider", password=password)
        self.room = ChatRoom.objects.create(
            room_type=ChatRoom.RoomType.DIRECT,
            direct_key=f"{self.sender.pk}:{self.receiver.pk}",
        )
        ChatParticipant.objects.create(room=self.room, user=self.sender)
        ChatParticipant.objects.create(room=self.room, user=self.receiver)

    def test_direct_room_shows_transfer_panel_for_other_participant(self):
        self.client.force_login(self.sender)
        response = self.client.get(reverse("chat:room", args=[self.room.public_id]))
        self.assertContains(response, "receiver님에게 송금하기")
        self.assertContains(response, reverse("chat:room_transfer", args=[self.room.public_id]))

    def test_successful_chat_transfer_changes_balances_and_creates_message(self):
        sender_before = self.sender.wallet.balance
        receiver_before = self.receiver.wallet.balance
        self.client.force_login(self.sender)
        response = self.client.post(
            reverse("chat:room_transfer", args=[self.room.public_id]),
            {"amount": 700, "idempotency_key": uuid.uuid4()},
        )
        self.assertRedirects(response, reverse("chat:room", args=[self.room.public_id]))
        self.sender.wallet.refresh_from_db()
        self.receiver.wallet.refresh_from_db()
        self.assertEqual(self.sender.wallet.balance, sender_before - 700)
        self.assertEqual(self.receiver.wallet.balance, receiver_before + 700)
        self.assertTrue(PointTransaction.objects.filter(sender=self.sender, receiver=self.receiver, amount=700).exists())
        self.assertTrue(Message.objects.filter(room=self.room, author=self.sender, content__contains="700 P를 송금했습니다").exists())

    def test_non_participant_cannot_transfer_through_room(self):
        self.client.force_login(self.outsider)
        response = self.client.post(
            reverse("chat:room_transfer", args=[self.room.public_id]),
            {"amount": 100, "idempotency_key": uuid.uuid4()},
        )
        self.assertEqual(response.status_code, 403)
        self.assertFalse(PointTransaction.objects.exists())
        self.assertFalse(Message.objects.exists())
