import cv2
import PySimpleGUI as sg
import numpy as np

def main():
    # Inicializa a câmera
    cap = cv2.VideoCapture(0)

    # Verifica se a câmera foi inicializada corretamente
    if not cap.isOpened():
        sg.Popup("Não foi possível abrir a câmera.")
        return

    # Define o layout da janela PySimpleGUI
    layout = [
        [sg.Image(filename='', key='-IMAGE-')],
        [sg.Button('Exit', size=(10, 1))]
    ]

    # Cria a janela
    window = sg.Window('OpenCV Video in PySimpleGUI', layout, location=(800, 400), finalize=True)

    while True:
        ret, frame = cap.read()  # Lê um frame da câmera
        if not ret:
            break
        
        # Redimensiona o frame para se adequar ao tamanho da janela PySimpleGUI
        frame = cv2.resize(frame, (640, 480))
        
        # Converte o frame do formato BGR (do OpenCV) para RGB (para PySimpleGUI)
        imgbytes = cv2.imencode('.png', frame)[1].tobytes()
        
        # Atualiza a imagem na janela PySimpleGUI
        window['-IMAGE-'].update(data=imgbytes)

        event, values = window.read(timeout=20)
        if event == sg.WINDOW_CLOSED or event == 'Exit':
            break

    window.close()
    cap.release()

main()
