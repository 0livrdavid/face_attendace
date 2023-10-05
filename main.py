from recognition import Recognition 
from interface import Interface 
import PySimpleGUI as sg

class App:
    def __init__(self):
        try:
            self.recognition = Recognition()
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