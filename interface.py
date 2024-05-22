import PySimpleGUI as sg
import os
import cv2 as cv
import logging
import time
import json
import csv
import uuid
import shutil
from screeninfo import get_monitors
import numpy as np
from recognition import Recognition
from pathlib import Path

class Interface:
    def __init__(self):
        home_dir = Path.home()
        log_file = home_dir / 'face_attendance_logs' / 'interface.log'
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(filename=str(log_file), level=logging.ERROR, 
                            format='%(asctime)s:%(levelname)s:%(message)s')

        if not self.init_variable_path():
            sg.PopupError("Erro ao carregar as pastas do projeto!")
            logging.error("Erro ao carregar as pastas do projeto!")
            return
        
        if not self.init_variables():
            sg.PopupError("Erro ao inicializar as variáveis!")
            logging.error("Erro ao inicializar as variáveis!")
            return
        
        if not self.init_recognition_class():
            sg.PopupError("Erro ao inicializar a interface de reconhecimento!")
            logging.error("Erro ao inicializar a interface de reconhecimento!")
            return
        
        if not self.init_persons():
            sg.PopupError("Erro ao inicializar as informações das pessoas!")
            logging.error("Erro ao inicializar as informações das pessoas!")
            return
        
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
        
    def run(self):
        while True:
            self.module_functions()
            event, values = self.window.read(timeout=5)
            if self.verify_window_event(event, values):
                break
        self.cleanup_resources()

    def init_recognition_class(self):
        try:
            self.recognition = Recognition(
                path_faces=self.PATH_FACES, 
                save_path_recognized=self.SAVE_PATH_RECOGNIZED, 
                save_path_unrecognized=self.SAVE_PATH_UNRECOGNIZED
            )
            return True
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar o módulo de reconhecimento: {str(e)}")
            logging.error(f"Erro ao inicializar o módulo de reconhecimento: {str(e)}")
            return False
        
    def init_variable_path(self):
        try:
            self.PATH_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')  # Pasta onde fica as imagens das pessoas conhecidas
            self.PATH_FACES = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces')  # Pasta onde fica as imagens das pessoas conhecidas
            self.SAVE_PATH_RECOGNIZED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognized_faces') # Pasta onde as imagens de conhecidos serão salvase
            self.SAVE_PATH_UNRECOGNIZED = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unrecognized_faces')  # Pasta onde as imagens de desconhecidos serão salvas
            return True
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar variaveis de path: {str(e)}")
            logging.error(f"Erro ao inicializar variaveis de path: {str(e)}")
            return False
        
    
    def init_persons(self):
        # Verifica se o arquivo persons.json existe e inicializa se necessário
        persons_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'persons.json')
        if not os.path.exists(persons_path):
            try:
                with open(persons_path, 'w') as file:
                    json.dump([], file)  # Cria um arquivo JSON vazio
                logging.info("Arquivo persons.json criado com sucesso.")
                return True
            except Exception as e:
                sg.PopupError(f"Erro ao criar o arquivo persons.json: {str(e)}")
                logging.error(f"Erro ao criar o arquivo persons.json: {str(e)}")
                return False
        else:
            logging.info("Arquivo persons.json já existe.")
            return True
        
    def init_variables(self):
        #definição de variaveis
        try:
            self.init_face_recognition = False
            self.full_screen_active = False
            self.full_screen_window = None
            self.camera_permission_error_shown = False
            self.cam_index = 0
            self.current_image_data = None 
            self.image_bytes_camera = None 
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
            [sg.Text('Threshold de Reflexão:', size=(20, 1)), sg.Text('0', key='-REFLECTION-THRESHOLD-')],
            [sg.Button('Abrir Tela Cheia', key='-FULL-SCREEN-CAMERA-')]
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
        )],[sg.Button('Exportar para CSV', key='-EXPORT-TO-CSV-')]]
        
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
            [sg.Button("Selecionar Câmera", key='-CAMERA-SELECT-LIST-'), sg.Button("Atualizar Câmeras", key='-CAMERA-UPDATE-LIST-')],
            [sg.Text("Maxímo de fotos capturadas:"), sg.InputText(self.recognition.MAX_CAPTURES_UNRECOGNIZED, key='-MAX-CAPTURES-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.MAX_CAPTURES_UNRECOGNIZED})")],
            [sg.Text("Interval de captura de imagens:"), sg.InputText(self.recognition.CAPTURE_INTERVAL_UNRECOGNIZED, key='-INTERVAL-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.CAPTURE_INTERVAL_UNRECOGNIZED})")],
            [sg.Text("Expansão de área de captura da imagem:"), sg.InputText(self.recognition.EXPAND_RATIO, key='-EXPAND-RATIO-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.EXPAND_RATIO})")],
            [sg.Text("Texture Threshold:"), sg.InputText(self.recognition.THRESHOLD_TEXTURE, key='-TEXTURE-THRESH-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.THRESHOLD_TEXTURE})")],
            [sg.Text("Reflection Threshold:"), sg.InputText(self.recognition.THRESHOLD_REFLECTION, key='-REFLECTION-THRESH-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.THRESHOLD_REFLECTION})")],
            [sg.Text("Distância Facial para a Camera:"), sg.InputText(self.recognition.FACE_HEIGHT_THRESHOLD, key='-HEIGHT-THRESH-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.FACE_HEIGHT_THRESHOLD})")],
            [sg.Text("Limite de Reconhecimento de Distância Facial:"), sg.InputText(self.recognition.DIS_FACE_ENCODING, key='-DIS-FACE-ENCODING-', size=(10, 1)), sg.Text(f"(Padrão: {self.recognition.DIS_FACE_ENCODING})")],
            [sg.Button("Aplicar Configurações", key='-APPLY-SETTINGS-')]
        ]

        # Nova coluna para cadastro de imagem
        adicionar_imagem_column = [
            [sg.Text("Identificador Único:")],
            [sg.InputText(key='-PERSON-NAME-')],
            [sg.Text("Selecione a Imagem ou Capture:")],
            [sg.InputText(key='-IMAGE-PATH-'), sg.FileBrowse(key='-IMAGE-FILE-'), sg.Button("Capturar", key='-CAPTURE-'), sg.Button("Excluir", key='-IMAGE-BTN-DELETE-')],
            [sg.Image(filename='', key='-IMAGE-PREVIEW-')],
            [sg.Button('<-', key='-IMAGE-BTN-PREV-'), sg.Button('->', key='-IMAGE-BTN-NEXT-')],
            [sg.Button("Salvar Imagem", key='-SAVE-ADD-IMAGE-'), sg.Button("Cancelar", key='-CANCEL-ADD-IMAGE-')]
        ]
        
        layout = [
            [sg.Text('Sistema de Reconhecimento Facial', justification='center', size=(30, 1), font=("Helvetica", 20))],
            [
                sg.Column(
                    [
                        [sg.Button('Iniciar Identificação', key='-INITIALIZE-IDENTIFY-FACES-', size=(15, 2))],
                        [sg.Button('Câmera', key='-LAYOUT-CAM-', size=(15, 2))],
                        [sg.Button('Cadastro Imagem', key='-IMAGE-REGISTRATION-FACE-LIST-', size=(15, 2))],
                        [sg.Button('Lista de Imagens', key='-IMAGES-FACE-LIST-', size=(15, 2))],
                        [sg.Button('Tabela Pessoas Identificadas', key='-TABLE-RECOGNIZED-FACES-', size=(15, 2))],
                        [sg.Button('Configurações', key='-CONFIG-', size=(15, 2))],
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
        try:
            table_data = [[record['name'], record['timestamp_recognized'], record['distance']] for record in self.recognition.recognized_faces]
            self.window['-TABLE-'].update(values=table_data)
        except Exception as e:
            logging.error(f"Error updating table: {str(e)}")
        
    # atualiza a lista de pessoas
    def update_person_list(self):
        try:
            list_data = [[id, name] for id, name in self.recognition.person_name.items()]
            self.window['-LIST-'].update(values=list_data)
        except Exception as e:
            logging.error(f"Error updating person list: {str(e)}")
      
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
        elif event == '-INITIALIZE-IDENTIFY-FACES-':
            if self.init_face_recognition: # Lógica para iniciar ou desligar a identificação de pessoas
                self.init_face_recognition = False
                self.window['-INITIALIZE-IDENTIFY-FACES-'].update(text='Iniciar Identificação')
            else: 
                self.recognition.reload_encodings() # Recarrega os encodes das faces
                time.sleep(0.1)
                self.init_face_recognition = True
                self.window['-INITIALIZE-IDENTIFY-FACES-'].update(text='Parar Identificação')
        elif event == '-FULL-SCREEN-CAMERA-':
            if not self.full_screen_active:
                self.full_screen_active = True
        elif event == '-LAYOUT-CAM-':
            self.updateVisibility('-CAMERA_COL-')
        elif event == '-IMAGE-REGISTRATION-FACE-LIST-':
            self.updateVisibility('-ADD_IMAGE_COL-')
        elif event == '-IMAGES-FACE-LIST-':
            self.update_person_list() # Recarrega os dados da lista de pessoas
            self.updateVisibility('-LIST_IMAGES_COL-')
        elif event == '-TABLE-RECOGNIZED-FACES-':
            self.updateVisibility('-TABLE_COL-')
        elif event == '-CONFIG-':
            self.updateVisibility('-SETTINGS_COL-')
        elif event == '-CAMERA-SELECT-LIST-':
            camera_selection = value['-CAMERA-LIST-']
            if camera_selection:
                # Pega o índice da câmera a partir da seleção
                self.cam_index = int(camera_selection[0].split(" - ")[0])
                self.cap.release()
                self.init_capture_webcam(self.cam_index)
                sg.PopupOK("A câmera foi selecionada!")
        elif event == '-CAMERA-UPDATE-LIST-':
            self.update_list_camera()
        elif event == '-CAPTURE-':
            self.capture_image()
        elif event == '-CANCEL-ADD-IMAGE-':
            self.window['-IMAGE-PREVIEW-'].update(data='')  # Limpar a visualização
            self.captured_image = None  # Resetar a imagem capturada
        elif event == '-SAVE-ADD-IMAGE-':
            person_name = value['-PERSON-NAME-']
            self.save_captured_image(person_name, '-IMAGE-PATH-')
        elif event == '-APPLY-SETTINGS-':
            try:
                max_captures = int(value['-MAX-CAPTURES-'])
                capture_interval = float(value['-INTERVAL-'])
                expand_ratio = float(value['-EXPAND-RATIO-'])
                threshold_texture = float(value['-TEXTURE-THRESH-'])
                threshold_reflection = float(value['-REFLECTION-THRESH-'])
                dis_face_encoding = float(value['-DIS-FACE-ENCODING-'])
                face_height_threshold = float(value['-HEIGHT-THRESH-'])

                self.recognition.setup_parameters(max_captures, capture_interval, expand_ratio, threshold_texture, threshold_reflection, dis_face_encoding, face_height_threshold)
                sg.Popup("Configurações atualizadas com sucesso!")
            except ValueError:
                sg.PopupError("Por favor, insira valores válidos para as configurações.")  
        elif event == '-IMAGE-BTN-NEXT-':
            self.navigate_faces(1)  # Move para a próxima face
        elif event == '-IMAGE-BTN-PREV-':
            self.navigate_faces(-1)  # Move para a face anterior
        elif event == '-IMAGE-BTN-DELETE-':
            self.window['-IMAGE-PREVIEW-'].update(data='')  # Limpa a visualização
            self.detected_faces = []  # Limpa a lista de faces detectadas
        elif event == '-EXPORT-TO-CSV-':
            self.export_table_to_csv(self.window)

        return False
    
    def updateVisibility(self, name):
        columns = ['-CAMERA_COL-', '-TABLE_COL-', '-SETTINGS_COL-', '-ADD_IMAGE_COL-', '-LIST_IMAGES_COL-']
        visibility = [name == col for col in columns]
        for col, vis in zip(columns, visibility):
            self.window[col].update(visible=vis)
    
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
            imgbytes = cv.imencode('.png', img)[1].tobytes()
            self.image_bytes_camera = imgbytes
            texture_threshold = f"{self.recognition.value_round_is_fake_via_texture} ({self.recognition.THRESHOLD_TEXTURE}) - {self.recognition.value_is_fake_via_texture}"
            reflection_threshold = f"{self.recognition.value_round_has_reflection} ({self.recognition.THRESHOLD_REFLECTION}) - {self.recognition.value_has_reflection}"
            self.window['-TEXTURE-THRESHOLD-'].update(f'{texture_threshold}')
            self.window['-REFLECTION-THRESHOLD-'].update(f'{reflection_threshold}')
        self.update_table()
        self.update_camera(camera_open, img)
        if self.full_screen_active:
            if self.full_screen_window:
                self.open_full_screen_camera(update_only=True)
            else:
                self.open_full_screen_camera()
                
    def get_screen_size(self):
        for m in get_monitors():
            return m.width, m.height  # Retorna a resolução do primeiro monitor
        
    def open_full_screen_camera(self, update_only=False):
        screen_width, screen_height = self.get_screen_size()
        if not update_only:
            if not self.full_screen_window:
                layout = [
                    [sg.Image(key='-FULL-IMAGE-CAMERA-', size=(screen_width, screen_height))],
                    [sg.Button('Fechar', size=(10, 1))]
                ]
                self.full_screen_window = sg.Window('Câmera em Tela Cheia', layout, no_titlebar=False, location=(0, 0), resizable=True, finalize=True, keep_on_top=True)
                self.full_screen_window.Maximize()
                self.full_screen_active = True
        if self.full_screen_active and self.full_screen_window:
            if self.image_bytes_camera:
                # Decode the image from the bytes
                frame = cv.imdecode(np.frombuffer(self.image_bytes_camera, np.uint8), cv.IMREAD_COLOR)
                original_height, original_width = frame.shape[:2]
                
                # Calculate the new height maintaining the aspect ratio
                new_height = int(screen_width * (original_height / original_width))
                
                # Resize the frame to the new dimensions
                frame_resized = cv.resize(frame, (screen_width, new_height))
                imgbytes = cv.imencode('.png', frame_resized)[1].tobytes()
                
                # Update the image in the window
                self.full_screen_window['-FULL-IMAGE-CAMERA-'].update(data=imgbytes, size=(screen_width, new_height))
            
            event, values = self.full_screen_window.read(timeout=10)
            if event == sg.WIN_CLOSED or event == 'Fechar':
                self.full_screen_active = False
                self.full_screen_window.close()
                self.full_screen_window = None

    def save_to_json(self, person_name, image_path, unique_id):
        data = {
            "id": unique_id,
            "name": person_name
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

    def capture_image(self):
        try:
            if self.cap.isOpened():
                time.sleep(0.1)  # Pequeno delay para garantir que a câmera esteja pronta
                ret, frame = self.cap.read()
                if ret:
                    self.detected_faces = self.recognition.extract_faces(frame)  # Modificada para extrair múltiplas faces
                    if self.detected_faces:
                        self.current_face_index = 0  # Inicializa com a primeira face
                        self.update_preview(self.current_face_index)
                    else:
                        sg.PopupError("Nenhuma face detectada.")
                else:
                    sg.PopupError("Falha ao capturar imagem da câmera.")
            else:
                sg.PopupError("A câmera não está inicializada.")
        except Exception as e:
            sg.PopupError(f"Erro ao acessar a câmera: {str(e)}")
            logging.error(f"Erro ao acessar a câmera: {str(e)}")
        
    def update_preview(self, index):
        if index < len(self.detected_faces):
            imgbytes = cv.imencode('.png', self.detected_faces[index])[1].tobytes()
            self.current_image_data = imgbytes  # Armazenar os dados da imagem
            self.window['-IMAGE-PREVIEW-'].update(data=imgbytes)
        else:
            self.current_image_data = None
            self.window['-IMAGE-PREVIEW-'].update(data=b'')  # Limpa a visualização se o índice não for válido


    def navigate_faces(self, direction):
        if self.detected_faces:
            self.current_face_index += direction
            self.current_face_index %= len(self.detected_faces)  # Garante um loop cíclico
            self.update_preview(self.current_face_index)

    def save_captured_image(self, person_name, image_path_key):
        if not person_name:
            sg.Popup("Por favor, forneça um nome ou identificador único.")
            return

        unique_id = str(uuid.uuid4())  # Gerar o ID único aqui
        file_name = f"{unique_id}.png"
        file_path = os.path.join(self.PATH_FACES, file_name)

        if self.current_image_data:  # Verifica se há dados de imagem armazenados
            img_array = cv.imdecode(np.frombuffer(self.current_image_data, np.uint8), cv.IMREAD_COLOR)
            cv.imwrite(file_path, img_array)
        elif os.path.isfile(self.window[image_path_key].get()):
            shutil.copy(self.window[image_path_key].get(), file_path)
        else:
            sg.Popup("Por favor, capture uma imagem ou selecione um arquivo.")
            return

        self.save_to_json(person_name, file_path, unique_id)  # Passar o unique_id para incluir no JSON
        sg.Popup("Cadastro salvo com sucesso!")
        self.window['-IMAGE-PREVIEW-'].update(data=b'')  # Limpar a visualização após salvar
        self.window['-PERSON-NAME-'].update('')
        self.current_image_data = None  # Resetar os dados da imagem após salvar
        self.detected_faces = []  # Limpar a lista de faces detectadas

    def export_table_to_csv(self, window):
        table_data = window['-TABLE-'].get() # Recuperar os dados da tabela
        filename = sg.popup_get_file('Salvar como', save_as=True, no_window=True, file_types=(("CSV Files", "*.csv"),), default_extension='.csv')
        
        if filename:
            with open(filename, 'w', newline='', encoding='utf-8') as file: # Abrir o arquivo para escrita
                writer = csv.writer(file, delimiter=';')
                writer.writerow(['Identificador', 'Data e Hora', 'Distancia Facial']) # Escrever o cabeçalho
                writer.writerows(table_data) # Escrever os dados da tabela
            sg.popup('Dados exportados com sucesso!', title='Sucesso')
        else:
            sg.popup('Exportação cancelada.', title='Cancelado')
        
