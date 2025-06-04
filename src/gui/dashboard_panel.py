from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
                           QTabWidget, QSplitter, QFrame)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime, timedelta
from ..core.analytics import DataAnalytics

class DashboardPanel(QWidget):
    """Painel de dashboard analítico para visualização de dados"""
    
    def __init__(self, parent=None, config=None):
        super().__init__(parent)
        self.config = config or {}
        self.analytics = DataAnalytics(self.config.get('analytics_dir', ''))
        self.init_ui()
    
    def init_ui(self):
        """Inicializa a interface do dashboard"""
        layout = QVBoxLayout(self)
        
        # Controles superiores
        controls_layout = QHBoxLayout()
        
        # Seleção de período
        period_label = QLabel("Período:")
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Últimos 7 dias", "Últimos 30 dias", "Este mês", "Este ano", "Todo o período"])
        self.period_combo.currentIndexChanged.connect(self.update_dashboard)
        
        # Seleção de tipo de documento
        doc_type_label = QLabel("Tipo de documento:")
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItem("Todos")
        self.doc_type_combo.currentIndexChanged.connect(self.update_dashboard)
        
        # Botão de atualização
        self.refresh_btn = QPushButton("Atualizar")
        self.refresh_btn.clicked.connect(self.refresh_data)
        
        controls_layout.addWidget(period_label)
        controls_layout.addWidget(self.period_combo)
        controls_layout.addWidget(doc_type_label)
        controls_layout.addWidget(self.doc_type_combo)
        controls_layout.addWidget(self.refresh_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Área principal do dashboard
        self.dashboard_tabs = QTabWidget()
        
        # Tab de visão geral
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # KPIs superiores
        kpi_layout = QHBoxLayout()
        
        # KPI: Total de documentos processados
        self.total_docs_frame = self.create_kpi_frame("Total de Documentos", "0")
        
        # KPI: Taxa de sucesso
        self.success_rate_frame = self.create_kpi_frame("Taxa de Sucesso", "0%")
        
        # KPI: Documentos hoje
        self.today_docs_frame = self.create_kpi_frame("Documentos Hoje", "0")
        
        # KPI: Tempo médio de processamento
        self.avg_time_frame = self.create_kpi_frame("Tempo Médio", "0s")
        
        kpi_layout.addWidget(self.total_docs_frame)
        kpi_layout.addWidget(self.success_rate_frame)
        kpi_layout.addWidget(self.today_docs_frame)
        kpi_layout.addWidget(self.avg_time_frame)
        
        overview_layout.addLayout(kpi_layout)
        
        # Gráficos
        charts_splitter = QSplitter(Qt.Horizontal)
        
        # Gráfico de documentos por dia
        self.docs_by_day_widget = QWidget()
        docs_by_day_layout = QVBoxLayout(self.docs_by_day_widget)
        docs_by_day_layout.addWidget(QLabel("<b>Documentos Processados por Dia</b>"))
        
        self.docs_by_day_figure = plt.figure(figsize=(5, 4))
        self.docs_by_day_canvas = FigureCanvas(self.docs_by_day_figure)
        docs_by_day_layout.addWidget(self.docs_by_day_canvas)
        
        # Gráfico de tipos de documentos
        self.doc_types_widget = QWidget()
        doc_types_layout = QVBoxLayout(self.doc_types_widget)
        doc_types_layout.addWidget(QLabel("<b>Tipos de Documentos</b>"))
        
        self.doc_types_figure = plt.figure(figsize=(5, 4))
        self.doc_types_canvas = FigureCanvas(self.doc_types_figure)
        doc_types_layout.addWidget(self.doc_types_canvas)
        
        charts_splitter.addWidget(self.docs_by_day_widget)
        charts_splitter.addWidget(self.doc_types_widget)
        
        overview_layout.addWidget(charts_splitter)
        
        # Tabela de documentos recentes
        recent_docs_layout = QVBoxLayout()
        recent_docs_layout.addWidget(QLabel("<b>Documentos Recentes</b>"))
        
        self.recent_docs_table = QTableWidget()
        self.recent_docs_table.setColumnCount(5)
        self.recent_docs_table.setHorizontalHeaderLabels(["Nome", "Tipo", "Data", "Status", "Confiança"])
        self.recent_docs_table.horizontalHeader().setStretchLastSection(True)
        
        recent_docs_layout.addWidget(self.recent_docs_table)
        
        overview_layout.addLayout(recent_docs_layout)
        
        # Tab de estatísticas detalhadas
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        # Gráficos detalhados
        detailed_charts_splitter = QSplitter(Qt.Vertical)
        
        # Gráfico de confiança por tipo de documento
        self.confidence_widget = QWidget()
        confidence_layout = QVBoxLayout(self.confidence_widget)
        confidence_layout.addWidget(QLabel("<b>Confiança por Tipo de Documento</b>"))
        
        self.confidence_figure = plt.figure(figsize=(8, 4))
        self.confidence_canvas = FigureCanvas(self.confidence_figure)
        confidence_layout.addWidget(self.confidence_canvas)
        
        # Gráfico de erros comuns
        self.errors_widget = QWidget()
        errors_layout = QVBoxLayout(self.errors_widget)
        errors_layout.addWidget(QLabel("<b>Erros Comuns</b>"))
        
        self.errors_figure = plt.figure(figsize=(8, 4))
        self.errors_canvas = FigureCanvas(self.errors_figure)
        errors_layout.addWidget(self.errors_canvas)
        
        detailed_charts_splitter.addWidget(self.confidence_widget)
        detailed_charts_splitter.addWidget(self.errors_widget)
        
        stats_layout.addWidget(detailed_charts_splitter)
        
        # Adiciona as tabs ao dashboard
        self.dashboard_tabs.addTab(overview_tab, "Visão Geral")
        self.dashboard_tabs.addTab(stats_tab, "Estatísticas Detalhadas")
        
        layout.addWidget(self.dashboard_tabs)
        
        # Carrega dados iniciais
        self.load_initial_data()
    
    def create_kpi_frame(self, title, value):
        """Cria um frame para exibir um KPI"""
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setLineWidth(1)
        frame.setMinimumHeight(100)
        
        layout = QVBoxLayout(frame)
        
        title_label = QLabel(f"<b>{title}</b>")
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(f"<h2>{value}</h2>")
        value_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Armazena o label de valor para atualizações
        frame.value_label = value_label
        
        return frame
    
    def load_initial_data(self):
        """Carrega dados iniciais para o dashboard"""
        # Carrega tipos de documentos disponíveis
        doc_types = self.analytics.get_document_types()
        self.doc_type_combo.clear()
        self.doc_type_combo.addItem("Todos")
        for doc_type in doc_types:
            self.doc_type_combo.addItem(doc_type)
        
        # Atualiza o dashboard
        self.update_dashboard()
    
    def refresh_data(self):
        """Atualiza os dados do dashboard"""
        self.analytics.refresh_data()
        self.load_initial_data()
    
    def update_dashboard(self):
        """Atualiza todos os elementos do dashboard"""
        # Obtém filtros selecionados
        period_idx = self.period_combo.currentIndex()
        doc_type = self.doc_type_combo.currentText()
        if doc_type == "Todos":
            doc_type = None
        
        # Determina o período de filtro
        start_date = None
        end_date = datetime.now()
        
        if period_idx == 0:  # Últimos 7 dias
            start_date = end_date - timedelta(days=7)
        elif period_idx == 1:  # Últimos 30 dias
            start_date = end_date - timedelta(days=30)
        elif period_idx == 2:  # Este mês
            start_date = datetime(end_date.year, end_date.month, 1)
        elif period_idx == 3:  # Este ano
            start_date = datetime(end_date.year, 1, 1)
        
        # Obtém dados filtrados
        data = self.analytics.get_filtered_data(start_date, end_date, doc_type)
        
        # Atualiza KPIs
        self.update_kpis(data)
        
        # Atualiza gráficos
        self.update_charts(data, start_date, end_date)
        
        # Atualiza tabela de documentos recentes
        self.update_recent_docs_table(data)
    
    def update_kpis(self, data):
        """Atualiza os KPIs com base nos dados filtrados"""
        # Total de documentos
        total_docs = len(data)
        self.total_docs_frame.value_label.setText(f"<h2>{total_docs}</h2>")
        
        # Taxa de sucesso
        if total_docs > 0:
            success_count = sum(1 for d in data if d.get('success', False))
            success_rate = (success_count / total_docs) * 100
            self.success_rate_frame.value_label.setText(f"<h2>{success_rate:.1f}%</h2>")
        else:
            self.success_rate_frame.value_label.setText("<h2>0%</h2>")
        
        # Documentos hoje
        today = datetime.now().date()
        today_count = sum(1 for d in data if datetime.fromisoformat(d.get('timestamp', '')).date() == today)
        self.today_docs_frame.value_label.setText(f"<h2>{today_count}</h2>")
        
        # Tempo médio de processamento
        if total_docs > 0:
            processing_times = [d.get('processing_time', 0) for d in data if 'processing_time' in d]
            if processing_times:
                avg_time = sum(processing_times) / len(processing_times)
                if avg_time < 1:
                    time_str = f"{avg_time*1000:.0f}ms"
                elif avg_time < 60:
                    time_str = f"{avg_time:.1f}s"
                else:
                    time_str = f"{avg_time/60:.1f}min"
                self.avg_time_frame.value_label.setText(f"<h2>{time_str}</h2>")
            else:
                self.avg_time_frame.value_label.setText("<h2>-</h2>")
        else:
            self.avg_time_frame.value_label.setText("<h2>-</h2>")
    
    def update_charts(self, data, start_date, end_date):
        """Atualiza os gráficos com base nos dados filtrados"""
        # Gráfico de documentos por dia
        self.docs_by_day_figure.clear()
        ax1 = self.docs_by_day_figure.add_subplot(111)
        
        if data:
            # Agrupa por data
            dates = [datetime.fromisoformat(d.get('timestamp', '')).date() for d in data]
            date_counts = pd.Series(dates).value_counts().sort_index()
            
            # Garante que todas as datas no intervalo estejam representadas
            if start_date:
                all_dates = pd.date_range(start=start_date.date(), end=end_date.date())
                date_counts = date_counts.reindex(all_dates, fill_value=0)
            
            ax1.bar(date_counts.index, date_counts.values, color='royalblue')
            ax1.set_xlabel('Data')
            ax1.set_ylabel('Documentos')
            ax1.tick_params(axis='x', rotation=45)
            self.docs_by_day_figure.tight_layout()
        
        self.docs_by_day_canvas.draw()
        
        # Gráfico de tipos de documentos
        self.doc_types_figure.clear()
        ax2 = self.doc_types_figure.add_subplot(111)
        
        if data:
            # Conta tipos de documentos
            doc_types = [d.get('doc_type', 'Desconhecido') for d in data]
            type_counts = pd.Series(doc_types).value_counts()
            
            colors = plt.cm.viridis(np.linspace(0, 1, len(type_counts)))
            wedges, texts, autotexts = ax2.pie(
                type_counts.values, 
                labels=type_counts.index, 
                autopct='%1.1f%%',
                colors=colors,
                startangle=90
            )
            ax2.axis('equal')
            
            # Ajusta o tamanho da fonte
            for text in texts + autotexts:
                text.set_fontsize(8)
        
        self.doc_types_figure.tight_layout()
        self.doc_types_canvas.draw()
        
        # Gráfico de confiança por tipo de documento
        self.confidence_figure.clear()
        ax3 = self.confidence_figure.add_subplot(111)
        
        if data:
            # Filtra apenas dados com confiança
            confidence_data = [(d.get('doc_type', 'Desconhecido'), d.get('confidence', 0)) 
                              for d in data if 'confidence' in d]
            
            if confidence_data:
                df = pd.DataFrame(confidence_data, columns=['doc_type', 'confidence'])
                avg_confidence = df.groupby('doc_type')['confidence'].mean().sort_values(ascending=False)
                
                ax3.bar(avg_confidence.index, avg_confidence.values, color='teal')
                ax3.set_xlabel('Tipo de Documento')
                ax3.set_ylabel('Confiança Média')
                ax3.set_ylim(0, 1.0)
                ax3.tick_params(axis='x', rotation=45)
        
        self.confidence_figure.tight_layout()
        self.confidence_canvas.draw()
        
        # Gráfico de erros comuns
        self.errors_figure.clear()
        ax4 = self.errors_figure.add_subplot(111)
        
        if data:
            # Extrai erros
            error_data = []
            for d in data:
                if not d.get('success', True) and 'error' in d:
                    error_data.append(d['error'])
            
            if error_data:
                error_counts = pd.Series(error_data).value_counts().head(10)  # Top 10 erros
                
                ax4.barh(error_counts.index, error_counts.values, color='indianred')
                ax4.set_xlabel('Ocorrências')
                ax4.set_ylabel('Erro')
                
                # Limita o tamanho do texto do erro
                labels = [label[:50] + '...' if len(label) > 50 else label for label in error_counts.index]
                ax4.set_yticklabels(labels)
        
        self.errors_figure.tight_layout()
        self.errors_canvas.draw()
    
    def update_recent_docs_table(self, data):
        """Atualiza a tabela de documentos recentes"""
        self.recent_docs_table.setRowCount(0)
        
        if not data:
            return
        
        # Ordena por data (mais recentes primeiro)
        sorted_data = sorted(data, key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Limita a 20 documentos mais recentes
        recent_docs = sorted_data[:20]
        
        self.recent_docs_table.setRowCount(len(recent_docs))
        
        for i, doc in enumerate(recent_docs):
            # Nome do arquivo
            filename = os.path.basename(doc.get('pdf_path', 'N/A'))
            self.recent_docs_table.setItem(i, 0, QTableWidgetItem(filename))
            
            # Tipo de documento
            doc_type = doc.get('doc_type', 'Desconhecido')
            self.recent_docs_table.setItem(i, 1, QTableWidgetItem(doc_type))
            
            # Data
            timestamp = doc.get('timestamp', '')
            if timestamp:
                date_str = datetime.fromisoformat(timestamp).strftime('%d/%m/%Y %H:%M')
            else:
                date_str = 'N/A'
            self.recent_docs_table.setItem(i, 2, QTableWidgetItem(date_str))
            
            # Status
            status_item = QTableWidgetItem("Sucesso" if doc.get('success', False) else "Falha")
            status_item.setForeground(QColor('green' if doc.get('success', False) else 'red'))
            self.recent_docs_table.setItem(i, 3, status_item)
            
            # Confiança
            confidence = doc.get('confidence', 0)
            confidence_item = QTableWidgetItem(f"{confidence:.2f}" if confidence else "N/A")
            self.recent_docs_table.setItem(i, 4, confidence_item)
        
        self.recent_docs_table.resizeColumnsToContents()