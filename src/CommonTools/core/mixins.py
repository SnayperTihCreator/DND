import hashlib
import shutil
from pathlib import Path


class ResourceLoaderMixin:
    assets: Path
    
    def loadTo(self, path: str | Path) -> str:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Source file not found: {path}")
        
        sha256hash = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256hash.update(chunk)
        
        filename = f"{sha256hash.hexdigest()[:16]}{path.suffix}"
        
        dest_path = self.assets / filename
        
        if not dest_path.exists():
            shutil.copy(str(path), str(dest_path))
        
        return filename

__all__ = ["ResourceLoaderMixin"]