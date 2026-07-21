from django.contrib import admin

from .models import ChatParticipant, ChatRoom, Message


class ChatParticipantInline(admin.TabularInline):
    model = ChatParticipant
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("joined_at",)


@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ("id", "room_type", "participant_names", "message_count", "created_at")
    list_filter = ("room_type", "created_at")
    search_fields = ("participants__username", "public_id", "direct_key")
    readonly_fields = ("public_id", "created_at")
    inlines = (ChatParticipantInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("participants", "messages")

    @admin.display(description="참여 사용자")
    def participant_names(self, obj):
        names = [user.username for user in obj.participants.all()]
        return ", ".join(names) if names else "참여자 없음"

    @admin.display(description="메시지 수")
    def message_count(self, obj):
        return len(obj.messages.all())


@admin.register(ChatParticipant)
class ChatParticipantAdmin(admin.ModelAdmin):
    list_display = ("user_name", "room_label", "other_participants", "joined_at")
    list_filter = ("room__room_type", "joined_at")
    search_fields = ("user__username", "room__participants__username", "room__public_id")
    autocomplete_fields = ("user", "room")
    list_select_related = ("user", "room")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("user", "room").prefetch_related("room__participants")

    @admin.display(description="사용자", ordering="user__username")
    def user_name(self, obj):
        return obj.user.username

    @admin.display(description="채팅방", ordering="room__id")
    def room_label(self, obj):
        return f"{obj.room.get_room_type_display()} #{obj.room_id}"

    @admin.display(description="대화 상대")
    def other_participants(self, obj):
        names = [user.username for user in obj.room.participants.all() if user.pk != obj.user_id]
        return ", ".join(names) if names else "-"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("author_name", "room_users", "content_preview", "created_at")
    list_filter = ("room__room_type", "created_at")
    search_fields = ("author__username", "content", "room__participants__username")
    autocomplete_fields = ("author", "room")
    readonly_fields = ("public_id", "created_at")
    list_select_related = ("author", "room")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author", "room").prefetch_related("room__participants")

    @admin.display(description="작성자", ordering="author__username")
    def author_name(self, obj):
        return obj.author.username

    @admin.display(description="채팅 참여자")
    def room_users(self, obj):
        return ", ".join(user.username for user in obj.room.participants.all()) or "-"

    @admin.display(description="메시지")
    def content_preview(self, obj):
        return obj.content[:80] + ("…" if len(obj.content) > 80 else "")
