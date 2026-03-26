import logging
from pathlib import Path
from typing import Optional

import aiofiles
import aiohttp
from psygnal import Signal

logger = logging.getLogger(__name__)


class FileTransferManager:
    """
    Manages both downloading and uploading files via HTTP.
    This class encapsulates all aiohttp logic for file transfers.
    """
    download_progress = Signal(str, int)  # file_id, percent
    file_downloaded = Signal(str, Path)  # file_id, local_path
    
    upload_progress = Signal(str, int)  # path, percent
    file_uploaded = Signal(str, str)  # path, remote_url
    
    transfer_failed = Signal(str, str)  # path, error_message
    
    def __init__(self):
        self.active_downloads: set[str] = set()
    
    def is_download(self, file_id: str) -> bool:
        return file_id in self.active_downloads
    
    async def download_file(self, url: str, local_path: Path, uid: str):
        """Downloads a file from a given URL to a local path."""
        file_id = local_path.name
        logger.info("Starting download: %s -> %s", url, local_path)
        headers = {"X-User-ID": uid}
        try:
            self.active_downloads.add(file_id)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    response.raise_for_status()
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    local_path.parent.mkdir(parents=True, exist_ok=True)
                    async with aiofiles.open(local_path, 'wb') as file:
                        while True:
                            chunk = await response.content.read(64 * 1024)
                            if not chunk: break
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                percent = int(downloaded / total_size * 100)
                                self.download_progress.emit(file_id, percent)
            
            self.file_downloaded.emit(file_id, local_path)
            logger.info("File downloaded successfully: %s", local_path)
        
        except Exception as e:
            error_msg = f"Download failed for URL {url}: {e}"
            logger.exception(error_msg)
            self.transfer_failed.emit(file_id, error_msg)
        
        finally:
            self.active_downloads.remove(file_id)
    
    async def upload_file(self, local_path: Path, upload_url: str, uid: str) -> Optional[str]:
        """Uploads a local file to the specified URL."""
        filename = local_path.name
        logger.info("Attempting to upload file %s to %s", local_path, upload_url)
        
        headers = {"X-User-ID": uid}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with aiofiles.open(local_path, 'rb') as file:
                    data = aiohttp.FormData()
                    data.add_field('file', file, filename=filename)
                    async with session.post(upload_url, data=data, headers=headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        remote_url = result.get('url')
                        logger.info("File uploaded successfully: %s -> %s", filename, remote_url)
                        self.file_uploaded.emit(filename, remote_url)
                        return remote_url
        except Exception as e:
            error_msg = f"Upload failed for file {filename}: {e}"
            logger.exception(error_msg)
            self.transfer_failed.emit(filename, error_msg)
            return None
