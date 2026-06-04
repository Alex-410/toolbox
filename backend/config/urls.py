from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('api/life/', include('life_simulator.urls')),
    path('api/pdf/', include('pdf_tools.urls')),
    path('api/anime-travel/', include('anime_travel.urls')),
]
