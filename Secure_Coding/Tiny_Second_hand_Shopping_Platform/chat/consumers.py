import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from core.security import rate_limited
from .models import ChatRoom, Message


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["public_id"]
        self.group_name = f"chat_{self.room_id.hex}"
        allowed = await self.can_access()
        if not allowed:
            await self.close(code=4403)
            return
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data or len(text_data) > 5000:
            await self.send_json_error("유효하지 않은 메시지입니다.")
            return
        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json_error("유효하지 않은 메시지입니다.")
            return
        content = str(payload.get("message", "")).strip()
        if not content or len(content) > 1000:
            await self.send_json_error("메시지는 1자 이상 1000자 이하여야 합니다.")
            return
        limited = await database_sync_to_async(rate_limited)("chat", f"{self.scope['user'].pk}:{self.room_id}")
        if limited:
            await self.send_json_error("메시지 전송이 너무 빠릅니다.")
            return
        saved = await self.save_message(content)
        if not saved:
            await self.close(code=4403)
            return
        await self.channel_layer.group_send(self.group_name, {"type": "chat.message", **saved})

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({"message": event["message"], "author": event["author"], "author_id": event["author_id"], "created_at": event["created_at"]}, ensure_ascii=False))

    async def send_json_error(self, message):
        await self.send(text_data=json.dumps({"error": message}, ensure_ascii=False))

    @database_sync_to_async
    def can_access(self):
        user = self.scope["user"]
        try:
            room = ChatRoom.objects.get(public_id=self.room_id)
        except ChatRoom.DoesNotExist:
            return False
        return room.user_can_access(user)

    @database_sync_to_async
    def save_message(self, content):
        user = self.scope["user"]
        try:
            room = ChatRoom.objects.get(public_id=self.room_id)
        except ChatRoom.DoesNotExist:
            return None
        if not room.user_can_access(user):
            return None
        message = Message.objects.create(room=room, author=user, content=content)
        return {"message": message.content, "author": user.username, "author_id": user.pk, "created_at": message.created_at.isoformat()}
