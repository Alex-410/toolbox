import uuid
from django.db import models


class GameSession(models.Model):
    WORLD_CHOICES = [
        ('modern', '现代都市'),
        ('ancient', '古代江湖'),
        ('future', '未来科幻'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    world_type = models.CharField(max_length=20, choices=WORLD_CHOICES)
    attributes = models.JSONField(default=dict)
    background = models.JSONField(default=dict)
    history = models.JSONField(default=list)
    current_stage = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    ending = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_world_type_display()} - {self.id}"
