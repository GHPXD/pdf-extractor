import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, 
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QLineEdit, QFileDialog, QTextEdit, QComboBox,
                             QProgressBar, QMessageBox, QAction, QToolBar,
                             QStatusBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtWebEngineWidgets import QWebEngineView

from .theme_manager import ThemeManager
from .batch_panel import BatchPanel
from .dashboard_panel import DashboardPanel
from .validation_panel import ValidationPanel

from ..core.downloader import PDFDownloader
from ..core.extractor import PDFExtractor
from ..core.exporter import DataExporter
from ..core.validator import DataValidator
from ..core.document_classifier import DocumentClassifier
from ..utils.config import get_config
from ..utils.language_detector import LanguageDetector

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, task_type, func, *args, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.func = func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.config = get_config()
        self.downloader = PDFDownloader(self.config['download_dir'])
        self.extractor = PDFExtractor()
        self.exporter = DataExporter(self.config['export_dir'])
        self.validator = DataValidator(self.config.get('schema_dir'))
        self.document_classifier = DocumentClassifier(
            model_path=self.config.get('classifier_model_path'),
            patterns_dir=self.config.get('patterns_dir')
        )
        self.language_detector = LanguageDetector()
        
        # Gerenciador de temas
        theme_config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config.json')
        self.theme_manager = ThemeManager(theme_config_path)
        
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("PDF Data Extractor")
        self.setGeometry(100, 100, 1200, 800)
        
        # Configura o tema inicial
        self.theme_manager.set_theme(self.theme_manager.get_current_theme())
        
        # Cria barra de ferramentas
        self.create_toolbar()
        
        # Cria barra de status
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Pronto")
        
        # Create main tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tabs
        self.download_tab = QWidget()
        self.extract_tab = QWidget()
        self.preview_tab = QWidget()
        self.batch_tab = BatchPanel(self, self.config)
        self.validation_tab = ValidationPanel(self, self.config)
        self.dashboard_tab = DashboardPanel(self, self.config)
        self.export_tab = QWidget()
        
        self.tabs.addTab(self.download_tab, "Download PDF")
        self.tabs.addTab(self.extract_tab, "Extract Data")
        self.tabs.addTab(self.preview_tab, "Preview Data")
        self.tabs.addTab(self.batch_tab, "Processamento em Lote")
        self.tabs.addTab(self.validation_tab, "Validação de Dados")
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.export_tab, "Export Data")
        
        # Setup each tab
        self.setup_download_tab()
        self.setup_extract_tab()
        self.setup_preview_tab()
        self.setup_export_tab()
        
        self.show()
    
    def create_toolbar(self):
        """Cria a barra de ferramentas"""
        toolbar = QToolBar("Barra de Ferramentas Principal")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Ação para alternar tema
        theme_action = QAction("Alternar Tema", self)
        theme_action.triggered.connect(self.toggle_theme)
        toolbar.addAction(theme_action)
        
        # Ação para abrir configurações
        settings_action = QAction("Configurações", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)
        
        # Ação para ajuda
        help_action = QAction("Ajuda", self)
        help_action.triggered.connect(self.open_help)
        toolbar.addAction(help_action)
    
    def toggle_theme(self):
        """Alterna entre os temas dark e light"""
        new_theme = self.theme_manager.toggle_theme()
        self.statusBar.showMessage(f"Tema alterado para {new_theme.capitalize()}")
    
    def open_settings(self):
        """Abre a janela de configurações"""
        # Implementação da janela de configurações
        QMessageBox.information(self, "Configurações", "Funcionalidade de configurações a ser implementada.")
    
    def open_help(self):
        """Abre a ajuda do aplicativo"""
        # Implementação da ajuda
        QMessageBox.information(self, "Ajuda", "PDF Data Extractor\n\nEste aplicativo permite baixar, extrair e processar dados de documentos PDF.")
    
    def setup_download_tab(self):
        layout = QVBoxLayout()
        
        # URL input
        url_layout = QHBoxLayout()
        url_label = QLabel("URL:")
        self.url_input = QLineEdit()
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        
        # Web view
        self.web_view = QWebEngineView()
        self.web_view.setUrl(Qt.QUrl("about:blank"))
        
        # Buttons
        button_layout = QHBoxLayout()
        self.load_url_btn = QPushButton("Load URL")
        self.download_pdf_btn = QPushButton("Download PDF")
        self.select_local_pdf_btn = QPushButton("Select Local PDF")
        
        button_layout.addWidget(self.load_url_btn)
        button_layout.addWidget(self.download_pdf_btn)
        button_layout.addWidget(self.select_local_pdf_btn)
        
        # Progress bar
        self.download_progress = QProgressBar()
        self.download_progress.setVisible(False)
        
        # Connect signals
        self.load_url_btn.clicked.connect(self.load_url)
        self.download_pdf_btn.clicked.connect(self.download_pdf)
        self.select_local_pdf_btn.clicked.connect(self.select_local_pdf)
        
        # Add to layout
        layout.addLayout(url_layout)
        layout.addWidget(self.web_view)
        layout.addLayout(button_layout)
        layout.addWidget(self.download_progress)
        
        self.download_tab.setLayout(layout)
    
    def setup_extract_tab(self):
        layout = QVBoxLayout()
        
        # PDF info
        self.pdf_path_label = QLabel("No PDF selected")
        
        # Extraction options
        options_layout = QHBoxLayout()
        
        method_label = QLabel("Extraction Method:")
        self.extraction_method = QComboBox()
        self.extraction_method.addItems(["Text", "Tables", "OCR"])
        
        options_layout.addWidget(method_label)
        options_layout.addWidget(self.extraction_method)
        
        pages_label = QLabel("Pages:")
        self.pages_input = QLineEdit("all")
        options_layout.addWidget(pages_label)
        options_layout.addWidget(self.pages_input)
        
        # Template selection
        template_label = QLabel("Template:")
        self.template_combo = QComboBox()
        self.template_combo.addItem("None")
        self.template_combo.addItem("Auto Detect")
        self.load_templates()
        options_layout.addWidget(template_label)
        options_layout.addWidget(self.template_combo)
        
        # Language options
        language_layout = QHBoxLayout()
        language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Auto Detect", "English", "Portuguese", "Spanish", "French", "German", "Chinese", "Japanese"])
        
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        language_layout.addStretch()
        
        # Extract button
        self.extract_btn = QPushButton("Extract Data")
        self.extract_btn.clicked.connect(self.extract_data)
        
        # Progress bar
        self.extract_progress = QProgressBar()
        self.extract_progress.setVisible(False)
        
        # Add to layout
        layout.addWidget(self.pdf_path_label)
        layout.addLayout(options_layout)
        layout.addLayout(language_layout)
        layout.addWidget(self.extract_btn)
        layout.addWidget(self.extract_progress)
        
        self.extract_tab.setLayout(layout)
    
    def setup_preview_tab(self):
        layout = QVBoxLayout()
        
        # Preview area
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        
        # Table view selector
        table_layout = QHBoxLayout()
        table_label = QLabel("Table:")
        self.table_selector = QComboBox()
        self.table_selector.currentIndexChanged.connect(self.show_selected_table)
        table_layout.addWidget(table_label)
        table_layout.addWidget(self.table_selector)
        
        # Validation button
        self.validate_btn = QPushButton("Validate Data")
        self.validate_btn.clicked.connect(self.validate_data)
        table_layout.addWidget(self.validate_btn)
        
        layout.addLayout(table_layout)
        layout.addWidget(self.preview_text)
        
        self.preview_tab.setLayout(layout)
    
    def setup_export_tab(self):
        layout = QVBoxLayout()
        
        # Export options
        options_layout = QHBoxLayout()
        
        format_label = QLabel("Export Format:")
        self.export_format = QComboBox()
        self.export_format.addItems(["CSV", "JSON", "SQL", "Excel"])
        options_layout.addWidget(format_label)
        options_layout.addWidget(self.export_format)
        
        filename_label = QLabel("Filename:")
        self.filename_input = QLineEdit("extracted_data")
        options_layout.addWidget(filename_label)
        options_layout.addWidget(self.filename_input)
        
        # Database options (for SQL export)
        db_layout = QHBoxLayout()
        db_label = QLabel("Database Connection:")
        self.db_connection = QLineEdit()
        self.db_connection.setPlaceholderText("sqlite:///database.db")
        self.db_connection.setEnabled(False)
        
        db_layout.addWidget(db_label)
        db_layout.addWidget(self.db_connection)
        
        # Connect signal to enable/disable DB connection
        self.export_format.currentTextChanged.connect(self.toggle_db_connection)
        
        # Export button
        self.export_btn = QPushButton("Export Data")
        self.export_btn.clicked.connect(self.export_data)
        
        # Export status
        self.export_status = QLabel("")
        
        # Add to layout
        layout.addLayout(options_layout)
        layout.addLayout(db_layout)
        layout.addWidget(self.export_btn)
        layout.addWidget(self.export_status)
        
        self.export_tab.setLayout(layout)
    
    def toggle_db_connection(self, format_text):
        """Habilita/desabilita campo de conexão com banco de dados"""
        self.db_connection.setEnabled(format_text == "SQL")
    
    def load_templates(self):
        """Load available templates from templates directory"""
        template_dir = self.config['template_dir']
        if os.path.exists(template_dir):
            for file in os.listdir(template_dir):
                if file.endswith('.json'):
                    self.template_combo.addItem(file)
    
    def load_url(self):
        """Load URL in web view"""
        url = self.url_input.text()
        if url:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            self.web_view.setUrl(Qt.QUrl(url))
    
    def download_pdf(self):
        """Download PDF from current URL"""
        url = self.url_input.text()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a URL")
            return
        
        self.download_progress.setVisible(True)
        self.download_progress.setValue(0)
        
        # Create worker thread for downloading
        self.download_thread = WorkerThread('download', self.downloader.download_pdf_direct, url)
        self.download_thread.update_progress.connect(self.update_download_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.error.connect(self.show_error)
        self.download_thread.start()
    
    def update_download_progress(self, value):
        self.download_progress.setValue(value)
    
    def download_finished(self, pdf_path):
        self.download_progress.setVisible(False)
        if pdf_path:
            self.pdf_path = pdf_path
            self.pdf_path_label.setText(f"PDF: {os.path.basename(pdf_path)}")
            
            # Tenta classificar o documento automaticamente
            doc_type, confidence = self.document_classifier.classify_document(pdf_path)
            if doc_type and confidence > 0.6:
                # Seleciona o template correspondente se disponível
                template_name = f"{doc_type}_template.json"
                index = self.template_combo.findText(template_name)
                if index >= 0:
                    self.template_combo.setCurrentIndex(index)
                    self.statusBar.showMessage(f"Documento classificado como {doc_type} com confiança {confidence:.2f}")
                else:
                    self.template_combo.setCurrentIndex(1)  # Auto Detect
            
            QMessageBox.information(self, "Success", f"PDF downloaded successfully to {pdf_path}")
            self.tabs.setCurrentIndex(1)  # Switch to extract tab
        else:
            QMessageBox.warning(self, "Error", "Failed to download PDF")
    
    def select_local_pdf(self):
        """Select a local PDF file"""
        file_dialog = QFileDialog()
        pdf_path, _ = file_dialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        
        if pdf_path:
            self.pdf_path = pdf_path
            self.pdf_path_label.setText(f"PDF: {os.path.basename(pdf_path)}")
            
            # Tenta classificar o documento automaticamente
            doc_type, confidence = self.document_classifier.classify_document(pdf_path)
            if doc_type and confidence > 0.6:
                # Seleciona o template correspondente se disponível
                template_name = f"{doc_type}_template.json"
                index = self.template_combo.findText(template_name)
                if index >= 0:
                    self.template_combo.setCurrentIndex(index)
                    self.statusBar.showMessage(f"Documento classificado como {doc_type} com confiança {confidence:.2f}")
                else:
                    self.template_combo.setCurrentIndex(1)  # Auto Detect
            
            self.tabs.setCurrentIndex(1)  # Switch to extract tab
    
    def extract_data(self):
        """Extract data from PDF"""
        if not hasattr(self, 'pdf_path'):
            QMessageBox.warning(self, "Warning", "Please select or download a PDF first")
            return
        
        method = self.extraction_method.currentText().lower()
        pages = self.pages_input.text()
        
        template = None
        template_name = self.template_combo.currentText()
        
        # Auto detect template
        if template_name == "Auto Detect":
            doc_type, confidence = self.document_classifier.classify_document(self.pdf_path)
            if doc_type and confidence > 0.5:
                template_path = os.path.join(self.config['template_dir'], f"{doc_type}_template.json")
                if os.path.exists(template_path):
                    with open(template_path, 'r') as f:
                        template = json.load(f)
                    self.statusBar.showMessage(f"Usando template para {doc_type} (confiança: {confidence:.2f})")
        elif template_name != "None":
            template_path = os.path.join(self.config['template_dir'], template_name)
            with open(template_path, 'r') as f:
                template = json.load(f)
        
        # Language handling
        language = self.language_combo.currentText()
        if language != "Auto Detect":
            # Set language for extractor
            pass  # Implementado no extrator
        
        self.extract_progress.setVisible(True)
        self.extract_progress.setValue(10)
        
        # Create worker thread for extraction
        self.extract_thread = WorkerThread('extract', self.extractor.extract_data, 
                                          self.pdf_path, method, pages, template)
        self.extract_thread.update_progress.connect(self.update_extract_progress)
        self.extract_thread.finished.connect(self.extraction_finished)
        self.extract_thread.error.connect(self.show_error)
        self.extract_thread.start()
    
    def update_extract_progress(self, value):
        self.extract_progress.setValue(value)
    
    def extraction_finished(self, data):
        self.extract_progress.setVisible(False)
        if data:
            self.extracted_data = data
            
            # Detecta idioma se disponível nos metadados
            if '_metadata' in data and 'language' in data['_metadata']:
                lang_code = data['_metadata']['language']
                lang_name = data['_metadata'].get('language_name', lang_code)
                self.statusBar.showMessage(f"Idioma detectado: {lang_name}")
            
            self.update_preview()
            QMessageBox.information(self, "Success", "Data extracted successfully")
            self.tabs.setCurrentIndex(2)  # Switch to preview tab
        else:
            QMessageBox.warning(self, "Error", "Failed to extract data")
    
    def update_preview(self):
        """Update preview with extracted data"""
        if not hasattr(self, 'extracted_data'):
            return
        
        # Clear previous data
        self.preview_text.clear()
        self.table_selector.clear()
        
        if isinstance(self.extracted_data, dict):
            # Add tables to selector
            for key in self.extracted_data.keys():
                if key != '_metadata':  # Skip metadata
                    self.table_selector.addItem(key)
            
            # Show first table/data
            if self.table_selector.count() > 0:
                self.show_selected_table(0)
        elif isinstance(self.extracted_data, pd.DataFrame):
            self.preview_text.setPlainText(self.extracted_data.to_string())
        else:
            self.preview_text.setPlainText(str(self.extracted_data))
    
    def show_selected_table(self, index):
        """Show selected table in preview"""
        if not hasattr(self, 'extracted_data') or index < 0:
            return
        
        key = self.table_selector.itemText(index)
        if key in self.extracted_data:
            data = self.extracted_data[key]
            if isinstance(data, pd.DataFrame):
                self.preview_text.setPlainText(data.to_string())
            else:
                self.preview_text.setPlainText(str(data))
    
    def validate_data(self):
        """Validate extracted data"""
        if not hasattr(self, 'extracted_data'):
            QMessageBox.warning(self, "Warning", "No data to validate")
            return
        
        # Switch to validation tab
        self.tabs.setCurrentIndex(4)  # Index of validation tab
        
        # Update validation panel with data
        if hasattr(self.validation_tab, 'set_data'):
            self.validation_tab.set_data(self.extracted_data)
    
    def export_data(self):
        """Export extracted data"""
        if not hasattr(self, 'extracted_data'):
            QMessageBox.warning(self, "Warning", "No data to export")
            return
        
        export_format = self.export_format.currentText().lower()
        filename = self.filename_input.text()
        
        if not filename:
            QMessageBox.warning(self, "Warning", "Please enter a filename")
            return
        
        result = None
        
        if export_format == 'csv':
            filename = filename if filename.endswith('.csv') else filename + '.csv'
            result = self.exporter.export_to_csv(self.extracted_data, filename, 
                                               structured=isinstance(self.extracted_data, (pd.DataFrame, dict)))
        elif export_format == 'json':
            filename = filename if filename.endswith('.json') else filename + '.json'
            result = self.exporter.export_to_json(self.extracted_data, filename)
        elif export_format == 'sql':
            filename = filename if filename.endswith('.sql') else filename + '.sql'
            connection_string = self.db_connection.text() if self.db_connection.isEnabled() else None
            result = self.exporter.export_to_sql(self.extracted_data, filename, connection_string)
        elif export_format == 'excel':
            filename = filename if filename.endswith('.xlsx') else filename + '.xlsx'
            result = self.exporter.export_to_excel(self.extracted_data, filename)
        
        if result:
            self.export_status.setText(f"Data exported successfully to {result}")
            QMessageBox.information(self, "Success", f"Data exported successfully to {result}")
            
            # Log the export for analytics
            if hasattr(self.dashboard_tab, 'analytics'):
                log_data = {
                    'pdf_path': getattr(self, 'pdf_path', 'unknown'),
                    'export_path': result,
                    'export_format': export_format,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                }
                
                if '_metadata' in self.extracted_data:
                    log_data.update(self.extracted_data['_metadata'])
                
                self.dashboard_tab.analytics.log_processing_result(log_data)
        else:
            self.export_status.setText("Failed to export data")
            QMessageBox.warning(self, "Error", "Failed to export data")
    
    def show_error(self, error_msg):
        """Show error message"""
        QMessageBox.critical(self, "Error", error_msg)