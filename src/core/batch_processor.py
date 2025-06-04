import os
import glob
import concurrent.futures
import time
from tqdm import tqdm
from ..utils.logger import get_logger
from .document_classifier import DocumentClassifier
from .extractor import PDFExtractor
from .exporter import DataExporter

logger = get_logger(__name__)

class BatchProcessor:
    """Processa múltiplos PDFs em lote"""
    
    def __init__(self, config):
        self.config = config
        self.document_classifier = DocumentClassifier(
            model_path=config.get('classifier_model_path'),
            patterns_dir=config.get('patterns_dir')
        )
        self.extractor = PDFExtractor()
        self.exporter = DataExporter(config.get('export_dir'))
        self.max_workers = config.get('max_workers', 4)
    
    def find_pdfs(self, input_path):
        """Encontra todos os PDFs em um diretório ou retorna um único arquivo"""
        if os.path.isdir(input_path):
            return glob.glob(os.path.join(input_path, "**", "*.pdf"), recursive=True)
        elif os.path.isfile(input_path) and input_path.lower().endswith('.pdf'):
            return [input_path]
        return []
    
    def process_pdf(self, pdf_path, extraction_method=None, template=None, export_format='csv'):
        """Processa um único PDF"""
        try:
            logger.info(f"Processando arquivo: {pdf_path}")
            
            # Classifica o documento se não houver template específico
            if not template:
                doc_type, confidence = self.document_classifier.classify_document(pdf_path)
                if doc_type and confidence > 0.5:
                    logger.info(f"Documento classificado como {doc_type} com confiança {confidence:.2f}")
                    # Carrega o template correspondente
                    template_path = os.path.join(self.config.get('template_dir', ''), f"{doc_type}_template.json")
                    if os.path.exists(template_path):
                        with open(template_path, 'r') as f:
                            template = json.load(f)
            
            # Determina o método de extração se não for especificado
            if not extraction_method:
                extraction_method = 'text'  # Método padrão
            
            # Extrai dados do PDF
            extracted_data = self.extractor.extract_data(pdf_path, extraction_method, 'all', template)
            
            if not extracted_data:
                logger.warning(f"Nenhum dado extraído de {pdf_path}")
                return None
            
            # Exporta os dados
            filename = os.path.splitext(os.path.basename(pdf_path))[0] + f".{export_format}"
            
            if export_format == 'csv':
                result = self.exporter.export_to_csv(extracted_data, filename)
            elif export_format == 'json':
                result = self.exporter.export_to_json(extracted_data, filename)
            elif export_format == 'sql':
                result = self.exporter.export_to_sql(extracted_data, filename)
            else:
                logger.error(f"Formato de exportação não suportado: {export_format}")
                return None
            
            return {
                'pdf_path': pdf_path,
                'export_path': result,
                'doc_type': doc_type if 'doc_type' in locals() else None,
                'confidence': confidence if 'confidence' in locals() else None
            }
        
        except Exception as e:
            logger.error(f"Erro ao processar {pdf_path}: {str(e)}")
            return None
    
    def process_batch(self, input_path, extraction_method=None, template=None, export_format='csv', callback=None):
        """Processa um lote de PDFs"""
        pdf_files = self.find_pdfs(input_path)
        
        if not pdf_files:
            logger.warning(f"Nenhum arquivo PDF encontrado em {input_path}")
            return []
        
        logger.info(f"Iniciando processamento em lote de {len(pdf_files)} arquivos")
        results = []
        
        # Configuração da barra de progresso
        progress_bar = tqdm(total=len(pdf_files), desc="Processando PDFs", unit="arquivo")
        
        # Processamento paralelo
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submete os trabalhos
            future_to_pdf = {
                executor.submit(self.process_pdf, pdf, extraction_method, template, export_format): pdf 
                for pdf in pdf_files
            }
            
            # Processa os resultados à medida que são concluídos
            for future in concurrent.futures.as_completed(future_to_pdf):
                pdf = future_to_pdf[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    
                    # Atualiza progresso
                    progress_bar.update(1)
                    
                    # Chama callback se fornecido
                    if callback:
                        callback(len(results), len(pdf_files), pdf)
                        
                except Exception as e:
                    logger.error(f"Erro ao processar {pdf}: {str(e)}")
                    progress_bar.update(1)
        
        progress_bar.close()
        logger.info(f"Processamento em lote concluído. {len(results)} de {len(pdf_files)} arquivos processados com sucesso.")
        
        return results
    
    def generate_batch_report(self, results, output_path=None):
        """Gera um relatório do processamento em lote"""
        if not results:
            return None
        
        import pandas as pd
        
        # Cria DataFrame com os resultados
        df = pd.DataFrame(results)
        
        # Adiciona informações adicionais
        df['success'] = df['export_path'].notnull()
        df['filename'] = df['pdf_path'].apply(os.path.basename)
        
        # Gera estatísticas
        stats = {
            'total_files': len(results),
            'successful': df['success'].sum(),
            'failed': (~df['success']).sum(),
            'success_rate': df['success'].mean() * 100,
            'document_types': df['doc_type'].value_counts().to_dict() if 'doc_type' in df.columns else {},
            'avg_confidence': df['confidence'].mean() if 'confidence' in df.columns else None,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Exporta relatório se caminho for fornecido
        if output_path:
            report_path = os.path.join(output_path, f"batch_report_{time.strftime('%Y%m%d_%H%M%S')}.json")
            with open(report_path, 'w') as f:
                json.dump({
                    'stats': stats,
                    'details': df.to_dict(orient='records')
                }, f, indent=4)
            
            logger.info(f"Relatório de lote salvo em {report_path}")
            return report_path
        
        return {
            'stats': stats,
            'details': df.to_dict(orient='records')
        }