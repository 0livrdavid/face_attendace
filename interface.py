# Importando biblioteca necessária
import PySimpleGUI as sg
import cv2 as cv  # OpenCV para manipulação de imagem e vídeo

class Interface():
    def __init__(self, recognition_instance):
        # Define uma variável para comunicação com a classe de reconhecimento facial
        self.recognition = recognition_instance
        
        self.camera_visible = True
        self.table_visible = False
        self.init_face_recognition = False
        
        # Defina o layout da janela
        self.layout = self.def_layout()
        
        self.window = sg.Window('Sistema de Reconhecimento Facial - Controle de Presença', self.layout, resizable=True, finalize=True)
        
        # Inicializa a interface
        self.init_interface()
        
    
    # Defina o layout da janela
    def def_layout(self):
        layout = [
            [sg.Text('Sistema de Reconhecimento Facial', justification='center', size=(30, 1), font=("Helvetica", 20))],
            [
                sg.Column(
                    [
                        [sg.Button('Iniciar/Desligar Identificação', size=(15, 2))],
                        [sg.Button('Cadastro de Imagens (Pessoas)', size=(15, 2))],
                        [sg.Button('Exclusão de Imagens (Pessoas)', size=(15, 2))],
                        [sg.Button('Ver Tabela Pessoas Identificadas', size=(15, 2))],
                        [sg.Button('Configurações', size=(15, 2))],
                    ],
                    element_justification='right',
                    vertical_alignment='top',
                ),
                sg.Image(filename='', key='-CAMERA-', size=(640, 480)),
                sg.Table(values=[['', '', '']], headings=['Nome', 'Data e Hora', 'Status da Presença'],
                        auto_size_columns=False, justification='right', num_rows=20, key='-TABLE-', 
                        col_widths=[20, 20, 20], visible=False),
            ],
        ]
        
        return layout
    
    def init_capture_webcam(self):
        # Iniciar captura de vídeo da webcam
        self.cap = cv.VideoCapture(0)
        if not self.cap.isOpened():
            print("Erro ao abrir a câmera!")
            return
        
    def cleanup_resources(self):
        self.cap.release()
        cv.destroyAllWindows()
        
    def init_interface(self):
        self.init_capture_webcam()
        
        # Verifica se a câmera foi inicializada corretamente
        if not self.cap.isOpened():
            sg.Popup("Não foi possível abrir a câmera.")
            return
        
        while True:
            success, img = self.cap.read()
            if not success:
                print("Erro ao acessar a webcam!")
                break
            
            if self.init_face_recognition:
                self.recognition.init_face_recognition(img)
            
            # Converte o frame do formato BGR (do OpenCV) para RGB (para PySimpleGUI)
            frame = cv.resize(img, (640, 480))
            self.imgbytes = cv.imencode('.png', frame)[1].tobytes()
            self.window['-CAMERA-'].update(data=self.imgbytes)
            
            event, values = self.window.read(timeout=5)
            if event == sg.WIN_CLOSED:
                break
            elif event == 'Iniciar/Desligar Identificação':
                # Lógica para iniciar ou desligar a identificação de pessoas
                if self.init_face_recognition:
                    self.init_face_recognition = False
                else: 
                    self.init_face_recognition = True
                pass
            elif event == 'Cadastro de Imagens (Pessoas)':
                # Lógica para o cadastro de imagens (pessoas)
                pass
            elif event == 'Exclusão de Imagens (Pessoas)':
                # Lógica para a exclusão de imagens (pessoas)
                pass
            elif event == 'Ver Tabela Pessoas Identificadas':
                if self.table_visible == True:
                    self.table_visible = False
                    self.window['-TABLE-'].update(visible=False)
                    
                    self.camera_visible = True
                    self.window['-CAMERA-'].update(visible=True)
                elif self.table_visible == False:
                    self.table_visible = True
                    self.window['-TABLE-'].update(visible=True)
                    
                    self.camera_visible = False
                    self.window['-CAMERA-'].update(visible=False)
                pass
            elif event == 'Configurações':
                # Lógica para abrir as configurações
                pass
            
        # Feche a janela ao sair
        self.window.close()
        self.cleanup_resources()