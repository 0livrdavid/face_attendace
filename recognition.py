import os
from datetime import datetime, timedelta
import logging
import re
import json
import pandas as pd
import numpy as np
import cv2 as cv  # OpenCV para manipulação de imagem e vídeo
import face_recognition as fr  # Para reconhecimento facial

class Recognition:
    def __init__(self, path_faces, save_path_recognized, save_path_unrecognized, max_captures_unrecognized = 4, capture_interval_unrecognized = 2.0, expand_ratio = 0.25, threshold_texture = 450, threshold_reflection = 180, dis_face_encoding = 0.55, face_height_threshold = 250):
        home_dir = os.path.expanduser('~')
        log_file = os.path.join(home_dir, 'recognition_logs', 'recognition.log')
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        logging.basicConfig(filename=log_file, level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')
        
        # Definição dos caminhos relativos as pastas
        if not self.init_variable_path(path_faces, save_path_recognized, save_path_unrecognized):
            logging.error("Failed to initialize path variables.")
        
        # variaveis de path
        if not self.setup_parameters(max_captures_unrecognized, capture_interval_unrecognized, expand_ratio, threshold_texture, threshold_reflection, dis_face_encoding, face_height_threshold):
            logging.error("Failed to setup parameters.")
        
        if not self.init_variable(): # variaveis de controle
            logging.error("Failed to initialize control variables.")
        
    # Setter para MAX_CAPTURES_UNRECOGNIZED
    def set_MAX_CAPTURES_UNRECOGNIZED(self, max_captures_unrecognized):
        self.MAX_CAPTURES_UNRECOGNIZED = max_captures_unrecognized

    # Setter para CAPTURE_INTERVAL_UNRECOGNIZED
    def set_CAPTURE_INTERVAL_UNRECOGNIZED(self, capture_interval_unrecognized):
        self.CAPTURE_INTERVAL_UNRECOGNIZED = capture_interval_unrecognized

    # Setter para EXPAND_RATIO
    def set_EXPAND_RATIO(self, expand_ratio):
        self.EXPAND_RATIO = expand_ratio

    # Setter para THRESHOLD_TEXTURE
    def set_THRESHOLD_TEXTURE(self, threshold_texture):
        self.THRESHOLD_TEXTURE = threshold_texture

    # Setter para THRESHOLD_REFLECTION
    def set_THRESHOLD_REFLECTION(self, threshold_reflection):
        self.THRESHOLD_REFLECTION = threshold_reflection
        
    # Setter para THRESHOLD_REFLECTION
    def set_THRESHOLD_HEIGHT(self, face_height_threshold):
        self.FACE_HEIGHT_THRESHOLD = face_height_threshold
    
    # Setter para DIS_FACE_ENCODING
    def set_DIS_FACE_ENCODING(self, dis_face_encoding):
        self.DIS_FACE_ENCODING = dis_face_encoding
        
    # Setter para FACE_HEIGHT_THRESHOLD
    def set_FACE_HEIGHT_THRESHOLD(self, face_height_threshold):
        self.FACE_HEIGHT_THRESHOLD = face_height_threshold
        
    def init_variable_path(self, path_faces, save_path_recognized, save_path_unrecognized):
        try:
            self.PATH_FACES = path_faces
            self.SAVE_PATH_RECOGNIZED = save_path_recognized
            self.SAVE_PATH_UNRECOGNIZED = save_path_unrecognized
            return True
        except Exception as e:
            logging.error(f"Error setting path variables: {str(e)}")
            return False
        
    def setup_parameters(self, max_captures=None, capture_interval=None, expand_ratio=None, threshold_texture=None, threshold_reflection=None, dis_face_encoding=None, face_height_threshold=None):
        try:
            if max_captures is not None:
                self.set_MAX_CAPTURES_UNRECOGNIZED(max_captures)
            if capture_interval is not None:
                self.set_CAPTURE_INTERVAL_UNRECOGNIZED(capture_interval)
            if expand_ratio is not None:
                self.set_EXPAND_RATIO(expand_ratio)
            if threshold_texture is not None:
                self.set_THRESHOLD_TEXTURE(threshold_texture)
            if threshold_reflection is not None:
                self.set_THRESHOLD_REFLECTION(threshold_reflection)
            if dis_face_encoding is not None:
                self.set_DIS_FACE_ENCODING(dis_face_encoding)
            if face_height_threshold is not None:
                self.set_FACE_HEIGHT_THRESHOLD(face_height_threshold)
            return True
        except Exception as e:
            logging.error(f"Error setting parameters: {str(e)}")
            return False
            
    def init_variable(self):
        try:
            self.recognized_faces = []  # Lista para armazenar informações sobre rostos conhecidos
            self.unrecognized_faces = []  # Lista para armazenar informações sobre rostos desconhecidos
            self.last_captured_time = datetime.now()
            self.value_has_reflection = False
            self.value_is_fake_via_texture = False
            self.value_round_is_fake_via_texture = 0
            self.value_round_has_reflection = 0
            self.image_count = {}
            self.last_capture_time_recognized = {}
            self.encodeListKnown = []
            self.person_name = {}
            return True
        except Exception as e:
            logging.error(f"Error initializing variables: {str(e)}")
            return False
        
    # verifica se é uma imagem
    def is_image_file(self, filename):
        return re.search(r'\.(jpg|jpeg|png)$', filename, re.IGNORECASE)
    
    # Função para encontrar encodings das faces nas imagens
    def find_encodings(self, images):
        encode_list = []
        for img in images:
            try:
                img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
                encode = fr.face_encodings(img)[0]
                encode_list.append(encode)
            except Exception as e:
                logging.error(f"Erro ao processar a imagem: {str(e)}")
        logging.info('Encoding Complete')
        return encode_list
    
    # Carrega as imagens do diretório especificado    
    def load_and_encode_images(self):
        self.images = []
        self.classNames = []
        try:
            for cl in os.listdir(self.PATH_FACES):
                if self.is_image_file(cl):
                    curImg = cv.imread(f'{self.PATH_FACES}/{cl}')
                    if curImg is not None:
                        self.images.append(curImg)
                        self.classNames.append(os.path.splitext(cl)[0])
                    else:
                        logging.error(f"Erro ao carregar a imagem {cl}.")
        except Exception as e:
            logging.error(f"Erro ao carregar imagens: {str(e)}")
        self.encodeListKnown = self.find_encodings(self.images)
        
    # carrega do json o nome das pessoas
    def load_person_names(self):
        try:
            with open('persons.json', 'r') as file:
                person_data = json.load(file)
            self.person_name = {entry['id']: entry['name'] for entry in person_data}
        except FileNotFoundError:
            self.person_name = {}
    
    # Função para checar ou atualizar array de rostos desconhecidos
    def check_or_update_unrecognized(self, face_encoding, _update):
        #primeira vez identificado
        for value in self.unrecognized_faces:
            matches = fr.compare_faces([value['encoding']], face_encoding)
            if matches[0]:
                if _update:
                    value['count'] += 1
                return value
        # caso não tenha sido identificado ainda
        new_face = {'encoding': face_encoding, 'count': 0, 'name': f'Desconhecido{len(self.unrecognized_faces)+1}'}
        self.unrecognized_faces.append(new_face)
        return new_face

    # Função para checar textura de imagem
    def is_fake_via_texture(self, face_image):
        gray = cv.cvtColor(face_image, cv.COLOR_BGR2GRAY)
        v = round(np.var(cv.Laplacian(gray, cv.CV_64F)),2)
        self.value_is_fake_via_texture = v > self.THRESHOLD_TEXTURE
        self.value_round_is_fake_via_texture = v
        return v > self.THRESHOLD_TEXTURE

    # Função para checar reflexão de imagem
    def has_reflection(self, face_image):
        hsv = cv.cvtColor(face_image, cv.COLOR_BGR2HSV)
        _, _, v = cv.split(hsv)
        avg_brightness = round(np.mean(v),2)
        self.value_has_reflection = avg_brightness > self.THRESHOLD_REFLECTION
        self.value_round_has_reflection = avg_brightness
        return avg_brightness > self.THRESHOLD_REFLECTION
    
    # Processa o frame atual para reconhecer faces armazenadas
    def process_current_frame(self, img):
        imgS = cv.resize(img, (0, 0), None, 0.25, 0.25) # Reduzindo o tamanho da imagem para acelerar o processamento
        imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB) # Convertendo imagem para RGB
        
        # Reconhecendo faces no frame atual
        facesCurFrame = fr.face_locations(imgS)
        encodesCurFrame = fr.face_encodings(imgS, facesCurFrame)
        return facesCurFrame, encodesCurFrame
    
    # Função para marcar a presença de uma pessoa reconhecida
    def mark_attendance(self, name, dis):
        now = datetime.now()
        dtString = now.strftime('%Y-%m-%d %H:%M:%S')

        existing_record = next((record for record in self.recognized_faces if record["name"] == name), None)
        if not existing_record:
            # logica caso a pessoa não foi identificada
            print(f"name: {name}, timestamp_recognized: {dtString}, timestamp: {dtString}, distance: {dis}")
            self.recognized_faces.append({"name": name, "timestamp_recognized": dtString, "timestamp": dtString, 'distance': dis})
        else:
            # logica caso a pessoa ja foi identificada
            last_seen = datetime.strptime(existing_record['timestamp'], '%Y-%m-%d %H:%M:%S')
            time_diff = now - last_seen
            
            # Atualiza o timestamp se a última identificação foi há mais de 2 horas
            if time_diff.total_seconds() > 2 * 60 * 60:  # 2 horas em segundos
                existing_record['timestamp'] = dtString
                
            # Atualiza a distância apenas se o novo valor for menor que o anterior
            if dis < existing_record['distance']:
                existing_record['distance'] = dis
        
    # Logica de processamento reconhecimento de face
    def handle_face_recognition(self, encodeFace, faceLoc, img):
        FACE_COLOR_NEAR = (0, 255, 0)  # Verde para "perto"
        FACE_COLOR_FAR = (0, 0, 255)   # Vermelho para "distante"
        
        current_time = datetime.now()
        matches = fr.compare_faces(self.encodeListKnown, encodeFace)
        faceDis = fr.face_distance(self.encodeListKnown, encodeFace)
        matchInRecognition = self.check_or_update_unrecognized(encodeFace, False)
        isUnknown = False
        matchIndex = np.argmin(faceDis)

        if matches[matchIndex]:
            # Primeiro nome provável
            name = self.person_name.get(self.classNames[matchIndex], "Desconhecido").upper()
            dis = round(faceDis[matchIndex], 2)
        else:
            name = matchInRecognition['name']
            dis = "Unknown"
            isUnknown = True

        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # Ajustando as coordenadas para o tamanho original

        # Estima a distância com base na altura do rosto
        face_height = y2 - y1
        if face_height >= self.FACE_HEIGHT_THRESHOLD:
            color = FACE_COLOR_NEAR
            distance_text = "Perto"
            value_distance_near = True
        else:
            color = FACE_COLOR_FAR
            distance_text = "Distante"
            value_distance_near = False

        # Desenhe os retângulos ao redor da face e os textos
        cv.rectangle(img, (x1, y1), (x2, y2), color, 8)
        cv.rectangle(img, (x1, y2 - 100), (x2, y2), color, cv.FILLED)
        cv.putText(img, f"{name} - {dis}", (x1 + 6, y2 - 70), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
        cv.putText(img, distance_text, (x1 + 6, y2 - 30), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

        # Captura apenas a área da face
        face_img = img[max(0, int(y1 - (y2 - y1) * self.EXPAND_RATIO)):min(img.shape[0], int(y2 + (y2 - y1) * self.EXPAND_RATIO)),
                    max(0, int(x1 - (x2 - x1) * self.EXPAND_RATIO)):min(img.shape[1], int(x2 + (x2 - x1) * self.EXPAND_RATIO))]
        
        # Verificação de textura e reflexão para falsificações
        # Se a face é desconhecida, salva a imagem na pasta
        if not self.is_fake_via_texture(face_img) and not self.has_reflection(face_img):
            if isUnknown:
                if matchInRecognition['count'] <= self.MAX_CAPTURES_UNRECOGNIZED and (
                        self.last_captured_time is None or (current_time - self.last_captured_time).total_seconds() > self.CAPTURE_INTERVAL_UNRECOGNIZED):
                    matchInRecognition = self.check_or_update_unrecognized(encodeFace, True)  # Atualiza array de rostos desconhecidos
                    filename = os.path.join(self.SAVE_PATH_UNRECOGNIZED, f"{matchInRecognition['name']}.{matchInRecognition['count']} - {current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
                    print(f"Salvando {filename}...")
                    self.save_image(filename, face_img)
                    self.last_captured_time = current_time
                    #self.mark_attendance(matchInRecognition['name'], 1.00)
            else:
                if dis != "Unknown" and dis < self.DIS_FACE_ENCODING and value_distance_near:
                    self.mark_attendance(name, dis)
                        
                    # Create a directory for the person if it doesn't exist
                    person_folder = os.path.join(self.SAVE_PATH_RECOGNIZED, name)
                    if not os.path.exists(person_folder):
                        os.makedirs(person_folder)    
                    
                    last_capture_time_recognized = self.last_capture_time_recognized.get(name)
                    if last_capture_time_recognized is None or (current_time - last_capture_time_recognized).total_seconds() > 1:
                        if self.image_count.get(name, 0) < 3:
                            filename = os.path.join(person_folder, f"{name}.{self.image_count.get(name, 0) + 1} - {current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg")
                            self.save_image(filename, face_img)
                            self.image_count[name] = self.image_count.get(name, 0) + 1
                            self.last_capture_time_recognized[name] = current_time
                            print(f"Salvando {filename}...")
        else:
            cv.putText(img, "PHONE DETECTED", (x1 + 6, y2), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    

        
    def save_image(self, path, image):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            cv.imwrite(path, image)
            return True
        except Exception as e:
            logging.error(f"Erro ao salvar a imagem {path}: {str(e)}")
            return False


    def init_face_recognition(self, img):
        facesCurFrame, encodesCurFrame = self.process_current_frame(img)

        # Comparando faces reconhecidas com faces conhecidas
        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            self.handle_face_recognition(encodeFace, faceLoc, img)
        pass
    
    # Recarregar todas as imagens e encodes
    def reload_encodings(self):
        self.load_and_encode_images()
        self.load_person_names()

    def extract_face(self, frame, expand_ratio=0.7):
        # Utilize face_recognition ou OpenCV para detectar faces
        face_locations = fr.face_locations(frame)
        if face_locations:
            top, right, bottom, left = face_locations[0]  # Considera apenas a primeira face detectada
            height = bottom - top
            width = right - left

            # Aplica o EXPAND_RATIO para expandir a área ao redor da face detectada
            expand_height = int(height * expand_ratio)
            expand_width = int(width * expand_ratio)

            # Recalcula os novos pontos de corte com base no EXPAND_RATIO
            new_top = max(0, top - expand_height)
            new_bottom = min(frame.shape[0], bottom + expand_height)
            new_left = max(0, left - expand_width)
            new_right = min(frame.shape[1], right + expand_width)

            # Corta a região expandida da imagem
            expanded_face_area = frame[new_top:new_bottom, new_left:new_right]

            # Redimensiona a imagem para o tamanho máximo de 150x150 pixels
            final_image = cv.resize(expanded_face_area, (300, 300), interpolation=cv.INTER_AREA)
            
            return final_image
        return None
    
    def extract_faces(self, frame, expand_ratio=0.7):
        faces = []
        face_locations = fr.face_locations(frame)
        for top, right, bottom, left in face_locations:
            # Calcula a altura e a largura da face detectada
            height = bottom - top
            width = right - left

            # Aplica o EXPAND_RATIO para expandir a área ao redor da face detectada
            expand_height = int(height * expand_ratio)
            expand_width = int(width * expand_ratio)

            # Recalcula os novos pontos de corte com base no EXPAND_RATIO
            new_top = max(0, top - expand_height)
            new_bottom = min(frame.shape[0], bottom + expand_height)
            new_left = max(0, left - expand_width)
            new_right = min(frame.shape[1], right + expand_width)

            # Corta a região expandida da imagem
            expanded_face_area = frame[new_top:new_bottom, new_left:new_right]

            # Redimensiona a imagem para o tamanho desejado de 300x300 pixels
            resized_face = cv.resize(expanded_face_area, (300, 300), interpolation=cv.INTER_AREA)
            faces.append(resized_face)
        return faces