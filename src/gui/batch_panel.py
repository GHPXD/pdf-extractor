from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QProgressBar, QFileDialog,
                           QComboBox, QCheckBox, QTableWidget, QTableWidgetItem,
                           QHeaderView, QMessageBox, QGroupBox, QRadioButton,
                           QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
from ..core.batch_processor import BatchProcessor
from ..utils.logger import get_logger

logger = get_logger(__name__)

class BatchWorker(QThread):
    """Thread worker para processamento em lote"""
    progress_updated = pyqtSignal(int, int, str)
    finished = pyqtSignal(list, dict)
    error = pyqtSignal(str)
    
    def __init__(self, batch_processor, input_path, extraction_method, template, export_format):
        super().__init__()
        self.batch_processor = batch_processor
        self.input_path = input_path
        self.extraction_method = extraction_method
        self.template = template
        self.export_format = export_format
    
    def run(self):
        try:
            # Define callback para atualizar progresso
            def progress_callback(processed, total, current_file):
                self.progress_updated.emit(processed, total, current_file)
            
            # Processa o lote
            results = self.batch_processor.process_batch(
                self.input_path, 
                self.extraction_method, 
                self.template, 
                self.export_format,
                progress_callback
            )
            
            # Gera relatório
            report = self.batch_processor.generate_batch_report(results)
            
            # Emite sinal de conclusão
            self.finished.emit(results, report)
            
        except Exception as e:
            logger.error(f"Erro no processamento em lote: {str(e)}")
            self.error.emit(str(e))

