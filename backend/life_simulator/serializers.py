from rest_framework import serializers
from .models import GameSession


class GameSessionSerializer(serializers.ModelSerializer):
    world_display = serializers.CharField(source='get_world_type_display', read_only=True)

    class Meta:
        model = GameSession
        fields = [
            'id', 'world_type', 'world_display', 'attributes',
            'background', 'history', 'current_stage', 'is_active',
            'ending', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StartGameSerializer(serializers.Serializer):
    world_type = serializers.ChoiceField(choices=['modern', 'ancient', 'future'])


class ChooseSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    choice_id = serializers.IntegerField()
