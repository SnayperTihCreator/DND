# -*- mode: python ; coding: utf-8 -*-
import pathlib
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

from PyInstaller.log import logger

DISTPATH: str


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
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['resource/icon.png'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Dnd Table',
)

buildZipFile(pathlib.Path(DISTPATH), coll.name)
