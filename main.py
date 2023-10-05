from recognition import Recognition 
from interface import Interface 
import PySimpleGUI as sg
import os

class App:
    def __init__(self):
        try:
            self.recognition = Recognition()
            
            path_images = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces')  # Pasta onde fica as imagens das pessoas conhecidas
            save_path_unrecognized = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unrecognized_faces')  # Pasta onde as imagens de desconhecidos serão salvas
            save_path_recognized = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognized_faces') # Pasta onde as imagens de conhecidos serão salvas
            
            for path in [path_images, save_path_unrecognized, save_path_recognized]:
                if not os.path.exists(path):
                    os.makedirs(path)
            
            self.recognition.PATH_IMAGES = path_images
            self.recognition.SAVE_PATH_UNRECOGNIZED = save_path_unrecognized
            self.recognition.SAVE_PATH_RECOGNIZED = save_path_recognized
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar o reconhecimento facial: {str(e)}")
            return
        
        try:
            self.interface = Interface(self.recognition)
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar a interface: {str(e)}")
            return
    
if __name__ == "__main__":
    app = App()