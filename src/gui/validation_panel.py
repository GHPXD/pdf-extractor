from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QTableWidget, QTableWidgetItem,
                           QComboBox, QTextEdit, QGroupBox, QHeaderView,
                           QMessageBox, QSplitter)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import pandas as pd
import json
import os
from ..core.validator import DataValidator
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ValidationPanel(QWidget):
    """Painel para validação de dados extraídos"""
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.validator = DataValidator(self.config.get('schema_dir'))
        self.data = None
        self.validation_results = None
        self.init_ui()
    
    def init_ui(self):
        """Inicializa a interface do painel de validação"""
        layout = QVBoxLayout(self)
        
        # Controles superiores
        controls_layout = QHBoxLayout()
        
        # Seleção de esquema de validação
        schema_label = QLabel("Esquema de Validação:")
        self.schema_combo = QComboBox()
        self.schema_combo.addItem("Auto Detect")
        self.load_schemas()
        
        # Botão de validação
        self.validate_btn = QPushButton("Validar Dados")
        self.validate_btn.clicked.connect(self.validate_data)
        
        controls_layout.addWidget(schema_label)
        controls_layout.addWidget(self.schema_combo)
        controls_layout.addWidget(self.validate_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Área principal dividida
        splitter = QSplitter(Qt.Vertical)
        
        # Área de dados
        data_group = QGroupBox("Dados para Validação")
        data_layout = QVBoxLayout(data_group)
        
        # Seleção de tabela/dados
        table_layout = QHBoxLayout()
        table_label = QLabel("Tabela/Dados:")
        self.data_selector = QComboBox()
        self.data_selector.currentIndexChanged.connect(self.show_selected_data)
        
        table_layout.addWidget(table_label)
        table_layout.addWidget(self.data_selector)
        table_layout.addStretch()
        
        data_layout.addLayout(table_layout)
        
        # Visualização de dados
        self.data_view = QTableWidget()
        self.data_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        data_layout.addWidget(self.data_view)
        
        # Área de resultados de validação
        results_group = QGroupBox("Resultados da Validação")
        results_layout = QVBoxLayout(results_group)
        
        # Status de validação
        self.status_label = QLabel("Nenhuma validação realizada")
        results_layout.addWidget(self.status_label)
        
        # Tabela de erros e avisos
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["Campo", "Valor", "Tipo", "Mensagem"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        results_layout.addWidget(self.results_table)
        
        # Detalhes do erro selecionado
        details_layout = QHBoxLayout()
        details_layout.addWidget(QLabel("Detalhes:"))
        
        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(100)
        
        details_layout.addWidget(self.details_text)
        results_layout.addLayout(details_layout)
        
        # Botões de ação
        action_layout = QHBoxLayout()
        
        self.export_results_btn = QPushButton("Exportar Resultados")
        self.export_results_btn.clicked.connect(self.export_validation_results)
        self.export_results_btn.setEnabled(False)
        
        self.fix_data_btn = QPushButton("Corrigir Dados")
        self.fix_data_btn.clicked.connect(self.fix_data)
        self.fix_data_btn.setEnabled(False)
        
        action_layout.addStretch()
        action_layout.addWidget(self.export_results_btn)
        action_layout.addWidget(self.fix_data_btn)
        
        results_layout.addLayout(action_layout)
        
        # Adiciona grupos ao splitter
        splitter.addWidget(data_group)
        splitter.addWidget(results_group)
        
        # Configura proporções iniciais
        splitter.setSizes([300, 400])
        
        layout.addWidget(splitter)
    
    def load_schemas(self):
        """Carrega esquemas de validação disponíveis"""
        schema_dir = self.config.get('schema_dir')
        if schema_dir and os.path.exists(schema_dir):
            for file in os.listdir(schema_dir):
                if file.endswith('.json'):
                    schema_name = os.path.splitext(file)[0]
                    self.schema_combo.addItem(schema_name)
    
    def set_data(self, data):
        """Define os dados para validação"""
        self.data = data
        self.update_data_view()
    
    def update_data_view(self):
        """Atualiza a visualização de dados"""
        if not self.data:
            return
        
        # Limpa seletor de dados
        self.data_selector.clear()
        
        if isinstance(self.data, dict):
            # Adiciona cada chave ao seletor
            for key in self.data.keys():
                if key != '_metadata':  # Ignora metadados
                    self.data_selector.addItem(key)
            
            # Mostra o primeiro item
            if self.data_selector.count() > 0:
                self.show_selected_data(0)
        elif isinstance(self.data, pd.DataFrame):
            self.data_selector.addItem("DataFrame")
            self.show_dataframe(self.data)
        else:
            self.data_selector.addItem("Dados")
            self.show_text_data(str(self.data))
    
    def show_selected_data(self, index):
        """Mostra os dados selecionados"""
        if not self.data or index < 0 or self.data_selector.count() == 0:
            return
        
        key = self.data_selector.itemText(index)
        
        if isinstance(self.data, dict) and key in self.data:
            value = self.data[key]
            
            if isinstance(value, pd.DataFrame):
                self.show_dataframe(value)
            elif isinstance(value, dict):
                self.show_dict_data(value)
            else:
                self.show_text_data(str(value))
    
    def show_dataframe(self, df):
        """Mostra um DataFrame na tabela de visualização"""
        self.data_view.clear()
        
        if df.empty:
            self.data_view.setRowCount(0)
            self.data_view.setColumnCount(0)
            return
        
        # Configura tabela
        self.data_view.setRowCount(len(df))
        self.data_view.setColumnCount(len(df.columns))
        self.data_view.setHorizontalHeaderLabels(df.columns)
        
        # Preenche dados
        for i, (_, row) in enumerate(df.iterrows()):
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.data_view.setItem(i, j, item)
    
    def show_dict_data(self, data):
        """Mostra um dicionário na tabela de visualização"""
        self.data_view.clear()
        
        if not data:
            self.data_view.setRowCount(0)
            self.data_view.setColumnCount(0)
            return
        
        # Configura tabela
        self.data_view.setRowCount(len(data))
        self.data_view.setColumnCount(2)
        self.data_view.setHorizontalHeaderLabels(["Campo", "Valor"])
        
        # Preenche dados
        for i, (key, value) in enumerate(data.items()):
            key_item = QTableWidgetItem(str(key))
            value_item = QTableWidgetItem(str(value))
            
            self.data_view.setItem(i, 0, key_item)
            self.data_view.setItem(i, 1, value_item)
    
    def show_text_data(self, text):
        """Mostra texto na tabela de visualização"""
        self.data_view.clear()
        self.data_view.setRowCount(1)
        self.data_view.setColumnCount(1)
        self.data_view.setHorizontalHeaderLabels(["Conteúdo"])
        
        item = QTableWidgetItem(text)
        self.data_view.setItem(0, 0, item)
    
    def validate_data(self):
        """Valida os dados com o esquema selecionado"""
        if not self.data:
            QMessageBox.warning(self, "Aviso", "Nenhum dado para validar")
            return
        
        # Obtém dados para validação
        data_to_validate = self.data
        current_key = self.data_selector.currentText()
        
        if isinstance(self.data, dict) and current_key in self.data:
            data_to_validate = self.data[current_key]
        
        # Determina o esquema a ser usado
        schema_name = self.schema_combo.currentText()
        if schema_name == "Auto Detect":
            # Tenta detectar o esquema apropriado
            if '_metadata' in self.data and 'document_type' in self.data['_metadata']:
                doc_type = self.data['_metadata']['document_type']
                schema_name = f"{doc_type}_schema"
                
                # Verifica se o esquema existe
                index = self.schema_combo.findText(schema_name)
                if index < 0:
                    schema_name = None
        
        if schema_name == "Auto Detect" or not schema_name:
            QMessageBox.warning(self, "Aviso", "Não foi possível detectar automaticamente o esquema. Por favor, selecione um esquema manualmente.")
            return
        
        # Executa a validação
        try:
            valid, results = self.validator.validate_data(data_to_validate, schema_name)
            self.validation_results = results
            
            # Atualiza interface com resultados
            self.update_validation_results(valid, results)
            
            # Habilita botões de ação
            self.export_results_btn.setEnabled(True)
            self.fix_data_btn.setEnabled(not valid)  # Só habilita se houver erros
            
        except Exception as e:
            logger.error(f"Erro na validação: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao validar dados: {str(e)}")
    
    def update_validation_results(self, valid, results):
        """Atualiza a interface com os resultados da validação"""
        # Atualiza label de status
        if valid:
            self.status_label.setText("✅ Validação bem-sucedida! Os dados estão corretos.")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText("❌ Validação falhou! Há erros nos dados.")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Limpa tabela de resultados
        self.results_table.setRowCount(0)
        
        # Adiciona erros à tabela
        errors = results.get('errors', {})
        warnings = results.get('warnings', {})
        
        row = 0
        
        # Adiciona erros
        for field, message in errors.items():
            self.results_table.insertRow(row)
            
            # Obtém o valor do campo
            value = self.get_field_value(field)
            
            self.results_table.setItem(row, 0, QTableWidgetItem(field))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
            type_item = QTableWidgetItem("Erro")
            type_item.setForeground(QColor('red'))
            self.results_table.setItem(row, 2, type_item)
            
            self.results_table.setItem(row, 3, QTableWidgetItem(message))
            
            row += 1
        
        # Adiciona avisos
        for field, message in warnings.items():
            self.results_table.insertRow(row)
            
            # Obtém o valor do campo
            value = self.get_field_value(field)
            
            self.results_table.setItem(row, 0, QTableWidgetItem(field))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(value)))
            
            type_item = QTableWidgetItem("Aviso")
            type_item.setForeground(QColor('orange'))
            self.results_table.setItem(row, 2, type_item)
            
            self.results_table.setItem(row, 3, QTableWidgetItem(message))
            
            row += 1
        
        # Conecta seleção de linha para mostrar detalhes
        self.results_table.itemSelectionChanged.connect(self.show_error_details)
    
    def get_field_value(self, field):
        """Obtém o valor de um campo dos dados atuais"""
        data_to_check = self.data
        current_key = self.data_selector.currentText()
        
        if isinstance(self.data, dict) and current_key in self.data:
            data_to_check = self.data[current_key]
        
        if isinstance(data_to_check, dict) and field in data_to_check:
            return data_to_check[field]
        elif isinstance(data_to_check, pd.DataFrame) and field in data_to_check.columns:
            return data_to_check[field].tolist()
        
        return "N/A"
    
    def show_error_details(self):
        """Mostra detalhes do erro/aviso selecionado"""
        selected_items = self.results_table.selectedItems()
        if not selected_items:
            return
        
        row = selected_items[0].row()
        
        field = self.results_table.item(row, 0).text()
        value = self.results_table.item(row, 1).text()
        error_type = self.results_table.item(row, 2).text()
        message = self.results_table.item(row, 3).text()
        
        details = f"Campo: {field}\n"
        details += f"Valor: {value}\n"
        details += f"Tipo: {error_type}\n"
        details += f"Mensagem: {message}\n\n"
        
        # Adiciona sugestões de correção
        if error_type == "Erro":
            details += "Sugestões de correção:\n"
            
            if "obrigatório" in message.lower():
                details += "- Este campo é obrigatório e deve ser preenchido.\n"
            elif "inválido" in message.lower():
                if "CPF" in field or "cpf" in field:
                    details += "- O CPF deve ter 11 dígitos no formato 000.000.000-00.\n"
                elif "CNPJ" in field or "cnpj" in field:
                    details += "- O CNPJ deve ter 14 dígitos no formato 00.000.000/0000-00.\n"
                elif "email" in field.lower():
                    details += "- O email deve estar no formato usuario@dominio.com.\n"
                elif "data" in field.lower():
                    details += "- A data deve estar em um formato válido (ex: DD/MM/AAAA).\n"
            elif "deve ser" in message.lower():
                details += "- Verifique o tipo de dado esperado para este campo.\n"
        
        self.details_text.setText(details)
    
    def export_validation_results(self):
        """Exporta os resultados da validação"""
        if not self.validation_results:
            return
        
        from PyQt5.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Resultados de Validação",
            "",
            "Arquivos JSON (*.json);;Arquivos CSV (*.csv);;Arquivos de Texto (*.txt)"
        )
        
        if not file_path:
            return
        
        try:
            _, ext = os.path.splitext(file_path)
            
            if ext.lower() == '.json':
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.validation_results, f, indent=4, ensure_ascii=False)
            elif ext.lower() == '.csv':
                # Converte para formato tabular
                rows = []
                
                for field, message in self.validation_results.get('errors', {}).items():
                    rows.append({
                        'field': field,
                        'type': 'error',
                        'message': message
                    })
                
                for field, message in self.validation_results.get('warnings', {}).items():
                    rows.append({
                        'field': field,
                        'type': 'warning',
                        'message': message
                    })
                
                df = pd.DataFrame(rows)
                df.to_csv(file_path, index=False)
            else:  # .txt
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"Resultados da Validação\n")
                    f.write(f"======================\n\n")
                    
                    f.write(f"Status: {'Válido' if self.validation_results.get('valid', False) else 'Inválido'}\n\n")
                    
                    if self.validation_results.get('errors'):
                        f.write("Erros:\n")
                        for field, message in self.validation_results['errors'].items():
                            f.write(f"- {field}: {message}\n")
                        f.write("\n")
                    
                    if self.validation_results.get('warnings'):
                        f.write("Avisos:\n")
                        for field, message in self.validation_results['warnings'].items():
                            f.write(f"- {field}: {message}\n")
            
            QMessageBox.information(
                self,
                "Exportação Concluída",
                f"Resultados da validação exportados para {file_path}"
            )
        
        except Exception as e:
            logger.error(f"Erro ao exportar resultados: {str(e)}")
            QMessageBox.critical(
                self,
                "Erro na Exportação",
                f"Ocorreu um erro ao exportar os resultados: {str(e)}"
            )
    
    def fix_data(self):
        """Tenta corrigir automaticamente os dados com problemas"""
        if not self.validation_results or not self.data:
            return
        
        data_to_fix = self.data
        current_key = self.data_selector.currentText()
        
        if isinstance(self.data, dict) and current_key in self.data:
            data_to_fix = self.data[current_key]
        
        # Verifica se os dados podem ser corrigidos
        if not isinstance(data_to_fix, (dict, pd.DataFrame)):
            QMessageBox.warning(
                self,
                "Correção Não Suportada",
                "A correção automática só é suportada para dicionários e DataFrames."
            )
            return
        
        # Tenta corrigir os erros
        fixed_count = 0
        
        if isinstance(data_to_fix, dict):
            # Corrige dicionário
            for field, message in self.validation_results.get('errors', {}).items():
                if field in data_to_fix:
                    fixed = self.try_fix_value(field, data_to_fix[field], message)
                    if fixed is not None:
                        data_to_fix[field] = fixed
                        fixed_count += 1
        
        elif isinstance(data_to_fix, pd.DataFrame):
            # Corrige DataFrame
            for field, message in self.validation_results.get('errors', {}).items():
                if field in data_to_fix.columns:
                    # Tenta corrigir cada valor na coluna
                    for i, value in enumerate(data_to_fix[field]):
                        fixed = self.try_fix_value(field, value, message)
                        if fixed is not None:
                            data_to_fix.at[i, field] = fixed
                            fixed_count += 1
        
        # Atualiza a visualização
        if isinstance(data_to_fix, pd.DataFrame):
            self.show_dataframe(data_to_fix)
        elif isinstance(data_to_fix, dict):
            self.show_dict_data(data_to_fix)
        
        # Executa nova validação
        if fixed_count > 0:
            QMessageBox.information(
                self,
                "Correção Automática",
                f"Foram corrigidos {fixed_count} problemas. Executando nova validação."
            )
            self.validate_data()
        else:
            QMessageBox.information(
                self,
                "Correção Automática",
                "Não foi possível corrigir automaticamente os problemas encontrados."
            )
    
    def try_fix_value(self, field, value, error_message):
        """Tenta corrigir um valor com base no erro"""
        # Valor vazio para campo obrigatório
        if "obrigatório" in error_message.lower():
            if field.lower() in ["data", "date"]:
                from datetime import datetime
                return datetime.now().strftime("%d/%m/%Y")
            elif field.lower() in ["valor", "total", "price", "amount"]:
                return 0.0
            elif field.lower() in ["quantidade", "quantity"]:
                return 1
            elif field.lower() in ["nome", "name", "description"]:
                return "N/A"
            return None  # Não sabe como corrigir
        
        # Formato inválido
        if "CPF" in error_message or "cpf" in field.lower():
            # Tenta corrigir CPF
            if isinstance(value, str):
                # Remove caracteres não numéricos
                digits = ''.join(filter(str.isdigit, value))
                if len(digits) == 11:
                    return f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            return None
        
        if "CNPJ" in error_message or "cnpj" in field.lower():
            # Tenta corrigir CNPJ
            if isinstance(value, str):
                # Remove caracteres não numéricos
                digits = ''.join(filter(str.isdigit, value))
                if len(digits) == 14:
                    return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
            return None
        
        if "email" in error_message.lower() or "email" in field.lower():
            # Tenta corrigir email
            if isinstance(value, str) and "@" not in value:
                return f"{value.lower().replace(' ', '')}@example.com"
            return None
        
        if "data" in error_message.lower() or "date" in field.lower():
            # Tenta corrigir data
            if isinstance(value, str):
                # Tenta converter para formato padrão
                import re
                digits = re.findall(r'\d+', value)
                if len(digits) >= 3:
                    day, month, year = digits[:3]
                    # Garante que o ano tenha 4 dígitos
                    if len(year) == 2:
                        year = "20" + year
                    # Garante que dia e mês tenham 2 dígitos
                    day = day.zfill(2)
                    month = month.zfill(2)
                    return f"{day}/{month}/{year}"
            return None
        
        # Tipo incorreto
        if "deve ser um número" in error_message.lower():
            # Tenta converter para número
            try:
                if isinstance(value, str):
                    # Tenta converter string para número
                    return float(value.replace(',', '.'))
                return 0.0
            except:
                return 0.0
        
        if "deve ser um inteiro" in error_message.lower():
            # Tenta converter para inteiro
            try:
                if isinstance(value, str):
                    # Tenta converter string para inteiro
                    return int(float(value.replace(',', '.')))
                elif isinstance(value, float):
                    return int(value)
                return 0
            except:
                return 0
        
        if "deve ser uma string" in error_message.lower():
            # Tenta converter para string
            return str(value)
        
        if "deve ser um booleano" in error_message.lower():
            # Tenta converter para booleano
            if isinstance(value, str):
                value = value.lower()
                if value in ["true", "yes", "sim", "1", "verdadeiro"]:
                    return True
                elif value in ["false", "no", "não", "0", "falso"]:
                    return False
            return False
        
        # Não conseguiu corrigir
        return None

