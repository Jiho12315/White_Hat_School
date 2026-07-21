import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


def avatar_image_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "img"
    return f"avatars/{instance.public_id}/{uuid.uuid4().hex}.{extension}"


class User(AbstractUser):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "활성"
        RESTRICTED = "RESTRICTED", "제한"
        DORMANT = "DORMANT", "휴면"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    bio = models.CharField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to=avatar_image_path, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE, db_index=True)

    @property
    def can_write(self):
        return self.is_authenticated and self.status == self.Status.ACTIVE
