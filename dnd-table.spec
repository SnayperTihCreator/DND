# -*- mode: python ; coding: utf-8 -*-
import pathlib
import zipfile
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyInstaller.building.build_main import Analysis
    from PyInstaller.building.api import COLLECT, EXE, PYZ

from PyInstaller.log import logger

DISTPATH: str

icon_path = os.path.join('resource', 'icon.ico')


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
    icon=[icon_path] if os.path.exists(icon_path) else None,
)

updater_a = Analysis(
    ["updater.py"],
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

updater_pyz = PYZ(updater_a.pure)

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
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    
    updater_exe,
    updater_a.binaries,
    updater_a.datas,
    
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Dnd Table',
)

buildZipFile(pathlib.Path(DISTPATH), coll.name)
