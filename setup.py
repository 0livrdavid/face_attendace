import os
from setuptools import setup

def gather_data_files(start_dir):
    """ Recupera todos os arquivos e diretórios vazios a partir do diretório inicial. """
    data_files = []
    
    for root, dirs, files in os.walk(start_dir):
        # Adicione todos os arquivos
        for f in files:
            full_path = os.path.join(root, f)
            data_files.append((full_path, root))
        
        # Adicione diretórios vazios
        for d in dirs:
            full_path = os.path.join(root, d)
            if not os.listdir(full_path):
                data_files.append((full_path, root))
                
    return data_files

# Use a função para obter todos os arquivos e diretórios a partir do diretório atual
all_data_files = gather_data_files('.')

# Aqui é o restante do seu código de configuração
face_recognition_path = '/opt/homebrew/lib/python3.11/site-packages/face_recognition'
dlib_path = '/opt/homebrew/lib/python3.11/site-packages/dlib'
face_recognition_models_path = '/opt/homebrew/lib/python3.11/site-packages/face_recognition_models'

setup(
    app=['main.py'],
    data_files=all_data_files + [
        (face_recognition_path, 'face_recognition'),
        (dlib_path, 'dlib'),
        (face_recognition_models_path, 'face_recognition_models')
    ],
    options={
        'py2app': {
            'packages': [
                face_recognition_path,
                dlib_path,
                face_recognition_models_path,
            ],
            'includes': [],
            'excludes': [],
            'argv_emulation': False,
            'plist': {
                'NSCameraUsageDescription': 'Nós usamos a câmera para reconhecimento facial.',
                'CFBundleDisplayName': 'main',
                'CFBundleIconFile': 'icon-windowed.icns',
                'NSHighResolutionCapable': 'True'
            }
        }
    },
    setup_requires=['py2app'],
)
