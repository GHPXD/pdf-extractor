import os
import json
import glob
from datetime import datetime
import pandas as pd
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DataAnalytics:
    """Analisa dados de documentos processados para o dashboard"""
    
    def __init__(self, analytics_dir):
        self.analytics_dir = analytics_dir
        os.makedirs(analytics_dir, exist_ok=True)
        self.data = []
        self.load_data()
    
    def load_data(self):
        """Carrega dados de análise do diretório de analytics"""
        try:
            self.data = []
            
            # Procura por arquivos de log de processamento
            log_files = glob.glob(os.path.join(self.analytics_dir, "*.json"))
            
            for log_file in log_files:
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                        
                        # Verifica se é um log individual ou um lote
                        if 'details' in log_data:
                            # Log de lote
                            for item in log_data.get('details', []):
                                if isinstance(item, dict):
                                    self.data.append(item)
                        elif isinstance(log_data, dict):
                            # Log individual
                            self.data.append(log_data)
                except Exception as e:
                    logger.error(f"Erro ao carregar arquivo de log {log_file}: {str(e)}")
            
            logger.info(f"Carregados dados de {len(self.data)} documentos processados")
        except Exception as e:
            logger.error(f"Erro ao carregar dados de análise: {str(e)}")
    
    def refresh_data(self):
        """Atualiza os dados de análise"""
        self.load_data()
    
    def get_document_types(self):
        """Retorna a lista de tipos de documentos únicos"""
        doc_types = set()
        for item in self.data:
            doc_type = item.get('doc_type')
            if doc_type:
                doc_types.add(doc_type)
        return sorted(list(doc_types))
    
    def get_filtered_data(self, start_date=None, end_date=None, doc_type=None):
        """Retorna dados filtrados por período e tipo de documento"""
        filtered_data = []
        
        for item in self.data:
            # Filtra por data
            include = True
            
            if 'timestamp' in item:
                try:
                    item_date = datetime.fromisoformat(item['timestamp'])
                    if start_date and item_date < start_date:
                        include = False
                    if end_date and item_date > end_date:
                        include = False
                except (ValueError, TypeError):
                    pass
            
            # Filtra por tipo de documento
            if include and doc_type and item.get('doc_type') != doc_type:
                include = False
            
            if include:
                filtered_data.append(item)
        
        return filtered_data
    
    def get_success_rate(self, start_date=None, end_date=None, doc_type=None):
        """Calcula a taxa de sucesso dos documentos processados"""
        data = self.get_filtered_data(start_date, end_date, doc_type)
        
        if not data:
            return 0
        
        success_count = sum(1 for item in data if item.get('success', False))
        return (success_count / len(data)) * 100
    
    def get_avg_confidence(self, start_date=None, end_date=None, doc_type=None):
        """Calcula a confiança média dos documentos processados"""
        data = self.get_filtered_data(start_date, end_date, doc_type)
        
        confidence_values = [item.get('confidence', 0) for item in data if 'confidence' in item]
        
        if not confidence_values:
            return 0
        
        return sum(confidence_values) / len(confidence_values)
    
    def get_document_count_by_date(self, start_date=None, end_date=None, doc_type=None):
        """Retorna contagem de documentos agrupados por data"""
        data = self.get_filtered_data(start_date, end_date, doc_type)
        
        date_counts = {}
        for item in data:
            if 'timestamp' in item:
                try:
                    date_str = datetime.fromisoformat(item['timestamp']).strftime('%Y-%m-%d')
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1
                except (ValueError, TypeError):
                    pass
        
        # Converte para DataFrame
        if date_counts:
            df = pd.DataFrame({
                'date': list(date_counts.keys()),
                'count': list(date_counts.values())
            })
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            return df
        
        return pd.DataFrame(columns=['date', 'count'])
    
    def get_document_count_by_type(self, start_date=None, end_date=None):
        """Retorna contagem de documentos agrupados por tipo"""
        data = self.get_filtered_data(start_date, end_date)
        
        type_counts = {}
        for item in data:
            doc_type = item.get('doc_type', 'Desconhecido')
            type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
        
        # Converte para DataFrame
        if type_counts:
            df = pd.DataFrame({
                'doc_type': list(type_counts.keys()),
                'count': list(type_counts.values())
            })
            df = df.sort_values('count', ascending=False)
            return df
        
        return pd.DataFrame(columns=['doc_type', 'count'])
    
    def log_processing_result(self, result):
        """Registra o resultado de um processamento para análise futura"""
        try:
            if not result:
                return
            
            # Adiciona timestamp se não existir
            if 'timestamp' not in result:
                result['timestamp'] = datetime.now().isoformat()
            
            # Gera nome de arquivo único
            filename = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(result)}.json"
            file_path = os.path.join(self.analytics_dir, filename)
            
            # Salva o resultado
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=4)
            
            # Adiciona aos dados em memória
            self.data.append(result)
            
            logger.info(f"Resultado de processamento registrado: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erro ao registrar resultado de processamento: {str(e)}")
            return None
    
    def log_batch_results(self, results, stats=None):
        """Registra os resultados de um processamento em lote"""
        try:
            if not results:
                return
            
            # Gera nome de arquivo único
            filename = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = os.path.join(self.analytics_dir, filename)
            
            # Prepara dados para salvar
            data_to_save = {
                'timestamp': datetime.now().isoformat(),
                'details': results
            }
            
            # Adiciona estatísticas se fornecidas
            if stats:
                data_to_save['stats'] = stats
            
            # Salva os resultados
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=4)
            
            # Adiciona aos dados em memória
            for result in results:
                if isinstance(result, dict):
                    self.data.append(result)
            
            logger.info(f"Resultados de lote registrados: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Erro ao registrar resultados de lote: {str(e)}")
            return None