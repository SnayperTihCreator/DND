import os
import platform
import sys
import requests
import subprocess
from packaging import version
from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QMessageBox, QProgressDialog

from .version import __version__

REPO = "SnayperTihCreator/DND"


class DownloadThread(QThread):
    progress = Signal(int)
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self._is_cancelled = False
    
    def cancel(self):
        self._is_cancelled = True
    
    def run(self):
        try:
            local_zip = "update.zip"
            r = requests.get(self.url, stream=True, timeout=10)
            r.raise_for_status()
            
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(local_zip, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        f.close()
                        if os.path.exists(local_zip):
                            os.remove(local_zip)
                        return
                    
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size:
                        self.progress.emit(int(downloaded / total_size * 100))
            
            self.finished.emit(local_zip)
        except Exception as e:
            self.error.emit(str(e))


class UpdateManager(QObject):
    def __init__(self, parent_window):
        super().__init__()
        self.parent = parent_window
        self.progress_dialog = None
        self.thread = None
    
    def find_correct_asset(self, assets):
        """Выбирает нужный URL из списка ассетов в зависимости от ОС"""
        current_os = platform.system().lower()  # 'windows' или 'linux'
        
        for asset in assets:
            asset_name = asset["name"].lower()
            if current_os in asset_name and asset_name.endswith(".zip"):
                return asset["browser_download_url"]
        
        return None
    
    def check_for_updates(self, silent=True):
        try:
            response = requests.get(f"https://api.github.com/repos/{REPO}/releases/latest", timeout=5)
            response.raise_for_status()
            data = response.json()
            latest_version = data["tag_name"]
            
            if version.parse(latest_version) > version.parse(__version__):
                download_url = self.find_correct_asset(data.get("assets", []))
                
                if download_url:
                    self.show_update_dialog(latest_version, download_url)
                else:
                    if not silent:
                        QMessageBox.warning(self.parent, "Ошибка",
                                            "Обновление найдено, но подходящий файл для вашей ОС не найден.")
            elif not silent:
                QMessageBox.information(self.parent, "Обновление", "У вас последняя версия!")
        except Exception as e:
            if not silent:
                QMessageBox.critical(self.parent, "Ошибка", f"Не удалось проверить обновления: {e}")
    
    def show_update_dialog(self, ver, url):
        msg = QMessageBox(self.parent)
        msg.setWindowTitle("Доступно обновление")
        msg.setText(f"Найдена новая версия: {ver}\nХотите обновить сейчас?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        if msg.exec() == QMessageBox.Yes:
            self.start_download(url)
    
    def start_download(self, url):
        self.progress_dialog = QProgressDialog("Загрузка обновления...", "Отмена", 0, 100, self.parent)
        self.progress_dialog.setWindowTitle("Обновление")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        
        self.thread = DownloadThread(url)
        
        self.thread.progress.connect(self.progress_dialog.setValue)
        
        self.thread.finished.connect(self.on_download_finished)
        self.thread.error.connect(self.on_download_error)
        
        self.progress_dialog.canceled.connect(self.thread.cancel)
        
        self.thread.start()
    
    def on_download_finished(self, zip_path):
        if self.progress_dialog:
            self.progress_dialog.close()
        self.run_updater(zip_path)
    
    def on_download_error(self, error_msg):
        if self.progress_dialog:
            self.progress_dialog.close()
        QMessageBox.critical(self.parent, "Ошибка загрузки", f"Не удалось скачать обновление:\n{error_msg}")
    
    def run_updater(self, zip_path):
        if getattr(sys, 'frozen', False):
            app_dir = os.path.dirname(sys.executable)
            main_exe = os.path.basename(sys.executable)
            updater_exe = os.path.join(app_dir, "updater.exe")
            
            if not os.path.exists(updater_exe):
                QMessageBox.critical(self.parent, "Ошибка", "Файл updater.exe не найден!")
                return
            
            subprocess.Popen([updater_exe, zip_path, app_dir, main_exe])
            sys.exit()
        else:
            QMessageBox.information(self.parent, "Update",
                                    f"Режим разработки. Файл скачан в: {zip_path}\nВ сборке здесь бы запустился updater.exe")
