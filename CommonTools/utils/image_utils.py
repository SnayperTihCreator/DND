import shutil
from pathlib import Path
from PIL import Image
from loguru import logger
from typing import Optional


def validate_and_resize_image(source_path: str, cache_folder: Path, max_size: int = 4096) -> Optional[str]:
    try:
        path_obj = Path(source_path)
        
        if path_obj.parent.resolve() == cache_folder.resolve():
            return str(path_obj.absolute())
        
        with Image.open(source_path) as img:
            width, height = img.size
            
            # Если размер больше максимального, уменьшаем
            if width > max_size or height > max_size:
                logger.info(f"Ресайз изображения: {width}x{height} -> max {max_size}px")
                img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                new_filename = f"resized_{path_obj.name}"
                target_path = cache_folder / new_filename
                
                # Сохраняем уменьшенную копию
                if path_obj.suffix.lower() in ['.jpg', '.jpeg']:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(target_path, "JPEG", quality=90, optimize=True)
                else:
                    img.save(target_path)
                
                return str(target_path.absolute())
            
            # Если размер нормальный, просто КОПИРУЕМ в кэш
            else:
                target_path = cache_folder / path_obj.name
                shutil.copy(source_path, target_path)
                logger.info(f"Файл '{path_obj.name}' скопирован в кэш.")
                return str(target_path.absolute())
    
    except Exception as e:
        logger.error(f"Критическая ошибка при обработке изображения: {e}")
        return None
