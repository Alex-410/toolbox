from django.urls import path
from . import views

urlpatterns = [
    path('pdf-to-images/', views.pdf_to_images_view, name='pdf-to-images'),
    path('images-to-pdf/', views.images_to_pdf_view, name='images-to-pdf'),
    path('pdf-to-word/', views.pdf_to_word_view, name='pdf-to-word'),
]
