import uuid

from django.conf import settings
from django.db import models


class ChatRoom(models.Model):
    class RoomType(models.TextChoices):
        GLOBAL = "GLOBAL", "전체"
        DIRECT = "DIRECT", "1:1"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    room_type = models.CharField(max_length=8, choices=RoomType.choices)
    direct_key = models.CharField(max_length=50, unique=True, null=True, blank=True)
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, through="ChatParticipant", related_name="chat_rooms")
    created_at = models.DateTimeField(auto_now_add=True)

    def user_can_access(self, user):
        if not user.is_authenticated or not user.can_write:
            return False
        return self.room_type == self.RoomType.GLOBAL or user.is_staff or self.participants.filter(pk=user.pk).exists()

    def __str__(self):
        return f"{self.get_room_type_display()} 채팅방 #{self.pk}"


class ChatParticipant(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["room", "user"], name="unique_chat_participant")]

    def __str__(self):
        return f"{self.user.username} · {self.room}"


class Message(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="messages")
    content = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["room", "created_at"])]

    def __str__(self):
        preview = self.content[:40]
        return f"{self.author.username}: {preview}"
