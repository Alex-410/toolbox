from django.urls import path
from api import views

urlpatterns = [
    path('health/', views.health_check, name='health-check'),
    path('tools/', views.tools_list, name='tools-list'),
    path('process/', views.process_image, name='process-image'),
]
