from django.db import models
from django.contrib.auth.models import User


class ChatMessage(models.Model):

    PERSONA_CHOICES = [
        ("krishna", "Krishna"),
        ("radha", "Radha"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="chat_messages"
    )

    message = models.TextField()

    reply = models.TextField()

    persona = models.CharField(
        max_length=20,
        choices=PERSONA_CHOICES,
        default="krishna"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.persona}"