class BatchPanel(QWidget):
    """Painel para processamento em lote de PDFs"""
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.batch_processor = BatchProcessor(self.config)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa a interface do painel de lote"""
        layout = QVBoxLayout(self)
        
        # Grupo de seleção de entrada
        input_group = QGroupBox("Fonte de Dados")
        input_layout = QVBoxLayout(input_group)
        
        # Opções de tipo de entrada
        input_type_layout = QHBoxLayout()
        self.input_type_group = QButtonGroup(self)
        
        self.file_radio = QRadioButton("Arquivo Único")
        self.folder_radio = QRadioButton("Pasta")
        self.folder_radio.setChecked(True)
        
        self.input_type_group.addButton(self.file_radio)
        self.input_type_group.addButton(self.folder_radio)
        
        input_type_layout.addWidget(self.file_radio)
        input_type_layout.addWidget(self.folder_radio)
        input_type_layout.addStretch()
        
        input_layout.addLayout(input_type_layout)
        
        # Seleção de caminho
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Caminho:"))
        
        self.path_input = QLineEdit()
        self.path_input.setPlaceholderText("Selecione uma pasta contendo PDFs...")
        
        self.browse_btn = QPushButton("Procurar...")
        self.browse_btn.clicked.connect(self.browse_path)
        
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_btn)
        
        input_layout.addLayout(path_layout)
        
        # Opções de processamento
        options_group = QGroupBox("Opções de Processamento")
        options_layout = QVBoxLayout(options_group)
        
        # Método de extração
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("Método de Extração:"))
        
        self.extraction_method = QComboBox()
        self.extraction_method.addItems(["Automático", "Texto", "Tabelas", "OCR"])
        
        method_layout.addWidget(self.extraction_method)
        options_layout.addLayout(method_layout)
        
        # Template
        template_layout = QHBoxLayout()
        template_layout.addWidget(QLabel("Template:"))
        
        self.template_combo = QComboBox()
        self.template_combo.addItem("Automático")
        self.load_templates()
        
        template_layout.addWidget(self.template_combo)
        options_layout.addLayout(template_layout)
        
        # Formato de exportação
        export_layout = QHBoxLayout()
        export_layout.addWidget(QLabel("Formato de Exportação:"))
        
        self.export_format = QComboBox()
        self.export_format.addItems(["CSV", "JSON", "SQL", "Excel"])
        
        export_layout.addWidget(self.export_format)
        options_layout.addLayout(export_layout)
        
        # Opções adicionais
        additional_layout = QHBoxLayout()
        
        self.auto_detect_cb = QCheckBox("Detecção Automática de Documentos")
        self.auto_detect_cb.setChecked(True)
        
        self.validate_cb = QCheckBox("Validar Dados Extraídos")
        self.validate_cb.setChecked(True)
        
        additional_layout.addWidget(self.auto_detect_cb)
        additional_layout.addWidget(self.validate_cb)
        
        options_layout.addLayout(additional_layout)
        
        # Botões de controle
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Iniciar Processamento")
        self.start_btn.clicked.connect(self.start_batch_processing)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        
        control_layout.addStretch()
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.cancel_btn)
        
        # Barra de progresso
        progress_layout = QVBoxLayout()
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        
        self.progress_label = QLabel("Pronto para iniciar")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        # Tabela de resultados
        results_layout = QVBoxLayout()
        results_layout.addWidget(QLabel("<b>Resultados:</b>"))
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["Arquivo", "Tipo", "Status", "Confiança", "Saída"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        results_layout.addWidget(self.results_table)
        
        # Botões de ação pós-processamento
        post_process_layout = QHBoxLayout()
        
        self.export_report_btn = QPushButton("Exportar Relatório")
        self.export_report_btn.clicked.connect(self.export_report)
        self.export_report_btn.setEnabled(False)
        
        self.view_dashboard_btn = QPushButton("Ver no Dashboard")
        self.view_dashboard_btn.clicked.connect(self.view_in_dashboard)
        self.view_dashboard_btn.setEnabled(False)
        
        post_process_layout.addStretch()
        post_process_layout.addWidget(self.export_report_btn)
        post_process_layout.addWidget(self.view_dashboard_btn)
        
        # Adiciona todos os componentes ao layout principal
        layout.addWidget(input_group)
        layout.addWidget(options_group)
        layout.addLayout(control_layout)
        layout.addLayout(progress_layout)
        layout.addLayout(results_layout)
        layout.addLayout(post_process_layout)
    
    def load_templates(self):
        """Carrega templates disponíveis"""
        template_dir = self.config.get('template_dir')
        if template_dir and os.path.exists(template_dir):
            for file in os.listdir(template_dir):
                if file.endswith('.json'):
                    self.template_combo.addItem(file)
    
    def browse_path(self):
        """Abre diálogo para selecionar arquivo ou pasta"""
        if self.file_radio.isChecked():
            path, _ = QFileDialog.getOpenFileName(
                self, "Selecionar PDF", "", "Arquivos PDF (*.pdf)"
            )
        else:
            path = QFileDialog.getExistingDirectory(
                self, "Selecionar Pasta com PDFs"
            )
        
        if path:
            self.path_input.setText(path)
    
    def start_batch_processing(self):
        """Inicia o processamento em lote"""
        input_path = self.path_input.text()
        
        if not input_path or not os.path.exists(input_path):
            QMessageBox.warning(self, "Caminho Inválido", "Por favor, selecione um caminho válido.")
            return
        
        # Determina o método de extração
        method_text = self.extraction_method.currentText()
        if method_text == "Automático":
            extraction_method = None
        else:
            extraction_method = method_text.lower()
        
        # Determina o template
        template = None
        template_text = self.template_combo.currentText()
        if template_text != "Automático":
            template_path = os.path.join(self.config.get('template_dir', ''), template_text)
            if os.path.exists(template_path):
                try:
                    with open(template_path, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                except Exception as e:
                    logger.error(f"Erro ao carregar template: {str(e)}")
        
        # Determina o formato de exportação
        export_format = self.export_format.currentText().lower()
        
        # Configura o processador de lote
        self.batch_processor.document_classifier.enabled = self.auto_detect_cb.isChecked()
        
        # Atualiza UI para processamento
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando processamento...")
        self.results_table.setRowCount(0)
        
        # Inicia worker thread
        self.batch_worker = BatchWorker(
            self.batch_processor,
            input_path,
            extraction_method,
            template,
            export_format
        )
        self.batch_worker.progress_updated.connect(self.update_progress)
        self.batch_worker.finished.connect(self.processing_finished)
        self.batch_worker.error.connect(self.processing_error)
        self.batch_worker.start()
    
    def cancel_processing(self):
        """Cancela o processamento em lote"""
        if hasattr(self, 'batch_worker') and self.batch_worker.isRunning():
            self.batch_worker.terminate()
            self.batch_worker.wait()
            
            self.progress_label.setText("Processamento cancelado")
            self.start_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
    
    def update_progress(self, processed, total, current_file):
        """Atualiza o progresso do processamento"""
        if total > 0:
            percent = int((processed / total) * 100)
            self.progress_bar.setValue(percent)
        
        self.progress_label.setText(f"Processando {processed} de {total}: {os.path.basename(current_file)}")
    
    def processing_finished(self, results, report):
        """Chamado quando o processamento em lote é concluído"""
        self.progress_bar.setValue(100)
        self.progress_label.setText(f"Processamento concluído: {len(results)} arquivos processados")
        
        # Atualiza UI
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.export_report_btn.setEnabled(True)
        self.view_dashboard_btn.setEnabled(True)
        
        # Armazena resultados e relatório
        self.batch_results = results
        self.batch_report = report
        
        # Preenche tabela de resultados
        self.results_table.setRowCount(len(results))
        
        for i, result in enumerate(results):
            # Arquivo
            filename = os.path.basename(result.get('pdf_path', 'N/A'))
            self.results_table.setItem(i, 0, QTableWidgetItem(filename))
            
            # Tipo de documento
            doc_type = result.get('doc_type', 'Desconhecido')
            self.results_table.setItem(i, 1, QTableWidgetItem(doc_type))
            
            # Status
            success = result.get('success', False)
            status_item = QTableWidgetItem("Sucesso" if success else "Falha")
            status_item.setForeground(Qt.green if success else Qt.red)
            self.results_table.setItem(i, 2, status_item)
            
            # Confiança
            confidence = result.get('confidence', 0)
            self.results_table.setItem(i, 3, QTableWidgetItem(f"{confidence:.2f}" if confidence else "N/A"))
            
            # Arquivo de saída
            export_path = result.get('export_path', 'N/A')
            if export_path:
                export_path = os.path.basename(export_path)
            self.results_table.setItem(i, 4, QTableWidgetItem(export_path))
        
        # Exibe estatísticas
        stats = self.batch_report.get('stats', {})
        if stats:
            success_rate = stats.get('success_rate', 0)
            QMessageBox.information(
                self,
                "Processamento Concluído",
                f"Processamento concluído com sucesso!\n\n"
                f"Total de arquivos: {stats.get('total_files', 0)}\n"
                f"Processados com sucesso: {stats.get('successful', 0)}\n"
                f"Falhas: {stats.get('failed', 0)}\n"
                f"Taxa de sucesso: {success_rate:.1f}%"
            )
    
    def processing_error(self, error_msg):
        """Chamado quando ocorre um erro no processamento em lote"""
        self.progress_label.setText(f"Erro: {error_msg}")
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        QMessageBox.critical(
            self,
            "Erro no Processamento",
            f"Ocorreu um erro durante o processamento em lote:\n\n{error_msg}"
        )
    
    def export_report(self):
        """Exporta o relatório de processamento em lote"""
        if not hasattr(self, 'batch_report') or not self.batch_report:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            "",
            "Arquivos JSON (*.json);;Arquivos CSV (*.csv);;Arquivos Excel (*.xlsx)"
        )
        
        if not file_path:
            return
        
        try:
            # Determina o formato com base na extensão
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.batch_report, f, indent=4)
            elif ext.lower() == '.csv':
                # Converte para DataFrame e salva como CSV
                import pandas as pd
                df = pd.DataFrame(self.batch_results)
                df.to_csv(file_path, index=False)
            elif ext.lower() == '.xlsx':
                # Converte para DataFrame e salva como Excel
                import pandas as pd
                
                with pd.ExcelWriter(file_path) as writer:
                    # Resultados detalhados
                    df_details = pd.DataFrame(self.batch_results)
                    df_details.to_excel(writer, sheet_name='Detalhes', index=False)
                    
                    # Estatísticas
                    if 'stats' in self.batch_report:
                        stats = self.batch_report['stats']
                        df_stats = pd.DataFrame([stats])
                        df_stats.to_excel(writer, sheet_name='Estatísticas', index=False)
            
            QMessageBox.information(
                self,
                "Relatório Exportado",
                f"Relatório exportado com sucesso para:\n{file_path}"
            )
        
        except Exception as e:
            logger.error(f"Erro ao exportar relatório: {str(e)}")
            QMessageBox.critical(
                self,
                "Erro na Exportação",
                f"Ocorreu um erro ao exportar o relatório:\n\n{str(e)}"
            )
    
    def view_in_dashboard(self):
        """Abre a visualização de dashboard com os resultados do lote"""
        # Esta função deve mudar para a aba de dashboard
        # e atualizar o dashboard com os dados do lote atual
        if hasattr(self, 'batch_results') and self.batch_results:
            # Sinal para mudar para a aba de dashboard
            self.parent().parent().setCurrentIndex(3)  # Índice da aba de dashboard
            
            # Atualiza o dashboard (implementação depende da estrutura da aplicação)
            try:
                dashboard_tab = self.parent().parent().widget(3)
                if hasattr(dashboard_tab, 'refresh_data'):
                    dashboard_tab.refresh_data()
            except Exception as e:
                logger.error(f"Erro ao atualizar dashboard: {str(e)}")

