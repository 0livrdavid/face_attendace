import PySimpleGUI as sg
import os
import cv2 as cv
import logging
import json
import uuid
import shutil
from recognition import Recognition

class Interface:
    def __init__(self):
        logging.basicConfig(filename='app.log', level=logging.ERROR)

        if not self.init_variable_path():
            sg.PopupError("Erro ao carregar as pastas do projeto!")
            logging.error("Erro ao carregar as pastas do projeto!")
            return
        
        if not self.init_variables():
            sg.PopupError("Erro ao carregar as variáveis do projeto!")
            logging.error("Erro ao carregar as variáveis do projeto!")
            return
        
        self.init_interface()
        
        self.layout = self.def_layout()
        if self.layout is None:
            sg.PopupError("Erro ao carregar o layout!")
            logging.error("Erro ao carregar o layout!")
            return
        
        self.window = sg.Window('Sistema de Reconhecimento Facial - Controle de Presença', self.layout, resizable=True, finalize=True)
        if self.window is None:
            sg.PopupError("Erro ao criar a janela!")
            logging.error("Erro ao criar a janela!")
            return

    def init_interface(self):
        self.recognition = Recognition(
            path_images=self.PATH_IMAGES, 
            save_path_recognized=self.SAVE_PATH_RECOGNIZED, 
            save_path_unrecognized=self.SAVE_PATH_UNRECOGNIZED
        )

    def run(self):
        while True:
            self.module_functions()
            event, values = self.window.read(timeout=5)
            if self.verify_window_event(event, values):
                break
        self.cleanup_resources()
        
    def init_variable_path(self):
        try:
            self.PATH_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')  # Pasta onde fica as imagens das pessoas conhecidas
            self.PATH_IMAGES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces')  # Pasta onde fica as imagens das pessoas conhecidas
            self.SAVE_PATH_RECOGNIZED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognized_faces') # Pasta onde as imagens de conhecidos serão salvase
            self.SAVE_PATH_UNRECOGNIZED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unrecognized_faces')  # Pasta onde as imagens de desconhecidos serão salvas
            return True
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar variaveis de path: {str(e)}")
            logging.error(f"Erro ao inicializar variaveis de path: {str(e)}")
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
                logging.error("Erro ao carregar a imagem placeholder!")
                return False
            return True
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar variaveis: {str(e)}")
            logging.error(f"Erro ao inicializar variaveis: {str(e)}")
            return False
    
    # Define o layout da janela
    def def_layout(self):
        camera_column = [
            [sg.Image(filename='', key='-CAMERA-', size=(640, 480))],
            [sg.Text('Threshold de Textura:', size=(20, 1)), sg.Text('0', key='-TEXTURE-THRESHOLD-')],
            [sg.Text('Threshold de Reflexão:', size=(20, 1)), sg.Text('0', key='-REFLECTION-THRESHOLD-')]
        ]
        
        table_column = [[sg.Table(
            values=[['', '', '']], 
            headings=['Nome', 'Data e Hora', 'Distância Facial'], 
            auto_size_columns=False, 
            justification='right', 
            num_rows=20, 
            key='-TABLE-', 
            col_widths=[20, 20, 20], 
            size=(640, 480)
        )]]
        
        list_images_column = [[sg.Table(
            values=[['', '']], 
            headings=['ID', 'Nome'], 
            auto_size_columns=False, 
            justification='right', 
            num_rows=20, 
            key='-LIST-', 
            col_widths=[20, 20, 20], 
            size=(640, 480)
        )]]
        
        settings_column = [
            [sg.Text("Selecione uma câmera")],
            [sg.Listbox(values=[f"{index} - {name}" for index, name in self.list_cameras()], size=(30, 10), key='-CAMERA-LIST-', enable_events=True)],
            [sg.Button("Selecionar Câmera"), sg.Button("Atualizar Câmeras")],
            [sg.Text("Maxímo de fotos capturadas:"), sg.InputText(self.recognition.MAX_CAPTURES_UNRECOGNIZED, key='-MAX-CAPTURES-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.MAX_CAPTURES_UNRECOGNIZED})")],
            [sg.Text("Interval de captura de imagens:"), sg.InputText(self.recognition.CAPTURE_INTERVAL_UNRECOGNIZED, key='-INTERVAL-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.CAPTURE_INTERVAL_UNRECOGNIZED})")],
            [sg.Text("Expansão de área de captura da imagem:"), sg.InputText(self.recognition.EXPAND_RATIO, key='-EXPAND-RATIO-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.EXPAND_RATIO})")],
            [sg.Text("Texture Threshold:"), sg.InputText(self.recognition.THRESHOLD_TEXTURE, key='-TEXTURE-THRESH-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.THRESHOLD_TEXTURE})")],
            [sg.Text("Reflection Threshold:"), sg.InputText(self.recognition.THRESHOLD_REFLECTION, key='-REFLECTION-THRESH-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.THRESHOLD_REFLECTION})")],
            [sg.Button("Aplicar Configurações", key='-APPLY-SETTINGS-')]
        ]

        # Nova coluna para cadastro de imagem
        adicionar_imagem_column = [
            [sg.Text("Nome da Pessoa:")],
            [sg.InputText(key='-PERSON-NAME-')],
            [sg.Text("Selecione a Imagem:")],
            [sg.InputText(), sg.FileBrowse(key='-IMAGE-FILE-')],
            [sg.Button("Salvar Imagem")]
        ]
        
        layout = [
            [sg.Text('Sistema de Reconhecimento Facial', justification='center', size=(30, 1), font=("Helvetica", 20))],
            [
                sg.Column(
                    [
                        [sg.Button('Iniciar Identificação', size=(15, 2))],
                        [sg.Button('Câmera', size=(15, 2))],
                        [sg.Button('Cadastro Imagem', size=(15, 2))],
                        [sg.Button('Lista de Imagens', size=(15, 2))],
                        [sg.Button('Tabela Pessoas Identificadas', size=(15, 2))],
                        [sg.Button('Configurações', size=(15, 2))],
                    ],
                    element_justification='right',
                    vertical_alignment='top',
                ),
                sg.Column(camera_column, key='-CAMERA_COL-', size=(640, 480)),
                sg.Column(table_column, key='-TABLE_COL-', visible=False, size=(640, 480)),
                sg.Column(list_images_column, key='-LIST_IMAGES_COL-', visible=False, size=(640, 480)),
                sg.Column(settings_column, key='-SETTINGS_COL-', visible=False, size=(640, 480)),
                sg.Column(adicionar_imagem_column, key='-ADD_IMAGE_COL-', visible=False, size=(640, 480))
            ],
        ]
        return layout

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
            logging.error(f"Ocorreu um erro: {str(e)}")
            return False
        
    # atualiza a tabela
    def update_table(self):
        table_data = [[record['name'], record['timestamp_recognized'], record['distance']] for record in self.recognition.recognized_faces]
        self.window['-TABLE-'].update(values=table_data)
        
    def update_person_list(self):
        list_data = [[id, name] for id, name in self.recognition.person_name.items()]
        self.window['-LIST-'].update(values=list_data)
      
    # atualiza a lista de cameras
    def update_list_camera(self):
        try:
            camera_data = [f"{index} - {name}" for index, name in self.list_cameras()]
            self.window['-CAMERA-LIST-'].update(values=camera_data)
            sg.PopupOK("As câmeras foram atualizadas!")
        except Exception as e:
            sg.PopupError(f"Ocorreu um erro ao atualizar a lista de câmeras: {str(e)}")
            logging.error(f"Ocorreu um erro ao atualizar a lista de câmeras: {str(e)}")

    # Converte o frame do formato BGR (do OpenCV) para RGB (para PySimpleGUI)    
    def update_camera(self, open, img):
        # Verifica se a imagem é válida
        if img is None or img.size == 0:
            open = False
            img = self.placeholder_img

        # Restante do código para redimensionar e atualizar a imagem...
        # Calcula o novo tamanho mantendo o aspect ratio
        max_width, max_height = 640, 480
        height, width = img.shape[:2]
        scale = min(max_width/width, max_height/height)

        # Redimensiona a imagem proporcionalmente
        new_size = (int(width * scale), int(height * scale))
        frame = cv.resize(img, new_size)

        self.imgbytes = cv.imencode('.png', frame)[1].tobytes()
        self.window['-CAMERA-'].update(data=self.imgbytes)

        if open:
            self.camera_permission_error_shown = False
        elif not open and not self.camera_permission_error_shown:
            self.camera_permission_error_shown = True
            sg.PopupError("Erro ao acessar a câmera. Por favor, verifique se a permissão da câmera está concedida nas configurações do sistema. Se o erro persistir reinicie o software")
            logging.error("Erro ao acessar a câmera")


    # limpa todos os recursos
    def cleanup_resources(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        cv.destroyAllWindows()
        self.window.close()
        
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
                self.window['Iniciar Identificação'].update(text='Parar Identificação')
        elif event == 'Câmera':
            self.window['-CAMERA_COL-'].update(visible=True)
            self.window['-TABLE_COL-'].update(visible=False)
            self.window['-SETTINGS_COL-'].update(visible=False)
            self.window['-ADD_IMAGE_COL-'].update(visible=False)
            self.window['-LIST_IMAGES_COL-'].update(visible=False)
        elif event == 'Cadastro Imagem':
            self.window['-CAMERA_COL-'].update(visible=False)
            self.window['-TABLE_COL-'].update(visible=False)
            self.window['-SETTINGS_COL-'].update(visible=False)
            self.window['-ADD_IMAGE_COL-'].update(visible=True)
            self.window['-LIST_IMAGES_COL-'].update(visible=False)
            pass
        elif event == 'Lista de Imagens':
            self.update_person_list()
            self.window['-CAMERA_COL-'].update(visible=False)
            self.window['-TABLE_COL-'].update(visible=False)
            self.window['-SETTINGS_COL-'].update(visible=False)
            self.window['-ADD_IMAGE_COL-'].update(visible=False)
            self.window['-LIST_IMAGES_COL-'].update(visible=True)
            pass
        elif event == 'Tabela Pessoas Identificadas':
            self.window['-TABLE_COL-'].update(visible=True)
            self.window['-CAMERA_COL-'].update(visible=False)
            self.window['-SETTINGS_COL-'].update(visible=False)
            self.window['-ADD_IMAGE_COL-'].update(visible=False)
            self.window['-LIST_IMAGES_COL-'].update(visible=False)
        elif event == 'Configurações':
            self.window['-SETTINGS_COL-'].update(visible=True)
            self.window['-CAMERA_COL-'].update(visible=False)
            self.window['-TABLE_COL-'].update(visible=False)
            self.window['-ADD_IMAGE_COL-'].update(visible=False)
            self.window['-LIST_IMAGES_COL-'].update(visible=False)
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
        elif event == 'Salvar Imagem':
            person_name = value['-PERSON-NAME-']
            image_file = value['-IMAGE-FILE-']

            if person_name and image_file:
                self.save_to_json(person_name, image_file) # salva o json e a imagem
                sg.Popup("Cadastro salvo com sucesso!")
                self.recognition.reload_encodings()  # Recarrega os encodes das faces
            else:
                sg.Popup("Por favor, preencha todos os campos.")
        elif event == '-APPLY-SETTINGS-':
            try:
                max_captures = int(value['-MAX-CAPTURES-'])
                interval = float(value['-INTERVAL-'])
                expand_ratio = float(value['-EXPAND-RATIO-'])
                texture_thresh = float(value['-TEXTURE-THRESH-'])
                reflection_thresh = float(value['-REFLECTION-THRESH-'])

                self.recognition.setup_parameters(max_captures, interval, expand_ratio, texture_thresh, reflection_thresh)
                sg.Popup("Configurações atualizadas com sucesso!")
            except ValueError:
                sg.PopupError("Por favor, insira valores válidos para as configurações.")            
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
            logging.error(f"Ocorreu um erro: {str(e)}")
            return False, None
        
    # inicializa a camera pelo index
    def init_capture_webcam(self, camera_index=0):
        try:
            self.cap = cv.VideoCapture(camera_index)
            if not self.cap.isOpened():
                self.cap = None
                return False
            return True
        except Exception as e:
            logging.error(f"Erro ao inicializar a webcam {camera_index}: {str(e)}")
            self.cap = None
            return False
        
    def try_open_cameras(self):
        max_cameras = 5  # Define o número máximo de câmeras para testar
        for index in range(max_cameras):
            if self.init_capture_webcam(index):
                return True, self.cameraIsOpen()
        return False, (False, self.placeholder_img)

    def module_functions(self):
        open, (camera_open, img) = self.try_open_cameras()

        if camera_open and self.init_face_recognition:
            self.recognition.init_face_recognition(img)
            # Atualiza os campos de texto com os valores de threshold
            texture_threshold = f"{self.recognition.value_round_is_fake_via_texture} ({self.recognition.THRESHOLD_TEXTURE}) - {self.recognition.value_is_fake_via_texture}"
            reflection_threshold = f"{self.recognition.value_round_has_reflection} ({self.recognition.THRESHOLD_REFLECTION}) - {self.recognition.value_has_reflection}"
            self.window['-TEXTURE-THRESHOLD-'].update(f'{texture_threshold}')
            self.window['-REFLECTION-THRESHOLD-'].update(f'{reflection_threshold}')

        self.update_table()
        self.update_camera(camera_open, img)

    def save_to_json(self, person_name, image_path):
        # Cria um ID único para a entrada
        unique_id = str(uuid.uuid4())
        data = {
            "id": unique_id,
            "name": person_name,
            "image_path": image_path
        }

        # Lê o arquivo JSON existente e adiciona a nova entrada
        try:
            with open('persons.json', 'r+') as file:
                file_data = json.load(file)
                file_data.append(data)
                file.seek(0)
                json.dump(file_data, file, indent=4)
        except FileNotFoundError:
            with open('persons.json', 'w') as file:
                json.dump([data], file, indent=4)

        # (Opcional) Copia a imagem para um diretório específico
        new_image_path = os.path.join(self.PATH_IMAGES, unique_id + os.path.splitext(image_path)[1])
        shutil.copy(image_path, new_image_path)