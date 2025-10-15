from rest_framework import serializers

from users.models import User

from .models import Message, MessageAttachment


class AuthorSerializer(serializers.ModelSerializer):
    """
    Slim serializer returning only the details required by the client.
    """

    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "name"]

    def get_name(self, obj: User) -> str:
        display_name = obj.get_full_name()
        return display_name if display_name else obj.email


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = [
            "file_url",
            "filename",
            "file_size",
            "mime_type",
        ]


class MessageSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    timestamp = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "author",
            "text",
            "timestamp",
            "attachments",
        ]
