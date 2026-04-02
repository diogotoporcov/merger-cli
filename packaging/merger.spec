# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

# Get the project root directory
SPEC_DIR = os.path.dirname(os.path.abspath(SPEC))
ROOT = os.path.abspath(os.path.join(SPEC_DIR, ".."))

datas = [(os.path.join(ROOT, 'src/merger-cli/merger_cli/resources'), 'merger_cli/resources')]
datas += collect_data_files('python_magic_bin')
datas += copy_metadata('merger-cli')
datas += copy_metadata('merger-api')

hiddenimports = ['merger_cli.cli.main', 'pydantic.deprecated.decorator', 'pip', 'setuptools', 'wheel', 'pkg_resources', 'merger_api']
hiddenimports += collect_submodules('pip')
hiddenimports += collect_submodules('setuptools')
hiddenimports += collect_submodules('wheel')
hiddenimports += collect_submodules('pkg_resources')

block_cipher = None

a = Analysis(
    [os.path.join(SPEC_DIR, 'merger_wrapper.py')],
    pathex=[os.path.join(ROOT, 'src/merger-cli'), os.path.join(ROOT, 'src/merger-api')],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['numpy', 'pandas', 'torch', 'torchvision', 'scipy', 'scikit-image', 'nipype', 'nibabel', 'opencv-python-headless', 'PyQt5', 'matplotlib', 'PIL', 'imageio', 'tifffile', 'PyWavelets', 'networkx', 'sympy', 'mpmath', 'lxml', 'cryptography', 'notebook', 'nbconvert', 'jupyter', 'IPython', 'pydoc'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='merger-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
