from django.db import models
from django.contrib.auth.models import User
from orders.models import Order


class Conversation(models.Model):
    user = models.ForeignKey(User, related_name='conversations', on_delete=models.CASCADE)
    order = models.ForeignKey(Order, related_name='conversations', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Conversation #{self.id} with {self.user.username} for order {self.order.id}"


class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
    ]
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.role}: {self.content}" # Agent: We are checking your request, please wait.


class AgentLog(models.Model):
    EVENT_CHOICES = [
        ("support", "Support"),
        ("tool_call", "Tool Call"),
        ("tool_result", "Tool Result"),
        ("manager", "Manager Agent"),
        ("risk", "Risk Agent"),
        ("final", "Final Replay"),
    ]
    conversation = models.ForeignKey(Conversation, related_name='agent_logs', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=20, choices=EVENT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"[{self.event_type}]: {self.message[:40]}"