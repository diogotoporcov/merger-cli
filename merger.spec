# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata

datas = [('src/merger/resources', 'merger/resources')]
datas += collect_data_files('python_magic_bin')
datas += copy_metadata('merger-cli')

hiddenimports = ['merger.cli.main', 'pydantic.deprecated.decorator', 'pip', 'setuptools', 'wheel', 'pkg_resources']
hiddenimports += collect_submodules('pip')
hiddenimports += collect_submodules('setuptools')
hiddenimports += collect_submodules('wheel')
hiddenimports += collect_submodules('pkg_resources')

block_cipher = None

a = Analysis(
    ['merger_wrapper.py'],
    pathex=['src'],
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
