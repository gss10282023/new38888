from django.conf import settings
from django.db import models


class Message(models.Model):
    """
    Represents a message posted inside a group conversation.
    """

    group = models.ForeignKey(
        "groups.Group",
        on_delete=models.CASCADE,
        related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.author} @ {self.group}: {self.text[:50]}"


class MessageAttachment(models.Model):
    """
    Stores metadata for files attached to a chat message.
    """

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file_url = models.URLField()
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    mime_type = models.CharField(max_length=100)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.filename
