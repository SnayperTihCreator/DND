# -*- mode: python ; coding: utf-8 -*-
import pathlib
import sys
import zipfile
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyInstaller.building.build_main import Analysis
    from PyInstaller.building.api import COLLECT, EXE, PYZ

from PyInstaller.log import logger


def get_runtime_binaries():
    base_path = sys.base_prefix
    # Пути, где обычно лежат жирные DLL в Windows-сборках Python
    search_paths = [
        base_path,
        os.path.join(base_path, 'Library', 'bin'),
        os.path.join(base_path, 'DLLs')
    ]
    
    found = []
    # Нам нужны именно эти ребята
    targets = ['libssl-3-x64.dll', 'libcrypto-3-x64.dll']
    
    for p in search_paths:
        for dll in targets:
            full_path = os.path.join(p, dll)
            if os.path.exists(full_path):
                # Кладем и в корень, и в _internal для надежности
                found.append((full_path, '.'))
    return found

SPEC_DIR = SPECPATH
PROJECT_ROOT = os.path.dirname(SPEC_DIR)
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
DISTPATH: str

icon_path = os.path.join(PROJECT_ROOT, 'resource', 'icon.ico')


def buildZipFile(dist: pathlib.Path, dir_name: str):
    folderApp = dist / dir_name
    zipFile = dist / f"{dir_name}.zip"
    if folderApp.exists():
        logger.info("📁 Сборка архива")
        with zipfile.ZipFile(zipFile, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
            for file_path in folderApp.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(folderApp)
                    zipf.write(file_path, arcname)
        logger.info("📁 Архив собран")


a = Analysis(
    [os.path.join(SRC_PATH, 'main.py')],
    pathex=[SRC_PATH, PROJECT_ROOT],
    binaries=get_runtime_binaries(),
    datas=[],
    hiddenimports=["dnd"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'api-ms-win-core-kernel32-legacy-l1-1-1.dll',  # Выкидываем серверный мусор
        'ucrtbase.dll'
    ],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Dnd Table Runner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[icon_path] if os.path.exists(icon_path) else None,
)

updater_a = Analysis(
    [os.path.join(SRC_PATH, 'updater.py')],
    pathex=[SRC_PATH, PROJECT_ROOT],
    binaries=get_runtime_binaries(),
    datas=[],
    hiddenimports=["dnd"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'api-ms-win-core-kernel32-legacy-l1-1-1.dll',  # Выкидываем серверный мусор
        'ucrtbase.dll'
    ],
    noarchive=False,
    optimize=1,
)

updater_pyz = PYZ(updater_a.pure)

exe_options = {}
if sys.platform == 'win32':
    exe_options |= dict(uac_admin=True)

updater_exe = EXE(
    updater_pyz,
    updater_a.scripts,
    [],
    exclude_binaries=True,
    name='updater',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    **exe_options
)

# --- Сборка SERVER ---
server_a = Analysis(
    [os.path.join(SRC_PATH, 'main_server.py')],
    pathex=[SRC_PATH, PROJECT_ROOT],
    binaries=get_runtime_binaries(),
    datas=[],
    hiddenimports=["dnd"],
    hookspath=[],
    runtime_hooks=[],
    excludes=['api-ms-win-core-kernel32-legacy-l1-1-1.dll', 'ucrtbase.dll'],
    noarchive=False,
    optimize=1,
)
server_pyz = PYZ(server_a.pure)

server_exe = EXE(
    server_pyz,
    server_a.scripts,
    [],
    exclude_binaries=True,
    name='DndServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=[icon_path] if os.path.exists(icon_path) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    
    updater_exe,
    updater_a.binaries,
    updater_a.datas,
    
    server_exe,
    server_a.binaries,
    server_a.datas,
    
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Dnd Table',
)

buildZipFile(pathlib.Path(DISTPATH), coll.name)
