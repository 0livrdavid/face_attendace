import os
from datetime import datetime

import pandas as pd
import numpy as np
import cv2 as cv  # OpenCV para manipulação de imagem e vídeo
import face_recognition as fr  # Para reconhecimento facial

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)

path_images = os.path.join(current_directory, 'faces')  # Pasta onde fica as imagens das pessoas conhecidas
save_path_unrecognized = os.path.join(current_directory, 'unrecognized_faces')  # Pasta onde as imagens de desconhecidos serão salvas
save_path_recognized = os.path.join(current_directory, 'recognized_faces')  # Pasta onde as imagens de conhecidos serão salvas

NAME_CSV = f'Attendance - {datetime.now().strftime("%d%m%Y %H%M")}.csv'

class Recognition:
    def __init__(self, max_captures_unrecognized = 3, capture_interval_unrecognized = 2.0, expand_ratio = 0.25, threshold_texture = 450, threshold_reflection = 180):
        # variaveis de controle
        self.MAX_CAPTURES_UNRECOGNIZED = max_captures_unrecognized # Número máximo de captura de fotos para um rosto desconhecido
        self.CAPTURE_INTERVAL_UNRECOGNIZED = capture_interval_unrecognized # intervalo segundos para captura de fotos
        self.EXPAND_RATIO = expand_ratio # Razão de expansão da imagem do rosto
        self.THRESHOLD_TEXTURE = threshold_texture # Limiar de reconhecimento de veracidade de textura
        self.THRESHOLD_REFLECTION = threshold_reflection # Limiar de reconhecimento de veracidade de reflexão
        
        self.unrecognized_faces = []  # Lista para armazenar informações sobre rostos desconhecidos
        self.last_captured_time = datetime.now()

        self.create_csv_file()
        self.load_images()
        
        # Obter encodings das imagens conhecidas
        self.encodeListKnown = self.findEncodings(self.images)
        
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
        csv_path = os.path.join(os.getcwd(), 'attendance', NAME_CSV)
        self.df = pd.DataFrame(list())
        self.df.to_csv(csv_path)
        
    def is_image_file(self, filename):
        # Lista das extensões permitidas
        allowed_extensions = ['.jpg', '.jpeg', '.png']

        # Pega a extensão do arquivo
        extension = os.path.splitext(filename)[1].lower()
        print(os.path.splitext(filename))

        return extension in allowed_extensions
    
     # Carrega as imagens do diretório especificado    
    def load_images(self):
        self.images = []
        self.classNames = []
        myList = os.listdir(path_images)
        print(myList)
        for cl in myList:
            if self.is_image_file(cl):
                try:
                    curImg = cv.imread(f'{path_images}/{cl}')
                    if curImg is None:  # Verifique se a imagem foi carregada corretamente
                        print(f"Erro ao carregar a imagem {cl}. Ela pode estar corrompida.")
                        continue
                    self.images.append(curImg)
                    self.classNames.append(os.path.splitext(cl)[0])
                except Exception as e:
                    print(f"Erro ao carregar a imagem {cl}: {str(e)}")
        print(self.classNames)


    # Função para encontrar encodings das faces nas imagens
    def findEncodings(self, images):
        self.encodeList = []
        for img in images:
            try:
                img = cv.cvtColor(img, cv.COLOR_BGR2RGB)  # Convertendo imagem para RGB
                encode = fr.face_encodings(img)[0]
                self.encodeList.append(encode)
            except Exception as e:
                print(f"Erro ao processar a imagem: {str(e)}")
        print('Encoding Complete')
        return self.encodeList
    
    # Função para marcar a presença de uma pessoa reconhecida
    def markAttendance(self, name):
        with open("attendance/"+NAME_CSV, 'r+') as f:
            myDataList = f.readlines()
            self.nameList = {}
            for line in myDataList:
                entry = line.split(',')
                if len(entry) > 1:  # Certifique-se de que temos pelo menos nome e timestamp
                    self.nameList[entry[0]] = datetime.strptime(entry[1].strip(), '%Y-%m-%d %H:%M:%S')  # Convertendo a string para um objeto datetime

            now = datetime.now()
            dtString = now.strftime('%Y-%m-%d %H:%M:%S')

            # Se a pessoa não foi marcada ainda ou se foi marcada há mais de 2 horas, a presença é registrada
            if name not in self.nameList:
                f.writelines(f'\n{name},{dtString}')
            else:
                last_seen = self.nameList[name]
                time_diff = now - last_seen
                if time_diff.total_seconds() > 2 * 60 * 60:  # 2 horas em segundos
                    f.writelines(f'\n{name},{dtString}')
    
    # Função para checar ou atualizar array de rostos desconhecidos
    def check_or_update_unrecognized(self, face_encoding, _update):
        for value in self.unrecognized_faces:
            matches = fr.compare_faces([value['encoding']], face_encoding)
            if matches[0]:
                if _update:
                    value['count'] += 1
                return value            
        new_face = {'encoding': face_encoding, 'count': 1, 'name': f'Desconhecido{len(self.unrecognized_faces)+1}'}
        self.unrecognized_faces.append(new_face)
        return new_face

    # Função para checar textura de imagem
    def is_fake_via_texture(self, face_image):
        gray = cv.cvtColor(face_image, cv.COLOR_BGR2GRAY)
        v = round(np.var(cv.Laplacian(gray, cv.CV_64F)),2)
        print("texture ",v)
        return v > self.THRESHOLD_TEXTURE

    # Função para checar reflexão de imagem
    def has_reflection(self, face_image):
        hsv = cv.cvtColor(face_image, cv.COLOR_BGR2HSV)
        _, _, v = cv.split(hsv)
        avg_brightness = round(np.mean(v),2)
        print("reflexao ",avg_brightness)
        return avg_brightness > self.THRESHOLD_REFLECTION
    
    # Exibindo o frame atual com as faces destacadas
    def display_results(self, img):
        cv.imshow('Webcam', img)
    
 
    def process_current_frame(self, img):
        imgS = cv.resize(img, (0, 0), None, 0.25, 0.25) # Reduzindo o tamanho da imagem para acelerar o processamento
        imgS = cv.cvtColor(imgS, cv.COLOR_BGR2RGB) # Convertendo imagem para RGB
        
        # Reconhecendo faces no frame atual
        facesCurFrame = fr.face_locations(imgS)
        encodesCurFrame = fr.face_encodings(imgS, facesCurFrame)
        return facesCurFrame, encodesCurFrame
        
    def handle_face_recognition(self, encodeFace, faceLoc, img):
        matches = fr.compare_faces(self.encodeListKnown, encodeFace)
        faceDis = fr.face_distance(self.encodeListKnown, encodeFace)
        matchInRecognition = self.check_or_update_unrecognized(encodeFace,False)
        isUnkwnown = False
        matchIndex = np.argmin(faceDis)
        
        # Se houver uma correspondência, a face é destacada e a presença é marcada
        if matches[matchIndex]:
            name = self.classNames[matchIndex].upper()
            dis = round(faceDis[matchIndex], 2)
            name2 = self.classNames[matchIndex+1].upper()
            dis2 = round(faceDis[matchIndex+1], 2)
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
        print(self.is_fake_via_texture(face_img),self.has_reflection(face_img))
        
        # Se a face é desconhecida, salva a imagem na pasta 'new_img'
        if isUnkwnown:
            current_time = datetime.now()
            
            # Se o rosto ainda não atingiu o limite e o intervalo de tempo for satisfeito
            if matchInRecognition['count'] <= self.MAX_CAPTURES_UNRECOGNIZED and (self.last_captured_time is None or (current_time - self.last_captured_time).total_seconds() > self.CAPTURE_INTERVAL_UNRECOGNIZED):
                matchInRecognition = self.check_or_update_unrecognized(encodeFace, True) # Função para checar ou atualizar array de rostos desconhecidos
                
                face_img = img[max(0, int(y1 - (y2 - y1) * self.EXPAND_RATIO)):min(img.shape[0], int(y2 + (y2 - y1) * self.EXPAND_RATIO)), max(0, int(x1 - (x2 - x1) * self.EXPAND_RATIO)):min(img.shape[1], int(x2 + (x2 - x1) * self.EXPAND_RATIO))]  # Capturando apenas a área da face
                filename = os.path.join(save_path_unrecognized, f"{matchInRecognition['name']}.{matchInRecognition['count']} - {current_time.strftime('%Y-%m-%d_%H-%M-%S')}.jpg") 
                print(f"Salvando {filename}...")
                self.save_image(filename, face_img) # salva imagem
                
                self.last_captured_time = current_time # Atualizando o tempo de captura
        
        self.markAttendance(name)
        
    def save_image(self, path, image):
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except OSError:
                print(f"Erro ao criar o diretório {directory}.")
                return False

        try:
            cv.imwrite(path, image)
            return True
        except Exception as e:
            print(f"Erro ao salvar a imagem {path}: {str(e)}")
            return False


    def init_face_recognition(self, img):
        facesCurFrame, encodesCurFrame = self.process_current_frame(img)

        # Comparando faces reconhecidas com faces conhecidas
        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            self.handle_face_recognition(encodeFace, faceLoc, img)

        # Exibindo o frame atual com as faces destacadas
        #self.display_results(img)
        pass