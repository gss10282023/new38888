from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Default Django user with room for future custom fields."""

    pass
