import base64
import io
from pathlib import Path
from typing import Optional

from PIL import Image
from loguru import logger
logger = logger.bind(module="UTILS")


def compress_image_to_base64(image_path, quality=75, max_width=None):
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
        logger.opt(exception=True).error("Ошибка сжатия изображения")
        raise


def validate_and_resize_image(source_path: str, cache_folder: Path, max_size: int = 4096) -> Optional[str]:
    """
    Проверяет и уменьшает изображение.
    Возвращает путь к файлу (оригинал или кэш).
    Возвращает None, если произошла ошибка (файл битый, памяти не хватило и т.д.).
    """
    try:
        path_obj = Path(source_path)
        
        with Image.open(source_path) as img:
            width, height = img.size
            
            # 1. Если размер ок — возвращаем оригинал
            if width <= max_size and height <= max_size:
                return source_path
            
            logger.info(f"Ресайз изображения: {width}x{height} -> max {max_size}px")
            
            # 2. Пытаемся уменьшить
            # Image.Resampling.LANCZOS дает лучшее качество, но жрет память.
            # Если карта огромная (10к+), тут может вылететь MemoryError -> попадем в except
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
            new_filename = f"resized_{max_size}_{path_obj.name}"
            target_path = cache_folder / new_filename
            
            # 3. Сохраняем
            if path_obj.suffix.lower() in ['.jpg', '.jpeg']:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(target_path, "JPEG", quality=90, optimize=True)
            else:
                img.save(target_path)
            
            return str(target_path.absolute())
    
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке изображения: {e}")
        return None  # Возвращаем None, чтобы показать ошибку в UI