from django.urls import path
from . import views

urlpatterns = [
    path('start/', views.start_game, name='life-start'),
    path('choose/', views.make_choice, name='life-choose'),
    path('session/<uuid:session_id>/', views.get_session, name='life-session'),
]
