# packaging/snipperai.spec
#
# PyInstaller spec for SnipperAI (Windows, --onedir build).
#
# Build with (from repo root):
#   uv run pyinstaller packaging/snipperai.spec --distpath dist --workpath build --noconfirm
#
# --onedir (not --onefile) is deliberate: SnipperAI is a background/tray
# app that stays running - onefile re-extracts everything to a temp dir on
# every launch, which adds startup lag for no benefit here.

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# SPECPATH is injected by PyInstaller = the directory containing this file
# (packaging/), so its parent is the repo root.
PROJECT_ROOT = Path(SPECPATH).parent

datas = [
    # The action menu's SVG icons are loaded at runtime via
    # Path(__file__).parent / "icons" (see snipperai/ui/icons.py) -
    # PyInstaller won't bundle non-Python files automatically, so this
    # has to be listed explicitly or the menu icons will be missing
    # from the packaged build even though they work fine from source.
    (str(PROJECT_ROOT / "snipperai" / "ui" / "icons"), "snipperai/ui/icons"),
]

# rapidocr_onnxruntime ships a config.yaml and its ONNX model weights
# alongside its Python code. PyInstaller only traces imports, so none of
# that non-Python data gets pulled in unless explicitly collected here -
# hence "FileNotFoundError: ...\_internal\rapidocr_onnxruntime\config.yaml"
# at runtime even though the build itself completed with no errors.
datas += collect_data_files("rapidocr_onnxruntime")

a = Analysis(
    [str(PROJECT_ROOT / "snipperai" / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="SnipperAI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # background app - no console window
    icon=str(PROJECT_ROOT / "packaging" / "icon.ico"),
    version=str(PROJECT_ROOT / "packaging" / "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="SnipperAI",
)
