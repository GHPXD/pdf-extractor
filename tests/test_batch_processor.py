# test_batch_processor.py
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.core.batch_processor import BatchProcessor

class TestBatchProcessor(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            'download_dir': os.path.join(self.temp_dir, 'downloads'),
            'export_dir': os.path.join(self.temp_dir, 'exports'),
            'template_dir': os.path.join(self.temp_dir, 'templates'),
            'patterns_dir': os.path.join(self.temp_dir, 'patterns'),
            'max_workers': 2
        }
        
        # Criar diretórios necessários
        for dir_path in [self.config['download_dir'], self.config['export_dir'], 
                         self.config['template_dir'], self.config['patterns_dir']]:
            os.makedirs(dir_path, exist_ok=True)
        
        # Criar PDFs de teste
        self.create_test_pdfs()
        
        self.batch_processor = BatchProcessor(self.config)

    def tearDown(self):
        # Limpar arquivos temporários
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(self.temp_dir)

    def create_test_pdfs(self):
        # Criar alguns PDFs de teste
        for i in range(3):
            pdf_path = os.path.join(self.config['download_dir'], f"test_{i}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(b"%PDF-1.5\nTest content")

    def test_find_pdfs(self):
        # Testar encontrar PDFs em um diretório
        pdfs = self.batch_processor.find_pdfs(self.config['download_dir'])
        self.assertEqual(len(pdfs), 3)
        
        # Testar encontrar um único PDF
        single_pdf = os.path.join(self.config['download_dir'], "test_0.pdf")
        pdfs = self.batch_processor.find_pdfs(single_pdf)
        self.assertEqual(len(pdfs), 1)
        self.assertEqual(pdfs[0], single_pdf)
        
        # Testar com caminho inválido
        pdfs = self.batch_processor.find_pdfs("invalid_path")
        self.assertEqual(len(pdfs), 0)

    @patch('src.core.extractor.PDFExtractor.extract_data')
    @patch('src.core.document_classifier.DocumentClassifier.classify_document')
    def test_process_pdf(self, mock_classify, mock_extract):
        # Configurar mocks
        mock_classify.return_value = ("invoice", 0.8)
        mock_extract.return_value = {"page_1": "Extracted text"}
        
        # Testar processamento de um único PDF
        pdf_path = os.path.join(self.config['download_dir'], "test_0.pdf")
        result = self.batch_processor.process_pdf(pdf_path, "text", None, "csv")
        
        self.assertIsNotNone(result)
        self.assertEqual(result['pdf_path'], pdf_path)
        self.assertEqual(result['doc_type'], "invoice")
        self.assertEqual(result['confidence'], 0.8)
        mock_classify.assert_called_once_with(pdf_path)
        mock_extract.assert_called_once()

    @patch('src.core.batch_processor.BatchProcessor.process_pdf')
    def test_process_batch(self, mock_process_pdf):
        # Configurar mock
        mock_process_pdf.return_value = {
            'pdf_path': 'test.pdf',
            'export_path': 'test.csv',
            'doc_type': 'invoice',
            'confidence': 0.8,
            'success': True
        }
        
        # Testar processamento em lote
        results = self.batch_processor.process_batch(self.config['download_dir'], "text", None, "csv")
        
        self.assertEqual(len(results), 3)
        mock_process_pdf.assert_called()
        self.assertEqual(mock_process_pdf.call_count, 3)

    def test_generate_batch_report(self):
        # Dados de teste
        results = [
            {
                'pdf_path': os.path.join(self.config['download_dir'], "test_0.pdf"),
                'export_path': os.path.join(self.config['export_dir'], "test_0.csv"),
                'doc_type': 'invoice',
                'confidence': 0.8,
                'success': True
            },
            {
                'pdf_path': os.path.join(self.config['download_dir'], "test_1.pdf"),
                'export_path': os.path.join(self.config['export_dir'], "test_1.csv"),
                'doc_type': 'receipt',
                'confidence': 0.7,
                'success': True
            },
            {
                'pdf_path': os.path.join(self.config['download_dir'], "test_2.pdf"),
                'export_path': None,
                'doc_type': None,
                'confidence': 0.0,
                'success': False
            }
        ]
        
        # Gerar relatório
        report = self.batch_processor.generate_batch_report(results)
        
        self.assertIsNotNone(report)
        self.assertIn('stats', report)
        self.assertEqual(report['stats']['total_files'], 3)
        self.assertEqual(report['stats']['successful'], 2)
        self.assertEqual(report['stats']['failed'], 1)
        self.assertAlmostEqual(report['stats']['success_rate'], 66.66666666666666)
        self.assertIn('details', report)

if __name__ == "__main__":
    unittest.main()