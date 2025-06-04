import os
import json
from PyQt5.QtWidgets import QApplication
import qdarktheme

class ThemeManager:
    """Gerencia os temas dark e light da aplicação"""
    
    LIGHT_THEME = "light"
    DARK_THEME = "dark"
    
    def __init__(self, config_path=None):
        self.current_theme = self.LIGHT_THEME
        self.config_path = config_path
        self.load_theme_preference()
    
    def load_theme_preference(self):
        """Carrega a preferência de tema salva"""
        if self.config_path and os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    if 'theme' in config:
                        self.current_theme = config['theme']
            except Exception as e:
                print(f"Erro ao carregar preferência de tema: {str(e)}")
    
    def save_theme_preference(self):
        """Salva a preferência de tema"""
        if self.config_path:
            try:
                config = {}
                if os.path.exists(self.config_path):
                    with open(self.config_path, 'r') as f:
                        config = json.load(f)
                
                config['theme'] = self.current_theme
                
                with open(self.config_path, 'w') as f:
                    json.dump(config, f, indent=4)
            except Exception as e:
                print(f"Erro ao salvar preferência de tema: {str(e)}")
    
    def toggle_theme(self):
        """Alterna entre os temas dark e light"""
        if self.current_theme == self.LIGHT_THEME:
            self.set_theme(self.DARK_THEME)
        else:
            self.set_theme(self.LIGHT_THEME)
        
        return self.current_theme
    
    def set_theme(self, theme):
        """Define o tema da aplicação"""
        self.current_theme = theme
        
        if theme == self.DARK_THEME:
            qdarktheme.setup_theme("dark")
        else:
            qdarktheme.setup_theme("light")
        
        self.save_theme_preference()
        
        return self.current_theme
    
    def get_current_theme(self):
        """Retorna o tema atual"""
        return self.current_theme