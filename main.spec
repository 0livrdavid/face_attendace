# -*- mode: python ; coding: utf-8 -*-

face_recognition_path = '/opt/homebrew/lib/python3.11/site-packages/face_recognition'
dlib_path = '/opt/homebrew/lib/python3.11/site-packages/dlib'
face_recognition_models_path = '/opt/homebrew/lib/python3.11/site-packages/face_recognition_models'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('faces', 'faces'),
        ('recognized_faces', 'recognized_faces'),
        ('unrecognized_faces', 'unrecognized_faces'),
        ('attendance', 'attendance'),
        (face_recognition_path, 'face_recognition'),
        (dlib_path, 'dlib'),
        (face_recognition_models_path, 'face_recognition_models')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Face Attendance',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='Face Attendance.app',
    icon=None,
    bundle_identifier=None,
    info_plist={
        'NSCameraUsageDescription': 'Nós usamos a câmera para reconhecimento facial.',
        'CFBundleDisplayName': 'main',
        'CFBundleIconFile': 'icon-windowed.icns',
        'NSHighResolutionCapable': 'True',
    },
)
