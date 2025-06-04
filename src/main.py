import sys
import os
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow
from utils.config import load_config, get_config
from utils.logger import setup_logger

def main():
    # Setup logger
    setup_logger()
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
    load_config(config_path)
    
    # Create necessary directories
    config = get_config()
    os.makedirs(config['download_dir'], exist_ok=True)
    os.makedirs(config['export_dir'], exist_ok=True)
    os.makedirs(config['template_dir'], exist_ok=True)
    os.makedirs(config.get('schema_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schemas')), exist_ok=True)
    os.makedirs(config.get('analytics_dir', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'analytics')), exist_ok=True)
    
    # Start application
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()