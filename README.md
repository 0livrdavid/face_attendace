
# Face Attendance

Aplicacao em Python para cadastro, captura e reconhecimento de rostos.

## Requisitos

- macOS com Homebrew instalado.
- Python 3.11. O projeto foi validado com Python 3.11.15.
- Camera funcionando e autorizada pelo macOS.
- Ferramentas nativas de compilacao da Apple. Se necessario, instale com:

```sh
xcode-select --install
```

## Instalacao no macOS

Instale as dependencias do sistema usadas pelo Python, Tkinter, OpenCV e `dlib`:

```sh
brew install python@3.11 cmake libpng pkg-config python-tk@3.11
```

Crie o ambiente virtual com Python 3.11:

```sh
/opt/homebrew/bin/python3.11 -m venv .venv
```

Ative o ambiente:

```sh
source .venv/bin/activate
```

Instale as dependencias do projeto:

```sh
python -m pip install -r requirements.txt
```

Valide a instalacao:

```sh
python -c "import cv2, numpy, pandas, PySimpleGUI, screeninfo, face_recognition, dlib, tkinter; print('imports ok')"
```

O resultado esperado e:

```text
imports ok
```

## Observacoes Importantes

- Use Python 3.11 para este projeto. Python 3.14 apresentou falha ao compilar `dlib`.
- O pacote `dlib` esta fixado em `19.24.6` porque essa versao compilou corretamente no macOS com as dependencias acima.
- O pacote `setuptools` esta fixado como `<81` porque `face_recognition_models` ainda depende de `pkg_resources`, removido nas versoes mais recentes.
- `python-tk@3.11` e necessario para o `PySimpleGUI`, que usa `tkinter`.
- `cmake`, `libpng` e `pkg-config` sao necessarios para compilar o `dlib` corretamente no macOS Apple Silicon.

## Uso

Ative o ambiente virtual:

```sh
source .venv/bin/activate
```

Execute a aplicacao:

```sh
python main.py
```

Depois, siga as instrucoes da interface para capturar e reconhecer rostos.

## Configuracao

1. Defina as imagens de rostos nas configuracoes da aplicacao.
2. Verifique se a camera esta funcionando e se o macOS concedeu permissao de camera ao terminal/aplicativo usado.
3. Consulte os arquivos de log do projeto se houver erro durante captura ou reconhecimento.
