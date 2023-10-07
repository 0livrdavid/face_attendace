# Importando biblioteca necessária
import PySimpleGUI as sg
import os
import cv2 as cv  # OpenCV para manipulação de imagem e vídeo
from recognition import Recognition 

class Interface():
    def __init__(self):
        init_variable_path = self.init_variable_path()
        if not init_variable_path:
            sg.PopupError("Erro ao carregar as pastas do projeto!")
            return
        
        init_variables = self.init_variables()
        if not init_variables:
            sg.PopupError("Erro ao carregar as pastas do projeto!")
            return
    
        self.layout = self.def_layout() # Defina o layout da janela
        if self.layout is None:
            sg.PopupError("Erro ao carregar o layout!")
            return
        
        self.window = sg.Window('Sistema de Reconhecimento Facial - Controle de Presença', self.layout, resizable=True, finalize=True)
        if self.window is None:
            sg.PopupError("Erro ao carregar o layout!")
            return

        self.init_interface() # Inicializa a interface
        
    def init_variable_path(self):
        try:
            self.PATH_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')  # Pasta onde fica as imagens das pessoas conhecidas
            self.PATH_IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces')  # Pasta onde fica as imagens das pessoas conhecidas
            self.SAVE_PATH_RECOGNIZED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognized_faces') # Pasta onde as imagens de conhecidos serão salvase
            self.SAVE_PATH_UNRECOGNIZED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unrecognized_faces')  # Pasta onde as imagens de desconhecidos serão salvas
            return True
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar variaveis de path: {str(e)}")
            return False
        
    def init_variables(self):
        #definição de variaveis
        try:
            self.init_face_recognition = False
            self.camera_permission_error_shown = False
            self.cam_index = 0

            self.placeholder_img = cv.imread(f'{self.PATH_SRC}/placeholder.png')
            if self.placeholder_img is None:
                sg.PopupError("Erro ao carregar a imagem placeholder!")
                return False
            return True
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar variaveis: {str(e)}")
            return False
    
    # Define o layout da janela
    def def_layout(self):
        camera_column = [[sg.Image(
            filename='', 
            key='-CAMERA-', 
            size=(640, 480)
        )]]
        table_column = [[sg.Table(
            values=[['', '', '']], 
            headings=['Nome', 'Data e Hora'], 
            auto_size_columns=False, 
            justification='right', 
            num_rows=20, 
            key='-TABLE-', 
            col_widths=[20, 20, 20], 
            size=(640, 480)
        )]]
        settings_column = [
            [sg.Text("Selecione uma câmera")],
            [sg.Listbox(
                values=[f"{index} - {name}" for index, name in self.list_cameras()], 
                size=(30, 10), 
                key='-CAMERA-LIST-', 
                enable_events=True)
            ],
            [sg.Button("Selecionar Câmera"),sg.Button("Atualizar Câmeras")]
        ]
        
        layout = [
            [sg.Text('Sistema de Reconhecimento Facial', justification='center', size=(30, 1), font=("Helvetica", 20))],
            [
                sg.Column(
                    [
                        [sg.Button('Iniciar Identificação', size=(15, 2))],
                        [sg.Button('Câmera', size=(15, 2))],
                        [sg.Button('Cadastro de Imagem (Pessoas)', size=(15, 2))],
                        [sg.Button('Exclusão de Imagem (Pessoas)', size=(15, 2))],
                        [sg.Button('Ver Tabela Pessoas Identificadas', size=(15, 2))],
                        [sg.Button('Configurações', size=(15, 2))],
                    ],
                    element_justification='right',
                    vertical_alignment='top',
                ),
                sg.Column(camera_column, key='-CAMERA_COL-', size=(640, 480)),
                sg.Column(table_column, key='-TABLE_COL-', visible=False, size=(640, 480)),
                sg.Column(settings_column, key='-SETTINGS_COL-', visible=False, size=(640, 480)),
            ],
        ]
        return layout
        
    # inicializa a camera pelo index
    def init_capture_webcam(self, camera_index=0):
        try:
            self.cap = cv.VideoCapture(camera_index)
            if not self.cap.isOpened():
                self.update_camera(False, self.placeholder_img)
                return False
            return True
        except Exception as e:
            sg.PopupError(f"Ocorreu um erro: {str(e)}")
            self.update_camera(False, self.placeholder_img)
            return False

    # lista as cameras
    def list_cameras(self):
        try:
            cameras = []
            for index in range(5):
                cap = cv.VideoCapture(index)
                if cap.read()[0]:
                    cameras.append((index, f"Camera {index}"))
                cap.release()
            return cameras
        except Exception as e:
            sg.PopupError(f"Ocorreu um erro: {str(e)}")
            return False
        
    # atualiza a tabela
    def update_table(self):
        table_data = [[record['name'], record['timestamp']] for record in self.recognition.recognized_faces]
        self.window['-TABLE-'].update(values=table_data)
      
    # atualiza a lista de cameras
    def update_list_camera(self):
        try:
            camera_data = [f"{index} - {name}" for index, name in self.list_cameras()]
            self.window['-CAMERA-LIST-'].update(values=camera_data)
            sg.PopupOK("As câmeras foram atualizadas!")
        except Exception as e:
            sg.PopupError(f"Ocorreu um erro ao atualizar a lista de câmeras: {str(e)}")

    # Converte o frame do formato BGR (do OpenCV) para RGB (para PySimpleGUI)    
    def update_camera(self, open, img):
        frame = cv.resize(img, (640, 480))
        self.imgbytes = cv.imencode('.png', frame)[1].tobytes()
        self.window['-CAMERA-'].update(data=self.imgbytes)
        
        if open:
            self.camera_permission_error_shown = False
        elif not open and not self.camera_permission_error_shown:
            self.camera_permission_error_shown = True
            sg.PopupError("Erro ao acessar a câmera. Por favor, verifique se a permissão da câmera está concedida nas configurações do sistema. Se o erro persistir reinicie o software")

    # limpa todos os recursos
    def cleanup_resources(self):
        self.window.close()
        self.cap.release()
        cv.destroyAllWindows()
        
    # verifica os eventos das janelas
    def verify_window_event(self, event, value):
        if event == sg.WIN_CLOSED:
            return True
        elif event == 'Iniciar Identificação':
            # Lógica para iniciar ou desligar a identificação de pessoas
            if self.init_face_recognition:
                self.init_face_recognition = False
                self.window['Iniciar Identificação'].update(text='Iniciar Identificação')
            else: 
                self.init_face_recognition = True
                self.window['Iniciar Identificação'].update(text='Desligar Identificação')
        elif event == 'Câmera':
            self.window['-CAMERA_COL-'].update(visible=True)
            self.window['-TABLE_COL-'].update(visible=False)
            self.window['-SETTINGS_COL-'].update(visible=False)
        elif event == 'Cadastro de Imagens (Pessoas)':
            # Lógica para o cadastro de imagens (pessoas)
            pass
        elif event == 'Exclusão de Imagens (Pessoas)':
            # Lógica para a exclusão de imagens (pessoas)
            pass
        elif event == 'Ver Tabela Pessoas Identificadas':
            self.window['-TABLE_COL-'].update(visible=True)
            self.window['-CAMERA_COL-'].update(visible=False)
            self.window['-SETTINGS_COL-'].update(visible=False)
        elif event == 'Configurações':
            self.window['-SETTINGS_COL-'].update(visible=True)
            self.window['-CAMERA_COL-'].update(visible=False)
            self.window['-TABLE_COL-'].update(visible=False)
        elif event == 'Selecionar Câmera':
            camera_selection = value['-CAMERA-LIST-']
            if camera_selection:
                # Pega o índice da câmera a partir da seleção
                self.cam_index = int(camera_selection[0].split(" - ")[0])
                self.cap.release()
                self.init_capture_webcam(self.cam_index)
                sg.PopupOK("As câmeras foi selecionada!")
        elif event == 'Atualizar Câmeras':
            self.update_list_camera()
            
        return False
    
    # verifica se a camera esta aberta
    def cameraIsOpen(self):
        try:
            if self.cap is not None and self.cap.isOpened():
                success, img = self.cap.read()
                if not success:
                    sg.PopupError("Erro ao acessar a webcam!")
                    return False, img
                return True, img
            else:
                sg.PopupError("Webcam não inicializada!")
                return False, self.placeholder_img
        except Exception as e:
            sg.PopupError(f"Ocorreu um erro: {str(e)}")
            return False, None

    # executa as funções do modulo do while loop
    def module_functions(self):
        self.init_capture_webcam(self.cam_index)
        open, img = self.cameraIsOpen()
        
        # Lógica para iniciar ou desligar a identificação de pessoas
        if open and self.init_face_recognition:
            self.recognition.init_face_recognition(img)
            
        self.update_table()
        
        # Converte o frame do formato BGR (do OpenCV) para RGB (para PySimpleGUI)
        self.update_camera(open, img)
            
    # inicializa a interface
    def init_interface(self):
        self.recognition = Recognition(path_images = self.PATH_IMAGES, save_path_recognized = self.SAVE_PATH_RECOGNIZED, save_path_unrecognized = self.SAVE_PATH_UNRECOGNIZED)
        
        while True:
            # chama as funções necessarias para verificação e validação
            self.module_functions()
            
            event, values = self.window.read(timeout=5)
            if self.verify_window_event(event, values):
                break
            
        # Fechar a janela ao sair
        self.cleanup_resources()