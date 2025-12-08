from PySide6.QtCore import QFile, QDir, QFileInfo, QIODevice, QTextStream, QStringConverter


class QRcPath:
    """
    Pathlib-style wrapper для Qt Resources (qrc).
    Использование: QRcPath(":/icons/my_icon.png")
    """
    
    def __init__(self, path: str):
        # Нормализуем слеши, чтобы Qt не тупил
        self._path = path.replace("\\", "/")
        # Убедимся, что путь начинается с двоеточия, если это корень,
        # но позволяем относительные пути для внутренней логики
        if not self._path.startswith(":") and not self._path.startswith("qrc:"):
            # Здесь можно добавить логику, если ты хочешь авто-префикс,
            # но лучше передавать полный путь ":/..."
            pass
    
    def __str__(self):
        return self._path
    
    def __repr__(self):
        return f"QRcPath('{self._path}')"
    
    def __truediv__(self, other):
        if isinstance(other, QRcPath):
            other = other._path
        new_path = f"{self._path.rstrip('/')}/{str(other).lstrip('/')}"
        return QRcPath(new_path)
    
    @property
    def name(self):
        return QFileInfo(self._path).fileName()
    
    @property
    def stem(self):
        return QFileInfo(self._path).baseName()
    
    @property
    def suffix(self):
        return "." + QFileInfo(self._path).suffix()
    
    @property
    def parent(self):
        return QRcPath(QFileInfo(self._path).path())
    
    def exists(self) -> bool:
        return QFileInfo(self._path).exists()
    
    def is_file(self) -> bool:
        return QFileInfo(self._path).isFile()
    
    def is_dir(self) -> bool:
        return QFileInfo(self._path).isDir()
    
    def read_text(self, encoding="Utf8") -> str:
        file = QFile(self._path)
        if not file.open(QIODevice.ReadOnly | QIODevice.Text):
            raise FileNotFoundError(f"Cannot open resource: {self._path}")
        
        stream = QTextStream(file)
        stream.setEncoding(getattr(QStringConverter.Encoding, encoding))
        content = stream.readAll()
        file.close()
        return content
    
    def read_bytes(self) -> bytes:
        file = QFile(self._path)
        if not file.open(QIODevice.ReadOnly):
            raise FileNotFoundError(f"Cannot open resource: {self._path}")
        
        data = file.readAll()
        file.close()
        return data.data()  # Конвертация QByteArray в bytes
    
    def iterdir(self):
        """Генератор, возвращающий объекты QRcPath для содержимого папки."""
        d = QDir(self._path)
        if not d.exists():
            raise NotADirectoryError(f"Resource directory not found: {self._path}")
        
        # Фильтр: без . и ..
        entry_list = d.entryList(QDir.NoDotAndDotDot | QDir.AllEntries)
        
        for entry in entry_list:
            yield self / entry
    
    def open(self, mode="r"):
        if "w" in mode or "a" in mode:
            raise PermissionError("Qt Resources are read-only")
        
        file = QFile(self._path)
        flags = QIODevice.ReadOnly
        if "b" not in mode:
            flags |= QIODevice.Text
        
        if not file.open(flags):
            raise FileNotFoundError(f"Cannot open {self._path}")
        return file
