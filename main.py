from recognition import Recognition 
from interface import Interface 
import PySimpleGUI as sg
import os

class App:
    def __init__(self):
        try:
            path_images = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces')  # Pasta onde fica as imagens das pessoas conhecidas
            save_path_unrecognized = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'unrecognized_faces')  # Pasta onde as imagens de desconhecidos serão salvas
            save_path_recognized = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recognized_faces') # Pasta onde as imagens de conhecidos serão salvase
                    
            self.recognition = Recognition(path_images = path_images, save_path_recognized = save_path_recognized, save_path_unrecognized = save_path_unrecognized)
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