from recognition import Recognition 
from interface import Interface 

class App:
    def __init__(self):
        self.recognition = Recognition()
        self.interface = Interface(self.recognition)
    
if __name__ == "__main__":
    app = App()