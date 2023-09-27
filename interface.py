# Importando biblioteca necessária
import PySimpleGUI as sg

class Interface():
    def __init__(self):
        # Defina o layout da janela
        self.layout = self.def_layout()
        
        # Crie a janela sem permitir redimensionamento
        self.window = sg.Window('Sistema de Reconhecimento Facial - Controle de Presença', self.layout, resizable=False)
        
        # Inicializa a interface
        self.init_interface()
    
    # Defina o layout da janela
    def def_layout(self):
        layout = [
            # Define o título de dentro da janela
            [sg.Text('Sistema de Reconhecimento Facial', justification='center', size=(30, 1), font=("Helvetica", 20))],
            [
                # Cria a tabela e suas colunas, além de personalizar suas características
                sg.Table(values=[['', '', '']], headings=['Nome', 'Data e Hora', 'Status da Presença'],
                        auto_size_columns=False, justification='right', num_rows=20, key='-TABLE-', 
                        col_widths=[20, 20, 20], size=(400, 400)),
                sg.Column(
                    [
                        [sg.Button('Iniciar/Desligar Identificação', size=(15, 2))],
                        [sg.Button('Cadastro de Imagens (Pessoas)', size=(15, 2))],
                        [sg.Button('Exclusão de Imagens (Pessoas)', size=(15, 2))],
                        [sg.Button('Ver Tabela Pessoas Identificadas', size=(15, 2))],
                        [sg.Button('Configurações', size=(15, 2))],
                    ],
                    element_justification='right',
                    vertical_alignment='top',
                )
            ],
        ]
        
        return layout
        
    def init_interface(self):
        while True:
            event, values = self.window.read()

            if event == sg.WIN_CLOSED:
                break
            elif event == 'Iniciar/Desligar Identificação':
                # Lógica para iniciar ou desligar a identificação de pessoas
                pass
            elif event == 'Cadastro de Imagens (Pessoas)':
                # Lógica para o cadastro de imagens (pessoas)
                pass
            elif event == 'Exclusão de Imagens (Pessoas)':
                # Lógica para a exclusão de imagens (pessoas)
                pass
            elif event == 'Ver Tabela Pessoas Identificadas':
                # Lógica para visualizar a tabela das pessoas identificadas
                pass
            elif event == 'Configurações':
                # Lógica para abrir as configurações
                pass
            
        # Feche a janela ao sair
        self.window.close()