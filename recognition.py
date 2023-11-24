import os
from datetime import datetime
import logging
import re
import json
import pandas as pd
import numpy as np
import cv2 as cv  # OpenCV para manipulação de imagem e vídeo
import face_recognition as fr  # Para reconhecimento facial

class Recognition:
    def __init__(self, path_images, save_path_recognized, save_path_unrecognized, max_captures_unrecognized = 4, capture_interval_unrecognized = 2.0, expand_ratio = 0.25, threshold_texture = 450, threshold_reflection = 180):
        logging.basicConfig(filename='recognition.log', level=logging.INFO)
        
        # Definição dos caminhos relativos as pastas
        self.setup_paths(path_images, save_path_recognized, save_path_unrecognized)
        
        # variaveis de controle
        self.setup_parameters(max_captures_unrecognized, capture_interval_unrecognized, expand_ratio, threshold_texture, threshold_reflection)
        
        self.recognized_faces = []  # Lista para armazenar informações sobre rostos conhecidos
        self.unrecognized_faces = []  # Lista para armazenar informações sobre rostos desconhecidos
        self.last_captured_time = datetime.now()

        self.load_and_encode_images()# Carrega as imagens do diretório especificado  
        self.encodeListKnown = self.find_encodings(self.images) # Obter encodings das imagens conhecidas
        self.load_person_names() # dicionário onde as chaves são os nomes dos arquivos de imagem
        
    def setup_paths(self, path_images, save_path_recognized, save_path_unrecognized):
        self.PATH_IMAGES = path_images
        self.SAVE_PATH_RECOGNIZED = save_path_recognized
        self.SAVE_PATH_UNRECOGNIZED = save_path_unrecognized
        
    def setup_parameters(self, max_captures=None, interval=None, expand_ratio=None, texture_thresh=None, reflection_thresh=None):
        if max_captures is not None:
            self.MAX_CAPTURES_UNRECOGNIZED = max_captures
        if interval is not None:
            self.CAPTURE_INTERVAL_UNRECOGNIZED = interval
        if expand_ratio is not None:
            self.EXPAND_RATIO = expand_ratio
        if texture_thresh is not None:
            self.THRESHOLD_TEXTURE = texture_thresh
        if reflection_thresh is not None:
            self.THRESHOLD_REFLECTION = reflection_thresh
        self.NAME_CSV = f'Attendance - {datetime.now().strftime("%d%m%Y %H%M")}.csv'

        
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
    
    # Cria um novo arquivo CSV vazio.
    def create_csv_file(self):
        csv_path = os.path.join(os.getcwd(), 'attendance', self.NAME_CSV)
        self.df = pd.DataFrame(list())
        self.df.to_csv(csv_path)
        
    # verifica se é uma imagem
    def is_image_file(self, filename):
        return re.search(r'\.(jpg|jpeg|png)$', filename, re.IGNORECASE)
    
     # Carrega as imagens do diretório especificado    
    def load_and_encode_images(self):
        self.images = []
        self.classNames = []
        try:
            for cl in os.listdir(self.PATH_IMAGES):
                if self.is_image_file(cl):
                    curImg = cv.imread(f'{self.PATH_IMAGES}/{cl}')
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
    
    # Exibindo o frame atual com as faces destacadas
    def display_results(self, img):
        cv.imshow('Webcam', img)
    
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
        matches = fr.compare_faces(self.encodeListKnown, encodeFace)
        faceDis = fr.face_distance(self.encodeListKnown, encodeFace)
        matchInRecognition = self.check_or_update_unrecognized(encodeFace,False)
        isUnkwnown = False
        matchIndex = np.argmin(faceDis)
        
        # Se houver uma correspondência, a face é destacada e a presença é marcada
        if matches[matchIndex]:
            # primeiro nome provavel
            name = self.person_name.get(self.classNames[matchIndex], "Desconhecido").upper()
            dis = round(faceDis[matchIndex], 2)
        
            # segundo nome provavel
            if matchIndex + 1 < len(self.classNames):
                name2 = self.person_name.get(self.classNames[matchIndex+1], "Desconhecido").upper()
            else: 
                name2 = None        
            
            if matchIndex + 1 < len(faceDis):
                dis2 = round(faceDis[matchIndex+1], 2)
            else: 
                dis2 = None
                
        else:
            name = matchInRecognition['name']
            dis = "Unknown"
            isUnkwnown = True
            
        y1, x2, y2, x1 = faceLoc
        y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # Ajustando as coordenadas para o tamanho original
        cv.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 8)
        cv.rectangle(img, (x1, y2 - 70), (x2, y2), (0, 255, 0), cv.FILLED)
        cv.putText(img, f"{name} - {dis}", (x1 + 6, y2 - 40), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
        if matches[matchIndex]:
            cv.putText(img, f"{name2} - {dis2}", (x1 + 6, y2 - 5), cv.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
        
        face_img = img[max(0, int(y1 - (y2 - y1) * self.EXPAND_RATIO)):min(img.shape[0], int(y2 + (y2 - y1) * self.EXPAND_RATIO)), max(0, int(x1 - (x2 - x1) * self.EXPAND_RATIO)):min(img.shape[1], int(x2 + (x2 - x1) * self.EXPAND_RATIO))]  # Capturando apenas a área da face
        self.is_fake_via_texture(face_img)
        self.has_reflection(face_img)
        
        # Se a face é desconhecida, salva a imagem na pasta 'new_img'
        if not self.value_has_reflection and not self.value_is_fake_via_texture:
            if isUnkwnown:
                current_time = datetime.now()
                
                # Se o rosto ainda não atingiu o limite e o intervalo de tempo for satisfeito
                if matchInRecognition['count'] <= self.MAX_CAPTURES_UNRECOGNIZED and (self.last_captured_time is None or (current_time - self.last_captured_time).total_seconds() > self.CAPTURE_INTERVAL_UNRECOGNIZED):
                    matchInRecognition = self.check_or_update_unrecognized(encodeFace, True) # Função para checar ou atualizar array de rostos desconhecidos
                    
                    face_img = img[max(0, int(y1 - (y2 - y1) * self.EXPAND_RATIO)):min(img.shape[0], int(y2 + (y2 - y1) * self.EXPAND_RATIO)), max(0, int(x1 - (x2 - x1) * self.EXPAND_RATIO)):min(img.shape[1], int(x2 + (x2 - x1) * self.EXPAND_RATIO))]  # Capturando apenas a área da face
                    filename = os.path.join(self.SAVE_PATH_UNRECOGNIZED, f"{matchInRecognition['name']}.{matchInRecognition['count']} - {current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg") 
                    print(f"Salvando {filename}...")
                    self.save_image(filename, face_img) # salva imagem
                    
                    self.last_captured_time = current_time # Atualizando o tempo de captura
                    self.mark_attendance(matchInRecognition['name'],1.00)
            else:
                if (dis < 0.45): 
                    self.mark_attendance(name,dis)
        
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

        # Exibindo o frame atual com as faces destacadas
        #self.display_results(img)
        pass
    
    # Recarregar todas as imagens e encodes
    def reload_encodings(self):
        self.load_and_encode_images()
        self.load_person_names()
