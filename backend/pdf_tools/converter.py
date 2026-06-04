import io
import base64
import fitz
from PIL import Image


def pdf_to_images(pdf_file, output_format='PNG', dpi=150):
    pdf_data = pdf_file.read()
    doc = fitz.open(stream=pdf_data, filetype='pdf')
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        
        img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
        
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        
        images.append({
            'page': page_num + 1,
            'data': img_io.getvalue(),
            'width': pix.width,
            'height': pix.height
        })
    
    doc.close()
    pdf_file.seek(0)
    return images


def images_to_pdf(image_files):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader
    
    output_buffer = io.BytesIO()
    page_width, page_height = letter
    c = canvas.Canvas(output_buffer, pagesize=(page_width, page_height))
    
    for img_file in image_files:
        img = Image.open(img_file)
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img_width, img_height = img.size
        
        ratio = min(page_width / img_width, page_height / img_height)
        new_width = img_width * ratio
        new_height = img_height * ratio
        x = (page_width - new_width) / 2
        y = (page_height - new_height) / 2
        
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG', quality=95)
        img_io.seek(0)
        
        c.drawImage(ImageReader(img_io), x, y, width=new_width, height=new_height)
        c.showPage()
    
    c.save()
    output_buffer.seek(0)
    return output_buffer.getvalue()


def pdf_to_word(pdf_file):
    pdf_data = pdf_file.read()
    doc = fitz.open(stream=pdf_data, filetype='pdf')
    text_content = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            text_content.append(f"--- 第 {page_num + 1} 页 ---\n{text}")
    
    doc.close()
    pdf_file.seek(0)
    
    full_text = '\n\n'.join(text_content)
    if not full_text.strip():
        return "无法从PDF中提取文本内容。可能是因为PDF是扫描件或图片形式的PDF。"
    return full_text
