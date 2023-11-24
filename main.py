from interface import Interface 
import PySimpleGUI as sg

class App:
    def __init__(self):
        try:
            self.interface = Interface()
        except Exception as e:
            sg.PopupError(f"Erro ao inicializar a interface: {str(e)}")
            return
    
if __name__ == "__main__":
    app = App()
    app.interface.run()