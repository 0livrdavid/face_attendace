# Importando bibliotecas necessárias
import os
from datetime import datetime

import pandas as pd
import numpy as np
import cv2  # OpenCV para manipulação de imagem e vídeo
import face_recognition as fr  # Para reconhecimento facial

# Caminho onde as imagens para reconhecimento estão armazenadas
path = r'/Users/davidoliveira/Documents/attendace/img'  # Atualize isso para o caminho correto
save_path = r'/Users/davidoliveira/Documents/attendace/new_img/'  # Pasta onde as imagens de desconhecidos serão salvas
unrecognized_faces = []  # Lista para armazenar informações sobre rostos desconhecidos
last_captured_time = datetime.now()

MAX_CAPTURES = 3  # Número máximo de fotos para um rosto desconhecido
CAPTURE_INTERVAL = 2.000  # intervalo segundos
EXPAND_RATIO = 0.25  # Razão de expansão da imagem do rosto
THRESHOLD_TEXTURE = 400  # Limiar de reconhecimento de veracidade de textura
THRESHOLD_REFLECTION = 160  # Limiar de reconhecimento de veracidade de reflexão
NAME_CSV = f'Attendance - {last_captured_time.strftime("%d%m%Y %H%M")}.csv'

class App:
    def __init__(self):
        global unrecognized_faces, last_captured_time

        self.create_csv_file()
        self.load_images()
        
        # Obter encodings das imagens conhecidas
        self.encodeListKnown = self.findEncodings(self.images)
        
        # Iniciar captura de vídeo da webcam
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Erro ao abrir a câmera!")
            return

        
        self.init_face_recognition()
    
    # Cria um novo arquivo CSV vazio.
    def create_csv_file(self):
        csv_path = os.path.join(os.getcwd(), 'attendance', NAME_CSV)
        self.df = pd.DataFrame(list())
        self.df.to_csv(csv_path)
    
     # Carrega as imagens do diretório especificado    
    def load_images(self):
        self.images = []
        self.classNames = []
        myList = os.listdir(path)
        print(myList)
        for cl in myList:
            if cl != ".DS_Store":
                curImg = cv2.imread(f'{path}/{cl}')
                self.images.append(curImg)
                self.classNames.append(os.path.splitext(cl)[0])
        print(self.classNames)
        
    # Função para encontrar encodings das faces nas imagens
    def findEncodings(self, images):
        self.encodeList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convertendo imagem para RGB
            encode = fr.face_encodings(img)[0]
            self.encodeList.append(encode)
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
        for value in unrecognized_faces:
            matches = fr.compare_faces([value['encoding']], face_encoding)
            if matches[0]:
                if _update:
                    value['count'] += 1
                return value            
        new_face = {'encoding': face_encoding, 'count': 1, 'name': f'Desconhecido{len(unrecognized_faces)+1}'}
        unrecognized_faces.append(new_face)
        return new_face

    # Função para checar textura de imagem
    def is_fake_via_texture(self, face_image):
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        v = round(np.var(cv2.Laplacian(gray, cv2.CV_64F)),2)
        print("texture ",v)
        return v > THRESHOLD_TEXTURE

    # Função para checar reflexão de imagem
    def has_reflection(self, face_image):
        hsv = cv2.cvtColor(face_image, cv2.COLOR_BGR2HSV)
        _, _, v = cv2.split(hsv)
        avg_brightness = round(np.mean(v),2)
        print("reflexao ",avg_brightness)
        return avg_brightness > THRESHOLD_REFLECTION

    def init_face_recognition(self):
        # Loop para processar cada frame do vídeo
        while True:
            success, img = self.cap.read()
            if not success:
                print("Erro ao acessar a webcam!")
                break

            imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Reduzindo o tamanho da imagem para acelerar o processamento
            imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)  # Convertendo imagem para RGB

            # Reconhecendo faces no frame atual
            facesCurFrame = fr.face_locations(imgS)
            encodesCurFrame = fr.face_encodings(imgS, facesCurFrame)

            # Comparando faces reconhecidas com faces conhecidas
            for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
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
                    isUnkwnown = True
                    
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4  # Ajustando as coordenadas para o tamanho original
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 8)
                cv2.rectangle(img, (x1, y2 - 70), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, f"{name} - {dis}", (x1 + 6, y2 - 40), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                cv2.putText(img, f"{name2} - {dis2}", (x1 + 6, y2 - 5), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                
                face_img = img[max(0, int(y1 - (y2 - y1) * EXPAND_RATIO)):min(img.shape[0], int(y2 + (y2 - y1) * EXPAND_RATIO)), max(0, int(x1 - (x2 - x1) * EXPAND_RATIO)):min(img.shape[1], int(x2 + (x2 - x1) * EXPAND_RATIO))]  # Capturando apenas a área da face
                print(self.is_fake_via_texture(face_img),self.has_reflection(face_img))
                
                # Se a face é desconhecida, salva a imagem na pasta 'new_img'
                if isUnkwnown:
                    current_time = datetime.now()
                    
                    # Se o rosto ainda não atingiu o limite e o intervalo de tempo for satisfeito
                    if matchInRecognition['count'] <= MAX_CAPTURES and (last_captured_time is None or (current_time - last_captured_time).total_seconds() > CAPTURE_INTERVAL):
                        timestamp = current_time.strftime('%Y-%m-%d_%H-%M-%S')
                        face_img = img[max(0, int(y1 - (y2 - y1) * EXPAND_RATIO)):min(img.shape[0], int(y2 + (y2 - y1) * EXPAND_RATIO)), max(0, int(x1 - (x2 - x1) * EXPAND_RATIO)):min(img.shape[1], int(x2 + (x2 - x1) * EXPAND_RATIO))]  # Capturando apenas a área da face
                        filename = os.path.join(save_path, f"{matchInRecognition['name']}.{matchInRecognition['count']} - {timestamp}.jpg") 
                        matchInRecognition = self.check_or_update_unrecognized(encodeFace, True)
                        print(f"Salvando {filename}...")
                        cv2.imwrite(filename, face_img) # salva imagem
                        last_captured_time = current_time # Atualizando o tempo de captura
                
                self.markAttendance(name)

            # Exibindo o frame atual com as faces destacadas
            cv2.imshow('Webcam', img)
            
            # Sair do loop se a tecla 'q' for pressionada
            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            
        # Liberando a captura de vídeo e fechando todas as janelas
        self.cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = App()