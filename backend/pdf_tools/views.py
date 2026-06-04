from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
import io
import base64
import logging
from . import converter

logger = logging.getLogger(__name__)


@api_view(['POST'])
def pdf_to_images_view(request):
    if 'file' not in request.FILES:
        return Response({'error': '请上传 PDF 文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    pdf_file = request.FILES['file']
    
    if not pdf_file.name.lower().endswith('.pdf'):
        return Response({'error': '请上传 PDF 文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        logger.info(f"Processing PDF: {pdf_file.name}")
        images = converter.pdf_to_images(pdf_file)
        logger.info(f"Converted to {len(images)} images")
        
        result = []
        for img in images:
            b64 = base64.b64encode(img['data']).decode('utf-8')
            result.append({
                'page': img['page'],
                'image': f'data:image/png;base64,{b64}'
            })
        
        return Response({
            'success': True,
            'pages': len(result),
            'images': result
        })
    except Exception as e:
        logger.error(f"PDF to images error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def images_to_pdf_view(request):
    if 'images' not in request.FILES:
        logger.error("No images in request")
        return Response({'error': '请上传图片文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    image_files = request.FILES.getlist('images')
    
    if not image_files:
        logger.error("Empty image list")
        return Response({'error': '请上传图片文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    logger.info(f"Processing {len(image_files)} images for PDF conversion")
    
    try:
        pdf_data = converter.images_to_pdf(image_files)
        logger.info(f"PDF generated, size: {len(pdf_data)} bytes")
        
        b64 = base64.b64encode(pdf_data).decode('utf-8')
        
        return Response({
            'success': True,
            'pdf': f'data:application/pdf;base64,{b64}'
        })
    except Exception as e:
        logger.error(f"Images to PDF error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def pdf_to_word_view(request):
    if 'file' not in request.FILES:
        return Response({'error': '请上传 PDF 文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    pdf_file = request.FILES['file']
    
    if not pdf_file.name.lower().endswith('.pdf'):
        return Response({'error': '请上传 PDF 文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        logger.info(f"Processing PDF to Word: {pdf_file.name}")
        text_content = converter.pdf_to_word(pdf_file)
        logger.info(f"Extracted {len(text_content)} characters")
        
        return Response({
            'success': True,
            'content': text_content
        })
    except Exception as e:
        logger.error(f"PDF to Word error: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
