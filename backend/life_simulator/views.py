from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import GameSession
from .serializers import GameSessionSerializer, StartGameSerializer, ChooseSerializer
from . import ai_service


@api_view(['POST'])
def start_game(request):
    serializer = StartGameSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    world_type = serializer.validated_data['world_type']
    attributes = ai_service.generate_attributes()
    background = ai_service.generate_background(world_type)
    story_data = ai_service.generate_initial_story(world_type, attributes, background)

    session = GameSession.objects.create(
        world_type=world_type,
        attributes=attributes,
        background=background,
        history=[{
            'stage': 0,
            'stage_index': 0,
            'stage_name': story_data.get('stage', '命运起点'),
            'story': story_data['story'],
            'options': story_data['options'],
            'event_tag': story_data.get('event_tag', ''),
            'choice_text': '',
        }],
        current_stage=0,
        is_active=True,
    )

    return Response({
        'session_id': str(session.id),
        'world_type': world_type,
        'attributes': attributes,
        'background': background,
        'story': story_data['story'],
        'options': story_data['options'],
        'stage': 0,
        'stage_name': story_data.get('stage', '命运起点'),
        'event_tag': story_data.get('event_tag', ''),
        'is_active': True,
    })


@api_view(['POST'])
def make_choice(request):
    serializer = ChooseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    session_id = serializer.validated_data['session_id']
    choice_id = serializer.validated_data['choice_id']

    try:
        session = GameSession.objects.get(id=session_id)
    except GameSession.DoesNotExist:
        return Response({'error': '游戏会话不存在'}, status=status.HTTP_404_NOT_FOUND)

    if not session.is_active:
        return Response({'error': '游戏已结束'}, status=status.HTTP_400_BAD_REQUEST)

    current = session.history[-1] if session.history else {}
    options = current.get('options', [])
    chosen = None
    for opt in options:
        if opt['id'] == choice_id:
            chosen = opt
            break

    if not chosen:
        return Response({'error': '无效的选择'}, status=status.HTTP_400_BAD_REQUEST)

    effect = chosen.get('effect', {})
    for key, val in effect.items():
        if key in session.attributes:
            session.attributes[key] = max(0, min(100, session.attributes[key] + val))

    session.history[-1]['choice_made'] = choice_id
    session.history[-1]['choice_text'] = chosen['text']

    new_stage = session.current_stage + 1
    max_stages = 10

    if new_stage >= max_stages:
        ending_data = ai_service.generate_ending(
            session.world_type, session.attributes, session.history
        )
        session.is_active = False
        session.current_stage = new_stage
        session.ending = ending_data.get('ending', '')
        session.save()

        return Response({
            'session_id': str(session.id),
            'attributes': session.attributes,
            'stage': new_stage,
            'stage_name': '终局',
            'is_active': False,
            'ending': ending_data.get('ending', ''),
            'score': ending_data.get('score', 50),
            'title': ending_data.get('title', '人生终章'),
            'tags': ending_data.get('tags', []),
            'history': session.history,
        })

    story_data = ai_service.generate_next_story(
        session.world_type, new_stage, session.attributes,
        session.history, chosen['text']
    )

    session.current_stage = new_stage
    session.history.append({
        'stage': new_stage,
        'stage_index': new_stage,
        'stage_name': story_data.get('stage', f'第{new_stage + 1}阶段'),
        'story': story_data['story'],
        'options': story_data['options'],
        'event_tag': story_data.get('event_tag', ''),
        'choice_text': '',
    })
    session.save()

    return Response({
        'session_id': str(session.id),
        'attributes': session.attributes,
        'story': story_data['story'],
        'options': story_data['options'],
        'stage': new_stage,
        'stage_name': story_data.get('stage', f'第{new_stage + 1}阶段'),
        'event_tag': story_data.get('event_tag', ''),
        'is_active': True,
    })


@api_view(['GET'])
def get_session(request, session_id):
    try:
        session = GameSession.objects.get(id=session_id)
    except GameSession.DoesNotExist:
        return Response({'error': '游戏会话不存在'}, status=status.HTTP_404_NOT_FOUND)

    data = GameSessionSerializer(session).data
    current = session.history[-1] if session.history else {}
    data['story'] = current.get('story', '')
    data['options'] = current.get('options', [])
    data['stage_name'] = current.get('stage_name', '')
    return Response(data)
