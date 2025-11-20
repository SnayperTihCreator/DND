import base64
import io
from pathlib import Path

from PIL import Image


def compress_image_to_base64(image_path, quality=75, max_width=1200):
    """Сжатие изображения в base64"""
    try:
        with Image.open(image_path) as img:
            # Изменяем размер если нужно
            if max_width and img.width > max_width:
                ratio = max_width / img.width
                new_height = int(img.height * ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            # Конвертируем в RGB если нужно
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Сохраняем с сжатием
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=quality, optimize=True)
          
            return base64.b64encode(buffer.getvalue()).decode('utf-8'), Path(image_path).suffix
    
    except Exception as e:
        print(f"❌ Ошибка сжатия изображения: {e}")
        raise